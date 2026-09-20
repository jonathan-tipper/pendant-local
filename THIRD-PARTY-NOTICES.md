# Third-party notices

## Pendant Bluetooth client and protocol

`src/pendant_client/`, `proto/` and `scripts/gen_proto.py` derive from
[MAkcanca/pendant-cli, commit 5e0eace94042096a74944861cc4d60060cd3aa8f](https://github.com/MAkcanca/pendant-cli/tree/5e0eace94042096a74944861cc4d60060cd3aa8f),
retrieved 15 September 2026. Copyright 2026 Mustafa Akcanca, MIT. The original
licence is retained verbatim in [LICENSES/pendant-cli-MIT.txt](LICENSES/pendant-cli-MIT.txt).
Generated protobuf bindings are included, using the upstream relative-import
rewrite. Local generator documentation describes this package's optional tools.

The supported `pendant-local` command uses its own capture/persistence path.
It does not call upstream CLI capture/sync or upload commands. The vendored CLI
contains deletion, reset and server-upload operations and is retained as upstream
source, not installed as an application entry point. Do not use it as a substitute
for the non-deleting dashboard workflow. No firmware image or vendor credentials
are distributed here.

## Swagger UI

Interactive API documentation bundles **Swagger UI Dist 5.32.15**, Apache-2.0,
from the official [swagger-api/swagger-ui](https://github.com/swagger-api/swagger-ui)
distribution. Its licence is in [src/pendant_api/static/LICENSE](src/pendant_api/static/LICENSE).
Exact asset URLs, sizes and SHA-256 checksums are recorded in
[src/pendant_api/static/provenance.json](src/pendant_api/static/provenance.json).
The assets are unmodified, served locally, and the online validator is disabled.

## Installed runtimes and downloaded models

Python packages installed by bootstrap are dependencies, not vendored binaries
in this source release. Their own licences apply. Optional transcription uses
[faster-whisper](https://github.com/SYSTRAN/faster-whisper) (MIT), which depends
on native packages including CTranslate2, ONNX Runtime and PyAV/FFmpeg. Whisper
weights are downloaded separately from Hugging Face when requested. The
[OpenAI Whisper repository](https://github.com/openai/whisper/blob/main/LICENSE)
provides the original model/code licence; consult the selected converted model's
repository for its distribution terms.

Optional speaker analysis uses **sherpa-onnx 1.13.8**, Apache-2.0. Explicit model
preparation downloads pyannote segmentation 3.0 (MIT, CNRS) and WeSpeaker VoxCeleb
ResNet34 LM (CC-BY-4.0, WeSpeaker authors), converted to ONNX by sherpa-onnx.
Weights are not in this repository. Their notices are retained beside the
installed files. See [model provenance](docs/DIARIZATION_DEPENDENCIES.md).

The Mac build collects dependency notices and a build-environment inventory.
Binary redistribution still needs a review of every bundled component, including
native FFmpeg libraries. Project MIT terms do not replace third-party licences.

Limitless and product names identify compatible hardware. This community project
is not affiliated with, endorsed by, or distributed by the hardware vendor.
