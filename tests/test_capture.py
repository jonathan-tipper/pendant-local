import asyncio
import importlib
import json
from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest

from pendant_client.decode import iter_messages_from_bin
from pendant_client.proto import flash_page_pb2, server_pb2

capture_module = importlib.import_module("pendant_api.capture")
device_module = importlib.import_module("pendant_api.device")


def storage_message(index, error=0):
    page = flash_page_pb2.FlashPage(absolute_timestamp_ms=1700000000000)
    page.chunks.add().audio_data.codec_beamforming_data = b"\xf8\xff\xfe"
    msg = server_pb2.PendantAllMsg()
    msg.storage_buffer.ingest_type = 2
    msg.storage_buffer.index = index
    msg.storage_buffer.run = 1
    msg.storage_buffer.flash_page = page.SerializeToString()
    msg.storage_buffer.flash_page_error = error
    return msg.SerializeToString(), msg


class FakeSession:
    def __init__(self, messages, oldest=1):
        self._inbox = asyncio.Queue()
        for message in messages:
            self._inbox.put_nowait(message)
        self.deleted = []
        self.stopped = False
        self.oldest = oldest
        self.before_delete = None

    async def get_device_info(self):
        return SimpleNamespace(device_id=1, serial_num="test", firmware_ver="1.1.20",
            battery_percent=70, oldest_flash_page=self.oldest, newest_flash_page=3,
            audio_encryption_pub_key=b"", raw=SimpleNamespace())

    async def begin_batch_download(self):
        pass

    async def stop_batch_download(self):
        self.stopped = True

    async def delete_flash_page(self, index):
        if self.before_delete:
            self.before_delete(index)
        self.deleted.append(index)


def use_session(monkeypatch, session):
    @asynccontextmanager
    async def connected(address):
        yield session
    monkeypatch.setattr(capture_module, "connected", connected)


def run_capture(folder, acknowledge=False):
    return asyncio.run(capture_module.capture("TEST", folder,
        acknowledge=acknowledge, idle_timeout=0.01, max_seconds=1))


def test_capture_defaults_to_no_delete_and_raw_is_replayable(tmp_path, monkeypatch):
    messages = [storage_message(1), storage_message(2)]
    session = FakeSession(messages)
    use_session(monkeypatch, session)
    result = run_capture(tmp_path)
    assert session.deleted == []
    assert session.stopped
    assert result["messages_saved"] == 2
    assert list(iter_messages_from_bin(tmp_path / "capture.bin")) == [p for p, _ in messages]
    assert not result["complete"]


def test_status_only_capture_is_distinguished_from_audio(tmp_path, monkeypatch):
    page = flash_page_pb2.FlashPage(absolute_timestamp_ms=1700000000000)
    page.chunks.add().battery_status.soc = 50
    msg = server_pb2.PendantAllMsg()
    msg.storage_buffer.ingest_type = 2
    msg.storage_buffer.index = 1
    msg.storage_buffer.flash_page = page.SerializeToString()
    session = FakeSession([(msg.SerializeToString(), msg)])
    use_session(monkeypatch, session)
    run_capture(tmp_path)
    result = capture_module.decode_capture(tmp_path, tmp_path / "keys")
    assert result["recordings"] == []
    assert result["warnings"] == {}
    assert result["content"] == {"pages": 1, "audio_chunks": 0, "status_chunks": 1}
    assert session.deleted == []


def test_raw_and_journal_are_fsynced_before_cumulative_delete(tmp_path, monkeypatch):
    session = FakeSession([storage_message(1), storage_message(2)])
    use_session(monkeypatch, session)
    fsynced = []
    original_flush = capture_module._flush

    def flush(handle):
        original_flush(handle)
        fsynced.append(handle.name)
    monkeypatch.setattr(capture_module, "_flush", flush)

    def verify_before_delete(index):
        assert fsynced[-2:] == [str(tmp_path / "capture.bin"), str(tmp_path / "journal.jsonl")]
        assert len(list(iter_messages_from_bin(tmp_path / "capture.bin"))) == index
        journal = [json.loads(line) for line in (tmp_path / "journal.jsonl").read_text().splitlines()]
        assert journal[-1]["event"] == "saved"
        assert journal[-1]["page_index"] == index
    session.before_delete = verify_before_delete
    result = run_capture(tmp_path, acknowledge=True)
    assert session.deleted == [1, 2]
    assert result["delete_commands_sent"] == 2


def test_gap_never_cumulatively_deletes_missing_page(tmp_path, monkeypatch):
    session = FakeSession([storage_message(1), storage_message(3)])
    use_session(monkeypatch, session)
    result = run_capture(tmp_path, acknowledge=True)
    assert session.deleted == [1]
    assert result["stop_reason"] == "page_gap"
    assert result["expected_page_index"] == 2
    assert result["messages_saved"] == 2


def test_first_page_gap_does_not_delete_anything(tmp_path, monkeypatch):
    session = FakeSession([storage_message(3)])
    use_session(monkeypatch, session)
    result = run_capture(tmp_path, acknowledge=True)
    assert session.deleted == []
    assert result["stop_reason"] == "page_gap"


def test_disk_failure_prevents_ack_and_keeps_partial_metadata(tmp_path, monkeypatch):
    session = FakeSession([storage_message(1)])
    use_session(monkeypatch, session)

    def fail_save(self, payload, sequence, msg):
        raise OSError("disk full")
    monkeypatch.setattr(capture_module.CaptureStore, "save", fail_save)
    with pytest.raises(OSError, match="disk full"):
        run_capture(tmp_path, acknowledge=True)
    assert session.deleted == []
    assert session.stopped
    meta = json.loads((tmp_path / "capture.json").read_text())
    assert meta["status"] == "partial"
    assert meta["error_type"] == "OSError"


def test_cancellation_keeps_durable_prefix_and_stops_download(tmp_path, monkeypatch):
    session = FakeSession([])
    message = storage_message(1)

    class CancelQueue:
        calls = 0
        async def get(self):
            self.calls += 1
            if self.calls == 1:
                return message
            raise asyncio.CancelledError()
    session._inbox = CancelQueue()
    use_session(monkeypatch, session)
    with pytest.raises(asyncio.CancelledError):
        run_capture(tmp_path)
    assert session.stopped
    assert session.deleted == []
    assert list(iter_messages_from_bin(tmp_path / "capture.bin")) == [message[0]]
    meta = json.loads((tmp_path / "capture.json").read_text())
    assert meta["stop_reason"] == "cancelled"
    assert meta["messages_saved"] == 1


def test_corrupt_page_is_archived_but_never_acknowledged(tmp_path, monkeypatch):
    session = FakeSession([storage_message(1, error=1)])
    use_session(monkeypatch, session)
    result = run_capture(tmp_path, acknowledge=True)
    assert session.deleted == []
    assert result["stop_reason"] == "page_error"
    assert len(list(iter_messages_from_bin(tmp_path / "capture.bin"))) == 1


def test_repeated_page_stops_no_delete_capture_without_duplicate_audio(tmp_path, monkeypatch):
    message = storage_message(1)
    session = FakeSession([message, message])
    use_session(monkeypatch, session)
    result = run_capture(tmp_path)
    assert result["stop_reason"] == "repeated_page"
    decoded = capture_module.decode_capture(tmp_path, tmp_path / "keys")
    assert decoded["recordings"][0]["packets"] == 1
    assert decoded["recordings"][0]["duration_seconds"] == 0.02
    assert (tmp_path / "audio/recording-0000.opus").read_bytes().startswith(b"OggS")


def test_key_file_exists_durably_before_device_is_changed(tmp_path, monkeypatch):
    from cryptography.hazmat.primitives.asymmetric import ec
    from pendant_client.crypto import export_server_pubkey
    public = export_server_pubkey(ec.generate_private_key(ec.SECP256R1()))
    sent = []

    class KeySession(FakeSession):
        async def get_device_info(self):
            value = await super().get_device_info()
            value.audio_encryption_pub_key = public
            return value
        async def set_server_public_key(self, value):
            private = tmp_path / device_module.key_id("TEST") / "server-key.pem"
            assert private.read_bytes().startswith(b"-----BEGIN PRIVATE KEY-----")
            assert (private.parent / "device.json").exists()
            if __import__("os").name != "nt":
                assert private.stat().st_mode & 0o777 == 0o600
            sent.append(value)

    @asynccontextmanager
    async def connected(address):
        yield KeySession([])
    monkeypatch.setattr(device_module, "connected", connected)
    first = asyncio.run(device_module.provision_key("TEST", tmp_path))
    second = asyncio.run(device_module.provision_key("TEST", tmp_path))
    assert first["new_key_created"]
    assert not second["new_key_created"]
    assert sent[0] == sent[1]
    assert "PRIVATE" not in json.dumps(first)


def test_run_change_stops_cumulative_acknowledgement(tmp_path, monkeypatch):
    payload, second = storage_message(2)
    second.storage_buffer.run = 2
    session = FakeSession([storage_message(1), (second.SerializeToString(), second)])
    use_session(monkeypatch, session)
    result = run_capture(tmp_path, acknowledge=True)
    assert session.deleted == [1]
    assert result["stop_reason"] == "storage_run_changed"


@pytest.mark.parametrize("damage", ["truncated_saved_message", "uncommitted_tail"])
def test_decode_uses_only_integrity_checked_durable_prefix(tmp_path, monkeypatch, damage):
    messages = [storage_message(1)]
    if damage == "truncated_saved_message":
        messages.append(storage_message(2))
    session = FakeSession(messages)
    use_session(monkeypatch, session)
    run_capture(tmp_path)
    archive = tmp_path / "capture.bin"
    data = archive.read_bytes()
    archive.write_bytes(data[:-2] if damage == "truncated_saved_message" else data + b"\x0a\xff")
    decoded = capture_module.decode_capture(tmp_path, tmp_path / "keys")
    assert decoded["recordings"][0]["packets"] == 1
    assert decoded["warnings"]["unverified_or_truncated_archive_tail"] == 1
    assert decoded["status"] == "decoded_with_warnings"


def test_decode_removes_previous_derived_outputs(tmp_path, monkeypatch):
    session = FakeSession([storage_message(1)])
    use_session(monkeypatch, session)
    run_capture(tmp_path)
    (tmp_path / "audio").mkdir()
    stale = tmp_path / "audio/recording-9999.opus"
    stale.write_bytes(b"old derived output")
    capture_module.decode_capture(tmp_path, tmp_path / "keys")
    assert not stale.exists()


def test_decode_durable_close_failure_is_not_reported_as_success(tmp_path, monkeypatch):
    session = FakeSession([storage_message(1)])
    use_session(monkeypatch, session)
    run_capture(tmp_path)
    original = capture_module._flush

    def fail_audio_flush(handle):
        if str(handle.name).endswith(".opus.tmp"):
            raise OSError("disk full")
        original(handle)
    monkeypatch.setattr(capture_module, "_flush", fail_audio_flush)
    with pytest.raises(OSError, match="disk full"):
        capture_module.decode_capture(tmp_path, tmp_path / "keys")
    assert not (tmp_path / "audio/recording-0000.opus").exists()
    assert json.loads((tmp_path / "decode.json").read_text())["status"] != "decoded"


def test_low_mtu_is_not_given_upstream_150_byte_fragment_floor(monkeypatch):
    transport = SimpleNamespace(_fragment_payload=150, _write_with_response=True)

    class SmallMtuSession:
        def __init__(self, address):
            self._transport = transport
            self._client = SimpleNamespace(mtu_size=23)
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass

    monkeypatch.setattr(device_module, "PendantSession", SmallMtuSession)

    async def check():
        async with device_module.connected("TEST"):
            assert 1 <= transport._fragment_payload < 20
    asyncio.run(check())


@pytest.mark.parametrize("fail_on_enter", [True, False])
def test_pairing_failure_does_not_repeat_upstream_reset_instructions(monkeypatch, fail_on_enter):
    from pendant_client.ble import PendantNotPairedError
    cleaned = []

    class PairingSession:
        def __init__(self, address):
            self._transport = None
            self._client = self
        async def __aenter__(self):
            if fail_on_enter:
                raise PendantNotPairedError("upstream destructive recovery instructions")
            return self
        async def __aexit__(self, *args):
            cleaned.append(True)
        async def disconnect(self):
            cleaned.append(True)

    monkeypatch.setattr(device_module, "PendantSession", PairingSession)

    async def check():
        async with device_module.connected("TEST"):
            raise PendantNotPairedError("upstream destructive recovery instructions")
    with pytest.raises(RuntimeError) as caught:
        asyncio.run(check())
    assert "Preserve any unsynced recordings" in str(caught.value)
    assert "upstream destructive" not in str(caught.value)
    assert cleaned


def test_ogg_final_packet_decodes_without_ffmpeg_errors(tmp_path, monkeypatch):
    import shutil
    import subprocess
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        pytest.skip("ffmpeg is not installed")
    page = flash_page_pb2.FlashPage(absolute_timestamp_ms=1700000000000)
    for _ in range(50):
        page.chunks.add().audio_data.codec_beamforming_data = b"\xf8\xff\xfe"
    msg = server_pb2.PendantAllMsg()
    msg.storage_buffer.ingest_type = 2
    msg.storage_buffer.index = 1
    msg.storage_buffer.run = 1
    msg.storage_buffer.flash_page = page.SerializeToString()
    session = FakeSession([(msg.SerializeToString(), msg)])
    use_session(monkeypatch, session)
    run_capture(tmp_path)
    decoded = capture_module.decode_capture(tmp_path, tmp_path / "keys")
    recording = decoded["recordings"][0]
    assert recording["duration_seconds"] == 1
    result = subprocess.run([ffmpeg, "-v", "error", "-i", str(tmp_path / recording["file"]),
                             "-f", "null", "-"], capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""


def test_long_transfer_passes_old_five_minute_boundary_and_stops_durably(tmp_path, monkeypatch):
    clock = SimpleNamespace(value=0)
    original_time = capture_module.time
    monkeypatch.setattr(capture_module, 'time', SimpleNamespace(
        time=original_time.time, monotonic=lambda: clock.value))
    messages = [storage_message(i) for i in range(1, 5)]
    session = FakeSession([])

    class TimedInbox:
        async def get(self):
            clock.value += 600
            return messages[int(clock.value / 600) - 1]

    session._inbox = TimedInbox()
    use_session(monkeypatch, session)
    result = asyncio.run(capture_module.capture('TEST', tmp_path, max_seconds=1800))
    assert result['stop_reason'] == 'time_limit'
    assert result['unique_pages_saved'] == 3  # Pages after the former 300-second cap survive.
    assert result['complete'] is False
    assert session.stopped and session.deleted == []
    assert list(iter_messages_from_bin(tmp_path / 'capture.bin')) == [p for p, _ in messages[:3]]
