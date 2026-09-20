"""Recording management and local transcription HTTP routes."""
from __future__ import annotations

from pathlib import Path
import asyncio
import importlib.util
import json
import mimetypes
import os
import wave
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator

from . import __version__
from .config import atomic_json, private_directory, valid_address
from .recordings import export_recording
from .transcription import MODELS, _validate_language, _validate_model

DEFAULT_WORKFLOW = {"default_model": "base.en", "default_language": "en", "auto_transcribe": False, "diarize": False}


class RecordEdit(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = Field(None, min_length=1, max_length=200)
    notes: str | None = Field(None, max_length=20000)
    tags: list[str] | None = Field(None, max_length=20)
    starred: bool | None = None
    archived: bool | None = None


class TranscribeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: str | None = None
    language: str | None = Field(None, pattern=r"^[a-z]{2,3}$")
    diarize: bool | None = None
    num_speakers: int | None = Field(None, strict=True, ge=1, le=20)

    @field_validator("model")
    @classmethod
    def supported_model(cls, value):
        return _validate_model(value) if value is not None else value


class BatchTranscribeRequest(TranscribeRequest):
    recording_ids: list[UUID] = Field(min_length=1, max_length=100)


class WorkflowEdit(BaseModel):
    model_config = ConfigDict(extra="forbid")
    default_model: str | None = None
    default_language: str | None = Field(None, pattern=r"^[a-z]{2,3}$")
    auto_transcribe: bool | None = None
    diarize: bool | None = None

    @field_validator("default_model")
    @classmethod
    def supported_model(cls, value):
        return _validate_model(value) if value is not None else value


class DeviceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    address: str


class SpeakerEdit(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision: str = Field(pattern=r"^[0-9a-f]{32}$")
    names: dict[str, str] = Field(min_length=1, max_length=100)

    @field_validator("names")
    @classmethod
    def valid_names(cls, names):
        if any(not name.strip() or len(name) > 80 or any(ord(c) < 32 for c in name) for name in names.values()):
            raise ValueError("Speaker names must be 1–80 characters without line breaks.")
        return {key: name.strip() for key, name in names.items()}


def load_workflow(settings):
    path = settings.data_dir / "workflow.json"
    stored = json.loads(path.read_text()) if path.exists() else {}
    return {**DEFAULT_WORKFLOW, **stored}


def _duration(path):
    if importlib.util.find_spec("av"):
        import av
        try:
            with av.open(str(path)) as container:
                if not container.streams.audio:
                    raise ValueError("This file has no audio stream.")
                if container.duration is not None:
                    return container.duration / av.time_base
                stream = container.streams.audio[0]
                return float(stream.duration * stream.time_base) if stream.duration is not None else None
        except Exception as exc:
            raise ValueError("Could not read this audio file.") from exc
    if path.suffix == ".wav":
        try:
            with wave.open(str(path)) as reader:
                return reader.getnframes() / reader.getframerate()
        except (wave.Error, EOFError) as exc:
            raise ValueError("Could not read this WAV file.") from exc
    return None


def add_workspace_routes(app, settings, store, queue, authorise, exclusive):
    router = APIRouter(prefix="/v1", dependencies=[Depends(authorise)])

    def detail(record_id):
        try:
            return store.detail(str(record_id))
        except (KeyError, FileNotFoundError):
            raise HTTPException(404, "Recording not found.")

    def settings_result():
        return {"address": app.state.device_address, "data_dir": str(settings.data_dir),
                "version": __version__, "local_only": True, "transcription": load_workflow(settings)}

    def auto_enqueue(record):
        config = load_workflow(settings)
        if config["auto_transcribe"] and record["status"] == "ready":
            try:
                queue.enqueue(record["id"], config["default_model"], config["default_language"], diarize=config["diarize"])
            except (ValueError, RuntimeError) as exc:
                store.set_status(record["id"], "transcription_failed", str(exc))
        return store.detail(record["id"])

    def transcription_options(request):
        config = load_workflow(settings)
        model = request.model or config["default_model"]
        language = request.language if "language" in request.model_fields_set else config["default_language"]
        diarize = request.diarize if request.diarize is not None else config["diarize"]
        from .diarization import validate_options
        validate_options(diarize, request.num_speakers)
        return model, _validate_language(language, model), {"diarize": diarize, "num_speakers": request.num_speakers}

    app.state.auto_enqueue_recording = auto_enqueue

    @router.get("/settings")
    async def get_settings():
        return settings_result()

    @router.patch("/settings")
    async def edit_settings(request: WorkflowEdit):
        config = load_workflow(settings)
        changes = request.model_dump(exclude_unset=True)
        if any(changes.get(key, config[key]) is None for key in ("default_model", "auto_transcribe", "diarize")):
            raise HTTPException(422, "Model, automatic transcription and speaker analysis cannot be null.")
        config.update(changes)
        try:
            config["default_language"] = _validate_language(config["default_language"], config["default_model"])
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        if config["diarize"]:
            try:
                queue.ensure_speakers_ready()
            except ValueError as exc:
                raise HTTPException(409, str(exc)) from exc
        if config["auto_transcribe"]:
            available = {item["id"]: item["downloaded"] for item in queue.status()["models"]}
            if not available.get(config["default_model"]):
                raise HTTPException(409, "Download the selected model in Settings before enabling automatic transcription.")
        atomic_json(settings.data_dir / "workflow.json", config)
        return settings_result()

    @router.put("/device/config")
    async def configure(request: DeviceConfig):
        try:
            address = valid_address(request.address)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        async with exclusive():
            settings.configure_address(address)
            app.state.device_address = address
        return {"address": address}

    @router.get("/recordings")
    async def recordings(query: str = Query("", max_length=500), archived: bool = False, status: str = "all"):
        return store.list_recordings(query, archived, status)

    @router.post("/recordings/import", status_code=201)
    async def import_audio(file: UploadFile = File(...)):
        extension = Path(file.filename or "").suffix.lower()
        if extension not in {".wav", ".mp3", ".m4a", ".ogg", ".opus", ".flac", ".aac", ".webm"}:
            await file.close()
            raise HTTPException(422, "Choose WAV, MP3, M4A, Ogg/Opus, FLAC, AAC or WebM audio.")
        directory = private_directory(store.imports / str(uuid4()))
        target = directory / ("audio" + extension)
        size = 0
        registered = False
        try:
            with target.open("xb") as handle:
                while chunk := await file.read(1024 * 1024):
                    size += len(chunk)
                    if size > 250 * 1024 * 1024:
                        raise HTTPException(413, "Maximum audio file size is 250 MB.")
                    handle.write(chunk)
                handle.flush()
                os.fsync(handle.fileno())
            if not size:
                raise HTTPException(422, "The file is empty.")
            try:
                duration = await asyncio.to_thread(_duration, target)
            except ValueError as exc:
                raise HTTPException(422, str(exc)) from exc
            record = store.add_recording(target, Path(file.filename or "Imported audio").stem, duration_seconds=duration)
            registered = True
            return auto_enqueue(record)
        finally:
            await file.close()
            if not registered:
                target.unlink(missing_ok=True)
                directory.rmdir()

    @router.get("/recordings/{record_id}")
    async def get_recording(record_id: UUID):
        return detail(record_id)

    @router.patch("/recordings/{record_id}")
    async def edit_recording(record_id: UUID, request: RecordEdit):
        detail(record_id)
        changes = request.model_dump(exclude_unset=True)
        if any(value is None for value in changes.values()):
            raise HTTPException(422, "Edit fields cannot be null.")
        if "title" in changes and not changes["title"].strip():
            raise HTTPException(422, "Give the recording a title.")
        if "tags" in changes and any(len(tag) > 60 for tag in changes["tags"]):
            raise HTTPException(422, "Tags must be 60 characters or fewer.")
        return store.update(str(record_id), changes)

    @router.get("/recordings/{record_id}/audio")
    async def audio(record_id: UUID):
        try:
            record = store.get_recording(str(record_id))
        except (KeyError, FileNotFoundError):
            raise HTTPException(404, "Recording not found.")
        path = store.safe_audio_path(record["audio_path"])
        media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if path.suffix == ".opus":
            media_type = "audio/ogg"
        return FileResponse(path, media_type=media_type, headers={"Cache-Control": "private, no-store"})

    @router.get("/recordings/{record_id}/export")
    async def export(record_id: UUID, format: Literal["txt", "md", "json", "srt"] = "txt"):
        record = detail(record_id)
        if format != "json" and not record["transcript"]:
            raise HTTPException(409, "Transcribe this recording before exporting its transcript.")
        text, media_type = export_recording(record, format)
        return Response(text, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="recording-{record_id}.{format}"', "Cache-Control": "no-store"})

    @router.post("/recordings/{record_id}/transcribe", status_code=202)
    async def transcribe(record_id: UUID, request: TranscribeRequest):
        detail(record_id)
        try:
            model, language, options = transcription_options(request)
            return queue.enqueue(str(record_id), model, language, **options)
        except (ValueError, RuntimeError) as exc:
            raise HTTPException(409, str(exc)) from exc

    @router.post("/transcription/batch", status_code=202)
    async def transcribe_batch(request: BatchTranscribeRequest):
        try:
            model, language, options = transcription_options(request)
            status = queue.status()
            if not status["installed"] or not any(item["id"] == model and item["downloaded"] for item in status["models"]):
                raise ValueError("Download the selected model in Settings before transcribing.")
            if options["diarize"]:
                queue.ensure_speakers_ready()
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        jobs, skipped = [], []
        for record_id in dict.fromkeys(map(str, request.recording_ids)):
            try:
                record = store.detail(record_id)
                if record.get("archived") or record.get("transcript") is not None:
                    raise ValueError("Archived or already transcribed. Open the recording to transcribe it again.")
                jobs.append(queue.enqueue(record_id, model, language, **options))
            except KeyError:
                skipped.append({"recording_id": record_id, "reason": "Recording not found."})
            except (ValueError, RuntimeError, FileNotFoundError) as exc:
                reason = "Recording audio is unavailable." if isinstance(exc, FileNotFoundError) else str(exc)
                skipped.append({"recording_id": record_id, "reason": reason})
        return {"jobs": jobs, "queued": len(jobs), "skipped": skipped}

    @router.get("/transcription/status")
    async def transcription_status():
        return queue.status()

    @router.post("/transcription/diarization/prepare", status_code=202)
    async def prepare_speakers():
        try:
            return queue.prepare_speaker_models()
        except (ValueError, RuntimeError) as exc:
            raise HTTPException(409, str(exc)) from exc

    @router.patch("/recordings/{record_id}/speakers")
    async def rename_speakers(record_id: UUID, request: SpeakerEdit):
        detail(record_id)
        if any(job["kind"] == "transcription" and job["recording_id"] == str(record_id)
               and job["status"] in {"queued", "running"} for job in queue.list_jobs()):
            raise HTTPException(409, "Wait for this recording's transcription to finish before naming speakers.")
        try:
            return store.rename_speakers(str(record_id), request.names, request.revision)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc

    @router.post("/transcription/models/{model}/prepare", status_code=202)
    async def prepare(model: str):
        if model not in MODELS:
            raise HTTPException(422, "Unsupported local model.")
        try:
            return queue.prepare_model(model)
        except (ValueError, RuntimeError) as exc:
            raise HTTPException(409, str(exc)) from exc

    @router.get("/jobs")
    async def jobs():
        return {"jobs": queue.list_jobs()}

    @router.post("/jobs/{job_id}/cancel")
    async def cancel(job_id: UUID):
        try:
            return queue.cancel(job_id.hex)
        except KeyError:
            raise HTTPException(404, "Job not found.")
        except (ValueError, RuntimeError) as exc:
            raise HTTPException(409, str(exc)) from exc

    @router.post("/jobs/{job_id}/retry", status_code=202)
    async def retry(job_id: UUID):
        try:
            return queue.retry(job_id.hex)
        except KeyError:
            raise HTTPException(404, "Job not found.")
        except (ValueError, RuntimeError) as exc:
            raise HTTPException(409, str(exc)) from exc

    app.include_router(router)
