"""Verified prefix matching for partial Pendant downloads. Never rewrites audio."""
from __future__ import annotations

import json
import re


def create_schema(db):
    db.execute("""CREATE TABLE IF NOT EXISTS pendant_recording_versions (
        source_key TEXT PRIMARY KEY, start_fingerprint TEXT NOT NULL,
        metadata TEXT NOT NULL)""")
    db.execute("""CREATE INDEX IF NOT EXISTS pendant_versions_start
        ON pendant_recording_versions(start_fingerprint)""")
    db.execute("""CREATE TABLE IF NOT EXISTS recording_version_merges (
        duplicate_id TEXT PRIMARY KEY, canonical_id TEXT NOT NULL,
        canonical_before TEXT NOT NULL, duplicate_before TEXT NOT NULL,
        created_at TEXT NOT NULL)""")


def inspect_capture(store, directory, decoded, counts=()):
    """Reconstruct identity from journal-verified raw bytes, including old captures."""
    required = ('capture.json', 'capture.bin', 'journal.jsonl')
    if directory.is_symlink() or not all((directory / name).is_file()
            and not (directory / name).is_symlink() for name in required):
        return {}
    from .capture import decode_capture
    try:
        actual = decode_capture(directory, store.root / 'keys', fingerprints_only=True,
                                prefix_packets=set(counts))
        expected = decoded.get('recordings', [])
        if actual['warnings'] or decoded.get('warnings') or len(expected) != len(actual['recordings']):
            return {}
        for old, new in zip(expected, actual['recordings']):
            if any(old.get(key) != new.get(key) for key in ('file', 'packets', 'duration_seconds')):
                return {}
            if old.get('fingerprint') and old['fingerprint'] != new['fingerprint']:
                return {}
        return {item['file']: item for item in actual['recordings']}
    except (OSError, ValueError, KeyError):
        return {}


def prepare_versions(store, directory, decoded):
    with store.connect() as db:
        known = {row[0] for row in db.execute('SELECT source_key FROM pendant_recording_versions')}
        if all(f"capture:{directory.name}:{item.get('file')}" in known
               for item in decoded.get('recordings', [])):
            return {}
        counts = {json.loads(row[0])['packets'] for row in db.execute(
            'SELECT metadata FROM pendant_recording_versions')}
    return {name: item for name, item in inspect_capture(store, directory, decoded, counts).items()
            if f'capture:{directory.name}:{name}' not in known}


def contains(store, longer, shorter, proofs):
    if longer['start_fingerprint'] != shorter['start_fingerprint']:
        return False
    if longer['packets'] == shorter['packets']:
        return longer['fingerprint'] == shorter['fingerprint']
    if longer['packets'] < shorter['packets'] or shorter['closed_with_stop_marker']:
        return False
    key = str(shorter['packets'])
    prefixes = longer.get('prefix_fingerprints', {})
    if key not in prefixes:
        path = store.safe_audio_path(longer['audio_path'])
        directory = path.parent.parent
        cache_key = (directory.name, shorter['packets'])
        if cache_key not in proofs:
            decoded = json.loads((directory / 'decode.json').read_text())
            proofs[cache_key] = inspect_capture(store, directory, decoded, [shorter['packets']])
        checked = proofs[cache_key].get('audio/' + path.name, {})
        if checked.get('fingerprint') != longer['fingerprint']:
            return False
        prefixes = checked.get('prefix_fingerprints', {})
    return prefixes.get(key) == shorter['fingerprint']


def find_version(store, db, incoming, excluded_id, proofs):
    if not incoming or not incoming.get('opened_with_start_marker'):
        return None
    rows = db.execute("""SELECT r.*, v.metadata FROM pendant_recording_versions v
        JOIN capture_recording_sources s ON s.source_key=v.source_key
        JOIN recordings r ON r.id=s.recording_id
        WHERE v.start_fingerprint=?""", (incoming['start_fingerprint'],)).fetchall()
    matches = {}
    for row in rows:
        if row['id'] == excluded_id:
            continue
        version = json.loads(row['metadata'])
        # Compare with the family's fullest audio, never an obsolete shorter member.
        if version['audio_path'] != row['audio_path'] or not version['opened_with_start_marker']:
            continue
        try:
            if contains(store, incoming, version, proofs) or contains(store, version, incoming, proofs):
                matches[row['id']] = (row, version)
        except (OSError, ValueError, KeyError):
            continue  # Missing or unverifiable older data cannot justify a merge.
    # A short prefix shared by conflicting longer versions is ambiguous.
    return next(iter(matches.values())) if len(matches) == 1 else None


def preserve_annotations(db, canonical_id, duplicate_id, stamp):
    """Keep original rows in the archive and record the pre-merge main row."""
    main = dict(db.execute('SELECT * FROM recordings WHERE id=?', (canonical_id,)).fetchone())
    duplicate = dict(db.execute('SELECT * FROM recordings WHERE id=?', (duplicate_id,)).fetchone())
    db.execute('INSERT INTO recording_version_merges VALUES (?,?,?,?,?)',
               (duplicate_id, canonical_id, json.dumps(main), json.dumps(duplicate), stamp))
    title = main['title']
    if re.fullmatch(r'Pendant recording \d+', title) and not re.fullmatch(r'Pendant recording \d+', duplicate['title']):
        title = duplicate['title']
    notes = main['notes']
    if duplicate['notes'] and duplicate['notes'] != notes:
        notes = '\n\n'.join(part for part in (notes, duplicate['notes']) if part)
    tags = list(dict.fromkeys(json.loads(main['tags']) + json.loads(duplicate['tags'])))
    transcript = main['transcript'] or duplicate['transcript']
    transcript_text = main['transcript_text'] if main['transcript'] else duplicate['transcript_text']
    status = main['status'] if main['transcript'] or not duplicate['transcript'] else duplicate['status']
    db.execute('''UPDATE recordings SET title=?,notes=?,tags=?,starred=?,transcript=?,
        transcript_text=?,status=?,updated_at=? WHERE id=?''',
        (title, notes, json.dumps(tags), main['starred'] or duplicate['starred'], transcript,
         transcript_text, status, stamp, canonical_id))
    changed = db.execute('UPDATE recordings SET archived=1 WHERE id=? AND archived=0', (duplicate_id,)).rowcount
    db.execute('UPDATE capture_recording_sources SET recording_id=? WHERE recording_id=?', (canonical_id, duplicate_id))
    db.execute('UPDATE pendant_fingerprints SET recording_id=? WHERE recording_id=?', (canonical_id, duplicate_id))
    # Preserve old links to archived rows; future source aliases point to the main entry.
    db.execute('UPDATE recording_version_merges SET canonical_id=? WHERE canonical_id=?', (canonical_id, duplicate_id))
    return changed
