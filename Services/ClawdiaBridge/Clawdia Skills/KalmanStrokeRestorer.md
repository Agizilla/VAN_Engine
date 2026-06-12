# Kalman Stroke Restorer

**Source:** UNR.Engine — `KalmanStrokeRestorer`

## Principle

Treats each row of a damaged/eroded document image as a 1D signal and applies a Kalman filter to estimate the true stroke intensity, bridging gaps caused by wear, bleed-through, or poor scanning.

## Algorithm

1. For each row pixel vector, initialize state estimate `x₀ = pixel[0]`
2. **Predict:** `x̂ₖ = xₖ₋₁ + Q·N(0,1)` (process noise models stroke variation)
3. **Update:** `xₖ = x̂ₖ + Kₖ · (pixelₖ - x̂ₖ)` where Kalman gain `Kₖ` depends on measurement noise R and predicted covariance
4. Adaptive R per pixel based on local variance — high variance = low confidence (text edges), low variance = high confidence (smooth areas)
5. Output restored row with gaps filled

## Parameters

| Parameter | Range | Default | Effect |
|-----------|-------|---------|--------|
| ProcessNoise | 1e-6–1.0 | 0.01 | Q — how much stroke intensity can vary |
| MeasurementNoise | 1e-6–1.0 | 0.1 | R₀ — base measurement uncertainty |
| AdaptiveR | bool | true | Scale R by local gradient magnitude |
| Iterations | 1–5 | 2 | Forward-backward smoothing passes |

## Usage

```
POST /api/v1/image/transform
{
  "model": "kalman",
  "params": { "processNoise": 0.01, "measurementNoise": 0.1, "iterations": 2 }
}
```
