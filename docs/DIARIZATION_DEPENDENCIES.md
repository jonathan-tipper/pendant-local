# Speaker engine and model provenance

| Component | Version/model | Licence and source |
| --- | --- | --- |
| Runtime | sherpa-onnx 1.13.8 | [Apache-2.0](https://github.com/k2-fsa/sherpa-onnx/blob/v1.13.8/LICENSE) |
| Native runtime | sherpa-onnx-core 1.13.8 | Pinned dependency of the official runtime wheel |
| Segmentation | pyannote segmentation 3.0, float ONNX | MIT, copyright 2022 CNRS; LICENSE from the [sherpa model archive](https://github.com/k2-fsa/sherpa-onnx/releases/tag/speaker-segmentation-models) is retained with installed weights |
| Embedding | WeSpeaker VoxCeleb ResNet34 LM, ONNX | CC-BY-4.0 in the [official model card](https://huggingface.co/Wespeaker/wespeaker-voxceleb-resnet34-LM/blob/main/README.md) |

The [sherpa model documentation](https://k2-fsa.github.io/sherpa/onnx/speaker-diarization/models.html)
links the distributions. WeSpeaker's code licence is not substituted for the
model's licence. No gated model account is required. Exact URLs and SHA-256 hashes
are pinned in `src/pendant_api/diarization.py`; extraction selects named regular
files and verifies their hashes. Unrestricted archive extraction is not used.

The adapter retains the segmentation licence and an attribution file linking
model authors, conversions and CC-BY-4.0 terms. Downloaded files are unmodified.
No weights are included in the source tree or Python wheel. Installing the
runtime does not prepare models.

Inference uses local paths and CPU. This adapter makes network requests only for
explicit model preparation. Cancellation waits for native work to return and
discards cancelled results. Whole-file audio decoding can require substantial
memory. Python-level socket checks do not cover native OS network calls.

Speaker counts and boundaries need listening checks. Automatic estimation can
under-count speakers, and a supplied count can improve a result. This is not an
identity-recognition system or a benchmarked long-meeting pipeline.

Updates require a dependency/licence review, advisory scan, new checksum evidence
for changed assets, automated tests and an isolated real-audio check. Keep the
engine behind `diarization.py` so changing it does not rewrite library storage
or speaker rename/export contracts.
