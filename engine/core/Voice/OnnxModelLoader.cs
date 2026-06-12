using System;
using System.IO;
using System.Threading.Tasks;

namespace VAN_Engine.Core.Voice
{
    public class OnnxModelLoader
    {
        private readonly string _modelPath;
        private bool _loaded = false;

        public OnnxModelLoader(string modelPath)
        {
            _modelPath = modelPath;
        }

        public bool IsModelAvailable()
        {
            return File.Exists(_modelPath);
        }

        public async Task<bool> LoadAsync()
        {
            if (_loaded) return true;
            if (!IsModelAvailable()) return false;

            await Task.Run(() =>
            {
                // Real implementation would use Microsoft.ML.OnnxRuntime
                // var session = new InferenceSession(_modelPath);
                System.Threading.Thread.Sleep(100);
                _loaded = true;
            });

            return _loaded;
        }

        public ModelInfo GetModelInfo()
        {
            var fileInfo = new FileInfo(_modelPath);
            return new ModelInfo
            {
                Path = _modelPath,
                SizeBytes = fileInfo.Exists ? fileInfo.Length : 0,
                Loaded = _loaded,
                Format = "ONNX"
            };
        }

        public void Unload()
        {
            _loaded = false;
        }
    }

    public class ModelInfo
    {
        public string Path { get; set; }
        public long SizeBytes { get; set; }
        public bool Loaded { get; set; }
        public string Format { get; set; }
    }
}
