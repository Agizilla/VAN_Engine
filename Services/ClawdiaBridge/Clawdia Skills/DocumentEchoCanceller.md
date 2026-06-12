# Document Echo Canceller

**Source:** UNR.Engine — `DocumentEchoCanceller`

## Principle

Borrowed from acoustic echo cancellation in teleconferencing: an adaptive NLMS (Normalized Least Mean Squares) filter learns the "echo path" — in document terms, the page bleed-through or header/footer ghosting pattern — and subtracts it from the main signal.

## Algorithm

1. Identify reference region (e.g. page margins where only ghosting exists)
2. Define primary region (content area with bleed-through)
3. Initialize NLMS filter with tap count = expected blur kernel size
4. For each pixel row:
   a. Filter reference signal `x[n]` through adaptive filter → echo estimate
   b. Subtract from primary signal: `e[n] = d[n] - h[n] * x[n]`
   c. Update filter taps: `h[n+1] = h[n] + μ · e[n] · x[n] / (||x||² + ε)`
   d. Adaptive step size μ based on signal power
5. Output clean image with ghosting/bleed removed

## Parameters

| Parameter | Range | Default | Effect |
|-----------|-------|---------|--------|
| FilterTaps | 4–64 | 16 | NLMS filter length |
| Mu | 0.01–0.5 | 0.1 | Adaptation step size |
| Leakage | 0.0–1.0 | 0.99 | Filter leakage factor (stability) |
| ReferenceMargin | 1–50 | 10 | Pixels from edge for reference |

## Usage

```
POST /api/v1/image/transform
{
  "model": "echo",
  "params": { "filterTaps": 16, "mu": 0.1, "referenceMargin": 10 }
}
```
