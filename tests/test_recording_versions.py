"""Growing partial recordings: exact provenance, lossless migration and retry."""
import json
import sqlite3
from uuid import uuid4

import pytest

from pendant_api.capture import CaptureStore, decode_capture
from pendant_api.config import atomic_json
from pendant_api.recordings import RecordingStore
from pendant_client.proto import flash_page_pb2, server_pb2
from test_recording_deduplication import ADDRESS, file_hashes


def partial_capture(root, packets, *, closed=False, start=True, run=1, changed=None, offset=0):
    folder = root / 'captures' / str(uuid4())
    folder.mkdir(parents=True)
    atomic_json(folder / 'capture.json', {'address': ADDRESS, 'device': {'device_id': 123,
        'storage_instance': 7, 'factory_reset_id': 1}, 'stop_reason': 'time_limit'})
    atomic_json(folder / 'job.json', {'started_at': f'2026-09-18T10:00:{offset:02d}+00:00'})
    page = flash_page_pb2.FlashPage(absolute_timestamp_ms=1700000000000, boot_uptime_ms=1000)
    if start:
        page.chunks.add().audio_data.did_start_recording = True
    for position in range(packets):
        chunk = page.chunks.add(time_offset_ms=position * 20)
        chunk.audio_data.codec_beamforming_data = b'\xf8\xff\xfe' if position != changed else b'\xf8\xff\xfd'
    if closed:
        page.chunks.add().audio_data.did_stop_recording = True
    msg = server_pb2.PendantAllMsg()
    msg.storage_buffer.ingest_type = 2
    msg.storage_buffer.run = run
    msg.storage_buffer.index = 1
    msg.storage_buffer.flash_page = page.SerializeToString()
    raw = CaptureStore(folder, ADDRESS)
    try:
        raw.save(msg.SerializeToString(), 0, msg)
    finally:
        raw.close()
    decode_capture(folder, root / 'keys')
    return folder


def test_longer_copy_extends_same_id_preserving_edits_transcript_and_all_files(tmp_path):
    store = RecordingStore(tmp_path)
    short = partial_capture(tmp_path, 20)
    original = store.ingest_capture(short.name)[0]
    store.update(original['id'], {'title': 'Meeting', 'notes': 'Decisions', 'tags': ['work'], 'starred': True})
    transcript = {'text': 'Existing text', 'duration': .4, 'speakers': {'one': 'Alex'}}
    store.update_transcription(original['id'], transcript)
    long = partial_capture(tmp_path, 40, closed=True)
    hashes = file_hashes(tmp_path)
    result = store.ingest_capture_result(long.name)
    assert (result['added'], result['extended'], result['already_present']) == (0, 1, 1)
    kept = result['recordings'][0]
    assert kept['id'] == original['id'] and kept['duration_seconds'] == .8
    assert kept['title'] == 'Meeting' and kept['notes'] == 'Decisions'
    assert kept['tags'] == ['work'] and kept['starred']
    assert kept['transcript'] == transcript and kept['transcript_needs_update']
    assert kept['audio_incomplete'] is False and kept['audio_version_count'] == 2
    assert store.list_recordings()['total'] == 1 and result['added_ids'] == []
    assert store.ingest_capture_result(long.name)['extended'] == 0
    shorter_retry = partial_capture(tmp_path, 20)
    assert store.ingest_capture(shorter_retry.name)[0]['duration_seconds'] == .8
    assert all(file_hashes(tmp_path)[name] == digest for name, digest in hashes.items())


@pytest.mark.parametrize('first,second', [(40, 20), (20, 40)])
def test_both_arrival_orders_keep_longest(tmp_path, first, second):
    store = RecordingStore(tmp_path)
    original = store.ingest_capture(partial_capture(tmp_path, first).name)[0]
    result = store.ingest_capture(partial_capture(tmp_path, second).name)[0]
    assert result['id'] == original['id'] and result['duration_seconds'] == .8
    assert result['audio_incomplete']


@pytest.mark.parametrize('changes', [{'run': 2}, {'start': False}, {'changed': 10}])
def test_uncertain_or_different_audio_stays_separate(tmp_path, changes):
    store = RecordingStore(tmp_path)
    store.ingest_capture(partial_capture(tmp_path, 20).name)
    result = store.ingest_capture_result(partial_capture(tmp_path, 40, **changes).name)
    assert result['added'] == 1 and result['extended'] == 0


def test_completed_recording_is_not_extended_past_its_stop(tmp_path):
    store = RecordingStore(tmp_path)
    store.ingest_capture(partial_capture(tmp_path, 20, closed=True).name)
    assert store.ingest_capture_result(partial_capture(tmp_path, 40).name)['added'] == 1


def test_later_stop_marker_with_identical_audio_updates_completion(tmp_path):
    store = RecordingStore(tmp_path)
    first = store.ingest_capture(partial_capture(tmp_path, 20).name)[0]
    result = store.ingest_capture(partial_capture(tmp_path, 20, closed=True).name)[0]
    assert result['id'] == first['id'] and result['audio_incomplete'] is False


def test_legacy_three_versions_consolidate_edits_once_and_restore_remains_respected(tmp_path):
    store = RecordingStore(tmp_path)
    folders = [partial_capture(tmp_path, count, offset=i) for i, count in enumerate((40, 20, 30))]
    records = []
    for i, folder in enumerate(folders):
        records.append(store.add_recording(folder / 'audio/recording-0000.opus',
            'Custom meeting title' if i == 1 else 'Pendant recording 1', source='pendant',
            source_key=f'capture:{folder.name}:audio/recording-0000.opus', duration_seconds=(40,20,30)[i]*.02))
        # Simulate existing exact-only indexes from 0.4.1.
        item = json.loads((folder / 'decode.json').read_text())['recordings'][0]
        with store.connect() as db:
            db.execute('INSERT INTO pendant_fingerprints VALUES (?,?)', (item['fingerprint'], records[-1]['id']))
            db.execute('INSERT INTO capture_recording_sources VALUES (?,?)',
                       (f'capture:{folder.name}:audio/recording-0000.opus', records[-1]['id']))
    store.update(records[0]['id'], {'notes': 'First notes', 'tags': ['a']})
    store.update(records[1]['id'], {'notes': 'Second notes', 'tags': ['b'], 'starred': True})
    store.update_transcription(records[1]['id'], {'text': 'Old transcript', 'duration': .4})
    hashes = file_hashes(tmp_path)
    store.index_existing_captures()
    active = store.list_recordings()['recordings']
    assert len(active) == 1 and active[0]['id'] == records[0]['id']
    main = store.detail(records[0]['id'])
    assert main['title'] == 'Custom meeting title' and main['duration_seconds'] == .8
    assert main['notes'] == 'First notes\n\nSecond notes' and main['tags'] == ['a', 'b'] and main['starred']
    assert main['transcript']['text'] == 'Old transcript' and main['transcript_needs_update']
    assert main['audio_version_count'] == 3
    assert store.detail(records[1]['id'])['notes'] == 'Second notes'
    assert store.detail(records[1]['id'])['merged_into'] == main['id']
    store.index_existing_captures()
    assert store.detail(main['id']) == main and file_hashes(tmp_path) == hashes
    store.update(records[1]['id'], {'archived': False})
    store.index_existing_captures()
    assert store.list_recordings()['total'] == 2


def test_version_merge_rolls_back_on_failure(tmp_path):
    store = RecordingStore(tmp_path)
    first = store.ingest_capture(partial_capture(tmp_path, 20).name)[0]
    longer = partial_capture(tmp_path, 40)
    with store.connect() as db:
        db.execute("""CREATE TRIGGER fail_version BEFORE INSERT ON pendant_recording_versions
            BEGIN SELECT RAISE(ABORT, 'write failed'); END""")
    with pytest.raises(sqlite3.IntegrityError):
        store.ingest_capture(longer.name)
    assert store.detail(first['id'])['duration_seconds'] == .4
    assert store.detail(first['id'])['audio_version_count'] == 1


def test_job_finishing_on_old_audio_cannot_shrink_extended_recording(tmp_path):
    store = RecordingStore(tmp_path)
    first = store.ingest_capture(partial_capture(tmp_path, 20).name)[0]
    store.set_status(first['id'], 'transcribing')
    store.ingest_capture(partial_capture(tmp_path, 40).name)
    store.update_transcription(first['id'], {'text': 'Old job', 'duration': .4})
    updated = store.detail(first['id'])
    assert updated['duration_seconds'] == .8 and updated['transcript_needs_update']


def test_ambiguous_shared_prefix_and_damaged_raw_do_not_merge(tmp_path):
    store = RecordingStore(tmp_path)
    store.ingest_capture(partial_capture(tmp_path, 40).name)
    store.ingest_capture(partial_capture(tmp_path, 40, changed=15).name)
    assert store.ingest_capture_result(partial_capture(tmp_path, 10).name)['added'] == 1
    damaged = partial_capture(tmp_path, 50)
    with (damaged / 'capture.bin').open('ab') as handle:
        handle.write(b'unverified tail')
    assert store.ingest_capture_result(damaged.name)['added'] == 1


def test_archived_main_stays_archived_when_extended(tmp_path):
    store = RecordingStore(tmp_path)
    original = store.ingest_capture(partial_capture(tmp_path, 20).name)[0]
    store.update(original['id'], {'archived': True})
    result = store.ingest_capture(partial_capture(tmp_path, 40).name)[0]
    assert result['id'] == original['id'] and result['archived'] and result['duration_seconds'] == .8
    assert store.list_recordings()['total'] == 0


def test_pending_legacy_job_defers_merge_until_finished(tmp_path):
    store = RecordingStore(tmp_path)
    store.ingest_capture(partial_capture(tmp_path, 40).name)
    short = partial_capture(tmp_path, 20)
    old = store.add_recording(short / 'audio/recording-0000.opus', 'Edited', source='pendant',
        source_key=f'capture:{short.name}:audio/recording-0000.opus', duration_seconds=.4)
    store.set_status(old['id'], 'queued')
    store.ingest_capture(short.name)
    assert store.list_recordings()['total'] == 2
    store.update_transcription(old['id'], {'text': 'Keep result', 'duration': .4})
    store.ingest_capture(short.name)
    assert store.list_recordings()['total'] == 1
    assert store.detail(old['id'])['transcript']['text'] == 'Keep result'


def test_transcription_can_fill_missing_legacy_duration(tmp_path):
    store = RecordingStore(tmp_path)
    folder = partial_capture(tmp_path, 20)
    old = store.add_recording(folder / 'audio/recording-0000.opus', 'Legacy', source='pendant')
    store.update_transcription(old['id'], {'text': 'Transcript', 'duration': .4})
    assert store.detail(old['id'])['duration_seconds'] == .4


def test_upgrade_respects_duplicate_restored_before_version_migration(tmp_path):
    store = RecordingStore(tmp_path)
    first = partial_capture(tmp_path, 20)
    main = store.ingest_capture(first.name)[0]
    repeated = partial_capture(tmp_path, 20)
    old = store.add_recording(repeated / 'audio/recording-0000.opus', 'Restored copy', source='pendant',
        source_key=f'capture:{repeated.name}:audio/recording-0000.opus', duration_seconds=.4)
    with store.connect() as db:
        db.execute('INSERT INTO capture_recording_sources VALUES (?,?)',
            (f'capture:{repeated.name}:audio/recording-0000.opus', main['id']))
    store.index_existing_captures()
    assert store.detail(old['id'])['archived'] is False
    assert store.list_recordings()['total'] == 2
