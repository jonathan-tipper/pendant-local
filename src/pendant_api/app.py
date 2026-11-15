from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import json
import hashlib
import hmac
from pathlib import Path, PurePosixPath
import secrets
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from filelock import FileLock, Timeout
from pydantic import BaseModel, Field, ConfigDict

from . import __version__
from .config import Settings, atomic_json, private_directory


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class CaptureRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    acknowledge: bool = Field(False, description="Delete only contiguous pages after durable raw capture. Default leaves the Pendant unchanged.")
    idle_timeout: float = Field(5, ge=1, le=30)
    max_seconds: float = Field(60, ge=1, le=3600,
                               description="Maximum transfer time, up to 1 hour. This is not the audio duration.")


class RecordingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool


class KeyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    confirm_future_recordings: bool = Field(description="Explicitly apply a local public key to future audio. Does not recover old encrypted recordings.")


def create_app(settings: Settings | None = None, device_backend=None, capture_backend=None, transcription_queue=None) -> FastAPI:
    settings = settings or Settings.load()
    if device_backend is None:
        from . import device as device_backend
    if capture_backend is None:
        from . import capture as capture_backend
    operation_lock = asyncio.Lock()
    process_lock = FileLock(str(settings.data_dir / "service.lock"))
    captures = private_directory(settings.data_dir / "captures")
    from .recordings import RecordingStore
    from .transcription import TranscriptionQueue
    store = RecordingStore(settings.data_dir)
    queue = transcription_queue or TranscriptionQueue(settings.data_dir, store)

    @asynccontextmanager
    async def lifespan(app):
        try:
            process_lock.acquire(timeout=0)
        except Timeout as exc:
            raise RuntimeError("Another Pendant API is using this data directory. Run one service worker.") from exc
        # A previous process may have stopped while capturing. Raw files remain.
        for path in captures.glob("*/job.json"):
            try:
                job = json.loads(path.read_text())
                if job.get("status") == "running":
                    job.update(status="interrupted", finished_at=now(), error="Service stopped during capture; inspect preserved raw files.")
                    atomic_json(path, job)
            except (OSError, ValueError):
                continue
        try:
            store.index_existing_captures()
            queue.start()
            yield
        finally:
            try:
                await queue.close()
            finally:
                process_lock.release()

    app = FastAPI(title="Pendant Local API", version=__version__, lifespan=lifespan, docs_url=None, redoc_url=None,
                  description="Local Bluetooth access and audio capture. No Limitless/Omi login or cloud processing. Start with scan and info, then non-destructive capture.")
    app.state.settings = settings
    app.state.device_address = settings.address
    app.state.recording_store = store
    app.state.transcription_queue = queue
    app.mount("/assets", StaticFiles(directory=Path(__file__).parent / "static"), name="assets")
    app.mount("/ui", StaticFiles(directory=Path(__file__).parent / "ui", html=True), name="ui")
    bearer = HTTPBearer(auto_error=False)

    async def authorise(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
        if credentials is None or not secrets.compare_digest(credentials.credentials, settings.token):
            raise HTTPException(401, "Use the local API token from `pendant-local token`.", headers={"WWW-Authenticate": "Bearer"})

    protected = [Depends(authorise)]

    def address() -> str:
        if not app.state.device_address:
            raise HTTPException(409, "No Pendant configured. Open Device in the dashboard to scan and select it.")
        return app.state.device_address

    @asynccontextmanager
    async def exclusive():
        if operation_lock.locked():
            raise HTTPException(409, "A Bluetooth or decoding operation is already running.")
        async with operation_lock:
            try:
                yield
            except HTTPException:
                raise
            except Exception as exc:
                raise HTTPException(503, f"Operation failed ({type(exc).__name__}): {exc}") from exc

    def capture_dir(capture_id: UUID) -> Path:
        path = captures / str(capture_id)
        if not path.is_dir() or path.is_symlink():
            raise HTTPException(404, "Capture not found.")
        return path

    def capture_summary(path: Path) -> dict:
        job = json.loads((path / "job.json").read_text())
        manifest = path / "capture.json"
        job["capture"] = json.loads(manifest.read_text()) if manifest.exists() else None
        files = list(path.iterdir())
        audio = path / "audio"
        if audio.is_dir() and not audio.is_symlink():
            files.extend(audio.iterdir())
        job["files"] = sorted(p.relative_to(path).as_posix() for p in files if p.is_file() and not p.is_symlink() and p.suffix in {".bin", ".json", ".jsonl", ".opus", ".wav"})
        return job

    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse("/ui/")

    @app.get("/docs", include_in_schema=False)
    async def docs():
        return get_swagger_ui_html(openapi_url="/openapi.json", title="Pendant Local API",
            swagger_js_url="/assets/swagger-ui-bundle.js", swagger_css_url="/assets/swagger-ui.css",
            swagger_favicon_url="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg'/>",
            swagger_ui_parameters={"validatorUrl": None, "persistAuthorization": False})

    @app.get("/health")
    async def health():
        return {"status": "ok", "version": __version__, "device_configured": bool(app.state.device_address),
                "hardware_verified": False, "operation_running": operation_lock.locked()}

    @app.get("/desktop/identity", include_in_schema=False)
    async def desktop_identity(challenge: str = Query(pattern=r"^[0-9a-f]{64}$")):
        # Prove this listener owns the local workspace before the native app
        # sends a bearer token. A random challenge prevents replaying a response.
        message = f"pendant-desktop-v1:{challenge}:{__version__}".encode()
        proof = hmac.new(settings.token.encode(), message, hashlib.sha256).hexdigest()
        from fastapi.responses import JSONResponse
        return JSONResponse({"version": __version__, "proof": proof}, headers={"Cache-Control": "no-store"})

    @app.get("/v1/desktop/status", dependencies=protected, include_in_schema=False)
    async def desktop_status():
        status = queue.status()
        return {"busy": operation_lock.locked() or status["busy"] or
                any(job["status"] in {"queued", "running"} for job in status["jobs"])}

    @app.get("/v1/devices/scan", dependencies=protected)
    async def scan(timeout: float = Query(8, ge=1, le=30)):
        async with exclusive():
            return {"devices": await device_backend.scan(timeout)}

    @app.get("/v1/device", dependencies=protected)
    async def info():
        target = address()
        async with exclusive():
            return await device_backend.info(target)

    @app.post("/v1/device/clock", dependencies=protected)
    async def clock():
        target = address()
        async with exclusive():
            return await device_backend.set_clock(target)

    @app.post("/v1/device/recording", dependencies=protected)
    async def recording(request: RecordingRequest):
        target = address()
        async with exclusive():
            return await device_backend.recording(target, request.enabled)

    @app.post("/v1/device/key", dependencies=protected)
    async def key(request: KeyRequest):
        if not request.confirm_future_recordings:
            raise HTTPException(422, "Confirm applying a local key to future recordings.")
        target = address()
        async with exclusive():
            return await device_backend.provision_key(target, settings.data_dir / "keys")

    @app.post("/v1/captures", dependencies=protected, status_code=201)
    async def capture(request: CaptureRequest):
        target = address()
        async with exclusive():
            capture_id = str(uuid4())
            path = private_directory(captures / capture_id)
            job = {"id": capture_id, "status": "running", "started_at": now(),
                   "acknowledge": request.acknowledge, "max_seconds": request.max_seconds}
            atomic_json(path / "job.json", job)
            try:
                result = await capture_backend.capture(target, path, **request.model_dump())
                job.update(status=result.get("status", "completed"), finished_at=now())
            except BaseException as exc:
                job.update(status="interrupted" if isinstance(exc, asyncio.CancelledError) else "failed", finished_at=now(), error=type(exc).__name__)
                atomic_json(path / "job.json", job)
                if isinstance(exc, asyncio.CancelledError):
                    raise
                raise HTTPException(503, {"message": str(exc), "capture_id": capture_id, "raw_data_preserved": (path / "capture.bin").exists()}) from exc
            atomic_json(path / "job.json", job)
            return capture_summary(path)

    @app.get("/v1/captures", dependencies=protected)
    async def list_captures(limit: int = Query(50, ge=1, le=200)):
        result = []
        for path in sorted(captures.glob("*/job.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                result.append(capture_summary(path.parent))
            except (OSError, ValueError):
                continue
            if len(result) >= limit:
                break
        return {"captures": result}

    @app.get("/v1/captures/{capture_id}", dependencies=protected)
    async def get_capture(capture_id: UUID):
        return capture_summary(capture_dir(capture_id))

    @app.post("/v1/captures/{capture_id}/decode", dependencies=protected)
    async def decode(capture_id: UUID):
        path = capture_dir(capture_id)
        async with exclusive():
            result = await asyncio.to_thread(capture_backend.decode_capture, path, settings.data_dir / "keys")
            indexed = await asyncio.to_thread(store.ingest_capture_result, str(capture_id))
            result["library_recordings"] = [app.state.auto_enqueue_recording(record)
                if record["id"] in indexed["added_ids"] else record for record in indexed["recordings"]]
            result["library_summary"] = {key: indexed[key] for key in ("added", "already_present", "duplicates_archived", "extended")}
            return result

    @app.get("/v1/captures/{capture_id}/files/{filename:path}", dependencies=protected)
    async def download(capture_id: UUID, filename: str):
        base = capture_dir(capture_id)
        parts = PurePosixPath(filename).parts
        if not parts or any(p in {".", ".."} for p in parts) or "\\" in filename or filename.startswith("/"):
            raise HTTPException(404, "File not found.")
        path = base / filename
        if path.parent not in {base, base / "audio"} or path.parent.is_symlink() or path.is_symlink() or not path.resolve().is_relative_to(base.resolve()) or path.suffix not in {".bin", ".json", ".jsonl", ".opus", ".wav"} or not path.is_file():
            raise HTTPException(404, "File not found.")
        return FileResponse(path, filename=path.name, media_type="application/octet-stream")

    from .workspace_routes import add_workspace_routes
    add_workspace_routes(app, settings, store, queue, authorise, exclusive)
    return app
