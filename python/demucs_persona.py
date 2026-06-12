#!/usr/bin/env python3
"""
Demucs Residual Extractor + Voice Persona Builder
Captures what Demucs throws away to evolve a unique voice persona.

Usage:
    python demucs_persona.py --interactive
    python demucs_persona.py --song song.mp3 --output persona.json
"""

import os
import sys
import json
import argparse
import time
import numpy as np
from pathlib import Path

try:
    import librosa
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False

try:
    from demucs.api import Separator
    HAS_DEMUCS = True
except ImportError:
    HAS_DEMUCS = False


class DemucsResidualExtractor:
    """Extract the 'soul' that Demucs discards — the artist's fingerprint."""

    def __init__(self, model_name="htdemucs", device=None):
        if HAS_DEMUCS:
            self.separator = Separator(model=model_name, device=device)
        else:
            self.separator = None
        self.sample_rate = 44100

    def extract(self, audio_path):
        """Separate stems and capture residual fingerprint."""
        if not HAS_LIBROSA:
            return self._synthetic_extract(audio_path)

        audio, sr = librosa.load(audio_path, sr=self.sample_rate, mono=False)
        if audio.ndim == 1:
            audio = audio.reshape(1, -1)

        if self.separator is not None:
            print(f"  Running Demucs separation on {Path(audio_path).name}...")
            stems = self.separator.separate_audio_file(audio_path)

            vocal = stems['vocals'].cpu().numpy()
            drums = stems['drums'].cpu().numpy()
            bass = stems['bass'].cpu().numpy()
            other = stems['other'].cpu().numpy()

            reconstructed = vocal + drums + bass + other
        else:
            print("  [demucs not installed — using synthetic stems for demo]")
            reconstructed = np.zeros_like(audio)

        if audio.shape[1] > reconstructed.shape[1]:
            pad = audio.shape[1] - reconstructed.shape[1]
            reconstructed = np.pad(reconstructed, ((0, 0), (0, pad)))
        elif audio.shape[1] < reconstructed.shape[1]:
            reconstructed = reconstructed[:, :audio.shape[1]]

        residual = audio - reconstructed
        fingerprint = self._analyze_residual(residual, audio)

        return {
            'residual': residual,
            'fingerprint': fingerprint
        }

    def _synthetic_extract(self, audio_path):
        """Fallback when librosa unavailable — generates synthetic fingerprint."""
        duration = 5.0
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        f0 = 100 + (hash(audio_path) % 200)
        residual = 0.01 * np.sin(2 * np.pi * f0 * t)

        fingerprint = {
            'spectral_centroid': float(500 + (hash(audio_path) % 1500)),
            'spectral_rolloff': float(1000 + (hash(audio_path) % 3000)),
            'spectral_bandwidth': float(200 + (hash(audio_path) % 800)),
            'rms_mean': float(0.01 + (hash(audio_path) % 100) / 10000),
            'rms_std': float(0.005),
            'zero_crossing_mean': float(0.05),
            'mfcc': [float(hash(audio_path + str(i)) % 100) / 10 for i in range(13)],
            'mfcc_std': [0.1] * 13,
            'residual_std': float(0.01),
            'residual_skew': float(0.0),
            'residual_kurtosis': float(0.0),
            'band_energy': [float(hash(audio_path + str(b)) % 100) / 100 for b in range(9)],
            'duration_sec': duration
        }
        return fingerprint

    def _analyze_residual(self, residual, original_audio=None):
        """Extract spectral fingerprint from residual noise."""
        residual_mono = residual.mean(axis=0) if residual.ndim > 1 else residual

        D = librosa.stft(residual_mono)
        magnitude = np.abs(D)

        spectral_centroid = librosa.feature.spectral_centroid(S=magnitude)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(S=magnitude)[0]
        spectral_bandwidth = librosa.feature.spectral_bandwidth(S=magnitude)[0]
        rms = librosa.feature.rms(y=residual_mono)[0]
        zero_crossing = librosa.feature.zero_crossing_rate(residual_mono)[0]
        mfcc = librosa.feature.mfcc(y=residual_mono, sr=self.sample_rate, n_mfcc=13)

        freqs = librosa.fft_frequencies(sr=self.sample_rate)
        band_edges = [0, 100, 200, 400, 800, 1600, 3200, 6400, 12800, 22050]
        band_energy = []
        for i in range(len(band_edges) - 1):
            mask = (freqs >= band_edges[i]) & (freqs < band_edges[i + 1])
            band_energy.append(float(np.mean(magnitude[mask])) if np.any(mask) else 0)

        return {
            'spectral_centroid': float(np.mean(spectral_centroid)),
            'spectral_rolloff': float(np.mean(spectral_rolloff)),
            'spectral_bandwidth': float(np.mean(spectral_bandwidth)),
            'rms_mean': float(np.mean(rms)),
            'rms_std': float(np.std(rms)),
            'zero_crossing_mean': float(np.mean(zero_crossing)),
            'mfcc': mfcc.mean(axis=1).tolist(),
            'mfcc_std': mfcc.std(axis=1).tolist(),
            'residual_std': float(np.std(residual_mono)),
            'residual_skew': float(self._skewness(residual_mono)),
            'residual_kurtosis': float(self._kurtosis(residual_mono)),
            'band_energy': band_energy,
            'duration_sec': float(len(residual_mono) / self.sample_rate)
        }

    @staticmethod
    def _skewness(x):
        std = float(np.std(x))
        if std == 0:
            return 0.0
        return float(np.mean(((x - np.mean(x)) / std) ** 3))

    @staticmethod
    def _kurtosis(x):
        std = float(np.std(x))
        if std == 0:
            return 0.0
        return float(np.mean(((x - np.mean(x)) / std) ** 4) - 3)


class VoicePersona:
    """Evolving voice persona that learns from music residuals."""

    def __init__(self, base_seed=0):
        self.base_seed = base_seed
        self.fingerprints = []
        self.current_latent = None
        self.song_history = []

    def ingest_song(self, audio_path):
        """Learn from a song's residual fingerprint."""
        extractor = DemucsResidualExtractor()
        result = extractor.extract(audio_path)

        self.fingerprints.append(result['fingerprint'])
        self.song_history.append({
            'path': audio_path,
            'fingerprint': result['fingerprint'],
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')
        })

        self._update_latent()
        return result

    def _update_latent(self):
        """Build latent vector from accumulated fingerprints."""
        if not self.fingerprints:
            return

        all_mfcc = np.array([fp['mfcc'] for fp in self.fingerprints])
        all_band = np.array([fp['band_energy'] for fp in self.fingerprints])
        all_spec = np.array([[fp['spectral_centroid'],
                               fp['spectral_bandwidth'],
                               fp['residual_std']] for fp in self.fingerprints])

        n = len(self.fingerprints)
        weights = np.exp(-0.3 * np.arange(n - 1, -1, -1))
        weights /= weights.sum()

        cmfcc = np.average(all_mfcc, axis=0, weights=weights)
        cband = np.average(all_band, axis=0, weights=weights)
        cspec = np.average(all_spec, axis=0, weights=weights)

        latent = np.zeros(256)
        latent[:13] = cmfcc
        latent[13:16] = cspec
        latent[16:25] = cband[:9]

        f0 = 80 + (cspec[0] / 2000) * 220
        for i in range(25, 256):
            latent[i] = (0.5 * np.sin(2 * np.pi * f0 * i / 256) +
                         0.3 * np.sin(2 * np.pi * f0 * 3 * i / 256) +
                         0.15 * np.sin(2 * np.pi * f0 * 5 * i / 256))

        latent = latent / (np.abs(latent).max() + 1e-8)
        self.current_latent = latent

    def get_voice_adapter(self):
        """Export persona as JSON adapter for .NET VAN Engine."""
        if self.current_latent is None:
            return None

        return {
            'version': '1.0',
            'type': 'VoicePersona',
            'base_seed': self.base_seed,
            'songs_ingested': len(self.song_history),
            'song_history': [
                {'path': s['path'], 'timestamp': s['timestamp']}
                for s in self.song_history
            ],
            'latent': self.current_latent.tolist(),
            'fingerprint_summary': {
                'mfcc_centroid': np.mean([fp['mfcc'] for fp in self.fingerprints], axis=0).tolist(),
                'spectral_signature': {
                    'centroid': float(np.mean([fp['spectral_centroid'] for fp in self.fingerprints])),
                    'bandwidth': float(np.mean([fp['spectral_bandwidth'] for fp in self.fingerprints]))
                }
            }
        }


# ============================================================================
# Interactive persona builder
# ============================================================================

def build_persona():
    print(r"""
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║              VOICE PERSONA BUILDER                                       ║
    ║              The Voice That Learns from Music                            ║
    ║                                                                          ║
    ║  1. Upload songs from artists you like                                   ║
    ║  2. Demucs extracts stems (vocals, drums, bass, other)                   ║
    ║  3. We capture the RESIDUAL — what Demucs throws away                    ║
    ║  4. That residual is the artist's unique fingerprint                     ║
    ║  5. The voice persona EVOLVES with each song                             ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    """)

    persona = VoicePersona()

    while True:
        print("\n" + "=" * 60)
        print("MENU:")
        print("  1. Add a song to the persona")
        print("  2. Show persona status")
        print("  3. Export voice adapter")
        print("  4. Exit")

        choice = input("  Choose: ").strip()

        if choice == '1':
            path = input("  Song path (MP3/WAV): ").strip()
            if not os.path.exists(path):
                print(f"  File not found: {path}")
                continue

            print(f"\n  Processing {Path(path).name}...")
            try:
                result = persona.ingest_song(path)
                fp = result['fingerprint']
                print(f"  Captured {fp['duration_sec']:.1f}s of artist fingerprint")
                print(f"  Spectral centroid: {fp['spectral_centroid']:.0f} Hz")
                print(f"  Persona evolved — {len(persona.song_history)} song(s) ingested")
            except Exception as e:
                print(f"  Error: {e}")

        elif choice == '2':
            print(f"\n  Songs ingested: {len(persona.song_history)}")
            if persona.song_history:
                print("  Recent:")
                for s in persona.song_history[-5:]:
                    print(f"    {Path(s['path']).name}")
            if persona.current_latent is not None:
                print(f"  Latent: {len(persona.current_latent)} dims, ready to export")

        elif choice == '3':
            if not persona.song_history:
                print("  No songs ingested yet.")
                continue

            out = input("  Save as (.json): ").strip() or f"persona_{len(persona.song_history)}songs.json"
            if not out.endswith('.json'):
                out += '.json'

            adapter = persona.get_voice_adapter()
            with open(out, 'w') as f:
                json.dump(adapter, f, indent=2)
            print(f"  Saved to {out}")
            print("  Load into .NET: VoicePersonaEngine(onnxPath, personaPath)")

        elif choice == '4':
            print("  Exiting.")
            break


def main():
    parser = argparse.ArgumentParser(description='Voice Persona Builder')
    parser.add_argument('--song', help='Process a single song and exit')
    parser.add_argument('--output', help='Output persona JSON path')
    parser.add_argument('--interactive', action='store_true', default=False)
    args = parser.parse_args()

    if args.song:
        persona = VoicePersona()
        persona.ingest_song(args.song)
        adapter = persona.get_voice_adapter()
        out = args.output or f"persona_{Path(args.song).stem}.json"
        with open(out, 'w') as f:
            json.dump(adapter, f, indent=2)
        print(f"  Persona saved to {out}")
    else:
        build_persona()


if __name__ == "__main__":
    main()
