# Local HTTP API

The interactive schema at [http://127.0.0.1:8765/docs](http://127.0.0.1:8765/docs)
is the authoritative request/response reference for the running Python service.
The Mac app uses port 8766. UI and Swagger assets are served locally.

All `/v1` routes require `Authorization: Bearer TOKEN`. In Swagger, click
**Authorize** and paste the token alone. Obtain it using `pendant-local token`
with the service's data directory. Do not place it in a query string or screenshot.
Health and static documentation endpoints do not need authentication.

## Example client

With the server running and a configured device:

```bash
.venv/bin/python scripts/example_client.py
```

This reads device information using the token saved locally. Add `--capture`
for a non-deleting capture of up to 60 seconds. Use `--data-dir` and `--port` if
the service uses custom values. The client does not start recording or provision
a key. Its response includes device details, so redact it before sharing.

## Capture and decode

`POST /v1/captures` accepts:

```json
{"acknowledge": false, "idle_timeout": 5, "max_seconds": 60}
```

The request stays open during capture. Allow for connection and cleanup time
beyond `max_seconds` (1–3600). Keep the returned `id`; then request
`POST /v1/captures/{id}/decode`. Inspect warnings, playable recordings and the
library summary. For example, decoded audio filenames use
`audio/recording-0000.opus` beneath the capture.

The API default is 60 seconds; the dashboard explicitly requests its selected
limit, defaulting to 30 minutes. Idle timeout accepts 1–30 seconds. No timeout
proves completeness. Partial raw data is retained after failure, with the capture
ID included where available so it can be inspected.

**`acknowledge: true` deletes acknowledged pages from the Pendant.** It is an
advanced, explicitly requested option. Raw bytes and the integrity journal are
flushed before cumulative deletion of an unbroken verified sequence. This does
not establish that encrypted audio can be decoded. Back up captures and original
keys and validate recovery before considering deletion. Dashboard sync never
uses this option.

## Route overview

| Method and route | Purpose |
| --- | --- |
| `GET /health` | Service status, without Bluetooth access |
| `GET /v1/settings`, `PATCH /v1/settings` | Settings and workflow defaults |
| `GET /v1/devices/scan` | Nearby discovery, optional timeout 1–30 seconds |
| `PUT /v1/device/config` | Save the address returned by scan |
| `GET /v1/device` | Device information and available status |
| `POST /v1/device/clock` | Synchronise computer time |
| `POST /v1/device/recording` | Start/stop with `{"enabled": true}` or `false` |
| `POST /v1/device/key` | Future-recording key, requires `confirm_future_recordings: true` |
| `POST /v1/captures`, `GET /v1/captures` | Capture or list captures |
| `GET /v1/captures/{id}` | Capture metadata and available files |
| `POST /v1/captures/{id}/decode` | Decode and index playable audio |
| `GET /v1/captures/{id}/files/{filename}` | Raw or decoded file download |
| `GET /v1/recordings` | Search/filter library |
| `POST /v1/recordings/import` | Multipart upload in field `file` |
| `GET /v1/recordings/{id}`, `PATCH /v1/recordings/{id}` | Read/edit metadata |
| `GET /v1/recordings/{id}/audio` | Authenticated audio, with range support |
| `GET /v1/recordings/{id}/export?format=txt` | TXT, Markdown (`md`), SRT or JSON |
| `POST /v1/recordings/{id}/transcribe` | Queue local transcription |
| `PATCH /v1/recordings/{id}/speakers` | Edit per-recording speaker names |
| `POST /v1/transcription/batch` | Queue 1–100 recording IDs |
| `GET /v1/transcription/status` | Engine and model readiness |
| `POST /v1/transcription/models/{model}/prepare` | Explicit Whisper model download |
| `POST /v1/transcription/diarization/prepare` | Explicit speaker model download |
| `GET /v1/jobs` | Persistent job list |
| `POST /v1/jobs/{id}/cancel`, `POST /v1/jobs/{id}/retry` | Cancel/retry work |

Accepted transcription/download jobs return `202`, which means queued, not
completed. Poll the jobs list for progress and final outcome. Missing/invalid
authentication returns `401`; absent objects `404`; conflicting operations or
unmet prerequisites `409`; invalid input `422`; device operation failures `503`.

A process lock prevents multiple services sharing storage. Device and decode
operations are serialised. Use one server worker. CLI scan/info must wait until
the server stops; UI/API device operations use the running service instead.
