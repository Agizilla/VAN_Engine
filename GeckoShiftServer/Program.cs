var builder = WebApplication.CreateBuilder(args);
builder.Services.AddCors(o => o.AddDefaultPolicy(p => p.AllowAnyOrigin().AllowAnyHeader().AllowAnyMethod()));
var app = builder.Build();
app.UseCors();

app.MapGet("/health", () => Results.Ok(new { status = "ok", service = "geckoshift", version = "1.0.0" }));

app.MapPost("/morph", async (HttpRequest req) =>
{
    var export = await req.ReadFromJsonAsync<VoiceExport>();
    if (export?.VoiceA?.Landmarks == null || export?.VoiceB?.Landmarks == null || export.VoiceA.Landmarks.Length == 0 || export.VoiceB.Landmarks.Length == 0)
        return Results.BadRequest(new { error = "Both voiceA and voiceB with landmarks required" });

    var pipeline = new MorphPipeline();
    var wavBytes = await pipeline.MorphAndSynthesizeAsync(export);
    return Results.File(wavBytes, "audio/wav", $"geckoshift-morph-{DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()}.wav");
});

app.Run();

public record Landmark(double Freq, double Amplitude, double Bandwidth);
public record VoiceSlot(Landmark[] Landmarks, double Duration, int SampleRate, string Name);
public record PaymentInfo(bool Paid, decimal Amount, string Currency);
public record VoiceExport(string Version, PaymentInfo Payment, VoiceSlot VoiceA, VoiceSlot VoiceB, double MorphRatio);

public class MorphPipeline
{
    public async Task<byte[]> MorphAndSynthesizeAsync(VoiceExport export)
    {
        var ratio = export.MorphRatio;
        var a = export.VoiceA.Landmarks;
        var b = export.VoiceB.Landmarks;

        var pairs = Math.Min(a.Length, b.Length);
        var interpolated = new Landmark[pairs];
        for (int i = 0; i < pairs; i++)
        {
            interpolated[i] = new Landmark(
                a[i].Freq * (1 - ratio) + b[i].Freq * ratio,
                a[i].Amplitude * (1 - ratio) + b[i].Amplitude * ratio,
                a[i].Bandwidth * (1 - ratio) + b[i].Bandwidth * ratio
            );
        }

        int sampleRate = 44100;
        double durationSec = Math.Max(export.VoiceA.Duration, export.VoiceB.Duration);
        if (durationSec <= 0) durationSec = 2.0;
        int totalSamples = (int)(sampleRate * durationSec);

        var samples = new float[totalSamples];
        double baseAmplitude = 0.3 / Math.Max(interpolated.Length, 1);

        foreach (var lm in interpolated)
        {
            double freq = Math.Clamp(lm.Freq, 30, sampleRate / 2 - 1);
            double amp = Math.Pow(10, Math.Max(-3, (lm.Amplitude + 70) / 35)) * baseAmplitude;
            double bw = Math.Max(lm.Bandwidth, 10);
            double decay = Math.Exp(-bw / sampleRate);

            double phase = 0;
            double envelope = 0;
            double attackSamples = sampleRate * 0.01;
            double releaseStart = totalSamples - sampleRate * 0.02;

            for (int i = 0; i < totalSamples; i++)
            {
                if (i < attackSamples)
                    envelope = i / attackSamples;
                else if (i > releaseStart)
                    envelope = (totalSamples - i) / (totalSamples - releaseStart);
                else
                    envelope = 1.0;

                samples[i] += (float)(amp * envelope * Math.Sin(phase));
                phase += 2 * Math.PI * freq / sampleRate;
                amp *= decay;
            }
        }

        float peak = 0;
        foreach (var s in samples) if (Math.Abs(s) > peak) peak = Math.Abs(s);
        if (peak > 0) for (int i = 0; i < totalSamples; i++) samples[i] /= peak;

        var pcm = new short[totalSamples];
        for (int i = 0; i < totalSamples; i++)
            pcm[i] = (short)Math.Clamp(samples[i] * short.MaxValue, short.MinValue, short.MaxValue);

        byte[] wavHeader = new byte[44];
        int dataSize = totalSamples * 2;
        int fileSize = 36 + dataSize;
        WriteWavHeader(wavHeader, sampleRate, 16, 1, dataSize);

        var result = new byte[44 + dataSize];
        Buffer.BlockCopy(wavHeader, 0, result, 0, 44);
        Buffer.BlockCopy(pcm, 0, result, 44, dataSize);

        return await Task.FromResult(result);
    }

    private static void WriteWavHeader(byte[] header, int sampleRate, int bitsPerSample, int channels, int dataSize)
    {
        Buffer.BlockCopy(new byte[] { 0x52, 0x49, 0x46, 0x46 }, 0, header, 0, 4);
        BitConverter.GetBytes(36 + dataSize).CopyTo(header, 4);
        Buffer.BlockCopy(new byte[] { 0x57, 0x41, 0x56, 0x45 }, 0, header, 8, 4);
        Buffer.BlockCopy(new byte[] { 0x66, 0x6D, 0x74, 0x20 }, 0, header, 12, 4);
        BitConverter.GetBytes(16).CopyTo(header, 16);
        BitConverter.GetBytes((short)1).CopyTo(header, 20);
        BitConverter.GetBytes((short)channels).CopyTo(header, 22);
        BitConverter.GetBytes(sampleRate).CopyTo(header, 24);
        BitConverter.GetBytes(sampleRate * channels * bitsPerSample / 8).CopyTo(header, 28);
        BitConverter.GetBytes((short)(channels * bitsPerSample / 8)).CopyTo(header, 32);
        BitConverter.GetBytes((short)bitsPerSample).CopyTo(header, 34);
        Buffer.BlockCopy(new byte[] { 0x64, 0x61, 0x74, 0x61 }, 0, header, 36, 4);
        BitConverter.GetBytes(dataSize).CopyTo(header, 40);
    }
}
