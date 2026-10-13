
import os
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"

python_path = VENV / (
    "Scripts/python.exe" if os.name == "nt"
    else "bin/python"
)

if not python_path.exists():
    print("Creating virtual environment...")
    venv.create(VENV, with_pip=True)

print("Installing dependencies...")
subprocess.check_call([
    str(python_path),
    "-m", "pip",
    "install",
    "-r", str(ROOT / "requirements.txt")
])

print("Starting API server on port 8000...")
subprocess.check_call([
    str(python_path),
    "-m", "uvicorn",
    "app.main:app",
    "--host", "0.0.0.0",
    "--port", "8000"
], cwd=ROOT)
