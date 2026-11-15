# Source release guide

This project distributes source and build instructions. A source release does
not imply a signed/notarised app, a PyPI publication or a hardware certification.
Keep these distribution decisions separate.

## Validate source

From a clean checkout and isolated development environment:

```bash
.venv/bin/python -m pytest -q
node --check src/pendant_api/ui/app.js
.venv/bin/python scripts/check_release.py
.venv/bin/python -m pip check
.venv/bin/python -m pip install build pip-audit
.venv/bin/python -m build
.venv/bin/python -m pip_audit --skip-editable
```

Review dependency findings. CI runs core tests on Linux, macOS and Windows and
checks the build and installed core dependencies. That configuration is not
evidence of passing until the hosted runs finish. Optional speech engines and
Mac native libraries need their own platform-specific audit.

Install the wheel in a fresh environment and verify startup, auth, bundled UI
and docs from outside the source directory. Inspect wheel and sdist contents:
retain licences and notices; exclude credentials, keys, recordings, databases,
models, logs, virtual environments and local machine paths. A clean `git status`
is not a substitute for reviewing tracked content.

Run a secret scanner over the full repository history, review the root tree,
and inspect commit author metadata before publication. The lightweight local
release check catches known private paths and accidental data files; it is not
a general secret scanner. Recheck any screenshots using synthetic content.

Update [VALIDATION.md](VALIDATION.md) with the exact checks performed. Record
hardware, native UI and inference evidence separately from mocked tests. Keep
release notes about current behaviour, compatibility and limitations.

## Publish a release

Releases are published from the reviewed `main` branch of
[jonathan-tipper/pendant-local](https://github.com/jonathan-tipper/pendant-local).
Use a scoped work branch for preparation. Keep application/package version,
changelog, installation links and validation evidence consistent. Preserve
unrelated local edits by using a separate checkout when needed.

Review passing Checks, Dependency audit and Secret scan runs for the exact
release commit. An account/runner failure is not a passing code check. Never
report a platform as tested merely because it appears in the matrix.

Create an annotated version tag only after checks pass. Build the wheel and sdist
from that commit, include a source ZIP made with `git archive`, and generate
SHA-256 checksums for each uploaded asset. Verify package licences and install the
wheel outside the source tree using temporary data. Do not include a development
virtual environment, local configuration, models, recordings or credentials.

Create a draft GitHub Release with explicit notes and the verified assets.
Download the draft assets and compare their hashes before publishing. State
compatibility limits and distinguish a Python/source release from a native app.
Tag and publish only to this repository; the original development repository is
not a release source and its visibility must not be changed.

Keep private vulnerability reporting, secret scanning, push protection and
Dependabot alerts enabled where available. Keep CI permissions read-only and
review dependency updates rather than merging them automatically.

## Native app distribution

`desktop/build.py` produces a locally signed Apple Silicon bundle. Before sharing
binaries, validate packaged Bluetooth permissions and real device operations on
target macOS versions, review all bundled native licences (including FFmpeg via
PyAV), and complete signing/notarisation and any required corresponding-source
or notice distribution. Copying licence files alone is not a complete review of
binary distribution obligations. The build inventory helps identify components.
