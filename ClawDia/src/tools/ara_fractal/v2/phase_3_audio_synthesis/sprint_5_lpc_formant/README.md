# Sprint 5 — Compact LPC & Formant Signal Engine

## Objective
Replace external StyleTTS2 server with inline wavelet formant synthesis. Build packed phoneme-to-frequency maps and procedural noise generators for breath/grit.

## Deliverables
- `formant_synth.js` — Multi-band resonant filter array (wavelet formant synthesizer)
- `phoneme_map.js` — Packed binary lookup (text → phoneme length, target F1/F2/F3, noise mask)
- `air_turbulence.js` — Procedural noise modulators (breath detail, vocal grit, unvoiced consonants)

## Integration
Outputs raw PCM frames into Sprint 1's audio buffer partition. AudioWorklet from Sprint 2 pipes to Web Audio graph.
