# Harmonic-Percussive Separation (HPS) — Audio Motif

**Source:** UNR.Engine — `HarmonicPercussiveExtractor`

## Principle

Borrowed from audio source separation: in the spectrogram, percussive events create vertical striations (broadband transients), while harmonic content creates horizontal striations. Applied to document images, **text strokes = percussive** (sharp vertical edges), **background/paper texture = harmonic** (slow horizontal variation).

## Algorithm

1. Compute 2D FFT of image patch → log-magnitude spectrogram
2. Apply morphological filters:
   - **Vertical kernel** (percussive mask) — preserves sharp text edges
   - **Horizontal kernel** (harmonic mask) — preserves smooth background
3. Soft mask multiplication in frequency domain
4. Inverse FFT to reconstruct separated layers
5. Recombine with configurable text/background weight ratio

## Parameters

| Parameter | Range | Default | Effect |
|-----------|-------|---------|--------|
| WindowSize | 32–512 | 128 | FFT window — larger = better frequency resolution |
| VerticalKernel | 3–31 | 7 | Percussive mask aggressiveness |
| HorizontalKernel | 3–31 | 15 | Harmonic mask smoothness |
| TextBoost | 1.0–5.0 | 1.5 | Gain on text layer |
| MaskThreshold | 0.0–1.0 | 0.3 | Binarization threshold on mask |

## Usage

```
POST /api/v1/image/transform
{
  "model": "hps",
  "params": { "windowSize": 128, "verticalKernel": 7, "horizontalKernel": 15 }
}
```
