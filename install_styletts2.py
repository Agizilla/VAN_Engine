#!/usr/bin/env python3
"""Installation script for StyleTTS 2 with LoRA support"""

import subprocess
import sys

def install():
    print("Installing StyleTTS 2 with LoRA support...")
    subprocess.run(["git", "clone", "https://github.com/yl4579/StyleTTS2.git"], check=False)
    deps = [
        "torch>=2.0.0",
        "torchaudio>=2.0.0",
        "librosa",
        "numpy",
        "phonemizer",
        "tqdm",
        "einops",
        "onnx",
        "onnxruntime",
        "soundfile",
        "monotonic-align"
    ]
    for dep in deps:
        subprocess.run([sys.executable, "-m", "pip", "install", dep])
    print("Installation complete!")

if __name__ == "__main__":
    install()
