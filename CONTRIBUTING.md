# Contributing

Useful contributions include reproducible Bluetooth compatibility reports,
clearer setup instructions, isolated bug fixes and tests for data preservation.
Discuss changes to capture deletion, encryption, storage or dependency downloads
before substantial implementation.

## Development setup

Use a separate checkout and data directory from your recording library.
Python 3.11+ is required. Node.js is only used to check JavaScript syntax; there
is no frontend build step.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade 'pip>=26.2'
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pytest -q
node --check src/pendant_api/ui/app.js
.venv/bin/python scripts/check_release.py
```

Windows: use `py -3` to create the environment and `.venv\Scripts\python.exe`
for Python commands. The core suite needs no Pendant, credentials or downloaded
models. FFmpeg enables one additional codec check; that test skips when the
executable is absent. Optional real inference work needs the `transcription`
and `diarization` extras and separately requested models.

To run an isolated development service on macOS/Linux:

```bash
PENDANT_DEV_DATA="$(mktemp -d)"
.venv/bin/pendant-local --data-dir "$PENDANT_DEV_DATA" serve --port 8767
```

In PowerShell, choose a fresh private temporary directory and pass it with
`--data-dir`. Keep using the same directory to retrieve its token. Never run
automated imports or jobs against a real recording library. One service owns
one data directory, regardless of port.

## Changes and pull requests

Use a scoped branch such as `fix/capture-retry`, `feat/library-filter` or
`docs/linux-setup`. Keep unrelated refactoring out of the change. Explain the
problem, final behaviour, checks run and remaining hardware limitations.
Add tests when behaviour or a security boundary changes.

Read the [architecture](docs/ARCHITECTURE.md) before changing service behaviour,
[recording versions](docs/RECORDING_VERSIONS.md) before changing duplicate handling,
and the [Mac guide](docs/MAC_APP.md) before changing packaging or lifecycle.

Preserve these invariants:

- Dashboard sync never acknowledges device deletion.
- Raw capture and journal writes precede any explicitly authorised deletion.
- Decode, queue and UI failures preserve recordings and encryption keys.
- All `/v1` routes require authentication; no token belongs in an audio URL.
- Keep the service on loopback and render user content as text.
- Installing dependencies never implicitly downloads transcription/speaker models.
- Imported or mocked speech tests never count as physical-device evidence.
- Keep upstream licences, provenance and generated protocol bindings.

Run the focused checks, then the full suite before proposing a release. Check
UI behaviour in a real browser using synthetic data. State software and hardware
checks separately. Include neither recordings nor private workspace paths in a PR.

## Dependency changes

Runtime and engine versions are declared in `pyproject.toml`; Mac build tools are
in `desktop/build-requirements.txt`. Review licences and advisories when updating.
The audit workflow resolves and scans the installed core dependencies. A separate
Gitleaks workflow scans Git history for secrets. Also audit
the platform-specific speech and native build environments before a binary release.
The direct pins do not constitute a fully locked cross-platform dependency tree.

Regenerate protobuf bindings only for an intentional protocol change. The checked-in
bindings mean users do not need `grpcio-tools`; install it through the `protocol`
extra when working on `scripts/gen_proto.py`.

Contributions are accepted under the project's MIT licence, with upstream notices
retained. Do not submit material you cannot license or personal recordings from
other people without permission.
