# MFCC Text Detector

**Source:** UNR.Engine — `MFCCTextDetector`

## Principle

Mel-Frequency Cepstral Coefficients (MFCCs) are the gold standard for speech recognition. By applying MFCC-like cepstral analysis to image patches, text regions are identified by their distinctive "cepstral signature" — high-frequency structure that differs from smooth background or photographic content.

## Algorithm

1. Divide image into blocks (e.g. 32×32)
2. For each block:
   a. Compute 2D power spectrum via FFT
   b. Apply mel-spaced triangular filter bank (12–26 filters)
   c. Log of filter bank energies
   d. DCT → first N cepstral coefficients (exclude 0th = DC)
3. Feature vector = cepstral coefficients + delta + delta-delta
4. Classify block as text/non-text via energy threshold in cepstral bands 2–8
5. Output text-region probability map

## Parameters

| Parameter | Range | Default | Effect |
|-----------|-------|---------|--------|
| BlockSize | 16–128 | 32 | Analysis block in pixels |
| NumFilters | 12–40 | 20 | Mel filter count |
| NumCoeffs | 4–20 | 8 | Cepstral coefficients to retain |
| Threshold | 0.1–0.9 | 0.4 | Text region detection sensitivity |

## Usage

```
POST /api/v1/image/transform
{
  "model": "mfcc",
  "params": { "blockSize": 32, "numFilters": 20, "numCoeffs": 8, "threshold": 0.4 }
}
```
