"""Optional offline speaker diarisation and word-to-speaker alignment.

Only prepare_models accesses the network. Inference uses checksum-verified local
ONNX files; speaker IDs are scoped to one recording, never voice identities.
"""
from __future__ import annotations

from collections import defaultdict
from bisect import bisect_right
from functools import lru_cache
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import tarfile

import httpx

MODEL_ID = "speaker-diarization-v1"
MODEL_LABEL = "Local speaker analysis"
DOWNLOAD_MB = 34
SEGMENTATION_URL = "https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-segmentation-models/sherpa-onnx-pyannote-segmentation-3-0.tar.bz2"
EMBEDDING_URL = "https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-recongition-models/wespeaker_en_voxceleb_resnet34_LM.onnx"
ARCHIVE_SHA256 = "24615ee884c897d9d2ba09bb4d30da6bb1b15e685065962db5b02e76e4996488"
FILES = {
    "segmentation.onnx": "220ad67ca923bef2fa91f2390c786097bf305bceb5e261d4af67b38e938e1079",
    "embedding.onnx": "e9848563da86f263117134dfd7ad63c92355b37de492b55e325400c9d9c39012",
}
ATTRIBUTION = """Local speaker analysis v1

Runtime: sherpa-onnx 1.13.8, Apache-2.0
https://github.com/k2-fsa/sherpa-onnx/tree/v1.13.8
Segmentation: pyannote segmentation 3.0, copyright (c) 2022 CNRS, MIT.
Converted to ONNX by the sherpa-onnx project; original licence is alongside this file.
https://huggingface.co/pyannote/segmentation-3.0
Embedding: WeSpeaker VoxCeleb ResNet34 LM, WeSpeaker project authors, CC-BY-4.0.
https://huggingface.co/Wespeaker/wespeaker-voxceleb-resnet34-LM
https://creativecommons.org/licenses/by/4.0/
ONNX conversion supplied by sherpa-onnx. No further model modifications.
"""


class DiarizationUnavailable(ValueError):
    """Safe, actionable setup error without audio or credential details."""


def installed() -> bool:
    return importlib.util.find_spec("sherpa_onnx") is not None


def validate_options(diarize: bool, num_speakers: int | None) -> None:
    if type(diarize) is not bool:
        raise ValueError("Identify speakers must be on or off.")
    if num_speakers is not None and (type(num_speakers) is not int or not 1 <= num_speakers <= 20):
        raise ValueError("Choose between 1 and 20 speakers, or estimate automatically.")
    if not diarize and num_speakers is not None:
        raise ValueError("Enable Identify speakers before choosing a speaker count.")


def complete_files(path: Path, *, verify: bool = False) -> bool:
    for name, digest in FILES.items():
        file = path / name
        if file.is_symlink() or not file.is_file() or file.stat().st_size == 0:
            return False
        if verify and _file_hash(file, file.stat().st_mtime_ns, file.stat().st_size) != digest:
            return False
    return (path / "SEGMENTATION-LICENSE").is_file() and (path / "ATTRIBUTION.txt").is_file()


@lru_cache(maxsize=16)
def _file_hash(path: Path, mtime: int, size: int) -> str:
    # Avoid rehashing 32 MB on every UI poll. A changed file is checked again.
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def downloaded(path: Path) -> bool:
    try:
        return (not path.is_symlink() and complete_files(path, verify=True)
                and json.loads((path / ".prepared.json").read_text()).get("model") == MODEL_ID)
    except (OSError, ValueError, AttributeError, TypeError):
        return False


def _download(url: str, target: Path, digest: str, max_bytes: int) -> None:
    # Fixed public release URLs, no credentials or user audio. Bounded download
    # plus pinned SHA-256 prevents a changed upstream asset from being loaded.
    size, sha = 0, hashlib.sha256()
    with httpx.stream("GET", url, follow_redirects=True, timeout=60) as response:
        response.raise_for_status()
        with target.open("xb") as output:
            for chunk in response.iter_bytes(256 * 1024):
                size += len(chunk)
                if size > max_bytes:
                    raise DiarizationUnavailable("Speaker model download exceeded its expected size. Retry later.")
                sha.update(chunk)
                output.write(chunk)
    if sha.hexdigest() != digest:
        raise DiarizationUnavailable("Speaker model integrity check failed. The download was not installed.")


def prepare_models(path: Path) -> None:
    archive = path / "segmentation.tar.bz2"
    _download(SEGMENTATION_URL, archive, ARCHIVE_SHA256, 8_000_000)
    base = "sherpa-onnx-pyannote-segmentation-3-0/"
    with tarfile.open(archive, "r:bz2") as source:
        for member_name, output_name in (("model.onnx", "segmentation.onnx"), ("LICENSE", "SEGMENTATION-LICENSE")):
            member = source.getmember(base + member_name)
            if not member.isfile() or member.size > 8_000_000:
                raise DiarizationUnavailable("Unexpected speaker model archive. Nothing was installed.")
            with source.extractfile(member) as input_file:
                (path / output_name).write_bytes(input_file.read())
    archive.unlink()
    _download(EMBEDDING_URL, path / "embedding.onnx", FILES["embedding.onnx"], 28_000_000)
    (path / "ATTRIBUTION.txt").write_text(ATTRIBUTION, encoding="utf-8")
    if not complete_files(path, verify=True):
        raise DiarizationUnavailable("Speaker model integrity check failed. Nothing was installed.")


def diarize_local(audio_path: Path, model_path: Path, num_speakers=None,
                  cancelled=None, progress=None) -> list[dict]:
    validate_options(True, num_speakers)
    if not complete_files(model_path, verify=True):
        raise DiarizationUnavailable("Speaker models are incomplete or damaged. Download them again in Settings.")
    import sherpa_onnx
    from faster_whisper.audio import decode_audio

    report = progress or (lambda **_: None)
    report(stage="loading_speaker_models")
    config = sherpa_onnx.OfflineSpeakerDiarizationConfig(
        segmentation=sherpa_onnx.OfflineSpeakerSegmentationModelConfig(
            pyannote=sherpa_onnx.OfflineSpeakerSegmentationPyannoteModelConfig(
                model=str(model_path / "segmentation.onnx")), num_threads=2, provider="cpu"),
        embedding=sherpa_onnx.SpeakerEmbeddingExtractorConfig(
            model=str(model_path / "embedding.onnx"), num_threads=2, provider="cpu"),
        clustering=sherpa_onnx.FastClusteringConfig(num_clusters=num_speakers or -1, threshold=0.5),
        min_duration_on=0.3, min_duration_off=0.5)
    if not config.validate():
        raise DiarizationUnavailable("Speaker model configuration could not load. Reinstall the local speaker engine.")
    engine = sherpa_onnx.OfflineSpeakerDiarization(config)
    audio = decode_audio(str(audio_path), sampling_rate=engine.sample_rate)
    if cancelled is not None and cancelled.is_set():
        raise InterruptedError()
    if not len(audio):
        return []
    duration = len(audio) / engine.sample_rate

    def callback(done, total):
        report(stage="identifying_speakers", processed_seconds=duration * done / max(1, total),
               audio_duration_seconds=duration)
        return 0

    turns = engine.process(audio, callback=callback).sort_by_start_time()
    if cancelled is not None and cancelled.is_set():
        raise InterruptedError()
    return [{"start": float(turn.start), "end": float(turn.end), "speaker": int(turn.speaker)} for turn in turns]


def label_transcript(transcript: dict, turns: list[dict], num_speakers=None) -> dict:
    """Split at word boundaries. Overlap/ties and unmatched words stay unknown.

    Preserve every ASR word, including speech not detected by segmentation.
    The ASR text remains unchanged for search and as a lossless fallback.
    """
    duration = transcript["duration"]
    clean = []
    for turn in turns:
        start, end = float(turn["start"]), float(turn["end"])
        if not (math.isfinite(start) and math.isfinite(end) and 0 <= start <= end
                and type(turn["speaker"]) is int and turn["speaker"] >= 0):
            raise ValueError("Invalid speaker turn")
        if start < duration and end > start:
            clean.append({"start": start, "end": min(duration, end), "speaker": turn["speaker"]})
    clean.sort(key=lambda turn: (turn["start"], turn["end"]))
    identifiers = {}
    for turn in clean:
        source = turn["speaker"]
        identifiers.setdefault(source, f"speaker_{len(identifiers) + 1}")
        turn["speaker"] = identifiers[source]
    names = {value: f"Speaker {i + 1}" for i, value in enumerate(identifiers.values())}
    latest_end = []
    for turn in clean:
        latest_end.append(max(turn["end"], latest_end[-1] if latest_end else 0))

    def match(start, end):
        overlaps = defaultdict(float)
        first = bisect_right(latest_end, start)
        for index in range(first, len(clean)):
            turn = clean[index]
            if turn["start"] > end:
                break
            overlap = max(0, min(end, turn["end"]) - max(start, turn["start"]))
            if end == start and turn["start"] <= start < turn["end"]:
                overlap = 1
            overlaps[turn["speaker"]] += overlap
        ranked = sorted(overlaps.items(), key=lambda item: item[1], reverse=True)
        if not ranked or ranked[0][1] <= 0:
            # Whisper can place a short initial word just before the acoustic
            # speech boundary. Permit at most 250 ms of midpoint drift; never
            # extend a speaker across a long pause or choose between tied voices.
            midpoint = (start + end) / 2
            nearby = {}
            for turn in clean[max(0, bisect_right(latest_end, midpoint - 0.25)):]:
                if turn["start"] > midpoint + 0.25:
                    break
                distance = max(turn["start"] - midpoint, midpoint - turn["end"], 0)
                if distance <= 0.25:
                    nearby[turn["speaker"]] = min(distance, nearby.get(turn["speaker"], float("inf")))
            nearest = sorted(nearby.items(), key=lambda item: item[1])
            if not nearest or (len(nearest) > 1 and nearest[1][1] - nearest[0][1] < 0.05):
                return None
            return nearest[0][0]
        if len(ranked) > 1 and ranked[1][1] >= ranked[0][1] * 0.5:
            return None
        return ranked[0][0]

    labelled = []
    for segment in transcript["segments"]:
        words = segment.get("words")
        if not words or "".join("".join(w["word"] for w in words).split()) != "".join(segment["text"].split()):
            labelled.append({"start": segment["start"], "end": segment["end"], "text": segment["text"], "speaker": None})
            continue
        group = None
        for word in words:
            speaker = match(word["start"], word["end"])
            if group is None or speaker != group["speaker"]:
                if group is not None:
                    group["text"] = group["text"].strip()
                group = {"start": word["start"], "end": word["end"], "text": word["word"], "speaker": speaker}
                labelled.append(group)
            else:
                group["end"] = max(group["end"], word["end"])
                group["text"] += word["word"]
        if group is not None:
            group["text"] = group["text"].strip()
    return {**transcript, "segments": labelled, "speakers": names,
            "diarization": {"model": MODEL_ID, "engine": "sherpa-onnx", "speaker_count": len(names),
                            "requested_speakers": num_speakers, "turns": clean,
                            "unassigned_segments": sum(s["speaker"] is None for s in labelled)}}
