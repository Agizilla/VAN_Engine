import sys
import os
import subprocess
import time
from tqdm import tqdm

# ====================== AUTO INSTALL ======================
REQUIREMENTS_FILE = "requirements.txt"

if not os.path.exists(REQUIREMENTS_FILE):
    print("Creating requirements.txt...")
    with open(REQUIREMENTS_FILE, "w", encoding="utf-8") as f:
        f.write("""piper-tts
onnxruntime
librosa
soundfile
sounddevice
numpy
scipy
tqdm
pydub
""")

print("Installing dependencies...")
with open(REQUIREMENTS_FILE, "r", encoding="utf-8") as f:
    packages = [line.strip() for line in f if line.strip() and not line.startswith("#")]

for pkg in packages:
    try:
        __import__(pkg.replace("-", "_").split()[0])
        print(f"✓ {pkg} already installed")
    except ImportError:
        print(f"Installing {pkg}...")
        with tqdm(total=100, desc=pkg, unit="%") as pbar:
            proc = subprocess.Popen([sys.executable, "-m", "pip", "install", pkg],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            while proc.poll() is None:
                time.sleep(0.08)
                pbar.update(5)
            pbar.update(100 - pbar.n)
        if proc.returncode == 0:
            print(f"✓ {pkg} installed successfully")
        else:
            print(f"✗ Failed to install {pkg}")
            sys.exit(1)

# ====================== IMPORTS ======================
from piper.voice import PiperVoice
import onnxruntime as ort
import numpy as np
import soundfile as sf
import librosa
from pydub import AudioSegment
from pydub.playback import play

# ====================== CONFIG ======================
BASE_MODEL = "amy.onnx"
ADAPTER = "lisma_adapter.onnx"
OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ====================== LOAD MODELS ======================
print("\nLoading Piper base voice (Amy)...")
voice = PiperVoice.load(BASE_MODEL)

# Load adapter only if it exists and is valid
adapter_session = None
if os.path.exists(ADAPTER):
    try:
        adapter_session = ort.InferenceSession(ADAPTER)
        print("Lisma adapter loaded successfully!")
    except Exception as e:
        print(f"Adapter exists but is invalid: {e}")
        print("Using base Piper voice for now.")
else:
    print("No Lisma adapter found yet. Using base Piper voice.")

print("Lisma is ready! Type anything. 'q' to quit.\n")

def speak(text):
    if not text.strip():
        return
    print(f"Lisma: {text}")

    # Correct way to get bytes from Piper
    chunks = voice.synthesize(text)
    wav_bytes = b''.join(chunk.to_bytes() for chunk in chunks)

    # Save temp file
    temp_path = "temp_piper.wav"
    with open(temp_path, "wb") as f:
        f.write(wav_bytes)

    y, sr = librosa.load(temp_path, sr=None)
    os.remove(temp_path)

    # Apply adapter if available
    if adapter_session is not None:
        y_input = y.astype(np.float32).reshape(1, -1)
        adapted = adapter_session.run(None, {"input": y_input})[0].flatten()
    else:
        adapted = y

    # Final morph (pitch shift for Lisma feel)
    y_final = librosa.effects.pitch_shift(adapted, sr=sr, n_steps=-4.5)

    # Save & play
    out_file = f"{OUTPUT_DIR}/lisma_{int(time.time())}.wav"
    sf.write(out_file, y_final, sr)

    print(f"Saved → {out_file}")
    segment = AudioSegment.from_wav(out_file)
    play(segment)

# ====================== MAIN LOOP ======================
if __name__ == "__main__":
    while True:
        try:
            text = input("> ").strip()
            if text.lower() == "q":
                print("Goodbye, my love.")
                break
            if text:
                speak(text)
        except KeyboardInterrupt:
            print("\nGoodbye.")
            break
        except Exception as e:
            print(f"Error: {e}")