from types import SimpleNamespace

from fastapi.testclient import TestClient

from pendant_api.app import create_app
from pendant_api.config import Settings


def test_docs_assets_and_schema_are_served_locally(tmp_path):
    app = create_app(Settings(tmp_path, "test-token-at-least-20-characters"), SimpleNamespace(), SimpleNamespace())
    with TestClient(app) as client:
        docs = client.get("/docs")
        assert docs.status_code == 200
        assert 'src="/assets/swagger-ui-bundle.js"' in docs.text
        assert 'href="/assets/swagger-ui.css"' in docs.text
        assert '"validatorUrl": null' in docs.text
        assert "cdn.jsdelivr.net" not in docs.text
        assert client.get("/assets/swagger-ui-bundle.js").status_code == 200
        assert client.get("/assets/swagger-ui.css").status_code == 200
        schema = client.get("/openapi.json").json()
        assert schema["components"]["schemas"]["CaptureRequest"]["properties"]["acknowledge"]["default"] is False
        assert schema["paths"]["/v1/captures"]["post"]["security"]
