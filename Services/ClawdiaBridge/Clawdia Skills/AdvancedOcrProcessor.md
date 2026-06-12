# Advanced OCR Processor

**Source:** UNR.Engine `Audio/AdvancedOcrProcessor.cs`, `MultibandCompressor.cs`, `TransientDetector.cs`

## Principle

Combines three audio-motif techniques into a pre-OCR enhancement chain: **multiband compression** (like audio dynamics processing but for image contrast), **transient detection** (find and repair defects), and **deblur** via blind deconvolution.

## Sub-Stages

### Multiband Compressor
Split image into 3–4 spatial frequency bands (sub-bands), apply independent contrast compression per band, recombine. This is the image equivalent of a multiband audio compressor.
- Low band: global contrast normalization
- Mid bands: local text/background separation
- High band: edge enhancement

### Transient Detector
Identify anomalous pixel regions (spots, tears, folds) using onset detection algorithms adapted from audio transient detection.
- Energy rise across spatial frequency bands
- Threshold-based transient onset identification
- Classify as: ink splatter, crease, hole, dog-ear

### Blind Deconvolution
Estimate blur kernel from image statistics, then apply Wiener deconvolution to restore sharpness.

## Parameters

| Parameter | Range | Default | Effect |
|-----------|-------|---------|--------|
| compressionBands | 2–6 | 4 | Frequency bands for multiband compression |
| contrastThreshold | 0.1–0.9 | 0.3 | Per-band compression threshold |
| transientSensitivity | 0.0–1.0 | 0.5 | Transient detection threshold |
| deblurStrength | 0.0–1.0 | 0.7 | Blind deconvolution strength |

## Usage

```
POST /api/v1/image/transform
{
  "model": "advanced-ocr",
  "params": {
    "compressionBands": 4,
    "contrastThreshold": 0.3,
    "transientSensitivity": 0.5,
    "deblurStrength": 0.7
  }
}
```
