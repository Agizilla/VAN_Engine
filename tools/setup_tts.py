#!/usr/bin/env python3
"""
Setup local TTS: StyleTTS2 repo + Python deps + Utils models.
Run: python tools/setup_tts.py
"""

import os
import sys
import subprocess
import json
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = ROOT / "models" / "Amelia1_ft_StyleTTS2"

PYTHON = sys.executable
if not PYTHON or "python" not in PYTHON.lower():
    PYTHON = "python"


def step(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")


def run(cmd, cwd=None, check=True):
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd or str(ROOT), capture_output=True, text=True)
    if result.returncode != 0 and check:
        print(f"  ERROR: {result.stderr.strip()}")
        sys.exit(1)
    for line in result.stdout.splitlines():
        print(f"  {line}")
    return result


def main():
    print(f"Python: {PYTHON}")
    print(f"Root:   {ROOT}")
    print(f"Model:  {MODEL_DIR}")

    # 1. Install Python deps
    step("Installing Python dependencies...")
    deps = ["numpy", "soundfile", "onnxruntime", "scipy", "librosa", "munch", "PyYAML"]
    run([PYTHON, "-m", "pip", "install"] + deps)

    # 2. Clone StyleTTS2 repo
    step("Cloning StyleTTS2 repo...")
    if (ROOT / "StyleTTS2").exists():
        print("  StyleTTS2 repo already exists, updating...")
        run(["git", "pull"], cwd=ROOT / "StyleTTS2", check=False)
    else:
        run(["git", "clone", "https://github.com/yl4579/StyleTTS2.git"])

    # 3. Install PyTorch (CPU)
    step("Installing PyTorch (CPU version)...")
    run([PYTHON, "-m", "pip", "install", "torch>=2.0.0", "torchaudio>=2.0.0", "--index-url", "https://download.pytorch.org/whl/cpu"])

    # 4. Link Utils dirs from StyleTTS2 if model doesn't have them
    step("Linking utility dependencies...")
    style_utils = ROOT / "StyleTTS2" / "Utils"
    model_utils = MODEL_DIR / "Utils"

    if style_utils.exists() and not model_utils.exists():
        try:
            import shutil
            shutil.copytree(str(style_utils), str(model_utils), dirs_exist_ok=True)
            print(f"  Copied Utils/ to {model_utils}")
        except Exception as e:
            print(f"  Warning: could not copy Utils: {e}")

    # 5. Download missing ASR / JDC / PLBERT models if needed
    step("Downloading missing model weights (ASR, JDC, PLBERT)...")
    utils_dir = model_utils if model_utils.exists() else style_utils

    downloads = {
        "ASR/epoch_00080.pth": "https://huggingface.co/yl4579/StyleTTS2-LibriTTS/resolve/main/Utils/ASR/epoch_00080.pth",
        "JDC/bst.t7": "https://huggingface.co/yl4579/StyleTTS2-LibriTTS/resolve/main/Utils/JDC/bst.t7",
    }

    for rel_path, url in downloads.items():
        target = utils_dir / rel_path
        if not target.exists():
            print(f"  Downloading {rel_path}...")
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                urllib.request.urlretrieve(url, str(target))
                print(f"    -> saved to {target}")
            except Exception as e:
                print(f"    Warning: download failed: {e}")

    # 6. Test inference
    step("Testing TTS pipeline...")
    test_result = subprocess.run(
        [PYTHON, str(ROOT / "tts_local.py"), "--text", "Hello, this is a test.", "--output", str(ROOT / "test_output.wav")],
        capture_output=True, text=True, cwd=str(ROOT)
    )
    print(f"  {test_result.stdout.strip()}")
    if test_result.returncode != 0:
        print(f"  Warning: test failed: {test_result.stderr.strip()}")
    else:
        test_wav = ROOT / "test_output.wav"
        if test_wav.exists():
            size = test_wav.stat().st_size
            print(f"  Output WAV: {test_wav} ({size} bytes)")
            test_wav.unlink()

    print(f"\n{'='*60}")
    print("  Setup complete!")
    print(f"{'='*60}")
    print(f"\nTry: python tts_local.py --text 'Hello world' --play")


if __name__ == "__main__":
    main()
