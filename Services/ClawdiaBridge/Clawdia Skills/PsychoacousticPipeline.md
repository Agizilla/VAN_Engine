# Psychoacoustic Image Pipeline

**Source:** UNR.Engine — `PsychoacousticPipeline`

## Principle

The human auditory system's perceptual tricks (frequency masking, just-noticeable differences, binaural localization, cochlear filter banks) are each mapped to a corresponding image processing operation. This is the crown jewel of the UNR approach — a pipeline of 10+ stages, each an audio→image analog.

## Pipeline Stages

| # | Stage | Audio Origin | Image Effect |
|---|-------|-------------|--------------|
| 1 | **Perspective Correction** | HRTF head-shadowing | Deskew via rotation matrix estimation |
| 2 | **Ink Bleed Removal** | Dereverberation | Erode/subtract scatter from ink spread |
| 3 | **Frequency Masking** | Simultaneous masking | Suppress noise below text contrast curve |
| 4 | **JND Thresholding** | Just-noticeable difference | Quantize to eyes-can't-see-the-difference levels |
| 5 | **Missing Fundamental** | Pitch restoration hallucination | Reconstruct broken strokes (Gestalt closure) |
| 6 | **Cochlear Edges** | Cochlear filter bank | Multiscale edge detection (24 channels) |
| 7 | **Scene Analysis** | Auditory scene analysis | Document layout segmentation |
| 8 | **Transient Detection** | Transient detection | Find spots, tears, ink splatters |
| 9 | **Authentication** | Voice biometrics | Document fingerprinting |
| 10 | **Shepard Encoding** | Shepard tone illusion | Infinite-ascending feature encoding |

## Parameters

Use `stages` bitmask to select which stages run. Each stage has its own parameters (see individual skill files).

| Parameter | Type | Default | Effect |
|-----------|------|---------|--------|
| stages | bitmask | All | `PipelineStages` selection |
| enableFrequencyMasking | bool | true | Toggle masking stage |
| enableJndThresholding | bool | true | Toggle JND stage |
| enableCochlearEdges | bool | true | Toggle cochlear edges |
| enableMissingFundamental | bool | false | Toggle stroke restoration |
| enableInkBleedRemoval | bool | true | Toggle ink bleed fix |
| enableSceneAnalysis | bool | true | Toggle layout analysis |
| enableAuthentication | bool | false | Toggle authentication |

## Usage

```
POST /api/v1/image/transform
{
  "model": "psychoacoustic",
  "params": {
    "stages": 127,
    "enableFrequencyMasking": true,
    "enableJndThresholding": true,
    "enableInkBleedRemoval": true
  }
}
```
