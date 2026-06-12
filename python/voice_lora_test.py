#!/usr/bin/env python3
"""
Voice LoRA Test Harness — Rapid experimentation without recompiling.
Part of VanEngine Voice Synthesis System.

Usage:
    python voice_lora_test.py --model tts_base.onnx --text "Hello world"
"""

import os
import sys
import json
import hashlib
import argparse
import numpy as np
from pathlib import Path

try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False

try:
    import soundfile as sf
    HAS_SOUNDFILE = True
except ImportError:
    HAS_SOUNDFILE = False

try:
    import onnxruntime as ort
    HAS_ONNX = True
except ImportError:
    HAS_ONNX = False


# ============================================================================
# Voice LoRA Engine — Python test version
# ============================================================================

class VoiceLoRA:
    """Lightweight voice adapter — pure math, no training required."""

    def __init__(self, latent_dim=256, seed=None):
        self.latent_dim = latent_dim
        self.rng = np.random.RandomState(seed if seed is not None else 42)
        self.latent = self._generate_latent()
        self.sample_rate = 22050

    def _generate_latent(self):
        """Generate unique voice from mathematical bounds."""
        latent = np.zeros(self.latent_dim)
        f0 = 80 + self.rng.rand() * 220
        formant1 = f0 * 3
        formant2 = f0 * 5
        formant3 = f0 * 7
        breathiness = self.rng.rand()
        vocal_tract = 0.8 + self.rng.rand() * 0.4

        for i in range(self.latent_dim):
            latent[i] = (
                0.5 * np.sin(2 * np.pi * f0 * i / self.latent_dim) +
                0.3 * np.sin(2 * np.pi * formant1 * i / self.latent_dim) +
                0.15 * np.sin(2 * np.pi * formant2 * i / self.latent_dim) +
                0.05 * np.sin(2 * np.pi * formant3 * i / self.latent_dim)
            )
            latent[i] *= vocal_tract

        latent += self._pink_noise(self.latent_dim) * breathiness * 0.2
        latent = latent / (np.abs(latent).max() + 1e-8)

        return latent.astype(np.float32)

    def _pink_noise(self, length):
        """Generate pink noise (1/f) using Paul Kellet's approximation."""
        white = self.rng.randn(length)
        b = np.zeros(7)
        pink = np.zeros(length)

        for i in range(length):
            ws = white[i]
            b[0] = 0.99886 * b[0] + ws * 0.0555179
            b[1] = 0.99332 * b[1] + ws * 0.0750759
            b[2] = 0.96900 * b[2] + ws * 0.1538520
            b[3] = 0.86650 * b[3] + ws * 0.3104856
            b[4] = 0.55000 * b[4] + ws * 0.5329522
            b[5] = -0.7616 * b[5] - ws * 0.0168980
            pink[i] = b[0] + b[1] + b[2] + b[3] + b[4] + b[5] + b[6] + ws * 0.5362
            b[6] = ws * 0.115926

        return pink / (np.abs(pink).max() + 1e-8)

    def apply_to_spectrogram(self, spectrogram, strength=0.7):
        """Apply voice characteristics to spectrogram via soft-knee injection."""
        latent_interp = np.interp(
            np.linspace(0, self.latent_dim, spectrogram.shape[1]),
            np.arange(self.latent_dim),
            self.latent
        )

        for i in range(spectrogram.shape[1]):
            influence = latent_interp[i]
            ratio = np.abs(influence) ** 1.5
            spectrogram[:, i] = (
                spectrogram[:, i] * (1 - ratio * strength) +
                influence * ratio * strength
            )

        return spectrogram

    def get_fingerprint(self):
        """Generate unique voice fingerprint."""
        return {
            'hash': hashlib.md5(self.latent.tobytes()).hexdigest()[:16],
            'f0_estimate': float(self._estimate_f0()),
            'breathiness': float(np.std(self.latent))
        }

    def _estimate_f0(self):
        fft = np.abs(np.fft.rfft(self.latent))
        freqs = np.fft.rfftfreq(self.latent_dim, 1 / self.sample_rate)
        mask = (freqs >= 80) & (freqs <= 300)
        if not np.any(mask):
            return 150.0
        peak_idx = np.argmax(fft[mask])
        return float(freqs[mask][peak_idx])


# ============================================================================
# Synthesizer
# ============================================================================

class VoiceSynthesizer:
    def __init__(self, onnx_path, lora_seed=None, sample_rate=22050):
        if HAS_ONNX:
            self.session = ort.InferenceSession(onnx_path)
        else:
            self.session = None
        self.lora = VoiceLoRA(seed=lora_seed)
        self.sample_rate = sample_rate

    def synthesize(self, text, strength=0.7, speaking_rate=1.0):
        """Convert text to audio with voice LoRA applied."""
        tokens = np.array([ord(c) for c in text], dtype=np.int64).reshape(1, -1)

        if self.session is not None:
            inputs = {'input_ids': tokens}
            outputs = self.session.run(None, inputs)
            spectrogram = outputs[0][0]
        else:
            n_freq = 128
            n_time = max(len(text) * 10, 32)
            spectrogram = np.random.randn(n_freq, n_time).astype(np.float32) * 0.1

        if spectrogram.ndim == 2:
            voiced = self.lora.apply_to_spectrogram(spectrogram, strength)
        else:
            voiced = spectrogram

        audio = self._spectrogram_to_audio(voiced, speaking_rate)
        return audio

    def _spectrogram_to_audio(self, spectrogram, speaking_rate):
        """
        Simplified Griffin-Lim for testing — random phase + overlap-add.
        """
        hop_length = 256
        audio_len = spectrogram.shape[1] * hop_length
        audio = np.zeros(audio_len, dtype=np.float32)

        for i in range(spectrogram.shape[1]):
            mag = spectrogram[:, i]
            phase = np.random.rand(len(mag)) * 2 * np.pi
            frame = mag * np.exp(1j * phase)
            frame_audio = np.fft.irfft(frame)[:hop_length]
            start = i * hop_length
            end = min(start + len(frame_audio), audio_len)
            audio[start:end] += frame_audio[:end - start]

        if speaking_rate != 1.0:
            indices = np.arange(0, len(audio), speaking_rate).astype(int)
            indices = indices[indices < len(audio)]
            audio = np.interp(
                np.arange(len(indices)),
                np.arange(len(indices)),
                audio[indices]
            )

        peak = np.abs(audio).max() + 1e-8
        audio = audio / peak

        return audio.astype(np.float32)


# ============================================================================
# Audio helpers
# ============================================================================

def play_audio(audio, sample_rate=22050):
    if HAS_SOUNDDEVICE:
        sd.play(audio, sample_rate)
        sd.wait()
    else:
        print("  [sounddevice not installed — install with: pip install sounddevice]")


def save_audio(audio, filepath, sample_rate=22050):
    if HAS_SOUNDFILE:
        sf.write(filepath, audio, sample_rate)
    else:
        from scipy.io.wavfile import write
        write(filepath, sample_rate, (audio * 32767).astype(np.int16))


# ============================================================================
# Interactive menu
# ============================================================================

def interactive_test():
    print(r"""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║              VAN ENGINE — VOICE LORA TEST HARNESS                    ║
    ║          Voice Synthesis from the Noise Floor                       ║
    ╚══════════════════════════════════════════════════════════════════════╝
    """)

    model_path = input("Enter ONNX TTS model path (or Enter for demo mode): ").strip()
    demo_mode = not (model_path and os.path.exists(model_path))
    if demo_mode:
        print("  Demo mode: synthetic voices (install onnxruntime for real TTS)")

    text = input("\nEnter text to speak: ").strip()
    if not text:
        text = "The signal rises from the noise floor. This voice has never existed before."
        print(f"  Using default text: \"{text}\"")

    print("\n" + "=" * 60)
    print("VOICE TUNING — Generating 3 variations...")
    print("=" * 60)

    seeds = [42, 12345, 999999]
    voices = []

    for i, seed in enumerate(seeds, 1):
        print(f"\n  Generating voice {i}/3 (seed={seed})...")

        if demo_mode:
            duration = max(len(text) * 0.08, 1.0)
            t = np.linspace(0, duration, int(22050 * duration))
            f0 = 100 + (seed % 200)
            audio = 0.5 * np.sin(2 * np.pi * f0 * t)
            for h in range(2, 5):
                audio += 0.15 * np.sin(2 * np.pi * f0 * h * t) / h
            audio = audio / (np.abs(audio).max() + 1e-8)
        else:
            synth = VoiceSynthesizer(model_path, lora_seed=seed)
            audio = synth.synthesize(text, strength=0.7)

        lora = VoiceLoRA(seed=seed)
        fp = lora.get_fingerprint()
        voices.append({'seed': seed, 'fingerprint': fp, 'audio': audio})

        print(f"  Voice {i}: hash={fp['hash']}, F0={fp['f0_estimate']:.0f}Hz, breathiness={fp['breathiness']:.2f}")
        print(f"  Playing voice {i}...")
        play_audio(audio)

    print("\n" + "=" * 60)
    print("SELECT YOUR VOICE")
    print("=" * 60)
    for i, v in enumerate(voices, 1):
        fp = v['fingerprint']
        print(f"  {i}. Hash={fp['hash']}, F0={fp['f0_estimate']:.0f}Hz, Breathiness={fp['breathiness']:.2f}")

    while True:
        try:
            choice = int(input("\nSelect voice (1-3): ").strip())
            if 1 <= choice <= 3:
                break
        except ValueError:
            pass
        print("  Enter 1, 2, or 3.")

    selected = voices[choice - 1]
    print(f"\n  Selected Voice {choice} (seed={selected['seed']})")

    # Fine tuning
    print("\n" + "=" * 60)
    print("FINE TUNING")
    print("=" * 60)

    strength = 0.7
    speaking_rate = 1.0

    while True:
        print(f"\n  Current: strength={strength:.2f}, rate={speaking_rate:.2f}")
        print("  1. Increase strength    2. Decrease strength")
        print("  3. Faster rate          4. Slower rate")
        print("  5. Play current         6. Save & continue")

        opt = input("  Choose: ").strip()
        if opt == '1':
            strength = min(1.0, strength + 0.1)
        elif opt == '2':
            strength = max(0.1, strength - 0.1)
        elif opt == '3':
            speaking_rate = min(2.0, speaking_rate + 0.1)
        elif opt == '4':
            speaking_rate = max(0.5, speaking_rate - 0.1)
        elif opt == '5':
            if demo_mode:
                duration = max(len(text) * 0.08, 1.0)
                t = np.linspace(0, duration, int(22050 * duration / speaking_rate))
                f0 = 100 + (selected['seed'] % 200)
                audio = 0.5 * np.sin(2 * np.pi * f0 * t) * strength
                for h in range(2, 5):
                    audio += 0.15 * np.sin(2 * np.pi * f0 * h * t) / h * strength
                audio = audio / (np.abs(audio).max() + 1e-8)
            else:
                synth = VoiceSynthesizer(model_path, lora_seed=selected['seed'])
                audio = synth.synthesize(text, strength=strength, speaking_rate=speaking_rate)
            print("  Playing...")
            play_audio(audio)
        elif opt == '6':
            break

    # Save adapter
    print("\n" + "=" * 60)
    print("SAVING VOICE ADAPTER")
    print("=" * 60)
    save_path = input("  Save as (.json): ").strip()
    if not save_path:
        save_path = f"voice_adapter_{selected['seed']}.json"
    if not save_path.endswith('.json'):
        save_path += '.json'

    import time
    adapter_data = {
        'version': '1.0',
        'type': 'VoiceLoRA',
        'seed': selected['seed'],
        'latent_dim': 256,
        'strength': strength,
        'speaking_rate': speaking_rate,
        'fingerprint': selected['fingerprint'],
        'text_sample': text,
        'created': time.strftime('%Y-%m-%dT%H:%M:%S')
    }

    with open(save_path, 'w') as f:
        json.dump(adapter_data, f, indent=2)
    print(f"  Saved to {save_path}")

    # Export audio
    print("\n" + "=" * 60)
    export = input("Export audio sample? (y/n): ").strip().lower()
    if export == 'y':
        audio_path = input("  Audio path: ").strip() or f"voice_sample_{selected['seed']}.wav"
        if not audio_path.endswith('.wav'):
            audio_path += '.wav'
        save_audio(selected['audio'], audio_path)
        print(f"  Saved to {audio_path}")

    print("\n  Done. Voice adapter saved — load into .NET VAN Engine via:")
    fname = Path(save_path).name
    print(f"    VoiceLoRAEngine.FromAdapter(\"tts_base.onnx\", \"{fname}\")")


def batch_mode(model_path, text, seed, output):
    print(f"Synthesizing with model={model_path}, seed={seed}...")
    synth = VoiceSynthesizer(model_path, lora_seed=seed)
    audio = synth.synthesize(text)
    if output:
        save_audio(audio, output)
        print(f"  Audio saved to {output}")
    else:
        play_audio(audio)


def main():
    parser = argparse.ArgumentParser(description='VanEngine Voice LoRA Test Harness')
    parser.add_argument('--model', help='Path to ONNX TTS model')
    parser.add_argument('--text', help='Text to synthesize')
    parser.add_argument('--seed', type=int, default=42, help='Voice seed')
    parser.add_argument('--output', help='Output WAV file path')
    args = parser.parse_args()

    if args.model and args.text:
        batch_mode(args.model, args.text, args.seed, args.output)
    else:
        interactive_test()


if __name__ == "__main__":
    main()
