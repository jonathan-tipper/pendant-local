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

## Initial publication

Create an **empty** repository in your chosen GitHub account. Do not fork or
change the visibility of a repository that contains personal development history.
Do not add a GitHub-generated README or licence before pushing this initial tree.
The prepared local repository has one root commit and no remote configured.

Use the new repository URL, never a private development remote:

```bash
git remote add origin NEW_REPOSITORY_URL
git push -u origin HEAD:main
```

Replace `NEW_REPOSITORY_URL` with your repository's actual clone URL. Review the
result before sharing it. Set `main` as the default branch. In GitHub settings,
enable private vulnerability reporting, secret scanning/push protection where
available, Dependabot alerts and branch protection after CI has reported its
check names. Confirm that Issues and Actions are enabled.

Publish a source tag only after the checks pass. State that downloaded speech
weights and native installers are not included. Do not attach a working directory
or an app bundle accidentally when uploading source archives.

## Native app distribution

`desktop/build.py` produces a locally signed Apple Silicon bundle. Before sharing
binaries, validate packaged Bluetooth permissions and real device operations on
target macOS versions, review all bundled native licences (including FFmpeg via
PyAV), and complete signing/notarisation and any required corresponding-source
or notice distribution. Copying licence files alone is not a complete review of
binary distribution obligations. The build inventory helps identify components.
