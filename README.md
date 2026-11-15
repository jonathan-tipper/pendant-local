# Pendant Local

Use your Limitless Pendant with a local recording library, Bluetooth controls and
audio downloads to your computer. Transcribe and label speakers using models on
your own computer. No Limitless account, subscription or cloud transcription
service is required.

**Experimental community software for hardware you own.** Start with a short test
recording. Recovery of old vendor-encrypted audio requires its original key;
creating a new key cannot recover it. This project is independent of Limitless
and is not an official client or firmware update.

## What you can do

- Scan for a Pendant, check its state, set its clock, and start or stop recording.
- Download and decode audio without requesting deletion from the Pendant.
- Play, organise, search and annotate recordings in a local web dashboard.
- Transcribe with faster-whisper on CPU, with optional local speaker diarisation.
- Export TXT, Markdown, SRT and JSON. Import existing audio to try the library
  before connecting hardware.
- Build an Apple Silicon Mac app using the same service and dashboard.

The service binds to `127.0.0.1`. Recordings, transcripts and keys are stored on
the computer running it. Installation and explicitly requested model downloads
need internet access; inference uses complete local models. Storage is **not
encrypted by this application**. Read the [security model](SECURITY.md).

## Quick start

[Download v0.5.0](https://github.com/jonathan-tipper/pendant-local/releases/tag/v0.5.0)
for the source ZIP and Python package. The source ZIP includes bootstrap and Mac
build instructions; no prebuilt Mac app or model weights are included.

You need Python **3.11 or newer**, a local Bluetooth adapter and a nearby Pendant.
macOS has physical-device evidence with firmware **1.1.20**. Linux has software
validation; Windows and other firmware need community testing. See the
[compatibility and validation notes](docs/VALIDATION.md).

Download and extract the release source ZIP. Alternatively, clone the release:

```bash
git clone --branch v0.5.0 --depth 1 https://github.com/jonathan-tipper/pendant-local.git
cd pendant-local
```

Open a terminal in the extracted or cloned repository folder, then run:

```bash
python3 bootstrap.py
.venv/bin/pendant-local serve
```

On Windows, use PowerShell:

```powershell
py -3 bootstrap.py
.venv\Scripts\pendant-local.exe serve
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765). In a second terminal in the
same folder, get your local sign-in token:

```bash
.venv/bin/pendant-local token
```

Windows: `.venv\Scripts\pendant-local.exe token`. Paste it into the dashboard.
Keep it private. **Lock workspace** clears the current browser session.

Bootstrap updates the virtual environment's pip installer, then installs the
application and speech engines into `.venv`; it does not
download model weights or connect to a Pendant. To install only the dashboard
and API, use `python3 bootstrap.py --without-transcription` (Windows:
`py -3 bootstrap.py --without-transcription`). Rerun without the flag to add the
speech engines later.

## First recording

1. Open **Device**, scan and select the exact address returned. Allow Bluetooth
   access if your operating system asks. Disconnect other apps using the Pendant.
2. Check the device. Preserve existing recordings before changing keys or settings;
   do not factory-reset it to troubleshoot a connection.
3. Press **Start**. It synchronises the clock and checks the reported recording
   state. Speak a short, distinctive test phrase, then press **Stop**.
4. Choose **Sync from Pendant** and wait for download and decoding. Dashboard sync
   leaves deletion off. Open the recovered recording and listen to the full clip.
5. In **Settings**, explicitly download a transcription model. Once ready, select
   a recording and choose **Transcribe recording**.

**A completed transfer does not prove a complete backup.** Non-deleting sync can
repeat early pages or stop before newer audio. Keep raw captures and keys. The
[first-use guide](docs/GETTING_STARTED.md) explains pairing, partial syncs and
key handling; [troubleshooting](docs/TROUBLESHOOTING.md) covers common failures.

## Mac app

Apple Silicon users can [build Pendant.app from source](docs/MAC_APP.md).
Python and speech engines are bundled; model weights remain separate downloads.
The build is ad-hoc signed for local use, not a notarised installer. Bluetooth
permission and device operations through the packaged app remain unverified.
The Python service is the route with physical-device evidence.

The app defaults to port **8766**, Python to **8765**. Both use the same macOS
workspace. Run only **one service per data directory**, even on different ports.

## Documentation

| Guide | Covers |
| --- | --- |
| [Getting started](docs/GETTING_STARTED.md) | Installation, first sync, safe device checks and keys |
| [Using the library](docs/WORKSPACE.md) | Imports, transcription, speakers, queue and exports |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Bluetooth, incomplete audio, dependencies and jobs |
| [Backup and restore](docs/BACKUP_AND_RESTORE.md) | Storage paths, upgrades and recovery |
| [Mac app](docs/MAC_APP.md) | Build, install, sign-in and lifecycle |
| [API](docs/API.md) | Authentication, examples and endpoint reference |
| [Architecture](docs/ARCHITECTURE.md) | Source map, data flow and capture guarantees |
| [Validation](docs/VALIDATION.md) | Checks performed and what remains unverified |
| [Contributing](CONTRIBUTING.md) | Development, tests and safe bug reports |

There is no hosted service, mobile Bluetooth client, automatic summary generator,
GPU inference or recognition of people across recordings. Speaker labels and
transcripts need human review. Record only where you have the necessary consent.

## Licence and credits

[MIT](LICENSE), with third-party components under their own licences. The
Bluetooth implementation builds on [Mustafa Akcanca's pendant-cli](https://github.com/MAkcanca/pendant-cli).
Its licence and pinned source attribution are retained. [Third-party notices](THIRD-PARTY-NOTICES.md)
cover the vendored client, local Swagger UI assets and separately downloaded models.
