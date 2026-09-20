"""Queue durability, explicit network access and transcript preservation."""
import asyncio
from copy import deepcopy
import json
from pathlib import Path
import sys
import threading
from types import SimpleNamespace

import pytest

from pendant_api.config import atomic_json
from pendant_api.transcription import (
    MODELS, TranscriptionQueue, TranscriptionUnavailable, _transcribe_local,
)


async def test_insufficient_disk_space_leaves_existing_audio_and_no_model(tmp_path, monkeypatch):
    queue, store = queue_for(tmp_path)
    before = (tmp_path / "one.wav").read_bytes()
    monkeypatch.setattr("pendant_api.transcription.shutil.disk_usage", lambda _: SimpleNamespace(free=1))
    queue.start()
    try:
        job = queue.prepare_model("large-v3-turbo")
        await until(lambda: status_of(queue, job) == "failed")
        assert "disk space" in queue.list_jobs()[0]["error"]
        assert not (queue.models_dir / "large-v3-turbo").exists()
        assert (tmp_path / "one.wav").read_bytes() == before
    finally:
        await queue.close()


async def test_real_adapter_reports_progress_without_speech_and_stores_timing(tmp_path, monkeypatch):
    prepared_model(tmp_path, "large-v3-turbo")
    started, release = threading.Event(), threading.Event()
    def fake_adapter(audio, path, language, cancelled, report):
        report(stage="transcribing", processed_seconds=1, audio_duration_seconds=2.5)
        started.set()
        assert release.wait(2)
        return deepcopy(TRANSCRIPT)
    monkeypatch.setattr("pendant_api.transcription._transcribe_local", fake_adapter)
    queue = TranscriptionQueue(tmp_path, Store(tmp_path), model_installer=install_fixture)
    queue.start()
    try:
        job = queue.enqueue("one", "large-v3-turbo", "en")
        await until(started.is_set)
        await until(lambda: queue.list_jobs()[0].get("progress", {}).get("processed_seconds") == 1)
        active = queue.list_jobs()[0]
        assert active["elapsed_seconds"] >= 0 and active["status"] == "running"
        assert TRANSCRIPT["text"] not in json.dumps(active)
        release.set()
        await until(lambda: status_of(queue, job) == "completed")
        result = queue.store.get_recording("one")["transcript"]
        assert result["model"] == "large-v3-turbo" and result["engine"] == "faster-whisper"
        assert result["processing_seconds"] >= 0 and result["transcribed_at"]
        assert queue.list_jobs()[0]["finished_at"]
    finally:
        release.set()
        await queue.close()


TRANSCRIPT = {"text": "Meet at 3.", "language": "en", "duration": 2.5,
              "segments": [{"start": 0.0, "end": 2.5, "text": "Meet at 3."}]}


class Store:
    def __init__(self, root):
        self.records = {}
        for recording_id in ("one", "two"):
            audio = root / f"{recording_id}.wav"
            audio.write_bytes(b"local audio fixture")
            self.records[recording_id] = {"id": recording_id, "audio_path": str(audio),
                                          "status": "ready", "transcript": None}

    def get_recording(self, recording_id):
        return deepcopy(self.records[recording_id])

    def update_transcription(self, recording_id, result):
        self.records[recording_id]["transcript"] = deepcopy(result)

    def set_status(self, recording_id, status, error=None):
        self.records[recording_id].update(status=status, error=error)


def install_fixture(model, path):
    path.mkdir(parents=True, exist_ok=True)
    for name in ("model.bin", "config.json", "tokenizer.json"):
        (path / name).write_text("fixture")


def prepared_model(root, model="base.en"):
    path = root / "models" / model
    install_fixture(model, path)
    atomic_json(path / ".prepared.json", {"model": model})
    return path


def queue_for(root, **kwargs):
    store = kwargs.pop("store", None) or Store(root)
    kwargs.setdefault("transcriber", lambda *_: deepcopy(TRANSCRIPT))
    kwargs.setdefault("model_installer", install_fixture)
    return TranscriptionQueue(root, store, **kwargs), store


async def until(predicate, timeout=2):
    async with asyncio.timeout(timeout):
        while not predicate():
            await asyncio.sleep(0.005)


def status_of(queue, job):
    return next(item for item in queue.list_jobs() if item["id"] == job["id"])["status"]


async def test_explicit_model_download_then_local_transcription_persists_result(tmp_path):
    calls = []

    def transcribe(audio, model, language):
        calls.append((audio, model, language))
        return deepcopy(TRANSCRIPT)

    queue, store = queue_for(tmp_path, transcriber=transcribe)
    queue.start()
    try:
        with pytest.raises(TranscriptionUnavailable, match="Prepare"):
            queue.enqueue("one")
        assert not list(queue.jobs_dir.glob("*.json"))
        prep = queue.prepare_model()
        await until(lambda: status_of(queue, prep) == "completed")
        job = queue.enqueue("one", language="en")
        await until(lambda: status_of(queue, job) == "completed")
        assert calls == [(tmp_path / "one.wav", tmp_path / "models/base.en", "en")]
        assert store.records["one"]["transcript"]["text"] == "Meet at 3."
        assert store.records["one"]["status"] == "transcribed"
        saved = json.loads((queue.jobs_dir / f"{job['id']}.json").read_text())
        assert saved["status"] == "completed"
        assert saved["attempts"] == 1
        assert "Meet at 3." not in json.dumps(saved)
    finally:
        await queue.close()


async def test_single_worker_and_cancellation_discard_active_result(tmp_path):
    prepared_model(tmp_path)
    started = threading.Event()
    release = threading.Event()
    calls = []

    def transcribe(audio, *_):
        calls.append(audio.name)
        if audio.name == "one.wav":
            started.set()
            assert release.wait(2)
        return deepcopy(TRANSCRIPT)

    queue, store = queue_for(tmp_path, transcriber=transcribe)
    previous = {"text": "Keep this previous transcript."}
    store.records["one"]["transcript"] = previous
    one = queue.enqueue("one")
    two = queue.enqueue("two")
    queue.start()
    try:
        await until(started.is_set)
        queue.cancel(one["id"])
        assert status_of(queue, one) == "cancelled"
        assert queue.status()["busy"] is True
        assert store.records["one"]["status"] == "transcribed"
        with pytest.raises(ValueError, match="still stopping"):
            queue.retry(one["id"])
        assert calls == ["one.wav"]
        assert status_of(queue, two) == "queued"
        release.set()
        await until(lambda: status_of(queue, two) == "completed")
        assert calls == ["one.wav", "two.wav"]
        assert store.records["one"]["transcript"] == previous
        assert status_of(queue, one) == "cancelled"
    finally:
        release.set()
        await queue.close()


async def test_cancel_queued_job_never_runs(tmp_path):
    prepared_model(tmp_path)
    calls = []
    queue, store = queue_for(tmp_path, transcriber=lambda *args: calls.append(args))
    job = queue.enqueue("one")
    assert queue.cancel(job["id"])["status"] == "cancelled"
    queue.start()
    await asyncio.sleep(0.02)
    await queue.close()
    assert calls == []
    assert store.records["one"]["status"] == "ready"


async def test_restart_marks_running_and_queued_downloads_interrupted(tmp_path):
    calls = []
    queue, store = queue_for(tmp_path, model_installer=lambda *args: calls.append(args))
    download = queue.prepare_model()
    prepared_model(tmp_path, "tiny.en")
    running = queue.enqueue("one", "tiny.en")
    job_path = queue.jobs_dir / f"{running['id']}.json"
    job = json.loads(job_path.read_text())
    job["status"] = "running"
    atomic_json(job_path, job)
    store.records["one"]["status"] = "transcribing"

    restarted, _ = queue_for(tmp_path, store=store, model_installer=lambda *args: calls.append(args))
    assert status_of(restarted, download) == "interrupted"
    assert status_of(restarted, running) == "interrupted"
    assert store.records["one"]["status"] == "ready"
    restarted.start()
    await asyncio.sleep(0.02)
    await restarted.close()
    assert calls == []


async def test_queued_transcription_resumes_once_on_restart(tmp_path):
    prepared_model(tmp_path)
    queue, store = queue_for(tmp_path)
    job = queue.enqueue("one")
    calls = []

    def transcribe(*args):
        calls.append(args)
        return deepcopy(TRANSCRIPT)

    restarted, _ = queue_for(tmp_path, store=store, transcriber=transcribe)
    restarted.start()
    restarted.start()  # App integration may call start twice; no second worker.
    await until(lambda: status_of(restarted, job) == "completed")
    await restarted.close()
    final, _ = queue_for(tmp_path, store=store, transcriber=transcribe)
    final.start()
    await asyncio.sleep(0.02)
    await final.close()
    assert len(calls) == 1


async def test_failure_redacts_exception_and_retry_survives_restart(tmp_path):
    prepared_model(tmp_path)

    def failing(*_):
        raise RuntimeError("Private text, /home/example/audio.wav, token=secret")

    queue, store = queue_for(tmp_path, transcriber=failing)
    job = queue.enqueue("one")
    queue.start()
    await until(lambda: status_of(queue, job) == "failed")
    await queue.close()
    saved = (queue.jobs_dir / f"{job['id']}.json").read_text()
    assert "Private" not in saved and "secret" not in saved and "/home" not in saved
    assert "RuntimeError" in saved
    restarted, _ = queue_for(tmp_path, store=store)
    assert restarted.retry(job["id"])["status"] == "queued"
    restarted.start()
    await until(lambda: status_of(restarted, job) == "completed")
    await restarted.close()
    assert restarted.list_jobs()[0]["attempts"] == 2


async def test_close_marks_active_job_interrupted_and_preserves_previous_transcript(tmp_path):
    prepared_model(tmp_path)
    started, release = threading.Event(), threading.Event()

    def transcribe(*_):
        started.set()
        assert release.wait(2)
        return deepcopy(TRANSCRIPT)

    queue, store = queue_for(tmp_path, transcriber=transcribe)
    store.records["one"]["transcript"] = {"text": "Existing"}
    job = queue.enqueue("one")
    queue.start()
    await until(started.is_set)
    closing = asyncio.create_task(queue.close())
    await until(lambda: status_of(queue, job) == "interrupted")
    assert not closing.done()
    release.set()
    await closing
    assert store.records["one"]["transcript"] == {"text": "Existing"}
    assert store.records["one"]["status"] == "transcribed"
    assert queue.status()["busy"] is False


async def test_cancelled_download_does_not_make_model_available(tmp_path):
    started, release = threading.Event(), threading.Event()

    def installer(model, path):
        install_fixture(model, path)
        started.set()
        assert release.wait(2)

    queue, _ = queue_for(tmp_path, model_installer=installer)
    job = queue.prepare_model()
    queue.start()
    await until(started.is_set)
    queue.cancel(job["id"])
    release.set()
    await until(lambda: not queue.status()["busy"])
    assert all(not model["downloaded"] for model in queue.status()["models"])
    assert list(queue.models_dir.iterdir()) == []
    await queue.close()


async def test_missing_tokenizer_after_enqueue_cannot_trigger_online_fallback(tmp_path):
    model_path = prepared_model(tmp_path)
    calls = []
    queue, _ = queue_for(tmp_path, transcriber=lambda *args: calls.append(args))
    job = queue.enqueue("one")
    (model_path / "tokenizer.json").unlink()
    queue.start()
    await until(lambda: status_of(queue, job) == "failed")
    await queue.close()
    assert calls == []
    with pytest.raises(TranscriptionUnavailable, match="incomplete"):
        _transcribe_local(tmp_path / "one.wav", model_path, "en")


def test_real_adapter_requires_local_files_and_cpu_int8(tmp_path, monkeypatch):
    model_path = prepared_model(tmp_path)
    calls = []

    class Whisper:
        def __init__(self, path, **kwargs):
            calls.append((path, kwargs))

        def transcribe(self, audio, **kwargs):
            assert kwargs["vad_filter"] is True
            return iter([SimpleNamespace(start=0, end=2.5, text=" Meet at 3. ")]), SimpleNamespace(language="en", duration=2.5)

    monkeypatch.setitem(sys.modules, "faster_whisper", SimpleNamespace(WhisperModel=Whisper))
    result = _transcribe_local(tmp_path / "one.wav", model_path, "en")
    assert result == TRANSCRIPT
    assert calls == [(str(model_path), {"device": "cpu", "compute_type": "int8",
                                      "local_files_only": True, "num_workers": 1})]


def test_invalid_models_languages_and_duplicate_jobs_are_rejected(tmp_path):
    prepared_model(tmp_path)
    queue, _ = queue_for(tmp_path)
    assert tuple(item["id"] for item in queue.status()["models"]) == MODELS
    with pytest.raises(ValueError, match="supported model"):
        queue.prepare_model("../../keys")
    with pytest.raises(ValueError, match="English-only"):
        queue.enqueue("one", language="fr")
    with pytest.raises(ValueError, match="language code"):
        queue.enqueue("one", language="ENGLISH")
    queue.enqueue("one")
    with pytest.raises(ValueError, match="already"):
        queue.enqueue("one")


def test_unprepared_or_incomplete_model_is_not_reported_downloaded(tmp_path):
    model_path = tmp_path / "models/base.en"
    install_fixture("base.en", model_path)
    queue, _ = queue_for(tmp_path)
    assert not any(model["downloaded"] for model in queue.status()["models"])
    with pytest.raises(TranscriptionUnavailable):
        queue.enqueue("one")
    prepared_model(tmp_path)
    (model_path / "model.bin").write_bytes(b"")
    assert not any(model["downloaded"] for model in queue.status()["models"])


def test_corrupt_job_is_reported_without_breaking_remaining_queue(tmp_path):
    queue, store = queue_for(tmp_path)
    job = queue.prepare_model()
    (queue.jobs_dir / "corrupt.json").write_text("{bad json")
    restarted, _ = queue_for(tmp_path, store=store)
    assert restarted.status()["invalid_saved_jobs"] == 1
    assert status_of(restarted, job) == "interrupted"


def test_structurally_damaged_saved_job_cannot_crash_worker(tmp_path):
    prepared_model(tmp_path)
    queue, store = queue_for(tmp_path)
    job = queue.enqueue("one")
    job["attempts"] = "damaged"
    atomic_json(queue.jobs_dir / f"{job['id']}.json", job)
    restarted, _ = queue_for(tmp_path, store=store)
    assert restarted.status()["invalid_saved_jobs"] == 1
    assert restarted.list_jobs() == []


def test_recording_path_cannot_escape_data_directory(tmp_path):
    prepared_model(tmp_path)
    queue, store = queue_for(tmp_path)
    store.records["one"]["audio_path"] = "../outside.wav"
    with pytest.raises(ValueError, match="inside"):
        queue.enqueue("one")


async def test_incomplete_model_download_and_malformed_transcript_fail_safely(tmp_path):
    queue, store = queue_for(tmp_path, model_installer=lambda *_: None,
                              transcriber=lambda *_: dict(TRANSCRIPT, duration=float("nan")))
    queue.start()
    prep = queue.prepare_model()
    await until(lambda: status_of(queue, prep) == "failed")
    assert not any(model["downloaded"] for model in queue.status()["models"])
    prepared_model(tmp_path)
    job = queue.enqueue("one")
    await until(lambda: status_of(queue, job) == "failed")
    await queue.close()
    assert store.records["one"]["transcript"] is None


def test_queue_views_are_detached_copies(tmp_path):
    queue, _ = queue_for(tmp_path)
    job = queue.prepare_model()
    job["status"] = "completed"
    listing = queue.list_jobs()
    listing[0]["status"] = "completed"
    assert queue.list_jobs()[0]["status"] == "queued"
