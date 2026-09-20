"""Durable, single-worker local transcription. Audio never leaves this process.

Only ``prepare_model`` may use the network. Installing the optional dependency
does not download a model. Queue methods run on the application's event-loop
thread; expensive inference and model downloads run in one worker thread.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
from datetime import datetime, timezone
import importlib.util
import json
import math
from pathlib import Path
import re
import shutil
import shlex
import subprocess
import sys
import threading
from typing import Callable, Protocol
from uuid import uuid4

from .config import atomic_json, private_directory
from .models import MODEL_CATALOGUE, MODELS, DEFAULT_MODEL, RECOMMENDED_MODEL
from . import diarization as speakers


_REQUIRED_MODEL_FILES = ("model.bin", "config.json", "tokenizer.json")
_ACTIVE = {"queued", "running"}
_RETRYABLE = {"failed", "cancelled", "interrupted"}


class RecordingStore(Protocol):
    def get_recording(self, recording_id: str) -> dict: ...
    def update_transcription(self, recording_id: str, result: dict) -> None: ...
    def set_status(self, recording_id: str, status: str, error: str | None = None) -> None: ...


class TranscriptionUnavailable(ValueError):
    """A recoverable configuration problem that is safe to show in the UI."""


class _Cancelled(Exception):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate_model(model: str) -> str:
    if model not in MODELS:
        raise ValueError(f"Choose a supported model: {', '.join(MODELS)}.")
    return model


def _validate_language(language: str | None, model: str) -> str | None:
    language = None if language in (None, "", "auto") else language
    if language is not None and not re.fullmatch(r"[a-z]{2,3}", language):
        raise ValueError("Use a language code such as en or fr, or auto.")
    if model.endswith(".en") and language not in (None, "en"):
        raise ValueError("English-only models require English; choose a multilingual model for other languages.")
    return language


def _complete_files(path: Path) -> bool:
    # In particular, a missing tokenizer triggers an online fallback inside
    # faster-whisper even when WhisperModel(local_files_only=True) was supplied.
    return all((path / name).is_file() and (path / name).stat().st_size > 0
               for name in _REQUIRED_MODEL_FILES)


def _install_model(model: str, model_path: Path) -> None:
    from faster_whisper.utils import download_model

    download_model(model, output_dir=str(model_path), local_files_only=False,
                   use_auth_token=False)


def _transcribe_local(audio_path: Path, model_path: Path, language: str | None,
                      cancelled: threading.Event | None = None, progress: Callable | None = None,
                      word_timestamps: bool = False) -> dict:
    if not _complete_files(model_path):
        raise TranscriptionUnavailable("The local model is incomplete. Prepare it again in Settings.")
    from faster_whisper import WhisperModel

    if importlib.util.find_spec("onnxruntime") is not None:
        import onnxruntime
        onnxruntime.disable_telemetry_events()

    report = progress or (lambda **_: None)
    report(stage="loading_model")
    model = WhisperModel(str(model_path), device="cpu", compute_type="int8",
                         local_files_only=True, num_workers=1)
    if cancelled is not None and cancelled.is_set():
        raise _Cancelled()
    report(stage="reading_audio")
    segments, info = model.transcribe(str(audio_path), language=language,
                                      vad_filter=True, beam_size=5,
                                      condition_on_previous_text=False, word_timestamps=word_timestamps)
    report(stage="transcribing", audio_duration_seconds=float(info.duration), processed_seconds=0.0)
    collected = []
    for segment in segments:
        if cancelled is not None and cancelled.is_set():
            raise _Cancelled()
        collected.append({"start": float(segment.start), "end": float(segment.end),
                          "text": segment.text.strip()})
        if word_timestamps:
            collected[-1]["words"] = [{"start": float(word.start), "end": float(word.end), "word": word.word}
                                      for word in (segment.words or [])]
        report(stage="transcribing", audio_duration_seconds=float(info.duration),
               processed_seconds=min(float(segment.end), float(info.duration)))
    return {"text": " ".join(segment["text"] for segment in collected).strip(),
            "language": info.language, "duration": float(info.duration),
            "segments": collected}


def _normalise_result(result: dict) -> dict:
    """Persist plain transcript data, never arbitrary model objects or NaNs."""
    text = result["text"]
    language = result["language"]
    duration = float(result["duration"])
    if not isinstance(text, str) or not isinstance(language, str):
        raise ValueError("Invalid transcript metadata")
    if not math.isfinite(duration) or duration < 0:
        raise ValueError("Invalid transcript duration")
    segments = []
    for item in result["segments"]:
        start, end, segment_text = float(item["start"]), float(item["end"]), item["text"]
        if not (math.isfinite(start) and math.isfinite(end) and 0 <= start <= end):
            raise ValueError("Invalid transcript timestamp")
        if not isinstance(segment_text, str):
            raise ValueError("Invalid transcript segment")
        segments.append({"start": start, "end": end, "text": segment_text})
        if "words" in item:
            words = []
            for word in item["words"]:
                begin, finish = float(word["start"]), float(word["end"])
                if not (math.isfinite(begin) and math.isfinite(finish) and 0 <= begin <= finish
                        and isinstance(word["word"], str)):
                    raise ValueError("Invalid transcript word")
                words.append({"start": begin, "end": finish, "word": word["word"]})
            segments[-1]["words"] = words
    return {"text": text, "language": language, "duration": duration, "segments": segments}


class TranscriptionQueue:
    def __init__(self, data_dir: Path, store: RecordingStore, *,
                 transcriber: Callable[[Path, Path, str | None], dict] | None = None,
                 model_installer: Callable[[str, Path], None] | None = None,
                 diarizer: Callable | None = None, speaker_installer: Callable | None = None):
        self.data_dir = private_directory(Path(data_dir).resolve())
        self.jobs_dir = private_directory(self.data_dir / "jobs")
        self.models_dir = private_directory(self.data_dir / "models")
        self.store = store
        self._transcriber = transcriber
        self._installer = model_installer or _install_model
        self._injected = transcriber is not None or model_installer is not None
        self._diarizer = diarizer or speakers.diarize_local
        self._speaker_installer = speaker_installer or speakers.prepare_models
        self._speaker_injected = diarizer is not None or speaker_installer is not None
        self._jobs: dict[str, dict] = {}
        self._wake = asyncio.Event()
        self._worker: asyncio.Task | None = None
        self._current: str | None = None
        self._cancel_event: threading.Event | None = None
        self._closing = False
        self._invalid_jobs = 0
        self._load()

    def _load(self) -> None:
        for path in sorted(self.jobs_dir.glob("*.json")):
            try:
                job = json.loads(path.read_text(encoding="utf-8"))
                if (not re.fullmatch(r"[0-9a-f]{32}", job["id"])
                        or path.stem != job["id"]
                        or job["kind"] not in {"transcription", "model_download", "speaker_model_download"}
                        or job["status"] not in _ACTIVE | _RETRYABLE | {"completed"}
                        or job["model"] not in (MODELS if job["kind"] != "speaker_model_download" else (speakers.MODEL_ID,))):
                    raise ValueError("Invalid saved job")
                datetime.fromisoformat(job["created_at"])
                datetime.fromisoformat(job["updated_at"])
                if not isinstance(job["attempts"], int) or job["attempts"] < 0:
                    raise ValueError("Invalid saved attempt count")
                if job["kind"] == "transcription" and not isinstance(job["recording_id"], str):
                    raise ValueError("Invalid saved recording identifier")
                if job["kind"] != "transcription" and job["recording_id"] is not None:
                    raise ValueError("Invalid saved model download")
                _validate_language(job["language"], job["model"])
                speakers.validate_options(job.get("diarize", False), job.get("num_speakers"))
            except (ValueError, KeyError, TypeError, OSError):
                # A damaged record should not hide the rest of the queue.
                self._invalid_jobs += 1
                continue
            self._jobs[job["id"]] = job
            # Never restart an interrupted download merely by opening the app.
            if job["status"] == "running" or (job["kind"] != "transcription" and job["status"] == "queued"):
                self._change(job, "interrupted", "Interrupted by shutdown. Retry when ready.")
                if job["kind"] == "transcription":
                    self._restore_recording(job)

    def start(self) -> None:
        if self._closing:
            raise RuntimeError("This queue is closed. Create a new queue to restart it.")
        if self._worker is None:
            self._worker = asyncio.create_task(self._run(), name="pendant-transcription")
            self._wake.set()

    async def close(self) -> None:
        """Stop after the current native call returns; queued jobs stay durable.

        A running transcription stops between segments. Native model downloading
        cannot be interrupted safely, so shutdown waits for that call, discards
        its completion and leaves the job interrupted for an explicit retry.
        """
        self._closing = True
        if self._current is not None:
            job = self._jobs[self._current]
            if job["status"] == "running":
                self._change(job, "interrupted", "Interrupted by shutdown. Retry when ready.")
                self._restore_recording(job)
            if self._cancel_event:
                self._cancel_event.set()
        self._wake.set()
        if self._worker is not None:
            await self._worker

    def _installed(self) -> bool:
        if self._injected:
            return True
        return importlib.util.find_spec("faster_whisper") is not None

    def _downloaded(self, model: str) -> bool:
        directory = self.models_dir / model
        marker = directory / ".prepared.json"
        try:
            return (_complete_files(directory)
                    and json.loads(marker.read_text(encoding="utf-8")).get("model") == model)
        except (OSError, ValueError, TypeError, AttributeError):
            return False

    def status(self) -> dict:
        command = [sys.executable, "-m", "pip", "install", "faster-whisper==1.2.1"]
        speaker_command = [sys.executable, "-m", "pip", "install", "sherpa-onnx==1.13.8"]
        speaker_status = {"installed": self._speaker_injected or speakers.installed(),
                          "downloaded": speakers.downloaded(self.models_dir / speakers.MODEL_ID),
                          "model": speakers.MODEL_ID, "label": speakers.MODEL_LABEL,
                          "download_mb": speakers.DOWNLOAD_MB, "engine": "sherpa-onnx", "execution": "CPU",
                          "install_command": subprocess.list2cmdline(speaker_command) if sys.platform == "win32" else shlex.join(speaker_command)}
        return {"installed": self._installed(), "default_model": DEFAULT_MODEL,
                "recommended_model": RECOMMENDED_MODEL, "engine": "faster-whisper",
                "execution": "CPU · int8", "speaker_labels": speaker_status["installed"] and speaker_status["downloaded"],
                "diarization": speaker_status,
                "install_command": subprocess.list2cmdline(command) if sys.platform == "win32" else shlex.join(command),
                "models": [{**model, "downloaded": self._downloaded(model["id"])} for model in MODEL_CATALOGUE],
                "busy": self._current is not None, "jobs": self.list_jobs(),
                "invalid_saved_jobs": self._invalid_jobs}

    def list_jobs(self) -> list[dict]:
        jobs = deepcopy(sorted(self._jobs.values(), key=lambda job: job["created_at"], reverse=True))
        for job in jobs:
            job["stopping"] = self._current == job["id"] and job["status"] in {"cancelled", "interrupted"}
            if job.get("started_at"):
                end = datetime.fromisoformat(job["finished_at"]) if job.get("finished_at") else datetime.now(timezone.utc)
                job["elapsed_seconds"] = max(0, (end - datetime.fromisoformat(job["started_at"])).total_seconds())
            if self._current == job["id"] and job["kind"] != "transcription":
                staging = self.models_dir / f".download-{job['id']}"
                try:
                    job["files_bytes"] = sum(path.stat().st_size for path in staging.rglob("*") if path.is_file())
                except OSError:
                    pass  # Promotion can move the directory between stats.
        return jobs

    def _ensure_available(self) -> None:
        if self._closing:
            raise ValueError("The transcription queue is shutting down.")
        if not self._installed():
            raise TranscriptionUnavailable("Install the local speech engine using the command in Settings, then restart the service.")

    def _audio_path(self, recording_id: str) -> Path:
        recording = self.store.get_recording(recording_id)
        path = Path(recording["audio_path"])
        path = path if path.is_absolute() else self.data_dir / path
        path = path.resolve()
        if not path.is_relative_to(self.data_dir):
            raise ValueError("Recording audio must be inside the local data directory.")
        if not path.is_file():
            raise ValueError("Recording audio is unavailable. Import or synchronise the audio first.")
        return path

    def enqueue(self, recording_id: str, model: str = DEFAULT_MODEL,
                language: str | None = None, *, diarize: bool = False, num_speakers: int | None = None) -> dict:
        self._ensure_available()
        _validate_model(model)
        language = _validate_language(language, model)
        speakers.validate_options(diarize, num_speakers)
        if diarize:
            self.ensure_speakers_ready()
        self._audio_path(recording_id)
        if not self._downloaded(model):
            raise TranscriptionUnavailable("Prepare the selected model in Settings before transcribing.")
        if any(job["kind"] == "transcription" and job["recording_id"] == recording_id
               and job["status"] in _ACTIVE for job in self._jobs.values()):
            raise ValueError("This recording already has a queued or running transcription.")
        job = self._create("transcription", model, recording_id, language, diarize=diarize, num_speakers=num_speakers)
        self.store.set_status(recording_id, "queued")
        return deepcopy(job)

    def ensure_speakers_ready(self) -> None:
        if not (self._speaker_injected or speakers.installed()):
            raise speakers.DiarizationUnavailable("Install the local speaker engine using the command in Settings, then restart the service.")
        if not speakers.downloaded(self.models_dir / speakers.MODEL_ID):
            raise speakers.DiarizationUnavailable("Download the speaker models in Settings before identifying speakers.")

    def prepare_speaker_models(self) -> dict:
        self._ensure_available()
        if not (self._speaker_injected or speakers.installed()):
            raise speakers.DiarizationUnavailable("Install the local speaker engine using the command in Settings, then restart the service.")
        for job in self._jobs.values():
            if job["kind"] == "speaker_model_download" and job["status"] in _ACTIVE:
                return deepcopy(job)
        job = self._create("speaker_model_download", speakers.MODEL_ID)
        if speakers.downloaded(self.models_dir / speakers.MODEL_ID):
            self._change(job, "completed")
        return deepcopy(job)

    def prepare_model(self, model: str = DEFAULT_MODEL) -> dict:
        self._ensure_available()
        _validate_model(model)
        for job in self._jobs.values():
            if job["kind"] == "model_download" and job["model"] == model and job["status"] in _ACTIVE:
                return deepcopy(job)
        job = self._create("model_download", model)
        if self._downloaded(model):
            self._change(job, "completed")
        return deepcopy(job)

    def _create(self, kind: str, model: str, recording_id: str | None = None,
                language: str | None = None, **options) -> dict:
        job = {"id": uuid4().hex, "kind": kind, "status": "queued", "recording_id": recording_id,
               "model": model, "language": language, "created_at": _now(), "updated_at": _now(),
               "error": None, "attempts": 0, **options}
        atomic_json(self.jobs_dir / f"{job['id']}.json", job)
        self._jobs[job["id"]] = job
        self._wake.set()
        return job

    def _change(self, job: dict, status: str, error: str | None = None) -> None:
        job.update(status=status, error=error, updated_at=_now())
        if status == "running":
            job.update(started_at=_now(), finished_at=None, progress={"stage": "starting"})
        elif status == "queued":
            job.update(started_at=None, finished_at=None, progress={"stage": "waiting"})
        else:
            job["finished_at"] = _now()
        atomic_json(self.jobs_dir / f"{job['id']}.json", job)

    def _progress(self, job_id: str, progress: dict) -> None:
        # Called only on the event loop. Never persist speech in job diagnostics.
        job = self._jobs[job_id]
        if job["status"] == "running":
            job["progress"] = progress

    def _get(self, job_id: str) -> dict:
        try:
            return self._jobs[job_id]
        except KeyError:
            raise KeyError("Job not found.") from None

    def _restore_recording(self, job: dict) -> None:
        if job["kind"] != "transcription":
            return
        try:
            record = self.store.get_recording(job["recording_id"])
            state = "transcribed" if record.get("transcript") is not None else "ready"
            self.store.set_status(job["recording_id"], state)
        except (KeyError, FileNotFoundError):
            pass  # The recording may have been removed while a job was running.

    def cancel(self, job_id: str) -> dict:
        job = self._get(job_id)
        if job["status"] in _ACTIVE:
            self._change(job, "cancelled")
            self._restore_recording(job)
            if self._current == job_id and self._cancel_event:
                self._cancel_event.set()
        return deepcopy(job)

    def retry(self, job_id: str) -> dict:
        self._ensure_available()
        job = self._get(job_id)
        if job["status"] not in _RETRYABLE:
            raise ValueError("Only failed, cancelled or interrupted jobs can be retried.")
        if self._current == job_id:
            raise ValueError("The cancelled native operation is still stopping. Retry when it finishes.")
        if job["kind"] == "transcription":
            self._audio_path(job["recording_id"])
            if job.get("diarize"):
                self.ensure_speakers_ready()
            if not self._downloaded(job["model"]):
                raise TranscriptionUnavailable("Prepare the selected model in Settings before retrying.")
            if any(other["id"] != job_id and other["kind"] == "transcription"
                   and other["recording_id"] == job["recording_id"]
                   and other["status"] in _ACTIVE for other in self._jobs.values()):
                raise ValueError("This recording already has a queued or running transcription.")
            self.store.set_status(job["recording_id"], "queued")
        elif any(other["id"] != job_id and other["kind"] == job["kind"]
                 and other["model"] == job["model"] and other["status"] in _ACTIVE
                 for other in self._jobs.values()):
            raise ValueError("This model already has a queued or running download.")
        self._change(job, "queued")
        self._wake.set()
        return deepcopy(job)

    async def _run(self) -> None:
        while not self._closing:
            pending = sorted((job for job in self._jobs.values() if job["status"] == "queued"),
                             key=lambda job: job["created_at"])
            if not pending:
                self._wake.clear()
                await self._wake.wait()
                continue
            job = pending[0]
            self._current = job["id"]
            self._cancel_event = threading.Event()
            job["attempts"] += 1
            self._change(job, "running")
            staging = self.models_dir / f".download-{job['id']}"
            try:
                if job["kind"] != "transcription":
                    speaker_download = job["kind"] == "speaker_model_download"
                    estimate = speakers.DOWNLOAD_MB if speaker_download else next(model["download_mb"] for model in MODEL_CATALOGUE if model["id"] == job["model"])
                    if shutil.disk_usage(self.models_dir).free < (estimate + 256) * 1_000_000:
                        raise TranscriptionUnavailable("Not enough free disk space for this model. Free space or choose a smaller model.")
                    private_directory(staging)
                    self._progress(job["id"], {"stage": "downloading"})
                    if speaker_download:
                        await asyncio.to_thread(self._speaker_installer, staging)
                    else:
                        await asyncio.to_thread(self._installer, job["model"], staging)
                    if job["status"] != "running":
                        continue
                    if not (speakers.complete_files(staging) if speaker_download else _complete_files(staging)):
                        raise TranscriptionUnavailable("The model download is incomplete. Retry the download.")
                    self._progress(job["id"], {"stage": "checking_model"})
                    atomic_json(staging / ".prepared.json", {"model": job["model"], "prepared_at": _now()})
                    target = self.models_dir / job["model"]
                    if target.exists():
                        shutil.rmtree(target)
                    staging.replace(target)
                else:
                    self.store.set_status(job["recording_id"], "transcribing")
                    if not self._downloaded(job["model"]):
                        raise TranscriptionUnavailable("The local model is unavailable. Prepare it again in Settings.")
                    audio_path = self._audio_path(job["recording_id"])
                    model_path = self.models_dir / job["model"]
                    loop = asyncio.get_running_loop()
                    job_id = job["id"]
                    def report(_id=job_id, **progress):
                        loop.call_soon_threadsafe(self._progress, _id, progress)
                    if self._transcriber is not None:
                        result = await asyncio.to_thread(self._transcriber, audio_path, model_path, job["language"])
                    else:
                        result = await asyncio.to_thread(_transcribe_local, audio_path, model_path,
                                                         job["language"], self._cancel_event, report,
                                                         **({"word_timestamps": True} if job.get("diarize") else {}))
                    if job["status"] != "running":
                        continue
                    result = _normalise_result(result)
                    if job.get("diarize"):
                        self.ensure_speakers_ready()
                        turns = await asyncio.to_thread(self._diarizer, audio_path, self.models_dir / speakers.MODEL_ID,
                                                       job.get("num_speakers"), self._cancel_event, report)
                        if job["status"] != "running":
                            continue
                        result = speakers.label_transcript(result, turns, job.get("num_speakers"))
                        result["speaker_revision"] = uuid4().hex
                    result["model"] = job["model"]
                    result["engine"] = "faster-whisper"
                    result["transcribed_at"] = _now()
                    result["processing_seconds"] = (datetime.now(timezone.utc) - datetime.fromisoformat(job["started_at"])).total_seconds()
                    self._progress(job["id"], {"stage": "saving_transcript"})
                    self.store.update_transcription(job["recording_id"], result)
                    self.store.set_status(job["recording_id"], "transcribed")
                self._change(job, "completed")
            except Exception as exc:
                if job["status"] == "running":
                    # Dependency exceptions can contain URLs, paths or transcript
                    # snippets. Do not expose their raw messages in persisted jobs.
                    if isinstance(exc, (TranscriptionUnavailable, speakers.DiarizationUnavailable)):
                        error = str(exc)
                    elif isinstance(exc, ImportError):
                        error = "Local speech dependencies could not load. Check the engine installation commands in Settings."
                    else:
                        label = "Model preparation" if job["kind"] != "transcription" else "Transcription and speaker analysis" if job.get("diarize") else "Transcription"
                        error = f"{label} failed ({type(exc).__name__}). Check the local installation and retry."
                    self._change(job, "failed", error)
                    if job["kind"] == "transcription":
                        try:
                            self.store.set_status(job["recording_id"], "transcription_failed", error)
                        except (KeyError, FileNotFoundError):
                            pass
            finally:
                if staging.exists():
                    shutil.rmtree(staging, ignore_errors=True)
                self._current = None
                self._cancel_event = None
