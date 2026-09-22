# Compatibility and validation

Version **0.5.0**. This page distinguishes software checks from physical hardware
evidence. It does not promise compatibility with every Pendant or operating system.

## Release checks: 22 September 2026

The v0.5.0 release candidate passed **195 tests with 1 FFmpeg-dependent skip**
on Apple Silicon macOS with Python 3.13.2 in a fresh core/test environment.
The 2 upstream test-client deprecation warnings remain. JavaScript syntax,
source/link/asset checks and dependency consistency passed. A fresh pip-audit
reported no known vulnerabilities in that installed environment. Gitleaks scanned
all repository branches without detecting secrets.

These checks used temporary synthetic data. No device, recording workspace,
model inference or native app build was involved. `.gitattributes` fixes text
line endings to LF so bundled asset hashes also remain valid on Windows.
Capture listings use forward slashes so their file references can be requested
through the download API on every operating system.

The [v0.5.0 release notes](https://github.com/jonathan-tipper/pendant-local/releases/tag/v0.5.0)
record the final hosted CI and package checks. [GitHub Actions](https://github.com/jonathan-tipper/pendant-local/actions)
is the live record for later commits. Passing software CI does not establish
Bluetooth support or the desktop application's permission path on that platform.

## Source preparation: 20 September 2026

Public source preparation, 20 September 2026, on Apple Silicon macOS 26.6.2
with Python 3.13.2:

- **195 passed, 1 skipped**, with 2 upstream test-client deprecation warnings.
  The skipped codec check requires the external FFmpeg executable. Tests ran
  against the clean source and again in a fresh installed environment.
- Fresh bootstrap installation succeeded with the dashboard/API option; both
  optional speech engines and development dependencies then installed without
  downloading transcription or speaker weights.
- JavaScript syntax and `pip check` passed. Local Markdown links and the bundled
  Swagger asset sizes/SHA-256 hashes passed the source release check.
- Built an sdist and wheel. The wheel was extracted outside the source checkout;
  isolated import, service startup, authentication rejection/acceptance, library
  access and bundled UI/API documentation assets passed. Package contents were
  inspected for private/runtime payloads and required licence files.
- pip-audit 2.10.1 reported **no known vulnerabilities** in the fresh installed
  environment, including faster-whisper and sherpa-onnx. This is a point-in-time
  package advisory check, not an audit of native code. An older development pip
  had advisories; bootstrap and setup instructions now upgrade pip to at least
  26.2 before package installation.
- Gitleaks 8.30.1 reported no secrets in the reviewed source snapshot.
  This complements manual removal of private development notes and artefacts.
- The retained upstream MIT licence matches the pinned source revision exactly.
  GitHub workflow YAML parses locally; hosted jobs have not run yet.

No real recording workspace or device was used. No new physical Bluetooth,
model inference, native build or real-browser UI test was performed during this
source preparation; existing evidence is scoped separately below.

## Existing hardware and runtime evidence

| Area | Evidence | Limits |
| --- | --- | --- |
| Python service on macOS | Physical Pendant, firmware 1.1.20: status, clock acknowledgement, Start/Stop readback, non-deleting transfer and fresh microphone audio decoded locally | No claim for other firmware, first pairing on every machine, full-buffer recovery or sustained reliability |
| Web UI | Browser checks on macOS/Linux with isolated or public test audio: login, library edits, playback, search, export, queue and responsive layouts | Not a hardware test; browser codec support varies |
| Local transcription | CPU inference through faster-whisper with explicit local models; imported/public and short device speech exercised | No general accuracy, long-meeting or multilingual benchmark |
| Speaker analysis | Local runtime exercised with short generated/public speech | Speaker counts can be wrong; no cross-recording identity recognition |
| Source-built Mac app | Apple Silicon, Python 3.13.2, macOS 26.6.2: launch, auto sign-in, file dialogs, playback, export, lock, quit/reopen and bundled inference | Packaged Bluetooth permission/device operations remain unverified; local ad-hoc signature only |
| Linux | Python 3.12 software suite and browser/inference baseline | Physical Bluetooth not validated |
| Windows | Installation instructions and a configured CI target | Installation, UI and real Bluetooth have not been validated |

These observations describe the shared implementation before source publication;
they are not new device tests for this source preparation. No private recordings,
backups, personal transcripts or model weights are part of the release.

## Known limits

- Old vendor-encrypted audio requires the original key. Actual encrypted-audio
  recovery and unsupported packet layouts need physical validation.
- Non-deleting sync can repeat pages or stop early. No resume offset is exposed.
  Idle/time limits and recovered stop markers do not prove a complete backup.
- The Mac build targets macOS 13+, but runtime evidence covers only macOS 26.6.2
  on Apple Silicon. Intel and other Mac versions remain unverified.
- Tests use synthetic transports and local temporary files. They cannot prove
  pairing, microphone intelligibility, battery life or firmware compatibility.
- Automated core CI does not download models or exercise real native inference.
  Hosted CI results must be inspected after publication.

## Repeatable checks

Follow [CONTRIBUTING.md](../CONTRIBUTING.md) for the suite and isolated service,
and [RELEASING.md](RELEASING.md) for package, content and dependency checks.
For a hardware report, follow the short labelled recording test in
[GETTING_STARTED.md](GETTING_STARTED.md), include firmware/OS, listen to both
ends of the clip and report uncertainty explicitly. Never attach personal audio,
keys, tokens or raw journals to a public issue.
