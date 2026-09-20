"""Persistent personal recording library; all paths stay under the local data root."""
from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path
import re
import sqlite3
from datetime import datetime, timezone
from uuid import UUID, uuid4

from .config import private_directory
from . import recording_versions as versions


def utc_now():
    return datetime.now(timezone.utc).isoformat()


class RecordingStore:
    def __init__(self, data_dir: Path):
        self.root = private_directory(Path(data_dir).resolve())
        self.imports = private_directory(self.root / "imports")
        self.db_path = self.root / "recordings.sqlite3"
        with self.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS recordings (
                id TEXT PRIMARY KEY, title TEXT NOT NULL, created_at TEXT NOT NULL,
                source TEXT NOT NULL, source_key TEXT UNIQUE NOT NULL, audio_path TEXT NOT NULL,
                duration_seconds REAL, tags TEXT NOT NULL DEFAULT '[]', notes TEXT NOT NULL DEFAULT '',
                starred INTEGER NOT NULL DEFAULT 0, archived INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'ready', transcript TEXT, transcript_text TEXT NOT NULL DEFAULT '',
                error TEXT, updated_at TEXT NOT NULL
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS pendant_fingerprints (
                fingerprint TEXT PRIMARY KEY, recording_id TEXT NOT NULL
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS capture_recording_sources (
                source_key TEXT PRIMARY KEY, recording_id TEXT NOT NULL
            )""")
            versions.create_schema(db)
        self.db_path.chmod(0o600)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.db_path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def safe_audio_path(self, value: str | Path) -> Path:
        path = Path(value)
        if not path.is_absolute():
            path = self.root / path
        # Reject symlink components, including links back inside the data root.
        try:
            relative = path.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("Recording is outside the local data directory.") from exc
        parent = self.root
        for part in relative.parts:
            if part in {".", ".."}:
                raise ValueError("Invalid recording path.")
            parent = parent / part
            if parent.is_symlink():
                raise ValueError("Recording symlinks are not supported.")
        if not path.resolve().is_relative_to(self.root) or not path.is_file():
            raise FileNotFoundError("Recording audio is missing.")
        return path

    def _serialise(self, row, *, full=True, private=False):
        result = dict(row)
        result["tags"] = json.loads(result["tags"])
        result["starred"] = bool(result["starred"])
        result["archived"] = bool(result["archived"])
        result["transcript"] = json.loads(result["transcript"]) if result["transcript"] else None
        result["has_transcript"] = result["transcript"] is not None
        with self.connect() as db:
            rows = db.execute('''SELECT v.metadata FROM pendant_recording_versions v
                JOIN capture_recording_sources s ON s.source_key=v.source_key
                WHERE s.recording_id=?''', (result['id'],)).fetchall()
            merged = db.execute('SELECT canonical_id FROM recording_version_merges WHERE duplicate_id=?',
                                (result['id'],)).fetchone()
        facts = [json.loads(item[0]) for item in rows]
        current = next((item for item in facts if item['audio_path'] == result['audio_path']), None)
        result['audio_incomplete'] = not current['closed_with_stop_marker'] if current else None
        result['audio_version_count'] = len({item['fingerprint'] for item in facts})
        result['merged_into'] = merged[0] if merged else None
        transcript_duration = (result['transcript'] or {}).get('audio_duration',
                              (result['transcript'] or {}).get('duration'))
        result['transcript_needs_update'] = bool(result['has_transcript'] and transcript_duration is not None
            and result['duration_seconds'] is not None and transcript_duration + 0.1 < result['duration_seconds'])
        result.pop("source_key", None)
        if private:
            result["audio_path"] = str(self.safe_audio_path(result["audio_path"]))
        else:
            result.pop("audio_path", None)
        if not full:
            result.pop("transcript", None)
        return result

    def get_recording(self, recording_id: str) -> dict:
        rid = str(UUID(str(recording_id)))
        with self.connect() as db:
            row = db.execute("SELECT * FROM recordings WHERE id=?", (rid,)).fetchone()
        if row is None:
            raise KeyError("Recording not found.")
        return self._serialise(row, private=True)

    def detail(self, recording_id: str) -> dict:
        result = self.get_recording(recording_id)
        result.pop("audio_path", None)
        return result

    def list_recordings(self, query="", archived=False, status="all") -> dict:
        clauses = ["archived=?"]
        params: list = [int(archived)]
        if query.strip():
            clauses.append("(title LIKE ? ESCAPE '\\' OR notes LIKE ? ESCAPE '\\' OR tags LIKE ? ESCAPE '\\' OR transcript_text LIKE ? ESCAPE '\\')")
            escaped = query.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            params.extend(["%" + escaped + "%"] * 4)
        if status != "all":
            clauses.append("status=?")
            params.append(status)
        where = " AND ".join(clauses)
        with self.connect() as db:
            rows = db.execute(f"SELECT * FROM recordings WHERE {where} ORDER BY starred DESC, created_at DESC LIMIT 500", params).fetchall()
            total = db.execute(f"SELECT COUNT(*) FROM recordings WHERE {where}", params).fetchone()[0]
        return {"recordings": [self._serialise(r, full=False) for r in rows], "total": total}

    def add_recording(self, path: Path, title: str, *, source="import", source_key=None,
                      created_at=None, duration_seconds=None) -> dict:
        path = self.safe_audio_path(path)
        source_key = source_key or "import:" + str(uuid4())
        record_id = str(uuid4())
        stamp = utc_now()
        with self.connect() as db:
            db.execute("""INSERT OR IGNORE INTO recordings
                (id,title,created_at,source,source_key,audio_path,duration_seconds,updated_at)
                VALUES (?,?,?,?,?,?,?,?)""", (record_id, title[:200] or "Untitled recording", created_at or stamp,
                source, source_key, str(path.relative_to(self.root)), duration_seconds, stamp))
            row = db.execute("SELECT id FROM recordings WHERE source_key=?", (source_key,)).fetchone()
        return self.detail(row["id"])

    def update(self, recording_id: str, fields: dict) -> dict:
        rid = str(UUID(str(recording_id)))
        changes = {}
        for field in ("title", "notes", "starred", "archived"):
            if field in fields:
                changes[field] = fields[field]
        if "tags" in fields:
            changes["tags"] = json.dumps(list(dict.fromkeys(tag.strip() for tag in fields["tags"] if tag.strip())))
        changes["updated_at"] = utc_now()
        with self.connect() as db:
            cursor = db.execute("UPDATE recordings SET " + ",".join(f"{key}=?" for key in changes) + " WHERE id=?", [*changes.values(), rid])
            if cursor.rowcount == 0:
                raise KeyError("Recording not found.")
        return self.detail(rid)

    def set_status(self, recording_id, status, error=None):
        with self.connect() as db:
            db.execute("UPDATE recordings SET status=?,error=?,updated_at=? WHERE id=?", (status, error, utc_now(), str(recording_id)))

    def update_transcription(self, recording_id, result):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT duration_seconds,source FROM recordings WHERE id=?', (recording_id,)).fetchone()
            if row and row['source'] == 'pendant' and 'duration' not in result:
                result = {**result, 'audio_duration': row['duration_seconds']}
            db.execute("""UPDATE recordings SET transcript=?,transcript_text=?,status='transcribed',error=NULL,
                duration_seconds=CASE WHEN source='pendant' AND duration_seconds IS NOT NULL
                    THEN duration_seconds ELSE COALESCE(?,duration_seconds) END,
                updated_at=? WHERE id=?""",
                (json.dumps(result, ensure_ascii=False), result.get("text", ""), result.get("duration"), utc_now(), str(recording_id)))

    def rename_speakers(self, recording_id: str, names: dict, revision: str) -> dict:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT transcript FROM recordings WHERE id=?", (recording_id,)).fetchone()
            transcript = json.loads(row["transcript"]) if row and row["transcript"] else {}
            if not transcript.get("speakers") or transcript.get("speaker_revision") != revision:
                raise ValueError("The transcript or speaker names have changed. Reopen the recording before editing.")
            if not set(names).issubset(transcript["speakers"]):
                raise ValueError("Choose speakers from this recording.")
            transcript["speakers"].update(names)
            transcript["speaker_revision"] = uuid4().hex
            db.execute("UPDATE recordings SET transcript=?,updated_at=? WHERE id=?",
                       (json.dumps(transcript, ensure_ascii=False), utc_now(), recording_id))
        return self.detail(recording_id)

    def ingest_capture(self, capture_id: str) -> list[dict]:
        return self.ingest_capture_result(capture_id)["recordings"]

    def _legacy_fingerprints(self, directory: Path, decoded: dict) -> dict:
        """Read verified raw data without rewriting old audio or decode manifests."""
        required = ("capture.json", "capture.bin", "journal.jsonl")
        if not all((directory / name).is_file() and not (directory / name).is_symlink() for name in required):
            return {}
        from .capture import decode_capture
        try:
            checked = decode_capture(directory, self.root / "keys", fingerprints_only=True)
            expected = decoded.get("recordings", [])
            actual = checked["recordings"]
            if checked["warnings"] or len(expected) != len(actual):
                return {}
            # A changed splitting/decoding algorithm must not relabel old files.
            if any(any(old.get(key) != new.get(key) for key in ("file", "packets", "duration_seconds"))
                   for old, new in zip(expected, actual)):
                return {}
            return {item["file"]: item["fingerprint"] for item in actual}
        except (OSError, ValueError, KeyError):
            return {}

    def ingest_capture_result(self, capture_id: str) -> dict:
        capture_id = str(UUID(str(capture_id)))
        directory = self.root / "captures" / capture_id
        if directory.is_symlink():
            raise ValueError("Capture symlinks are not supported.")
        manifest = directory / "decode.json"
        report = {"recordings": [], "added_ids": [], "added": 0, "already_present": 0,
                  "duplicates_archived": 0, "extended": 0, "extended_ids": []}
        if not manifest.is_file() or manifest.is_symlink():
            return report
        decoded = json.loads(manifest.read_text())
        job_path = directory / "job.json"
        job = json.loads(job_path.read_text()) if job_path.exists() else {}
        items = []
        for index, item in enumerate(decoded.get("recordings", [])):
            name = item.get("file", "")
            path = directory / name
            if path.parent != directory / "audio":
                continue
            try:
                safe_path = self.safe_audio_path(path)
            except (ValueError, OSError):
                continue
            items.append((index, item, safe_path, f"capture:{capture_id}:{name}"))
        with self.connect() as db:
            known = {row["source_key"] for row in db.execute(
                "SELECT source_key FROM capture_recording_sources WHERE source_key LIKE ?",
                (f"capture:{capture_id}:%",))}
        fingerprints = {}
        if any(key not in known and not item.get("fingerprint") for _, item, _, key in items):
            fingerprints = self._legacy_fingerprints(directory, decoded)
        verified = versions.prepare_versions(self, directory, decoded)
        proofs = {}
        ids = []
        with self.connect() as db:
            # Source aliases and canonical identities must become visible together.
            db.execute("BEGIN IMMEDIATE")
            for index, item, path, source_key in items:
                alias = db.execute("SELECT recording_id FROM capture_recording_sources WHERE source_key=?", (source_key,)).fetchone()
                existing = db.execute("SELECT id FROM recordings WHERE source_key=?", (source_key,)).fetchone()
                if alias and existing and alias['recording_id'] != existing['id']:
                    # A previous release already reconciled this source. Backfill
                    # evidence without re-archiving a copy the user may have restored.
                    if item['file'] in verified:
                        fact = {**verified[item['file']], 'audio_path': str(path.relative_to(self.root))}
                        stored = {key: value for key, value in fact.items() if key != 'prefix_fingerprints'}
                        db.execute('INSERT OR REPLACE INTO pendant_recording_versions VALUES (?,?,?)',
                                   (source_key, fact['start_fingerprint'], json.dumps(stored)))
                    ids.append(alias['recording_id'])
                    report['already_present'] += 1
                    continue
                if alias and item['file'] not in verified:
                    ids.append(alias["recording_id"])
                    report["already_present"] += 1
                    continue
                fingerprint = item.get("fingerprint") or fingerprints.get(item["file"])
                if not isinstance(fingerprint, str) or not re.fullmatch(r"pendant-audio-v1:[0-9a-f]{64}", fingerprint):
                    fingerprint = None
                canonical = db.execute("SELECT recording_id FROM pendant_fingerprints WHERE fingerprint=?", (fingerprint,)).fetchone() if fingerprint else None
                fact = verified.get(item['file'])
                if fact:
                    fact = {**fact, 'audio_path': str(path.relative_to(self.root))}
                matched = None
                deferred = False
                if fact:
                    matched = versions.find_version(self, db, fact, existing['id'] if existing else None, proofs)
                    if matched:
                        main, previous = matched
                        if existing and (main['status'] in ('queued', 'transcribing') or db.execute(
                                'SELECT status FROM recordings WHERE id=?', (existing['id'],)).fetchone()[0]
                                in ('queued', 'transcribing')):
                            matched, deferred = None, True
                        else:
                            canonical = {'recording_id': main['id']}
                if canonical:
                    rid = canonical["recording_id"]
                    report["already_present"] += 1
                    if existing and existing["id"] != rid:
                        # Keep the row, its annotations, jobs and audio recoverable.
                        if matched:
                            report['duplicates_archived'] += versions.preserve_annotations(db, rid, existing['id'], utc_now())
                        else:
                            changed = db.execute("UPDATE recordings SET archived=1 WHERE id=? AND archived=0", (existing["id"],))
                            report["duplicates_archived"] += changed.rowcount
                    if matched and (fact['packets'] > previous['packets'] or
                            (fact['packets'] == previous['packets'] and fact['closed_with_stop_marker']
                             and not previous['closed_with_stop_marker'])):
                        db.execute('UPDATE recordings SET audio_path=?,duration_seconds=?,updated_at=? WHERE id=?',
                                   (fact['audio_path'], fact['duration_seconds'], utc_now(), rid))
                        if fact['packets'] > previous['packets']:
                            report['extended'] += 1
                            report['extended_ids'].append(rid)
                else:
                    if existing:
                        rid = existing["id"]
                        report["already_present"] += 1
                    else:
                        rid, stamp = str(uuid4()), utc_now()
                        db.execute("""INSERT INTO recordings
                            (id,title,created_at,source,source_key,audio_path,duration_seconds,updated_at)
                            VALUES (?,?,?,?,?,?,?,?)""", (rid, f"Pendant recording {index + 1}", job.get("started_at") or stamp,
                            "pendant", source_key, str(path.relative_to(self.root)), item.get("duration_seconds"), stamp))
                        report["added"] += 1
                        report["added_ids"].append(rid)
                if fingerprint:
                    db.execute('INSERT INTO pendant_fingerprints VALUES (?,?) ON CONFLICT(fingerprint) DO UPDATE SET recording_id=excluded.recording_id', (fingerprint, rid))
                db.execute('INSERT INTO capture_recording_sources VALUES (?,?) ON CONFLICT(source_key) DO UPDATE SET recording_id=excluded.recording_id', (source_key, rid))
                if fact and not deferred:
                    stored = {key: value for key, value in fact.items() if key != 'prefix_fingerprints'}
                    db.execute('INSERT OR REPLACE INTO pendant_recording_versions VALUES (?,?,?)',
                               (source_key, fact['start_fingerprint'], json.dumps(stored)))
                ids.append(rid)
        report["recordings"] = [self.detail(rid) for rid in dict.fromkeys(ids)]
        return report

    def index_existing_captures(self):
        def captured_at(manifest):
            try:
                return json.loads((manifest.parent / "job.json").read_text()).get("started_at", "")
            except (OSError, ValueError):
                return ""
        for manifest in sorted((self.root / "captures").glob("*/decode.json"), key=captured_at):
            try:
                self.ingest_capture(manifest.parent.name)
            except (ValueError, OSError, KeyError):
                continue


def export_recording(recording: dict, format: str) -> tuple[str, str]:
    title = recording["title"]
    transcript = recording.get("transcript") or {}
    text = transcript.get("text", "")
    def segment_text(segment):
        if not transcript.get("diarization"):
            return segment["text"].strip()
        name = transcript.get("speakers", {}).get(segment.get("speaker"), "Speaker uncertain")
        return name + ": " + segment["text"].strip()
    if transcript.get("diarization") and transcript.get("segments"):
        text = "\n\n".join(segment_text(segment) for segment in transcript["segments"])
    if format == "json":
        return json.dumps(recording, indent=2, ensure_ascii=False), "application/json"
    if format == "txt":
        return title + "\n\n" + text + "\n", "text/plain; charset=utf-8"
    if format == "md":
        return f"# {title}\n\n{recording['created_at']}\n\n{text}\n\n## Notes\n\n{recording.get('notes', '')}\n", "text/markdown; charset=utf-8"
    if format == "srt":
        def timestamp(seconds):
            milliseconds = max(0, round(float(seconds) * 1000))
            hours, rest = divmod(milliseconds, 3600000)
            minutes, rest = divmod(rest, 60000)
            seconds, millis = divmod(rest, 1000)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"
        lines = []
        for i, segment in enumerate(transcript.get("segments", []), 1):
            lines.append(f"{i}\n{timestamp(segment['start'])} --> {timestamp(segment['end'])}\n{segment_text(segment)}\n")
        return "\n".join(lines), "application/x-subrip"
    raise ValueError("Unsupported export format.")
