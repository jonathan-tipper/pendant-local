from __future__ import annotations

import json
import os
from pathlib import Path
import re
import secrets
from dataclasses import dataclass

from platformdirs import user_data_path

ADDRESS_RE = re.compile(r"(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}|[0-9A-Fa-f]{8}(?:-[0-9A-Fa-f]{4}){3}-[0-9A-Fa-f]{12}")


def valid_address(value: str) -> str:
    if not ADDRESS_RE.fullmatch(value):
        raise ValueError("Use the Bluetooth MAC address or macOS UUID returned by scan.")
    return value.upper()


def private_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name != "nt":
        path.chmod(0o700)
    return path


def atomic_json(path: Path, data: dict) -> None:
    temp = path.with_name(path.name + ".tmp")
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)
    if os.name != "nt":
        fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    token: str
    address: str | None = None

    @classmethod
    def load(cls, data_dir: str | Path | None = None) -> "Settings":
        base = data_dir or os.environ.get("PENDANT_DATA_DIR") or user_data_path("pendant-local-api", appauthor=False)
        root = private_directory(Path(base).expanduser().resolve())
        config_path = root / "config.json"
        config = json.loads(config_path.read_text()) if config_path.exists() else {}
        token = os.environ.get("PENDANT_API_TOKEN") or config.get("api_token")
        if token is None:
            token = secrets.token_urlsafe(32)
            config["api_token"] = token
            atomic_json(config_path, config)
        if len(token) < 20:
            raise ValueError("PENDANT_API_TOKEN must contain at least 20 characters.")
        address = os.environ.get("PENDANT_ADDRESS") or config.get("address")
        if address:
            address = valid_address(address)
        private_directory(root / "captures")
        private_directory(root / "keys")
        return cls(root, token, address)

    def configure_address(self, address: str) -> None:
        path = self.data_dir / "config.json"
        config = json.loads(path.read_text()) if path.exists() else {}
        config["address"] = valid_address(address)
        atomic_json(path, config)
