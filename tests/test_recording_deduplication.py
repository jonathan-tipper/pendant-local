"""Repeat transfers, conservative identity and lossless legacy migration."""
import hashlib
import json
import sqlite3
from uuid import uuid4

import pytest

from pendant_api.capture import CaptureStore, decode_capture
from pendant_api.config import atomic_json
from pendant_api.recordings import RecordingStore
from pendant_client.proto import flash_page_pb2, server_pb2


ADDRESS = "AA:BB:CC:DD:EE:FF"


def saved_capture(root, pages=(1,), *, address=ADDRESS, run=1, reset=1, legacy=False, timestamp=1700000000000):
    folder = root / "captures" / str(uuid4())
    folder.mkdir(parents=True)
    atomic_json(folder / "capture.json", {"address": address, "device": {
        "device_id": "123", "storage_instance": "7", "factory_reset_id": reset}})
    atomic_json(folder / "job.json", {"started_at": f"2026-09-16T10:00:{pages[0]:02d}+00:00"})
    raw = CaptureStore(folder, address)
    try:
        for sequence, index in enumerate(pages):
            page = flash_page_pb2.FlashPage(absolute_timestamp_ms=timestamp, boot_uptime_ms=1000)
            for position in range(2):
                chunk = page.chunks.add(time_offset_ms=position * 20)
                chunk.audio_data.codec_beamforming_data = b"\xf8\xff\xfe"
                chunk.audio_data.did_start_recording = position == 0
                chunk.audio_data.did_stop_recording = position == 1
            msg = server_pb2.PendantAllMsg()
            msg.storage_buffer.ingest_type = 2
            msg.storage_buffer.run = run
            msg.storage_buffer.index = index
            msg.storage_buffer.flash_page = page.SerializeToString()
            raw.save(msg.SerializeToString(), sequence, msg)
    finally:
        raw.close()
    result = decode_capture(folder, root / "keys")
    if legacy:
        for item in result["recordings"]:
            item.pop("fingerprint")
        atomic_json(folder / "decode.json", result)
    return folder


def file_hashes(folder):
    return {str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in folder.rglob("*") if p.is_file() and p.suffix != ".sqlite3"}


def test_repeat_transfer_reuses_original_and_adds_only_new_audio(tmp_path):
    store = RecordingStore(tmp_path)
    first = saved_capture(tmp_path)
    original = store.ingest_capture_result(first.name)["recordings"][0]
    store.update(original["id"], {"title": "Keep this title", "notes": "Keep these notes", "tags": ["test"], "starred": True})
    store.update_transcription(original["id"], {"text": "Preserve transcript", "segments": []})
    second = saved_capture(tmp_path, (1, 2))
    result = store.ingest_capture_result(second.name)
    assert (result["added"], result["already_present"]) == (1, 1)
    kept = next(r for r in result["recordings"] if r["id"] == original["id"])
    assert kept["title"] == "Keep this title"
    assert kept["notes"] == "Keep these notes"
    assert kept["tags"] == ["test"] and kept["starred"]
    assert kept["transcript"]["text"] == "Preserve transcript"
    assert len(result["added_ids"]) == 1
    assert store.list_recordings()["total"] == 2
    retry = store.ingest_capture_result(second.name)
    assert (retry["added"], retry["already_present"]) == (0, 2)
    store.update(original["id"], {"archived": True})
    third = saved_capture(tmp_path)
    assert store.ingest_capture_result(third.name)["recordings"][0]["archived"]
    assert store.list_recordings()["total"] == 1


@pytest.mark.parametrize("changes", [{"pages": (2,)}, {"run": 2}, {"reset": 2},
    {"address": "11:22:33:44:55:66"}, {"timestamp": 1700000001000}])
def test_identical_audio_from_separate_device_events_is_not_merged(tmp_path, changes):
    store = RecordingStore(tmp_path)
    first = saved_capture(tmp_path)
    second = saved_capture(tmp_path, **changes)
    store.ingest_capture(first.name)
    assert store.ingest_capture_result(second.name)["added"] == 1
    assert store.list_recordings()["total"] == 2


def test_legacy_duplicates_are_archived_once_without_losing_edits_or_files(tmp_path):
    store = RecordingStore(tmp_path)
    folders = [saved_capture(tmp_path, legacy=True) for _ in range(2)]
    records = []
    for index, folder in enumerate(folders):
        atomic_json(folder / "job.json", {"started_at": f"2026-09-16T10:0{index}:00+00:00"})
        records.append(store.add_recording(folder / "audio/recording-0000.opus", f"Edited title {index}",
            source="pendant", source_key=f"capture:{folder.name}:audio/recording-0000.opus"))
    store.update(records[1]["id"], {"notes": "Notes on the second copy", "tags": ["keep"], "starred": True})
    before = file_hashes(tmp_path)
    store.index_existing_captures()
    assert store.list_recordings()["total"] == 1
    duplicate = store.list_recordings(archived=True)["recordings"][0]
    assert duplicate["id"] == records[1]["id"]
    assert duplicate["notes"] == "Notes on the second copy" and duplicate["starred"]
    assert file_hashes(tmp_path) == before
    # Archive is reversible; startup must not undo a deliberate restore.
    store.update(duplicate["id"], {"archived": False})
    RecordingStore(tmp_path).index_existing_captures()
    assert store.list_recordings()["total"] == 2
    assert file_hashes(tmp_path) == before


def test_legacy_archive_without_verifiable_raw_is_left_separate(tmp_path):
    store = RecordingStore(tmp_path)
    first = saved_capture(tmp_path, legacy=True)
    second = saved_capture(tmp_path, legacy=True)
    (second / "journal.jsonl").write_text("damaged journal")
    store.ingest_capture(first.name)
    assert store.ingest_capture_result(second.name)["added"] == 1
    assert store.list_recordings()["total"] == 2


def test_read_only_identity_pass_never_rewrites_audio_or_manifest(tmp_path):
    folder = saved_capture(tmp_path)
    before = file_hashes(folder)
    original = json.loads((folder / "decode.json").read_text())
    inspected = decode_capture(folder, tmp_path / "keys", fingerprints_only=True)
    assert inspected["recordings"] == original["recordings"]
    assert file_hashes(folder) == before


def test_index_transaction_rolls_back_if_source_mapping_cannot_be_saved(tmp_path):
    store = RecordingStore(tmp_path)
    folder = saved_capture(tmp_path)
    with store.connect() as db:
        db.execute("""CREATE TRIGGER reject_alias BEFORE INSERT ON capture_recording_sources
            BEGIN SELECT RAISE(ABORT, 'simulated write failure'); END""")
    with pytest.raises(sqlite3.IntegrityError):
        store.ingest_capture(folder.name)
    with store.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM recordings").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM pendant_fingerprints").fetchone()[0] == 0
    assert (folder / "capture.bin").is_file()
