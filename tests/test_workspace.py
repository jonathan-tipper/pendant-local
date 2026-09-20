"""Personal workspace flows through HTTP, SQLite and the real background queue.

Bluetooth and model inference are injected; the API, file validation, queue
transitions, transcript exports and restart persistence use the real code.
"""
from __future__ import annotations

from copy import deepcopy
import io
import json
from pathlib import Path
import threading
import time
from types import SimpleNamespace
from uuid import uuid4
import wave

from fastapi.testclient import TestClient
import pytest

from pendant_api.app import create_app
from pendant_api.config import Settings, atomic_json
from pendant_api.recordings import RecordingStore
from pendant_api.transcription import TranscriptionQueue


ADDRESS = "AA:BB:CC:DD:EE:FF"
TRANSCRIPT = {
    "text": "Discuss the reservoir. Send Alex the follow-up.",
    "language": "en", "duration": 2.5,
    "segments": [
        {"start": 0.125, "end": 1.25, "text": "Discuss the reservoir."},
        {"start": 1.4, "end": 2.5, "text": "Send Alex the follow-up."},
    ],
}


def wav_bytes():
    result = io.BytesIO()
    with wave.open(result, "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(16000)
        output.writeframes(b"\0\0" * 40000)
    return result.getvalue()


def install_fixture(model, path):
    path.mkdir(parents=True, exist_ok=True)
    for name in ("model.bin", "config.json", "tokenizer.json"):
        (path / name).write_text("test model fixture")


def make_workspace(root, *, transcriber=None):
    settings = Settings.load(root)
    calls = []

    async def info(address):
        calls.append(("info", address))
        return {"address": address, "firmware_ver": "test"}

    async def capture(address, path, **options):
        calls.append(("capture", address, options))
        (path / "capture.bin").write_bytes(b"retained raw capture")
        manifest = {"status": "completed", "complete": True}
        atomic_json(path / "capture.json", manifest)
        return manifest

    def decode_capture(path, keys_dir):
        audio = path / "audio"
        audio.mkdir(exist_ok=True)
        (audio / "recording.wav").write_bytes(wav_bytes())
        manifest = {"status": "decoded", "recordings": [
            {"file": "audio/recording.wav", "duration_seconds": 2.5},
        ]}
        atomic_json(path / "decode.json", manifest)
        return manifest

    backend = SimpleNamespace(info=info, capture=capture, decode_capture=decode_capture)
    store = RecordingStore(settings.data_dir)
    queue = TranscriptionQueue(settings.data_dir, store,
        transcriber=transcriber or (lambda *_: deepcopy(TRANSCRIPT)),
        model_installer=install_fixture)
    app = create_app(settings, backend, backend, transcription_queue=queue)
    return SimpleNamespace(app=app, settings=settings, store=store, queue=queue, calls=calls)


@pytest.fixture
def workspace(tmp_path):
    return make_workspace(tmp_path)


@pytest.fixture
def client(workspace):
    with TestClient(workspace.app) as api:
        api.headers["Authorization"] = f"Bearer {workspace.settings.token}"
        yield api


def import_recording(client, filename="Morning notes.wav"):
    response = client.post("/v1/recordings/import", files={"file": (filename, wav_bytes(), "audio/wav")})
    assert response.status_code == 201, response.text
    return response.json()


def wait_job(client, job_id, status="completed"):
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        jobs = client.get("/v1/jobs").json()["jobs"]
        job = next(item for item in jobs if item["id"] == job_id)
        if job["status"] == status:
            return job
        if status == "completed" and job["status"] == "failed":
            pytest.fail(f"Background job failed: {job}")
        time.sleep(0.01)
    pytest.fail(f"Job did not reach {status}: {job}")


def test_stronger_models_preferences_and_explicit_language_detection(client):
    catalogue = client.get("/v1/transcription/status").json()
    assert catalogue["recommended_model"] == "large-v3-turbo"
    assert {"medium", "medium.en", "large-v3", "large-v3-turbo"} <= {m["id"] for m in catalogue["models"]}
    download = client.post("/v1/transcription/models/large-v3-turbo/prepare")
    assert download.status_code == 202
    wait_job(client, download.json()["id"])
    assert client.patch("/v1/settings", json={"default_model": "large-v3-turbo", "default_language": "fr"}).status_code == 200
    first = import_recording(client)
    job = client.post(f"/v1/recordings/{first['id']}/transcribe", json={}).json()
    assert job["model"] == "large-v3-turbo" and job["language"] == "fr"
    wait_job(client, job["id"])
    second = import_recording(client)
    job = client.post(f"/v1/recordings/{second['id']}/transcribe", json={"language": None}).json()
    assert job["language"] is None
    wait_job(client, job["id"])
    assert client.patch("/v1/settings", json={"default_model": "untrusted/repository"}).status_code == 422
    assert client.post(f"/v1/recordings/{second['id']}/transcribe", json={"model": "../model"}).status_code == 422


def test_batch_keeps_transcripts_archives_and_handles_missing_or_active_records(client, workspace):
    prepare_model(client)
    records = [import_recording(client, f"clip-{index}.wav") for index in range(4)]
    workspace.store.update_transcription(records[0]["id"], TRANSCRIPT)
    client.patch(f"/v1/recordings/{records[1]['id']}", json={"archived": True, "notes": "Keep these notes"})
    existing = client.post(f"/v1/recordings/{records[2]['id']}/transcribe", json={}).json()
    # Either queued/running or already completed must be skipped, never duplicated.
    missing = str(uuid4())
    ids = [record["id"] for record in records] + [missing, records[3]["id"]]
    response = client.post("/v1/transcription/batch", json={"recording_ids": ids})
    assert response.status_code == 202
    batch = response.json()
    assert batch["queued"] == 1 and len(batch["skipped"]) == 4
    assert batch["jobs"][0]["recording_id"] == records[3]["id"]
    wait_job(client, existing["id"])
    wait_job(client, batch["jobs"][0]["id"])
    assert client.get(f"/v1/recordings/{records[0]['id']}").json()["transcript"] == TRANSCRIPT
    archived = client.get(f"/v1/recordings/{records[1]['id']}").json()
    assert archived["archived"] and archived["notes"] == "Keep these notes"
    repeated = client.post("/v1/transcription/batch", json={"recording_ids": ids}).json()
    assert repeated["queued"] == 0
    assert all(record["has_transcript"] for record in client.get("/v1/recordings").json()["recordings"])


def test_batch_preflight_does_not_download_or_queue_and_bounds_input(client, workspace):
    record = import_recording(client)
    response = client.post("/v1/transcription/batch", json={"recording_ids": [record["id"]], "model": "large-v3"})
    assert response.status_code == 409 and workspace.queue.list_jobs() == []
    assert client.post("/v1/transcription/batch", json={"recording_ids": []}).status_code == 422
    assert client.post("/v1/transcription/batch", json={"recording_ids": [record["id"]] * 101}).status_code == 422
    assert client.post("/v1/transcription/batch", json={"recording_ids": [record["id"]]}, headers={"Authorization": "Bearer invalid"}).status_code == 401


def test_missing_engine_explains_setup_without_starting_downloads(client, workspace, monkeypatch):
    monkeypatch.setattr(workspace.queue, "_installed", lambda: False)
    status = client.get("/v1/transcription/status").json()
    assert status["installed"] is False
    assert "-m pip install faster-whisper==1.2.1" in status["install_command"]
    assert status["speaker_labels"] is False
    response = client.post("/v1/transcription/models/large-v3-turbo/prepare")
    assert response.status_code == 409 and "Settings" in response.json()["detail"]
    assert workspace.queue.list_jobs() == [] and not list(workspace.queue.models_dir.iterdir())


def prepare_model(client):
    response = client.post("/v1/transcription/models/base.en/prepare")
    assert response.status_code == 202, response.text
    wait_job(client, response.json()["id"])


def test_import_organise_transcribe_export_and_restart(tmp_path):
    workspace = make_workspace(tmp_path)
    with TestClient(workspace.app) as api:
        api.headers["Authorization"] = f"Bearer {workspace.settings.token}"
        record = import_recording(api)
        rid = record["id"]
        assert record["duration_seconds"] == pytest.approx(2.5)
        assert record["status"] == "ready"
        assert "audio_path" not in record
        edits = {"title": "Water utility follow-up", "tags": [" work ", "work", "water"],
                 "notes": "Ask about the 35% latency reduction.", "starred": True}
        response = api.patch(f"/v1/recordings/{rid}", json=edits)
        assert response.status_code == 200
        assert response.json()["tags"] == ["work", "water"]
        for query in ("utility", "35%", "water"):
            found = api.get("/v1/recordings", params={"query": query}).json()
            assert [item["id"] for item in found["recordings"]] == [rid]
        assert api.get("/v1/recordings", params={"query": "%"}).json()["total"] == 1
        assert api.get("/v1/recordings", params={"query": "_"}).json()["total"] == 0
        assert api.get(f"/v1/recordings/{rid}/export?format=srt").status_code == 409
        # Import and opening the workspace must never download a model implicitly.
        assert api.get("/v1/jobs").json() == {"jobs": []}
        assert api.post(f"/v1/recordings/{rid}/transcribe", json={}).status_code == 409
        prepare_model(api)
        response = api.post(f"/v1/recordings/{rid}/transcribe", json={"model": "base.en", "language": "en"})
        assert response.status_code == 202
        job = wait_job(api, response.json()["id"])
        detail = api.get(f"/v1/recordings/{rid}").json()
        assert detail["status"] == "transcribed"
        assert detail["transcript"]["segments"] == TRANSCRIPT["segments"]
        assert api.get("/v1/recordings", params={"query": "reservoir"}).json()["total"] == 1
        txt = api.get(f"/v1/recordings/{rid}/export?format=txt")
        assert txt.status_code == 200
        assert txt.text == "Water utility follow-up\n\n" + TRANSCRIPT["text"] + "\n"
        srt = api.get(f"/v1/recordings/{rid}/export?format=srt")
        assert "1\n00:00:00,125 --> 00:00:01,250\nDiscuss the reservoir." in srt.text
        assert "2\n00:00:01,400 --> 00:00:02,500\nSend Alex the follow-up." in srt.text
        exported = api.get(f"/v1/recordings/{rid}/export?format=json").json()
        assert exported["notes"] == edits["notes"]
        assert exported["transcript"]["text"] == TRANSCRIPT["text"]
        assert "audio_path" not in exported
        assert "source_key" not in exported
        assert str(tmp_path) not in json.dumps(exported)

    restarted = make_workspace(tmp_path)
    with TestClient(restarted.app) as api:
        api.headers["Authorization"] = f"Bearer {restarted.settings.token}"
        detail = api.get(f"/v1/recordings/{rid}").json()
        assert detail["title"] == edits["title"]
        assert detail["starred"] is True
        assert detail["transcript"]["segments"] == TRANSCRIPT["segments"]
        assert wait_job(api, job["id"])["attempts"] == 1
        assert api.get(f"/v1/recordings/{rid}/audio").content == wav_bytes()


def test_audio_auth_ranges_and_archive_preserve_recordings(client, workspace):
    rid = import_recording(client)["id"]
    audio_url = f"/v1/recordings/{rid}/audio"
    response = client.get(audio_url, headers={"Range": "bytes=0-43"})
    assert response.status_code == 206
    assert response.content == wav_bytes()[:44]
    assert response.headers["content-range"] == f"bytes 0-43/{len(wav_bytes())}"
    assert "no-store" in response.headers["cache-control"]
    client.headers.pop("Authorization")
    assert client.get(audio_url).status_code == 401
    client.headers["Authorization"] = f"Bearer {workspace.settings.token}"
    assert client.patch(f"/v1/recordings/{rid}", json={"archived": True}).status_code == 200
    assert client.get("/v1/recordings").json()["total"] == 0
    archived = client.get("/v1/recordings?archived=true").json()
    assert archived["recordings"][0]["id"] == rid
    assert client.get(audio_url).content == wav_bytes()
    assert client.patch(f"/v1/recordings/{rid}", json={"archived": False}).status_code == 200
    assert client.get("/v1/recordings").json()["total"] == 1


def test_selecting_device_takes_effect_immediately_and_survives_restart(client, workspace):
    assert client.get("/v1/device").status_code == 409
    assert workspace.calls == []
    selected = client.put("/v1/device/config", json={"address": ADDRESS.lower()})
    assert selected.status_code == 200
    assert selected.json()["address"] == ADDRESS
    assert client.get("/v1/device").json()["address"] == ADDRESS
    assert workspace.calls == [("info", ADDRESS)]
    assert client.get("/health").json()["device_configured"] is True
    assert Settings.load(workspace.settings.data_dir).address == ADDRESS
    assert client.put("/v1/device/config", json={"address": "../other-device"}).status_code == 422
    assert client.get("/v1/settings").json()["address"] == ADDRESS


def test_capture_decode_and_startup_indexing_are_idempotent(client, workspace):
    enqueued = []
    workspace.app.state.auto_enqueue_recording = lambda record: enqueued.append(record["id"]) or record
    client.put("/v1/device/config", json={"address": ADDRESS})
    capture = client.post("/v1/captures", json={})
    assert capture.status_code == 201
    cid = capture.json()["id"]
    first = client.post(f"/v1/captures/{cid}/decode")
    assert first.status_code == 200
    rid = first.json()["library_recordings"][0]["id"]
    assert first.json()["library_summary"]["added"] == 1
    client.patch(f"/v1/recordings/{rid}", json={"title": "Keep my title", "notes": "Edited by Alex"})
    repeated = client.post(f"/v1/captures/{cid}/decode")
    assert repeated.json()["library_recordings"][0]["id"] == rid
    assert repeated.json()["library_summary"] == {"added": 0, "already_present": 1, "duplicates_archived": 0, "extended": 0}
    assert enqueued == [rid]
    RecordingStore(workspace.settings.data_dir).index_existing_captures()
    listing = client.get("/v1/recordings").json()
    assert listing["total"] == 1
    assert listing["recordings"][0]["title"] == "Keep my title"
    assert listing["recordings"][0]["notes"] == "Edited by Alex"
    assert listing["recordings"][0]["source"] == "pendant"
    assert client.get(f"/v1/captures/{cid}/files/capture.bin").content == b"retained raw capture"
    assert workspace.calls[0][2]["acknowledge"] is False


@pytest.mark.parametrize("filename,payload", [
    ("empty.wav", b""), ("corrupt.wav", b"This is not audio"), ("script.py", b"print('hello')"),
])
def test_invalid_imports_leave_no_record_or_audio(client, workspace, filename, payload):
    response = client.post("/v1/recordings/import", files={"file": (filename, payload)})
    assert response.status_code == 422
    assert client.get("/v1/recordings").json()["total"] == 0
    assert list(workspace.store.imports.iterdir()) == []


def test_import_filenames_and_capture_manifests_cannot_escape_data_root(client, workspace, tmp_path):
    record = import_recording(client, "../../outside.wav")
    stored_path = Path(workspace.store.get_recording(record["id"])["audio_path"])
    assert stored_path.is_relative_to(workspace.store.imports)
    assert not (tmp_path.parent / "outside.wav").exists()
    cid = str(uuid4())
    directory = workspace.settings.data_dir / "captures" / cid
    audio = directory / "audio"
    audio.mkdir(parents=True)
    outside = tmp_path.parent / f"outside-{uuid4()}.wav"
    outside.write_bytes(wav_bytes())
    try:
        linked = audio / "linked.wav"
        linked.symlink_to(outside)
        atomic_json(directory / "decode.json", {"recordings": [
            {"file": str(outside)}, {"file": "../../" + outside.name}, {"file": "audio/linked.wav"},
        ]})
        assert workspace.store.ingest_capture(cid) == []
        for path in (outside, linked, workspace.settings.data_dir / ".." / outside.name):
            with pytest.raises((ValueError, FileNotFoundError)):
                workspace.store.add_recording(path, "Should be rejected")
        assert client.get("/v1/recordings").json()["total"] == 1
    finally:
        outside.unlink()


def test_new_workspace_routes_reject_unauthenticated_requests(workspace):
    rid, jid = str(uuid4()), uuid4().hex
    requests = [
        ("GET", "/v1/settings", None),
        ("PATCH", "/v1/settings", {"auto_transcribe": False}),
        ("PUT", "/v1/device/config", {"address": ADDRESS}),
        ("GET", "/v1/recordings", None),
        ("GET", f"/v1/recordings/{rid}", None),
        ("PATCH", f"/v1/recordings/{rid}", {"title": "Changed"}),
        ("GET", f"/v1/recordings/{rid}/audio", None),
        ("GET", f"/v1/recordings/{rid}/export", None),
        ("POST", f"/v1/recordings/{rid}/transcribe", {}),
        ("GET", "/v1/transcription/status", None),
        ("POST", "/v1/transcription/models/base.en/prepare", None),
        ("GET", "/v1/jobs", None),
        ("POST", f"/v1/jobs/{jid}/cancel", None),
        ("POST", f"/v1/jobs/{jid}/retry", None),
    ]
    with TestClient(workspace.app) as api:
        for method, url, payload in requests:
            response = api.request(method, url, json=payload)
            assert response.status_code == 401, (method, url, response.text)
        response = api.post("/v1/recordings/import", files={"file": ("private.wav", wav_bytes())})
        assert response.status_code == 401
    assert workspace.calls == []
    assert workspace.store.list_recordings()["total"] == 0
    assert workspace.queue.list_jobs() == []


def test_auto_transcription_requires_explicit_model_preparation(client):
    assert client.patch("/v1/settings", json={"auto_transcribe": True}).status_code == 409
    assert client.get("/v1/settings").json()["transcription"]["auto_transcribe"] is False
    prepare_model(client)
    assert client.patch("/v1/settings", json={"auto_transcribe": True}).status_code == 200
    record = import_recording(client)
    jobs = client.get("/v1/jobs").json()["jobs"]
    job = next(item for item in jobs if item["recording_id"] == record["id"])
    wait_job(client, job["id"])
    assert client.get(f"/v1/recordings/{record['id']}").json()["transcript"]["text"] == TRANSCRIPT["text"]


def test_workflow_rejects_incompatible_language_without_overwriting_settings(client):
    original = client.get("/v1/settings").json()["transcription"]
    response = client.patch("/v1/settings", json={"default_language": "fr"})
    assert response.status_code == 422
    assert client.get("/v1/settings").json()["transcription"] == original
    changed = client.patch("/v1/settings", json={"default_model": "base", "default_language": "fr"})
    assert changed.status_code == 200
    response = client.patch("/v1/settings", json={"default_model": "small.en"})
    assert response.status_code == 422
    saved = client.get("/v1/settings").json()["transcription"]
    assert saved["default_model"] == "base"
    assert saved["default_language"] == "fr"
    assert client.patch("/v1/settings", json={"default_language": None}).status_code == 200


def test_cancel_and_retry_use_job_ids_returned_by_api(tmp_path):
    started, release = threading.Event(), threading.Event()
    calls = []

    def transcribe(*args):
        calls.append(args)
        if len(calls) == 1:
            started.set()
            assert release.wait(3), "Test did not release transcription"
        return deepcopy(TRANSCRIPT)

    workspace = make_workspace(tmp_path, transcriber=transcribe)
    with TestClient(workspace.app) as api:
        api.headers["Authorization"] = f"Bearer {workspace.settings.token}"
        rid = import_recording(api)["id"]
        prepare_model(api)
        response = api.post(f"/v1/recordings/{rid}/transcribe", json={})
        assert response.status_code == 202
        jid = response.json()["id"]
        try:
            assert started.wait(2)
            cancelled = api.post(f"/v1/jobs/{jid}/cancel")
            assert cancelled.status_code == 200, cancelled.text
            assert cancelled.json()["status"] == "cancelled"
            assert api.get(f"/v1/recordings/{rid}").json()["transcript"] is None
        finally:
            release.set()
        deadline = time.monotonic() + 3
        while api.get("/v1/transcription/status").json()["busy"]:
            assert time.monotonic() < deadline
            time.sleep(0.01)
        retried = api.post(f"/v1/jobs/{jid}/retry")
        assert retried.status_code == 202, retried.text
        assert retried.json()["id"] == jid
        assert wait_job(api, jid)["attempts"] == 2
        assert api.get(f"/v1/recordings/{rid}").json()["status"] == "transcribed"
