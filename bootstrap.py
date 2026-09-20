"""Run `python3 bootstrap.py` (Windows: `py -3 bootstrap.py`)."""
from pathlib import Path
import argparse
import subprocess
import sys
import venv

root = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description="Install the local Pendant dashboard and transcription engine.")
parser.add_argument("--without-transcription", action="store_true", help="Install the dashboard/API without local Whisper dependencies")
options = parser.parse_args()
if sys.version_info < (3, 11):
    raise SystemExit("Python 3.11 or newer is required.")
environment = root / ".venv"
if not environment.exists():
    venv.EnvBuilder(with_pip=True).create(environment)
binary = environment / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
# Refresh the venv installer before processing downloaded packages.
subprocess.run([str(binary), "-m", "pip", "install", "--upgrade", "pip>=26.2"], check=True)
spec = str(root) + ("" if options.without_transcription else "[transcription,diarization]")
subprocess.run([str(binary), "-m", "pip", "install", "-e", spec], check=True)
command = environment / ("Scripts/pendant-local.exe" if sys.platform == "win32" else "bin/pendant-local")
print(f'\nInstalled. Start the dashboard: "{command}" serve\nThen open http://127.0.0.1:8765\nGet your local login token: "{command}" token')
