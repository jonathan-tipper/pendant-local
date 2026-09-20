"""Check tracked release contents, local Markdown links and bundled asset hashes.

This is a small release hygiene check, not a substitute for a secret scanner.
It uses only the standard library and never opens a recording workspace.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "build", "dist", ":memory:.ses"}
DATA_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".bin", ".opus", ".wav", ".flac",
                 ".mp3", ".m4a", ".ogg", ".aac", ".webm", ".sqlite", ".sqlite3",
                 ".db", ".jsonl", ".log", ".onnx", ".safetensors", ".bundle", ".ses", ".pyc", ".pyo"}
PRIVATE_NAMES = {"config.json", "workflow.json", "service.lock", "CODEX_HANDOVER.md",
                 "dashboard-validation.json", "transcription-validation.json"}
LINK = re.compile(r"\[[^\]]*\]\(([^\s)]+)(?:\s+[^)]*)?\)")
LOCAL_HOME = re.compile(r"(?<![\w])(?:/Users|/home)/[A-Za-z0-9_.-]+/")


def release_files() -> list[Path]:
    try:
        top = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "--show-toplevel"],
                                      stderr=subprocess.DEVNULL, text=True).strip()
        if Path(top).resolve() == ROOT:
            names = subprocess.check_output(["git", "-C", str(ROOT), "ls-files", "-z"]).decode().split("\0")
            return [ROOT / name for name in names if name]
    except (OSError, subprocess.CalledProcessError):
        pass
    return sorted(p for p in ROOT.rglob("*") if p.is_file()
                  and not (set(p.relative_to(ROOT).parts) & SKIP)
                  and not any(part.endswith(".egg-info") for part in p.parts))


def main() -> int:
    failures = []
    files = release_files()
    for path in files:
        relative = path.relative_to(ROOT)
        if path.is_symlink():
            failures.append(f"Symlink is not a release file: {relative}")
        if (path.suffix.lower() in DATA_SUFFIXES or path.name in PRIVATE_NAMES
                or path.name == ".env" or path.name.startswith(".env.") and path.name != ".env.example"):
            failures.append(f"Private/runtime file: {relative}")
        if any(part in {".git", ".venv", "captures", "imports", "keys", "models", "jobs"} for part in relative.parts):
            failures.append(f"Runtime directory: {relative}")
        if path.suffix.lower() not in {".md", ".py", ".toml", ".yml", ".yaml", ".swift", ".json"}:
            continue
        text = path.read_text(encoding="utf-8")
        # Deliberately synthetic home paths can appear in error-redaction tests.
        matches = LOCAL_HOME.findall(text)
        if any(item not in {"/home/example/", "/Users/example/"} for item in matches):
            failures.append(f"Machine-specific home path: {relative}")
        if path.suffix != ".md":
            continue
        for target in LINK.findall(text):
            target = unquote(target.split("#", 1)[0])
            if not target or re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", target):
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.is_relative_to(ROOT) or not resolved.exists():
                failures.append(f"Broken/nonportable local link: {relative}: {target}")
    static = ROOT / "src/pendant_api/static"
    for record in json.loads((static / "provenance.json").read_text()):
        data = (static / record["file"]).read_bytes()
        if len(data) != record["size"] or hashlib.sha256(data).hexdigest() != record["sha256"]:
            failures.append(f"Bundled asset mismatch: {record['file']}")
    for name in ["LICENSE", "LICENSES/pendant-cli-MIT.txt", "THIRD-PARTY-NOTICES.md",
                 "SECURITY.md", "CONTRIBUTING.md", "README.md"]:
        if not (ROOT / name).is_file():
            failures.append(f"Missing release document: {name}")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(f"Checked {len(files)} source files, local Markdown links and bundled asset checksums.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
