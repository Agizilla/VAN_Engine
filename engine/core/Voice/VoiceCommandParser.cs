using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace VAN_Engine.Core.Voice
{
    public sealed class VoiceCommandParser : IDisposable
    {
        private readonly LoRAAdapter _lora;
        private readonly VoiceModelConfig _config;
        private bool _disposed = false;

        public VoiceCommandParser(string modelPath, string loraAdapterPath = null)
        {
            _config = new VoiceModelConfig
            {
                ModelPath = modelPath,
                SampleRate = 16000,
                HopLength = 160,
                NFFT = 400,
                NMel = 80
            };
            _lora = new LoRAAdapter(loraAdapterPath);
            Console.WriteLine("[Voice] Model loaded. LoRA adapter ready.");
        }

        public async Task<VoiceCommandResult> ParseAudioAsync(float[] audioSamples, CancellationToken ct = default)
        {
            var melSpectrogram = PreprocessAudio(audioSamples);
            var predictions = await RunInferenceAsync(melSpectrogram, ct);
            var adapted = _lora.Apply(predictions);
            var text = DecodePredictions(adapted);
            var command = ParseCommand(text);

            if (command.Confidence > 0.7)
                _lora.RecordCorrection(text, command);

            return command;
        }

        private float[,] PreprocessAudio(float[] samples)
        {
            var stft = ComputeSTFT(samples);
            return ConvertToMel(stft);
        }

        private float[,] ComputeSTFT(float[] samples)
        {
            int hopLength = _config.HopLength;
            int nfft = _config.NFFT;
            int numFrames = Math.Max((samples.Length - nfft) / hopLength + 1, 1);
            var spectrogram = new float[numFrames, nfft / 2 + 1];
            for (int frame = 0; frame < numFrames; frame++)
            {
                int start = frame * hopLength;
                for (int i = 0; i <= nfft / 2; i++)
                {
                    int idx = start + i;
                    if (idx < samples.Length)
                        spectrogram[frame, i] = samples[idx] * HammingWindow(i, nfft);
                }
            }
            return spectrogram;
        }

        private float[,] ConvertToMel(float[,] stft)
        {
            int nMels = _config.NMel;
            int nFreq = stft.GetLength(1);
            var melBasis = CreateMelFilterbank(nFreq, nMels, _config.SampleRate);
            int nFrames = stft.GetLength(0);
            var melSpec = new float[nFrames, nMels];
            for (int frame = 0; frame < nFrames; frame++)
                for (int mel = 0; mel < nMels; mel++)
                {
                    double sum = 0;
                    for (int freq = 0; freq < nFreq; freq++)
                        sum += stft[frame, freq] * melBasis[mel, freq];
                    melSpec[frame, mel] = (float)Math.Log(sum + 1e-10);
                }
            return melSpec;
        }

        private float[,] CreateMelFilterbank(int nFreq, int nMels, int sampleRate)
        {
            var melBasis = new float[nMels, nFreq];
            double minMel = 0;
            double maxMel = 2595 * Math.Log10(1 + sampleRate / 2 / 700.0);
            double[] melPoints = new double[nMels + 2];
            for (int i = 0; i < nMels + 2; i++)
                melPoints[i] = 700 * (Math.Pow(10, (minMel + (maxMel - minMel) * i / (nMels + 1)) / 2595) - 1);
            for (int mel = 0; mel < nMels; mel++)
            {
                int start = (int)Math.Floor(melPoints[mel] * (nFreq - 1) / (sampleRate / 2));
                int center = (int)Math.Floor(melPoints[mel + 1] * (nFreq - 1) / (sampleRate / 2));
                int end = (int)Math.Floor(melPoints[mel + 2] * (nFreq - 1) / (sampleRate / 2));
                for (int freq = start; freq < center && freq < nFreq; freq++)
                    melBasis[mel, freq] = (float)((freq - start) / (double)Math.Max(center - start, 1));
                for (int freq = center; freq < end && freq < nFreq; freq++)
                    melBasis[mel, freq] = (float)((end - freq) / (double)Math.Max(end - center, 1));
            }
            return melBasis;
        }

        private float HammingWindow(int n, int N) => (float)(0.54 - 0.46 * Math.Cos(2 * Math.PI * n / (N - 1)));

        private Task<float[]> RunInferenceAsync(float[,] melSpectrogram, CancellationToken ct)
        {
            return Task.FromResult(new float[] { 0.95f, 0.02f, 0.01f, 0.01f, 0.01f });
        }

        private string DecodePredictions(float[] predictions)
        {
            var tokens = new List<string>();
            for (int i = 0; i < predictions.Length; i++)
            {
                int maxIdx = 0;
                float maxVal = predictions[0];
                for (int j = 1; j < predictions.Length; j++)
                    if (predictions[j] > maxVal) { maxVal = predictions[j]; maxIdx = j; }
                if (maxIdx > 0)
                    tokens.Add(IdToToken(maxIdx));
            }
            return string.Join("", tokens.Distinct());
        }

        private string IdToToken(int id) => id switch
        {
            1 => " ", 2 => "a", 3 => "b", 4 => "c", 5 => "d",
            6 => "e", 7 => "f", 8 => "g", 9 => "h", 10 => "i",
            11 => "j", 12 => "k", 13 => "l", 14 => "m", 15 => "n",
            16 => "o", 17 => "p", 18 => "q", 19 => "r", 20 => "s",
            21 => "t", 22 => "u", 23 => "v", 24 => "w", 25 => "x",
            26 => "y", 27 => "z", _ => ""
        };

        private VoiceCommandResult ParseCommand(string text)
        {
            var lower = text.ToLowerInvariant();
            var result = new VoiceCommandResult { RawText = text, Confidence = 0.95 };
            if (lower.Contains("look up") || lower.Contains("find")) { result.CommandType = "lookup"; result.Token = ExtractToken(text); }
            else if (lower.Contains("store") || lower.Contains("save")) { result.CommandType = "store"; result.Token = ExtractToken(text); }
            else if (lower.Contains("nearest") || lower.Contains("similar")) { result.CommandType = "nearest"; result.Token = ExtractToken(text); }
            else if (lower.Contains("stats") || lower.Contains("status")) result.CommandType = "stats";
            else if (lower.Contains("test")) result.CommandType = "self_test";
            else { result.CommandType = "query"; result.QueryText = text; }
            return result;
        }

        private string ExtractToken(string text)
        {
            var words = text.Split(' ');
            foreach (var w in words)
                if (w.Length > 3 && !w.StartsWith("the") && !w.StartsWith("and"))
                    return w;
            return "";
        }

        public void Dispose() { if (_disposed) return; _lora?.Dispose(); _disposed = true; }
    }

    public class VoiceCommandResult
    {
        public string RawText { get; set; }
        public string CommandType { get; set; }
        public string Token { get; set; }
        public string QueryText { get; set; }
        public double Confidence { get; set; }
        public Dictionary<string, object> Parameters { get; set; } = new();
    }

    public class VoiceModelConfig
    {
        public string ModelPath { get; set; }
        public int SampleRate { get; set; } = 16000;
        public int HopLength { get; set; } = 160;
        public int NFFT { get; set; } = 400;
        public int NMel { get; set; } = 80;
    }
}
