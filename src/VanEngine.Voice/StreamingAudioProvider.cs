using System.Runtime.CompilerServices;

namespace VanEngine.Voice;

public sealed class StreamingAudioProvider
{
    private const int ChunkSize = 4096;

    public VoiceStreamResult StreamFromText(VoiceLoRAEngine engine, string text, float strength = 0.7f, float speakingRate = 1.0f)
    {
        var audio = engine.Synthesize(text, strength, speakingRate);
        return new VoiceStreamResult
        {
            Chunks = StreamChunks(audio),
            SampleRate = 22050
        };
    }

    private static async IAsyncEnumerable<float[]> StreamChunks(float[] audio, [EnumeratorCancellation] CancellationToken ct = default)
    {
        int offset = 0;
        while (offset < audio.Length)
        {
            ct.ThrowIfCancellationRequested();
            int count = Math.Min(ChunkSize, audio.Length - offset);
            var chunk = new float[count];
            Array.Copy(audio, offset, chunk, 0, count);
            offset += count;
            yield return chunk;
            await Task.Yield();
        }
    }

    public async IAsyncEnumerable<float[]> StreamFromTextAsync(VoiceLoRAEngine engine, string text, float strength = 0.7f, [EnumeratorCancellation] CancellationToken ct = default)
    {
        var audio = await Task.Run(() => engine.Synthesize(text, strength), ct);
        int offset = 0;
        while (offset < audio.Length)
        {
            ct.ThrowIfCancellationRequested();
            int count = Math.Min(ChunkSize, audio.Length - offset);
            var chunk = new float[count];
            Array.Copy(audio, offset, chunk, 0, count);
            offset += count;
            yield return chunk;
        }
    }
}
