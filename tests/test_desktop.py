"""Native launcher handshake. No user workspace or hardware is touched."""
import hashlib
import hmac

from fastapi.testclient import TestClient

from pendant_api import __version__
from pendant_api.app import create_app
from pendant_api.config import Settings


def test_identity_proves_local_token_without_disclosing_it(tmp_path):
    token = "test-native-token-not-a-real-secret"
    with TestClient(create_app(Settings(tmp_path, token))) as client:
        challenge = "ab" * 32
        response = client.get("/desktop/identity", params={"challenge": challenge})
        expected = hmac.new(token.encode(), f"pendant-desktop-v1:{challenge}:{__version__}".encode(), hashlib.sha256).hexdigest()
        assert response.json() == {"version": __version__, "proof": expected}
        assert response.headers["cache-control"] == "no-store"
        assert token not in response.text
        assert client.get("/desktop/identity", params={"challenge": "cd" * 32}).json()["proof"] != expected
        for invalid in ("", "short", "A" * 64, "a" * 65):
            assert client.get("/desktop/identity", params={"challenge": invalid}).status_code == 422


def test_native_quit_status_is_authenticated_and_includes_pending_jobs(tmp_path):
    token = "test-native-token-not-a-real-secret"
    app = create_app(Settings(tmp_path, token))
    with TestClient(app) as client:
        assert client.get("/v1/desktop/status").status_code == 401
        client.headers["Authorization"] = f"Bearer {token}"
        assert client.get("/v1/desktop/status").json() == {"busy": False}
        queue = app.state.transcription_queue
        original = queue.status
        try:
            for state in ("queued", "running"):
                queue.status = lambda: {"busy": False, "jobs": [{"status": state}]}
                assert client.get("/v1/desktop/status").json() == {"busy": True}
            queue.status = lambda: {"busy": True, "jobs": []}
            assert client.get("/v1/desktop/status").json() == {"busy": True}
        finally:
            queue.status = original
