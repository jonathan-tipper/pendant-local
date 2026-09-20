# Architecture

A single FastAPI process serves a bundled vanilla-JavaScript dashboard and a
local authenticated API. A Swift/AppKit launcher can start a PyInstaller bundle
of that same service and show the dashboard in WKWebView. SQLite holds library
metadata and transcripts; audio and raw capture files live beside it.

```text
Browser / WKWebView -> FastAPI -> SQLite + local files
                         |
                         +-> BLE adapter -> owned Pendant
                         |
                         +-> persistent queue -> faster-whisper / sherpa-onnx
```

## Source map

| Location | Responsibility |
| --- | --- |
| `src/pendant_api/cli.py`, `config.py` | CLI, workspace paths, token and atomic settings |
| `src/pendant_api/app.py` | Service lifecycle, auth, device/capture routes and native identity |
| `src/pendant_api/workspace_routes.py` | Library, imports, playback, export and workflow routes |
| `src/pendant_api/device.py` | Bluetooth operations and key provisioning |
| `src/pendant_api/capture.py` | Durable raw capture, journal, guarded acknowledgement and decoding |
| `src/pendant_api/recordings.py` | SQLite, imports, indexing and exports |
| `src/pendant_api/recording_versions.py` | Verified partial-version matching and reversible merges |
| `src/pendant_api/transcription.py` | Persistent single-worker queue and local transcription |
| `src/pendant_api/diarization.py` | Speaker model preparation, inference and alignment |
| `src/pendant_api/ui/`, `static/` | Bundled dashboard and API documentation assets |
| `src/pendant_client/`, `proto/` | Vendored upstream Bluetooth/protocol code and bindings |
| `desktop/` | Native launcher and local build scripts |
| `tests/` | Synthetic storage, API, queue, device and failure-path checks |

## Capture and storage invariants

One service owns each workspace using a process lock. A separate async lock
serialises device/decode operations, with competing requests returning 409.
Transient connection setup failure can retry once with a fresh session; an
operation is not replayed after it starts.

Capture preserves wire bytes and a SHA-256 integrity journal. Deletion is off by
default and always off in dashboard requests. The optional API acknowledgement
path requires a contiguous sequence and durable bytes plus journal entries before
sending cumulative delete commands. Interrupted or failed work retains raw files.
Neither an idle timeout nor a stop marker proves the whole device was backed up.

Exact duplicates use encoded audio and device/page/time provenance. Verified
longer prefixes can extend an incomplete library recording while preserving
original files, metadata and old transcripts. Conflicting or unverifiable copies
remain separate. See [recording versions](RECORDING_VERSIONS.md).

The queue writes jobs before execution and processes one at a time. Queued
transcriptions survive restart; interrupted native work and downloads need retry.
Cancellation discards results but may wait for a native call to finish. Engine
installation and explicit model preparation are separate operations.

## Boundaries

This is a single-user local tool, not a multi-tenant server. Models, imported
files and native libraries are trusted inputs to local execution. See
[SECURITY.md](../SECURITY.md) for the threat model, storage limits and private
reporting guidance. Bluetooth compatibility requires real hardware; API and
unit tests use injected implementations.
