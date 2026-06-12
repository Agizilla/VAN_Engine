# Phase Vocoder Upscaler

**Source:** UNR.Engine — `PhaseVocoderUpscaler`

## Principle

The phase vocoder allows time-stretching audio without pitch change by manipulating phase in the STFT domain. Applied to images, this becomes a **super-resolution** technique: "time-stretching" the image dimensions while preserving local phase structure (text features).

## Algorithm

1. Compute STFT of image with overlapping windows
2. Estimate instantaneous frequency from phase differences across frames
3. For upscaling factor N:
   a. Interpolate magnitude spectrogram by factor N
   b. Propagate phase using phase-locking heuristic:
      `φ_new = φ_old + N · Δφ` (horizontal/vertical)
4. Ensure phase consistency via phase gradient estimation
5. Inverse STFT → upscaled image
6. Optional: sharpen with unsharp mask on text regions

## Parameters

| Parameter | Range | Default | Effect |
|-----------|-------|---------|--------|
| ScaleFactor | 1.5–4.0 | 2.0 | Upscaling multiplier |
| WindowSize | 32–128 | 64 | STFT window |
| PhaseLock | 0.0–1.0 | 0.7 | Phase consistency constraint |
| Sharpening | 0.0–2.0 | 0.5 | Post-upscale text sharpening |

## Usage

```
POST /api/v1/image/transform
{
  "model": "vocoder",
  "params": { "scaleFactor": 2.0, "windowSize": 64, "phaseLock": 0.7 }
}
```
