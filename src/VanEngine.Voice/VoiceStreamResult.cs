namespace VanEngine.Voice;

public sealed class VoiceStreamResult
{
    public required IAsyncEnumerable<float[]> Chunks { get; init; }
    public required int SampleRate { get; init; }
    public int Channels { get; init; } = 1;
}
