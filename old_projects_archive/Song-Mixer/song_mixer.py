import os
import sys
import librosa
import numpy as np
import soundfile as sf
from pydub import AudioSegment, effects

# --- 1. FORCE SYSTEM PATH (The Fix) ---
FFMPEG_DIR = r"C:\ffmpeg\bin"
# This adds the directory to the current process's PATH so all subprocesses see it
os.environ["PATH"] += os.pathsep + FFMPEG_DIR

# Explicitly tell pydub where the binaries are
AudioSegment.converter = os.path.join(FFMPEG_DIR, "ffmpeg.exe")
AudioSegment.ffprobe = os.path.join(FFMPEG_DIR, "ffprobe.exe")

def mp3_to_librosa(path):
    """Bridge Pydub and Librosa for robust MP3 loading."""
    print(f"Opening {path}...")
    # Pydub uses ffprobe here to check file info
    audio = AudioSegment.from_file(path, format="mp3")
    samples = np.array(audio.set_channels(1).get_array_of_samples()).astype(np.float32)
    samples /= np.iinfo(np.int16).max
    return samples, audio.frame_rate

def separate_vocals_robust(path, tag):
    """Decompose the audio into Harmonic and Percussive layers."""
    print(f"Step 1: Extracting frequencies for Song {tag}...")
    y, sr = mp3_to_librosa(path)
    
    # Mathematical separation (HPSS)
    y_harmonic, y_percussive = librosa.effects.hpss(y, margin=3.0)
    
    v_path, b_path = f"vocal_{tag}.wav", f"beat_{tag}.wav"
    sf.write(v_path, y_harmonic, sr)
    sf.write(b_path, y_percussive, sr)
    return v_path, b_path

def sync_and_mix(song1_path, song2_path, output_name="final_mashup.mp3"):
    # Check if files exist before starting
    for p in [song1_path, song2_path]:
        if not os.path.exists(p):
            print(f"Error: Could not find file at {os.path.abspath(p)}")
            return

    # 1. Extraction
    v1_wav, back1_wav = separate_vocals_robust(song1_path, "1")
    v2_wav, _ = separate_vocals_robust(song2_path, "2")

    # 2. BPM Alignment
    print("Step 2: Syncing tempos...")
    y1, sr1 = mp3_to_librosa(song1_path)
    y2, sr2 = mp3_to_librosa(song2_path)
    
    tempo1, _ = librosa.beat.beat_track(y=y1, sr=sr1)
    tempo2, _ = librosa.beat.beat_track(y=y2, sr=sr2)
    
    t1, t2 = float(tempo1), float(tempo2)
    stretch_ratio = t1 / t2
    print(f"Master: {t1:.1f} BPM | Syncing Guest: {t2:.1f} BPM")

    # 3. Time-stretching
    print("Step 3: Adjusting Guest Artist speed...")
    v2_data, _ = librosa.load(v2_wav, sr=sr2)
    v2_stretched = librosa.effects.time_stretch(v2_data, rate=1.0/stretch_ratio)
    
    temp_v2 = "v2_synced.wav"
    sf.write(temp_v2, v2_stretched, sr2)

    # 4. Final Assembly
    print("Step 4: Mixing and Mastering...")
    v1 = AudioSegment.from_wav(v1_wav)
    v2_sync = AudioSegment.from_wav(temp_v2)
    backing = AudioSegment.from_wav(back1_wav)

    # Normalize to prevent volume mismatch
    v1 = effects.normalize(v1)
    v2_sync = effects.normalize(v2_sync)

    # Calculate verse length (32 beats)
    beat_ms = (60 / t1) * 1000
    verse_ms = int(beat_ms * 32)

    # Combine with a 1.5s crossfade
    combined_vocals = v1[:verse_ms].append(v2_sync[verse_ms : verse_ms * 2], crossfade=1500)
    
    # Overlay onto song 1's beat
    final_mix = backing[:verse_ms * 2].overlay(combined_vocals)

    # 5. Export
    final_mix.export(output_name, format="mp3", bitrate="320k")
    print(f"\n+++ SUCCESS +++\nResult: {output_name}")

    # Cleanup
    for f in [v1_wav, back1_wav, v2_wav, temp_v2]:
        try: os.remove(f)
        except: pass

if __name__ == "__main__":
    sync_and_mix("song1.mp3", "song2.mp3")