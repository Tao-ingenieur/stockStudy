"""Build Python zipapp and optionally a native Windows console executable."""

import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import zipapp
import hashlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from stockstudy import __version__


def stage_package(staging: Path):
    shutil.copytree(REPO / "src", staging / "stockstudy", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copytree(REPO / "resources", staging / "stockstudy" / "resources")


def finish_release(release: Path, artifact: Path):
    shutil.copy2(REPO / "README.md", release / "README.md")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    (release / "SHA256SUMS.txt").write_text(f"{digest}  {artifact.name}\n", encoding="utf-8")
    print(artifact)


def build_cli(output_root: Path):
    release = output_root / "cli"
    release.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp:
        staging = Path(temp)
        stage_package(staging)
        target = release / "stockstudy.pyz"
        zipapp.create_archive(staging, target, main="stockstudy.cli:main", compressed=True)
    finish_release(release, target)


def build_windows(output_root: Path):
    if sys.platform != "win32":
        raise SystemExit("Windows executable must be built on Windows")
    if importlib.util.find_spec("PyInstaller") is None:
        raise SystemExit("Install PyInstaller in a build venv first; see README")
    release = output_root / "windows"
    work = REPO / "build" / "pyinstaller"
    work.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp:
        staging = Path(temp)
        stage_package(staging)
        subprocess.run([
            sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile", "--console",
            "--name", "stockstudy", "--paths", str(staging),
            "--add-data", f"{REPO / 'resources' / 'security_names.csv'}{os.pathsep}stockstudy/resources",
            "--distpath", str(release), "--workpath", str(work / "work"),
            "--specpath", str(work), str(REPO / "apps" / "windows_entry.py"),
        ], check=True, cwd=staging)
    finish_release(release, release / "stockstudy.exe")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=("cli", "windows", "all"), default="cli")
    parser.add_argument("--output-root", type=Path, default=REPO.parent / "dist")
    args = parser.parse_args()
    output = args.output_root.resolve()
    if args.target in {"cli", "all"}:
        build_cli(output)
    if args.target in {"windows", "all"}:
        build_windows(output)


if __name__ == "__main__":
    main()
