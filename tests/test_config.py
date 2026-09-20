"""Configuration persistence and local credential handling."""
import json
import os
import stat

import pytest

from pendant_api.config import Settings, valid_address


@pytest.fixture(autouse=True)
def clear_environment(monkeypatch):
    for name in ("PENDANT_DATA_DIR", "PENDANT_API_TOKEN", "PENDANT_ADDRESS"):
        monkeypatch.delenv(name, raising=False)


def test_generated_token_is_persistent_and_kept_when_configuring(tmp_path):
    first = Settings.load(tmp_path)
    assert len(first.token) >= 32
    assert Settings.load(tmp_path).token == first.token
    first.configure_address("aa:bb:cc:dd:ee:ff")
    reloaded = Settings.load(tmp_path)
    assert reloaded.address == "AA:BB:CC:DD:EE:FF"
    assert reloaded.token == first.token
    assert (tmp_path / "captures").is_dir()
    assert (tmp_path / "keys").is_dir()


def test_explicit_directory_overrides_environment(tmp_path, monkeypatch):
    env_dir = tmp_path / "environment"
    explicit = tmp_path / "explicit"
    monkeypatch.setenv("PENDANT_DATA_DIR", str(env_dir))
    assert Settings.load().data_dir == env_dir
    assert Settings.load(explicit).data_dir == explicit


def test_environment_credentials_override_without_rewriting_saved_values(tmp_path, monkeypatch):
    saved = Settings.load(tmp_path)
    saved.configure_address("AA:BB:CC:DD:EE:FF")
    config_before = (tmp_path / "config.json").read_bytes()
    monkeypatch.setenv("PENDANT_API_TOKEN", "different-environment-token-123456")
    monkeypatch.setenv("PENDANT_ADDRESS", "12:34:56:78:9a:bc")
    settings = Settings.load(tmp_path)
    assert settings.token == "different-environment-token-123456"
    assert settings.address == "12:34:56:78:9A:BC"
    assert (tmp_path / "config.json").read_bytes() == config_before


def test_short_token_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("PENDANT_API_TOKEN", "weak")
    with pytest.raises(ValueError, match="at least 20"):
        Settings.load(tmp_path)


@pytest.mark.parametrize("address,expected", [
    ("aa:bb:cc:dd:ee:ff", "AA:BB:CC:DD:EE:FF"),
    ("b1a8f1a9-e7e9-43ec-85f6-e3b51b99490f", "B1A8F1A9-E7E9-43EC-85F6-E3B51B99490F"),
])
def test_bluetooth_addresses_accept_mac_and_macos_uuid(address, expected):
    assert valid_address(address) == expected


@pytest.mark.parametrize("address", ["", "Pendant", "../../config.json", "00:11:22:33:44", "AA:BB:CC:DD:EE:FF\n", "http://localhost"])
def test_invalid_address_is_rejected_without_changing_saved_config(tmp_path, address):
    settings = Settings.load(tmp_path)
    previous = (tmp_path / "config.json").read_bytes()
    with pytest.raises(ValueError, match="Bluetooth"):
        settings.configure_address(address)
    assert (tmp_path / "config.json").read_bytes() == previous


@pytest.mark.skipif(os.name == "nt", reason="POSIX mode bits are not Windows ACLs")
def test_credentials_and_data_directories_are_private_on_posix(tmp_path):
    Settings.load(tmp_path)
    for directory in (tmp_path, tmp_path / "keys", tmp_path / "captures"):
        assert stat.S_IMODE(directory.stat().st_mode) == 0o700
    assert stat.S_IMODE((tmp_path / "config.json").stat().st_mode) == 0o600
    assert "api_token" in json.loads((tmp_path / "config.json").read_text())
