"""HTTP contract checks with fake backends; no Bluetooth hardware is contacted."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient

from pendant_api.app import create_app
from pendant_api.config import Settings, atomic_json


TOKEN = "local-test-token-with-enough-entropy"
ADDRESS = "AA:BB:CC:DD:EE:FF"


@pytest.fixture
def settings(tmp_path):
    return Settings(tmp_path, TOKEN, ADDRESS)


@pytest.fixture
def backend():
    calls = []

    async def scan(timeout):
        calls.append(("scan", timeout))
        return [{"address": ADDRESS, "name": "Test Pendant"}]

    async def info(address):
        calls.append(("info", address))
        return {"address": address, "firmware_ver": "test"}

    async def set_clock(address):
        calls.append(("clock", address))
        return {"command_sent": "set_current_time"}

    async def recording(address, enabled):
        calls.append(("recording", address, enabled))
        return {"command_sent": "start_recording" if enabled else "stop_recording"}

    async def provision_key(address, keys_dir):
        calls.append(("key", address, keys_dir))
        return {"command_sent": "set_server_public_key"}

    async def capture(address, folder, **options):
        calls.append(("capture", address, folder, options))
        (folder / "capture.bin").write_bytes(b"saved raw audio")
        result = {"status": "partial", "complete": False, "acknowledge": options["acknowledge"]}
        atomic_json(folder / "capture.json", result)
        return result

    def decode_capture(folder, keys_dir):
        calls.append(("decode", folder, keys_dir))
        return {"status": "decoded", "raw_capture_preserved": True}

    return SimpleNamespace(calls=calls, scan=scan, info=info, set_clock=set_clock,
                           recording=recording, provision_key=provision_key,
                           capture=capture, decode_capture=decode_capture)


@pytest.fixture
def client(settings, backend):
    with TestClient(create_app(settings, backend, backend)) as api:
        api.headers["Authorization"] = f"Bearer {TOKEN}"
        yield api


def seed_capture(settings, *, status="captured"):
    capture_id = str(uuid4())
    folder = settings.data_dir / "captures" / capture_id
    folder.mkdir(parents=True)
    atomic_json(folder / "job.json", {"id": capture_id, "status": status})
    (folder / "capture.bin").write_bytes(b"preserved audio")
    return capture_id, folder


CAPTURE_ID = "5f58937c-946c-42cd-a189-a2c9a1526c04"
PROTECTED_ROUTES = [
    ("GET", "/v1/devices/scan", None),
    ("GET", "/v1/device", None),
    ("POST", "/v1/device/clock", None),
    ("POST", "/v1/device/recording", {"enabled": True}),
    ("POST", "/v1/device/key", {"confirm_future_recordings": True}),
    ("POST", "/v1/captures", {}),
    ("GET", "/v1/captures", None),
    ("GET", f"/v1/captures/{CAPTURE_ID}", None),
    ("POST", f"/v1/captures/{CAPTURE_ID}/decode", None),
    ("GET", f"/v1/captures/{CAPTURE_ID}/files/capture.bin", None),
]


@pytest.mark.parametrize("method,path,body", PROTECTED_ROUTES)
@pytest.mark.parametrize("credentials", [None, "Bearer incorrect-token", f"Basic {TOKEN}"])
def test_sensitive_routes_require_bearer_auth(settings, backend, method, path, body, credentials):
    with TestClient(create_app(settings, backend, backend)) as api:
        headers = {} if credentials is None else {"Authorization": credentials}
        response = api.request(method, path, json=body, headers=headers)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert backend.calls == []


def test_startup_health_docs_do_not_touch_device(settings, backend):
    with TestClient(create_app(settings, backend, backend)) as api:
        health = api.get("/health")
        assert health.status_code == 200
        assert health.json()["hardware_verified"] is False
        assert health.json()["operation_running"] is False
        assert TOKEN not in health.text
        assert ADDRESS not in health.text
        assert api.get("/docs").status_code == 200
    assert backend.calls == []


@pytest.mark.parametrize("method,path,body", PROTECTED_ROUTES[1:6])
def test_missing_address_returns_configuration_error(tmp_path, backend, method, path, body):
    with TestClient(create_app(Settings(tmp_path, TOKEN), backend, backend)) as api:
        response = api.request(method, path, json=body, headers={"Authorization": f"Bearer {TOKEN}"})
    assert response.status_code == 409
    assert "configure" in response.json()["detail"]
    assert backend.calls == []


def test_scan_works_before_address_is_configured(tmp_path, backend):
    with TestClient(create_app(Settings(tmp_path, TOKEN), backend, backend)) as api:
        response = api.get("/v1/devices/scan?timeout=2", headers={"Authorization": f"Bearer {TOKEN}"})
    assert response.status_code == 200
    assert response.json()["devices"][0]["address"] == ADDRESS
    assert backend.calls == [("scan", 2)]


@pytest.mark.parametrize("body,expected", [({}, False), ({"acknowledge": False}, False), ({"acknowledge": True}, True)])
def test_capture_acknowledgement_requires_explicit_opt_in(client, backend, body, expected):
    response = client.post("/v1/captures", json=body)
    assert response.status_code == 201
    job = response.json()
    assert job["acknowledge"] is expected
    assert job["status"] == "partial"
    assert job["capture"]["complete"] is False
    assert backend.calls[0][3]["acknowledge"] is expected
    assert backend.calls[0][3]["max_seconds"] == 60
    assert client.get(f"/v1/captures/{job['id']}/files/capture.bin").content == b"saved raw audio"


@pytest.mark.parametrize("body", [{"unknown": True}, {"max_seconds": 3601}, {"max_seconds": 0}, {"idle_timeout": 31}])
def test_invalid_capture_options_do_not_start_device(client, backend, body):
    assert client.post("/v1/captures", json=body).status_code == 422
    assert backend.calls == []


@pytest.mark.parametrize("seconds", [600, 900, 1800, 3600])
def test_long_capture_limits_reach_backend_without_deleting_audio(client, backend, seconds):
    response = client.post("/v1/captures", json={"max_seconds": seconds})
    assert response.status_code == 201
    job = response.json()
    assert job["max_seconds"] == seconds
    assert backend.calls[0][3]["max_seconds"] == seconds
    assert backend.calls[0][3]["acknowledge"] is False
    assert client.get(f"/v1/captures/{job['id']}/files/capture.bin").content == b"saved raw audio"


def test_key_requires_specific_confirmation(client, backend):
    assert client.post("/v1/device/key", json={}).status_code == 422
    assert client.post("/v1/device/key", json={"confirm_future_recordings": False}).status_code == 422
    assert backend.calls == []
    assert client.post("/v1/device/key", json={"confirm_future_recordings": True}).status_code == 200
    assert backend.calls[0][0] == "key"


def test_failed_capture_keeps_raw_bytes_and_is_listable(settings, backend):
    async def fail_after_write(address, folder, **options):
        (folder / "capture.bin").write_bytes(b"valuable prefix")
        atomic_json(folder / "capture.json", {"status": "partial", "complete": False})
        raise RuntimeError("Bluetooth disconnected")

    backend.capture = fail_after_write
    with TestClient(create_app(settings, backend, backend)) as api:
        api.headers["Authorization"] = f"Bearer {TOKEN}"
        response = api.post("/v1/captures", json={})
        assert response.status_code == 503
        detail = response.json()["detail"]
        assert detail["raw_data_preserved"] is True
        capture_id = detail["capture_id"]
        job = api.get(f"/v1/captures/{capture_id}").json()
        assert job["status"] == "failed"
        assert job["error"] == "RuntimeError"
        assert api.get("/v1/captures").json()["captures"][0]["id"] == capture_id
        assert api.get(f"/v1/captures/{capture_id}/files/capture.bin").content == b"valuable prefix"


def test_restart_marks_running_capture_interrupted_without_removing_raw(settings, backend):
    capture_id, folder = seed_capture(settings, status="running")
    with TestClient(create_app(settings, backend, backend)) as api:
        response = api.get(f"/v1/captures/{capture_id}", headers={"Authorization": f"Bearer {TOKEN}"})
    assert response.json()["status"] == "interrupted"
    assert (folder / "capture.bin").read_bytes() == b"preserved audio"
    assert backend.calls == []


async def test_concurrent_device_and_decode_operations_are_rejected(settings, backend):
    entered, release = asyncio.Event(), asyncio.Event()

    async def slow_info(address):
        backend.calls.append(("info", address))
        entered.set()
        await release.wait()
        return {"address": address}

    backend.info = slow_info
    capture_id, _ = seed_capture(settings)
    app = create_app(settings, backend, backend)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test", headers={"Authorization": f"Bearer {TOKEN}"}) as api:
        running = asyncio.create_task(api.get("/v1/device"))
        await asyncio.wait_for(entered.wait(), 2)
        try:
            assert (await api.get("/health")).json()["operation_running"] is True
            blocked = [
                ("GET", "/v1/device", None),
                ("GET", "/v1/devices/scan", None),
                ("POST", "/v1/device/clock", None),
                ("POST", "/v1/device/recording", {"enabled": True}),
                ("POST", "/v1/device/key", {"confirm_future_recordings": True}),
                ("POST", "/v1/captures", {}),
                ("POST", f"/v1/captures/{capture_id}/decode", None),
            ]
            for method, path, body in blocked:
                assert (await api.request(method, path, json=body)).status_code == 409
            assert backend.calls == [("info", ADDRESS)]
            assert (await api.get("/v1/captures")).status_code == 200
        finally:
            release.set()
            assert (await running).status_code == 200
        assert (await api.get("/health")).json()["operation_running"] is False


@pytest.mark.parametrize("suffix", ["", "/decode", "/files/capture.bin"])
def test_invalid_capture_ids_are_rejected(client, backend, suffix):
    method = "POST" if suffix == "/decode" else "GET"
    response = client.request(method, "/v1/captures/not-a-uuid" + suffix)
    assert response.status_code == 422
    assert backend.calls == []


def test_unknown_capture_returns_404(client):
    assert client.get(f"/v1/captures/{uuid4()}").status_code == 404


def test_files_stay_inside_capture_and_include_decoded_audio(client, settings):
    capture_id, folder = seed_capture(settings)
    (folder / "audio").mkdir()
    (folder / "audio" / "recording-0001.opus").write_bytes(b"OggS fake test bytes")
    (folder / "private.pem").write_text("private key")
    base = f"/v1/captures/{capture_id}/files/"
    assert client.get(base + "capture.bin").content == b"preserved audio"
    assert client.get(base + "audio/recording-0001.opus").content == b"OggS fake test bytes"
    listed = client.get(f"/v1/captures/{capture_id}").json()["files"]
    assert "audio/recording-0001.opus" in listed
    assert all("\\" not in name for name in listed)
    for name in listed:
        assert client.get(base + name).status_code == 200
    assert client.get("/v1/captures").json()["captures"][0]["files"] == listed
    for path in ["private.pem", "missing.opus", "%2e%2e%2fconfig.json", "audio/%2e%2e/%2e%2e/config.json"]:
        assert client.get(base + path).status_code == 404


def test_symlink_files_and_directories_are_not_exposed(client, settings, tmp_path):
    capture_id, folder = seed_capture(settings)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.json").write_text('{"secret": "do not serve"}')
    try:
        (folder / "secret.json").symlink_to(outside / "secret.json")
        (folder / "audio").symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("This host does not allow test symlinks")
    base = f"/v1/captures/{capture_id}/files/"
    assert client.get(base + "secret.json").status_code == 404
    assert client.get(base + "audio/secret.json").status_code == 404
    listed = client.get(f"/v1/captures/{capture_id}").json()["files"]
    assert "secret.json" not in listed
    assert "audio/secret.json" not in listed
