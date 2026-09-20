# Build Pendant for Mac

The native app hosts the same dashboard in WKWebView and starts its bundled local
Python service. Build it on **Apple Silicon macOS** with Python 3.11+ and Xcode
Command Line Tools. The tested build environment uses Python 3.13.2 and macOS
26.6.2. The deployment target is macOS 13; that does not establish compatibility
with every release from 13 onwards. Intel builds are not supported by this recipe.

## Build and install

From the repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade 'pip>=26.2'
.venv/bin/python -m pip install -e '.[transcription,diarization]'
.venv/bin/python -m pip install -r desktop/build-requirements.txt
.venv/bin/python desktop/build.py
```

The result is `dist/Pendant.app`. It includes Python, faster-whisper and
sherpa-onnx. It excludes recordings, keys, credentials and downloaded Whisper or
speaker model weights. The small Silero voice activity model supplied with
faster-whisper is a bundled runtime asset.

Quit any existing Pendant app while idle. Create `~/Applications` if needed and
copy `dist/Pendant.app` there using Finder. Open it from Finder, Spotlight or the
Dock. A separately installed Python and the checkout are not needed for daily
use. Rebuild after source updates; changing a checkout does not update an
already installed app.

The bundle is ad-hoc signed for local use, not notarised or an App Store release.
Do not disable system security globally to install it. Public binary distribution
needs the separate checks in [RELEASING.md](RELEASING.md).

## Daily use

Opening Pendant starts its local service at `127.0.0.1:8766` and signs the embedded
window in. No Bluetooth recording or transfer starts on launch. Closing the
window leaves the application running; its Dock icon reopens the window.

Command-Q stops the service it owns. If capture, transcription or model work is
active or queued, the app asks you to keep it running. Finish or cancel work in
the workspace before quitting. Normal quit/reopen is the supported path.
Sleep pauses work, so keep the computer awake for transfers.

**Lock workspace** clears the window's session. **Pendant > Unlock Workspace**
signs it in again. This is a session lock, not protection from another process
or person with access to your macOS account. Import/export use native file dialogs;
the menu provides **Show Workspace Folder** and **Show Service Log**. Logs may
contain paths or device information; review and redact them before sharing.

On a first device operation, macOS may request Bluetooth permission. Packaged
Bluetooth permission and physical device operations are **not yet validated**.
Use the Python route if this fails, after quitting the app.

## Shared workspace and browser access

The app and Python service default to:

```text
~/Library/Application Support/pendant-local-api/
```

Replacing the app does not replace recordings or models. Back up the whole
workspace before updates affecting storage. A custom Python `--data-dir` is not
automatically selected by the native launcher.

Only one service can use a workspace. To change launch methods, finish jobs,
stop the existing service and start the other. To use a browser alongside the
app, leave Pendant running and open [http://127.0.0.1:8766/ui/](http://127.0.0.1:8766/ui/).
Copy its token to the clipboard from Terminal:

```bash
~/Applications/Pendant.app/Contents/MacOS/pendant-service token | pbcopy
```

Paste it into the browser sign-in form; never put it in a URL. Clear the clipboard
after use. Browser sessions, colour choices and remembered sync limits are
separate from those of the native window. Recordings and saved workflow settings
are shared.

The launcher verifies a challenge response before sending a token to an existing
listener. It can reuse a matching service; normal quit leaves a reused service
running. Unknown or incompatible listeners produce an error and are not killed.
Native HTTP requests refuse redirects. WKWebView stays on its local service;
explicit external links open in the system browser.

## Development and redistribution

For native QA, a separate bundle can set `PendantWorkspacePath` and
`PendantServicePort` in Info.plist **before signing**. Use synthetic audio and an
isolated directory. Never automate imports or jobs against a personal library.

The build copies licence/notice files and an environment inventory into
`Contents/Resources/licences/`. Python and native dependencies retain their own
licences. Review the actual contents and obligations, particularly FFmpeg via
PyAV, before redistributing a bundle. The project's MIT licence alone is not
permission to disregard those requirements.
