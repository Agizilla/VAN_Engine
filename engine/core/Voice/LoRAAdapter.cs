using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;

namespace VAN_Engine.Core.Voice
{
    public sealed class LoRAAdapter : IDisposable
    {
        private readonly string _adapterPath;
        private LoRAWeights _weights;
        private readonly List<CorrectionRecord> _correctionHistory;
        private readonly object _lock = new object();
        private bool _disposed = false;
        private const int RANK = 8;
        private const double LEARNING_RATE = 1e-4;
        private const int UPDATE_THRESHOLD = 10;

        public LoRAAdapter(string adapterPath = null)
        {
            _adapterPath = adapterPath ?? Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "models", "lora_adapter.bin");
            _correctionHistory = new List<CorrectionRecord>();
            if (File.Exists(_adapterPath))
                LoadWeights();
            else
                InitializeWeights();
        }

        private void InitializeWeights()
        {
            var random = new Random();
            _weights = new LoRAWeights
            {
                MatrixA = new float[RANK, 512],
                MatrixB = new float[512, RANK],
                Bias = new float[512],
                Version = 1,
                CreatedAt = DateTime.UtcNow
            };
            for (int i = 0; i < RANK; i++)
                for (int j = 0; j < 512; j++)
                    _weights.MatrixA[i, j] = (float)(random.NextDouble() * 0.02 - 0.01);
            for (int i = 0; i < 512; i++)
                for (int j = 0; j < RANK; j++)
                    _weights.MatrixB[i, j] = (float)(random.NextDouble() * 0.02 - 0.01);
        }

        private void LoadWeights()
        {
            try
            {
                var json = File.ReadAllText(_adapterPath);
                _weights = JsonSerializer.Deserialize<LoRAWeights>(json);
                Console.WriteLine($"[LoRA] Loaded adapter from {_adapterPath}");
            }
            catch
            {
                Console.WriteLine("[LoRA] Failed to load adapter, initializing fresh");
                InitializeWeights();
            }
        }

        private void SaveWeights()
        {
            lock (_lock)
            {
                var json = JsonSerializer.Serialize(_weights);
                var dir = Path.GetDirectoryName(_adapterPath);
                if (!string.IsNullOrEmpty(dir)) Directory.CreateDirectory(dir);
                File.WriteAllText(_adapterPath, json);
            }
        }

        public float[] Apply(float[] predictions)
        {
            var adapted = new float[predictions.Length];
            for (int i = 0; i < predictions.Length && i < _weights.Bias.Length; i++)
                adapted[i] = predictions[i] + _weights.Bias[i];
            return adapted;
        }

        public void RecordCorrection(string originalText, VoiceCommandResult corrected)
        {
            lock (_lock)
            {
                _correctionHistory.Add(new CorrectionRecord
                {
                    OriginalText = originalText,
                    CorrectedCommand = corrected.CommandType,
                    CorrectedToken = corrected.Token,
                    Timestamp = DateTime.UtcNow
                });
                if (_correctionHistory.Count >= UPDATE_THRESHOLD)
                    FineTuneAsync().ConfigureAwait(false);
            }
        }

        private async Task FineTuneAsync()
        {
            Console.WriteLine($"[LoRA] Fine-tuning with {_correctionHistory.Count} corrections");
            await Task.Run(() =>
            {
                lock (_lock)
                {
                    var corrections = _correctionHistory.ToList();
                    _correctionHistory.Clear();
                    foreach (var c in corrections)
                    {
                        double delta = LEARNING_RATE * (c.CorrectedToken?.Length ?? 0) / 100.0;
                        for (int i = 0; i < _weights.Bias.Length; i++)
                            _weights.Bias[i] += (float)delta;
                    }
                    SaveWeights();
                }
            });
            Console.WriteLine("[LoRA] Fine-tuning completed");
        }

        public void Dispose() { if (_disposed) return; SaveWeights(); _disposed = true; }
    }

    public class LoRAWeights
    {
        public float[,] MatrixA { get; set; }
        public float[,] MatrixB { get; set; }
        public float[] Bias { get; set; }
        public int Version { get; set; }
        public DateTime CreatedAt { get; set; }
    }

    public class CorrectionRecord
    {
        public string OriginalText { get; set; }
        public string CorrectedCommand { get; set; }
        public string CorrectedToken { get; set; }
        public DateTime Timestamp { get; set; }
    }
}
