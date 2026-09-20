"""Durable raw capture, conservative acknowledgement, and offline decoding."""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import time
from pathlib import Path

from pendant_client.cli import OggOpusWriter
from pendant_client.crypto import decrypt_audio, keyset_from_existing
from pendant_client.decode import RecordingSplitter
from pendant_client.flash_page import parse_flash_page
from pendant_client.session import AudioChunk, parse_pendant_all

from .device import connected, durable_json, info_dict, key_id, sync_directory


def _varint(value: int) -> bytes:
    out = bytearray()
    while value > 127:
        out.append((value & 127) | 128)
        value >>= 7
    out.append(value)
    return bytes(out)


def _flush(handle) -> None:
    handle.flush()
    os.fsync(handle.fileno())


class CaptureStore:
    """Each saved message is recoverable without a successful capture close."""

    def __init__(self, folder: Path, address: str):
        folder.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.folder = folder
        self.raw = None
        self.journal = None
        try:
            self.raw = (folder / "capture.bin").open("xb")
            self.journal = (folder / "journal.jsonl").open("x", encoding="utf-8")
            # BatchIngestRequest field 2 is legal before repeated field 1.
            identifier = address.encode()
            self.raw.write(b"\x12" + _varint(len(identifier)) + identifier)
            _flush(self.raw)
            _flush(self.journal)
            sync_directory(folder)
            sync_directory(folder.parent)
        except BaseException:
            self.close()
            raise

    def event(self, event: dict) -> None:
        self.journal.write(json.dumps(event, separators=(",", ":")) + "\n")
        _flush(self.journal)

    def save(self, payload: bytes, sequence: int, msg) -> None:
        start = self.raw.tell()
        self.raw.write(b"\x0a" + _varint(len(payload)) + payload)
        _flush(self.raw)
        sb = msg.storage_buffer if msg.WhichOneof("content") == "storage_buffer" else None
        self.event({"event": "saved", "sequence": sequence,
                    "offset": start, "end_offset": self.raw.tell(),
                    "received_unix_ms": int(time.time() * 1000),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "page_index": sb.index if sb is not None else None,
                    "ingest_type": sb.ingest_type if sb is not None else None})

    def close(self) -> None:
        for handle in (self.raw, self.journal):
            if handle is not None:
                handle.close()


async def capture(address: str, output_dir: Path, acknowledge: bool = False,
                  idle_timeout: float = 5, max_seconds: float = 60) -> dict:
    """Capture without deletion by default. An idle timeout is not proof of completeness.

    Explicit acknowledgement deletes cumulatively, only from the observed oldest
    page through an unbroken sequence of durably archived, error-free batch pages.
    Other ingest streams and ambiguous indexes stop acknowledgement immediately.
    """
    if idle_timeout <= 0 or max_seconds <= 0:
        raise ValueError("Capture time limits must be positive")
    folder = Path(output_dir)
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    if any((folder / name).exists() for name in ("capture.bin", "capture.json", "journal.jsonl")):
        raise FileExistsError("Capture directory already contains an archive")
    result = {"address": address, "status": "running", "stop_reason": None,
              "acknowledge": acknowledge, "messages_saved": 0,
              "unique_pages_saved": 0, "delete_commands_sent": 0,
              "last_delete_index": None, "complete": False,
              "raw_file": "capture.bin", "journal_file": "journal.jsonl",
              "started_unix_ms": int(time.time() * 1000)}
    store = None
    try:
        async with connected(address) as session:
            di = await session.get_device_info()
            result["connection_attempts"] = getattr(session, "connection_attempts", 1)
            result["device"] = info_dict(di, address)
            durable_json(folder / "capture.json", result)
            store = CaptureStore(folder, address)
            expected = di.oldest_flash_page
            acknowledged_run = None
            seen: dict[tuple[int, int, int], str] = {}
            deadline = time.monotonic() + max_seconds
            started = False
            try:
                # Set before sending: cleanup is still needed if a write partly succeeds.
                started = True
                await session.begin_batch_download()
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        result["stop_reason"] = "time_limit"
                        break
                    try:
                        payload, msg = await asyncio.wait_for(
                            session._inbox.get(), min(idle_timeout, remaining))
                    except asyncio.TimeoutError:
                        result["stop_reason"] = "time_limit" if time.monotonic() >= deadline else "idle_timeout"
                        break
                    store.save(payload, result["messages_saved"], msg)
                    result["messages_saved"] += 1
                    if msg.WhichOneof("content") != "storage_buffer":
                        continue
                    sb = msg.storage_buffer
                    identity = (sb.ingest_type, sb.run, sb.index)
                    digest = hashlib.sha256(sb.flash_page).hexdigest()
                    if identity in seen:
                        result["stop_reason"] = "repeated_page" if seen[identity] == digest else "page_changed"
                        break
                    seen[identity] = digest
                    result["unique_pages_saved"] += 1
                    if not acknowledge:
                        continue
                    if sb.ingest_type != 2:
                        result["stop_reason"] = "unexpected_ingest_type"
                        break
                    if acknowledged_run is not None and sb.run != acknowledged_run:
                        result["stop_reason"] = "storage_run_changed"
                        break
                    if sb.flash_page_error or not sb.flash_page:
                        result["stop_reason"] = "page_error"
                        break
                    try:
                        parse_flash_page(bytes(sb.flash_page))
                    except Exception:
                        result["stop_reason"] = "malformed_page"
                        break
                    if not (0 <= expected <= 0x7FFFFFFF) or sb.index < 0:
                        result["stop_reason"] = "invalid_page_index"
                        break
                    if sb.index != expected:
                        result["stop_reason"] = "page_gap"
                        result["expected_page_index"] = expected
                        result["received_page_index"] = sb.index
                        break
                    # Both raw bytes and their journal entry have been fsynced.
                    # Do not use upstream's error-swallowing download generator.
                    await session.delete_flash_page(sb.index)
                    acknowledged_run = sb.run
                    result["delete_commands_sent"] += 1
                    result["last_delete_index"] = sb.index
                    store.event({"event": "delete_command_sent", "page_index": sb.index})
                    expected += 1
            finally:
                if started:
                    try:
                        await session.stop_batch_download()
                    except Exception as exc:
                        result["cleanup_error"] = type(exc).__name__
            result["status"] = "captured" if result["stop_reason"] == "idle_timeout" else "partial"
    except BaseException as exc:
        result["status"] = "partial"
        result["stop_reason"] = "cancelled" if isinstance(exc, asyncio.CancelledError) else "error"
        result["error_type"] = type(exc).__name__
        raise
    finally:
        result["finished_unix_ms"] = int(time.time() * 1000)
        if store is not None:
            store.close()
        # If the disk itself has failed this may fail too; the fsynced prefix remains.
        durable_json(folder / "capture.json", result)
    return result


def _opus_samples(packet: bytes) -> int:
    """Ogg granules use 48 kHz; derive duration from the Opus TOC."""
    if not packet:
        raise ValueError("Empty Opus packet")
    config = packet[0] >> 3
    if config >= 16:
        frame_samples = 120 << (config & 3)
    elif config >= 12:
        frame_samples = 960 if config & 1 else 480
    else:
        frame_samples = (480, 960, 1920, 2880)[config & 3]
    code = packet[0] & 3
    if code == 0:
        frames = 1
    elif code in (1, 2):
        frames = 2
    elif len(packet) >= 2:
        frames = packet[1] & 63
    else:
        raise ValueError("Truncated Opus packet")
    samples = frames * frame_samples
    if frames == 0 or samples > 5760:
        raise ValueError("Invalid Opus packet duration")
    return samples


class _FingerprintWriter:
    """Identify the same device audio independently of its Ogg stream serial.

    Page/run/time provenance keeps separate recordings of identical silence
    distinct. Receipt times and transfer IDs deliberately do not participate.
    """
    def __init__(self, path: Path, scope: list):
        self.path = path
        self.packets = 0
        self.samples = 0
        self.opened_with_start_marker = False
        self.closed_with_stop_marker = False
        self.digest = hashlib.sha256(json.dumps(scope, separators=(",", ":")).encode())
        self.start_fingerprint = None
        self.prefix_packets = set()
        self.prefix_fingerprints = {}

    def add(self, chunk) -> None:
        self.samples += _opus_samples(chunk.opus)
        self.packets += 1
        provenance = [chunk.run, chunk.page_index, chunk.absolute_timestamp_ms,
                      chunk.boot_uptime_ms, chunk.chunk.time_offset_ms, len(chunk.opus)]
        self.digest.update(json.dumps(provenance, separators=(",", ":")).encode() + b"\0")
        self.digest.update(chunk.opus)
        if self.packets == 1:
            self.start_fingerprint = self.fingerprint
        if self.packets in self.prefix_packets:
            self.prefix_fingerprints[str(self.packets)] = self.fingerprint

    @property
    def fingerprint(self):
        return "pendant-audio-v1:" + self.digest.hexdigest()

    def close(self) -> None:
        pass


class _Writer(_FingerprintWriter):
    def __init__(self, path: Path, scope: list):
        super().__init__(path, scope)
        self.tmp = path.with_suffix(path.suffix + ".tmp")
        self.writer = OggOpusWriter(self.tmp)
        self.pending_packet = None
        self.closed = False

    def add(self, chunk) -> None:
        samples = _opus_samples(chunk.opus)
        super().add(chunk)
        if self.pending_packet is not None:
            previous, previous_samples = self.pending_packet
            self.writer._granule += previous_samples
            self.writer._write_page(previous, granule=self.writer._granule)
        # Retain one packet so EOS can be set on the final real Opus packet.
        # An additional empty packet is invalid audio, even if its Ogg CRC is valid.
        self.pending_packet = (chunk.opus, samples)

    def close(self) -> None:
        if not self.closed:
            # Upstream close suppresses write/flush errors. Surface them here,
            # and expose the finished recording only after a durable close.
            self.closed = True
            try:
                if self.pending_packet is not None:
                    packet, samples = self.pending_packet
                    self.writer._granule += samples
                    self.writer._write_page(packet, is_last=True, granule=self.writer._granule)
                    self.pending_packet = None
                _flush(self.writer._fp)
            finally:
                self.writer._fp.close()
            os.replace(self.tmp, self.path)
            sync_directory(self.path.parent)


def _verified_messages(folder: Path, address: str, warn):
    """Only journal-committed messages survive replay, including after a crash."""
    identifier = address.encode()
    expected_offset = 1 + len(_varint(len(identifier))) + len(identifier)
    with (folder / "capture.bin").open("rb") as raw, (folder / "journal.jsonl").open() as journal:
        for line in journal:
            try:
                record = json.loads(line)
            except (ValueError, UnicodeError):
                warn("incomplete_journal_tail")
                break
            if record.get("event") != "saved":
                continue
            try:
                start, end = record["offset"], record["end_offset"]
                if not isinstance(start, int) or not isinstance(end, int) or start != expected_offset or end <= start:
                    raise ValueError("Invalid journal offsets")
                raw.seek(start)
                frame = raw.read(end - start)
                if len(frame) != end - start or frame[:1] != b"\x0a":
                    raise ValueError("Incomplete protobuf record")
                length = 0
                shift = 0
                pos = 1
                while True:
                    if pos >= len(frame) or shift > 63:
                        raise ValueError("Invalid protobuf length")
                    value = frame[pos]
                    pos += 1
                    length |= (value & 127) << shift
                    if not value & 128:
                        break
                    shift += 7
                payload = frame[pos:]
                if len(payload) != length or hashlib.sha256(payload).hexdigest() != record["sha256"]:
                    raise ValueError("Archive integrity check failed")
            except (ValueError, TypeError, KeyError):
                warn("unverified_archive_record")
                break
            expected_offset = end
            yield payload
        raw.seek(0, os.SEEK_END)
        if raw.tell() != expected_offset:
            warn("unverified_or_truncated_archive_tail")


def decode_capture(output_dir: Path, keys_dir: Path, *, fingerprints_only: bool = False,
                   prefix_packets: set[int] | None = None) -> dict:
    """Decode the saved archive, never contacting the Pendant or a cloud API."""
    folder = Path(output_dir)
    metadata = json.loads((folder / "capture.json").read_text())
    device = metadata.get("device", {})
    keys = None
    private_path = Path(keys_dir) / key_id(metadata["address"]) / "server-key.pem"
    if private_path.exists() and device.get("pendant_public_key_hex"):
        keys = keyset_from_existing(private_path.read_bytes(), bytes.fromhex(device["pendant_public_key_hex"]))
    audio_dir = folder / "audio"
    if not fingerprints_only:
        audio_dir.mkdir(exist_ok=True, mode=0o700)
        durable_json(folder / "decode.json", {"status": "decoding", "recordings": []})
        for old in [*audio_dir.glob("recording-*.opus"), *audio_dir.glob("recording-*.opus.tmp")]:
            old.unlink()
    writers = []
    warnings: dict[str, int] = {}
    content = {"pages": 0, "audio_chunks": 0, "status_chunks": 0}
    seen = set()

    def warn(kind: str):
        warnings[kind] = warnings.get(kind, 0) + 1

    def open_writer(index, chunk):
        scope = [metadata["address"].upper(), device.get("device_id"),
                 device.get("storage_instance"), device.get("factory_reset_id")]
        writer_type = _FingerprintWriter if fingerprints_only else _Writer
        writer = writer_type(audio_dir / f"recording-{index:04d}.opus", scope)
        writer.prefix_packets = prefix_packets or set()
        writers.append(writer)
        return writer

    splitter = RecordingSplitter(open_writer)
    try:
        for payload in _verified_messages(folder, metadata["address"], warn):
            try:
                msg = parse_pendant_all(payload)
                if msg.WhichOneof("content") != "storage_buffer":
                    continue
                sb = msg.storage_buffer
                if sb.ingest_type not in (1, 2):
                    continue
                identity = (sb.ingest_type, sb.run, sb.index, hashlib.sha256(sb.flash_page).digest())
                if identity in seen:
                    continue
                seen.add(identity)
                if sb.flash_page_error:
                    warn("flash_page_errors")
                page = parse_flash_page(bytes(sb.flash_page))
                content["pages"] += 1
            except Exception:
                warn("malformed_messages")
                continue
            for chunk in page.chunks:
                if chunk.audio is not None and chunk.audio.has_audio:
                    content["audio_chunks"] += 1
                elif chunk.audio is None:
                    content["status_chunks"] += 1
                if chunk.audio is not None:
                    audio = chunk.audio
                    if audio.encrypted is not None:
                        if keys is None:
                            warn("encrypted_chunks_without_key")
                            continue
                        try:
                            audio.opus_packets = decrypt_audio(audio, keys.aes_key)
                        except Exception:
                            warn("decryption_failures")
                            continue
                        # Offset semantics for multi-packet encrypted chunks need
                        # hardware validation; retain raw data rather than emit noise.
                        offsets = audio.encrypted.packet_offsets
                        if len(offsets) > 1 or (offsets and offsets[0] not in (0, len(audio.opus_packets))):
                            warn("unsupported_packet_offsets")
                            continue
                    if audio.opus_packets:
                        try:
                            _opus_samples(audio.opus_packets)
                        except ValueError:
                            warn("invalid_opus_packets")
                            continue
                wrapped = AudioChunk(chunk=chunk, page_index=sb.index,
                    storage_session=sb.session, run=sb.run, ingest_type=sb.ingest_type,
                    absolute_timestamp_ms=page.absolute_timestamp_ms,
                    boot_uptime_ms=page.boot_uptime_ms)
                splitter.feed(wrapped)
    finally:
        splitter.finalize()
        for writer in writers:
            writer.close()
    files = [{"file": "audio/" + writer.path.name, "packets": writer.packets,
              "fingerprint": writer.fingerprint,
              "start_fingerprint": writer.start_fingerprint,
              **({"prefix_fingerprints": writer.prefix_fingerprints} if prefix_packets else {}),
              "duration_seconds": writer.samples / 48000,
              "opened_with_start_marker": writer.opened_with_start_marker,
              "closed_with_stop_marker": writer.closed_with_stop_marker}
             for writer in writers if writer.packets]
    result = {"status": "decoded_with_warnings" if warnings else "decoded",
              "recordings": files, "warnings": warnings,
              "content": content,
              "recording_boundaries": "Heuristic; VAD sessions may be joined.",
              "raw_capture_preserved": True}
    if not fingerprints_only:
        durable_json(folder / "decode.json", result)
    return result
