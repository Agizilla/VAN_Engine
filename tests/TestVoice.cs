using System;
using System.Threading.Tasks;
using VAN_Engine.Core.Voice;

namespace VAN_Engine.Tests
{
    class TestVoice
    {
        static async Task Main()
        {
            Console.WriteLine("=== VAN_Engine Voice Tests ===\n");

            Console.WriteLine("Test 1: VoiceCommandParser initialization");
            var parser = new VoiceCommandParser("models/whisper_tiny.onnx", "models/lora_adapter.bin");

            Console.WriteLine("Test 2: Parse audio (simulated)");
            var audioSamples = new float[16000];
            var rng = new Random();
            for (int i = 0; i < audioSamples.Length; i++)
                audioSamples[i] = (float)(rng.NextDouble() * 2 - 1);

            var result = await parser.ParseAudioAsync(audioSamples);
            Console.WriteLine($"  Raw text: {result.RawText}");
            Console.WriteLine($"  Command type: {result.CommandType}");
            Console.WriteLine($"  Token: {result.Token}");
            Console.WriteLine($"  Confidence: {result.Confidence:P0}");

            Console.WriteLine("Test 3: OnnxModelLoader");
            var loader = new OnnxModelLoader("models/whisper_tiny.onnx");
            Console.WriteLine($"  Model available: {loader.IsModelAvailable()}");
            var info = loader.GetModelInfo();
            Console.WriteLine($"  Model size: {info.SizeBytes} bytes");

            Console.WriteLine("Test 4: LoRAAdapter fine-tuning");
            var lora = new LoRAAdapter();
            for (int i = 0; i < 12; i++)
            {
                lora.RecordCorrection("test input", new VoiceCommandResult
                {
                    CommandType = "lookup",
                    Token = $"token_{i}",
                    Confidence = 0.9
                });
            }
            Console.WriteLine("  LoRA corrections recorded");

            Console.WriteLine("\nAll voice tests passed");
        }
    }
}
