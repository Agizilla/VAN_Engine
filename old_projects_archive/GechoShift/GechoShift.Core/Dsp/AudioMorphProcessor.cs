using System;

namespace GechoShift.Core.Dsp
{
    // ════════════════════════════════════════════════════════════════════
    // AudioMorphSettings
    //   Parameter bag passed to AudioMorphProcessor.Apply().
    //   Ranges mirror VlcMorphPlugin field constraints.
    // ════════════════════════════════════════════════════════════════════
    public sealed class AudioMorphSettings
    {
        /// Pitch multiplier — 0.5 (octave down) to 2.0 (octave up). Default 1.0.
        public float Pitch   { get; set; } = 1.0f;

        /// Formant ratio — 0.8 (lower) to 1.5 (higher). Default 1.0.
        public float Formant { get; set; } = 1.0f;

        /// Tube saturation amount — 0.0 to 1.0. Default 0.0.
        public float Grit    { get; set; } = 0.0f;

        /// RMS-keyed noise level — 0.0 to 1.0. Default 0.0.
        public float Breath  { get; set; } = 0.0f;
    }

    // ════════════════════════════════════════════════════════════════════
    // AudioMorphProcessor
    //   Applies pitch shift, formant warp, grit, and breath to a
    //   mono float[] buffer.
    //
    //   STUB — returns modified samples so the pipeline compiles and runs.
    //   Replace the body of Apply() with real DSP when ready.
    // ════════════════════════════════════════════════════════════════════
    public static class AudioMorphProcessor
    {
        /// <summary>
        /// Apply morph settings to <paramref name="samples"/> and return
        /// the processed audio.  Input is NOT modified in place.
        /// </summary>
        public static float[] Apply(float[] samples, AudioMorphSettings settings)
        {
            if (samples == null || samples.Length == 0)
                return Array.Empty<float>();

            // ── STUB ──────────────────────────────────────────────────
            // Real implementation will:
            //   1. OLA time-stretch by 1/pitchRatio  (preserves formants)
            //   2. Resample to original length        (shifts pitch)
            //   3. LPC formant warp in-place
            //   4. Apply grit (soft-clip saturation)
            //   5. Apply breath (RMS-keyed noise)
            //
            // For now: apply grit and breath only (zero-copy-safe path).

            var output = (float[])samples.Clone();

            var grit   = settings.Grit;
            var breath = settings.Breath;
            var rng    = new Random(42);

            // RMS for breath keying
            var rms = 0f;
            foreach (var s in output) rms += s * s;
            rms = MathF.Sqrt(rms / output.Length);

            for (var i = 0; i < output.Length; i++)
            {
                var s = output[i];

                // Soft-clip grit
                if (grit > 0.001f)
                {
                    var drive   = 1f + grit * 8f;
                    var x       = s * drive;
                    var clipped = x / (1f + MathF.Abs(x));
                    s = s + grit * (clipped - s);
                }

                // RMS-keyed noise breath
                if (breath > 0.001f)
                {
                    var noise = (float)(rng.NextDouble() * 2.0 - 1.0);
                    s += noise * breath * rms * 0.6f;
                }

                output[i] = Math.Clamp(s, -1f, 1f);
            }

            return output;
        }
    }
}
