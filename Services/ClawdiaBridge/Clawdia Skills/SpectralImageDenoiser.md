# Spectral Image Denoiser

**Source:** UNR.Engine — `SpectralImageDenoiser`

## Principle

Borrowed from spectral subtraction in audio denoising: transform image patches to 2D frequency domain via STFT, estimate noise floor from low-magnitude bins, apply Wiener gain, reconstruct via inverse STFT with overlap-add.

## Algorithm

1. Divide image into overlapping patches (50% overlap)
2. Apply Hanning window to each patch
3. 2D FFT (row-wise → column-wise) → complex spectrum
4. Estimate noise magnitude from running average of quietest bins
5. Compute Wiener gain `G = SNR / (SNR + 1)` with configurable exponent β
6. Apply gain in frequency domain
7. Inverse 2D FFT → reconstruct patch
8. Overlap-add all patches to form output

## Parameters

| Parameter | Range | Default | Effect |
|-----------|-------|---------|--------|
| WindowSize | 32–256 | 128 | STFT window, power-of-2 |
| NoiseFloor | 0.01–0.2 | 0.05 | Minimum noise magnitude estimate |
| Beta | 1.0–4.0 | 2.0 | Wiener gain exponent (higher = more aggressive) |

## Usage

```
POST /api/v1/image/transform
{
  "model": "spectral",
  "params": { "windowSize": 128, "noiseFloor": 0.05, "beta": 2.0 }
}
```
