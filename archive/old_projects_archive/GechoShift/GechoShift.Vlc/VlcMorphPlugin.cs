using System;
using System.Buffers;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using GechoShift.Contracts;
using GechoShift.Core.Dsp;
using GechoShift.Infrastructure;
using LibVLCSharp.Shared;
using NAudio.Dsp;
using NAudio.Wave;

namespace GechoShift.Vlc
{
    public sealed class VlcMorphPlugin : IMorphPlugin, INativeBridgeControl
    {
        private readonly LibVLC libVlc;
        private readonly ITaskLogger logger;
        private MediaPlayer? mediaPlayer;
        private readonly string tempRoot;
        private readonly object stateLock = new object();
        private readonly object telemetryLock = new object();
        private bool controlsInjected;
        private readonly TimeSpan operationTimeout = TimeSpan.FromMinutes(2);
        private readonly string telemetryLatestPath;
        private int extractBeatCount;
        private int extractVocalsCount;
        private int applyMorphCount;
        private long extractBeatMs;
        private long extractVocalsMs;
        private long applyMorphMs;
        private int errorCount;
        private readonly List<PluginErrorEvent> recentErrors = new List<PluginErrorEvent>();
        private readonly List<PluginOperationEvent> operationEvents = new List<PluginOperationEvent>();
        private readonly INativeFilterBridge nativeBridge;
        private bool nativeBridgeEnabled;
        private bool nativeBridgeAttached;

        private float pitch = 1.0f;
        private float formant = 1.0f;
        private float grit = 0.0f;
        private float breath = 0.0f;

        private string? lastSourcePath;
        private string? lastVocalsPath;
        private string? lastBeatPath;
        private string? lastMorphedPath;

        public VlcMorphPlugin(LibVLC libVlc) : this(libVlc, null, null) { }

        public VlcMorphPlugin(LibVLC libVlc, ITaskLogger? logger = null, string? tempDirectory = null)
        {
            this.libVlc = libVlc ?? throw new ArgumentNullException(nameof(libVlc));
            this.logger = logger ?? new ConsoleTaskLogger();
            tempRoot = tempDirectory ?? Path.Combine(Path.GetTempPath(), "VlcMorphPlugin");
            Directory.CreateDirectory(tempRoot);
            telemetryLatestPath = Path.Combine(tempRoot, "telemetry_latest.json");
            nativeBridge = new VlcNativeFilterBridge(tempRoot);
            nativeBridgeEnabled = true;
        }

        public void Attach(MediaPlayer player)
        {
            mediaPlayer = player ?? throw new ArgumentNullException(nameof(player));
            mediaPlayer.Playing += OnPlaying;
            mediaPlayer.PositionChanged += OnPositionChanged;
            mediaPlayer.EncounteredError += OnEncounteredError;
            LogInfo("Attached to MediaPlayer.");
        }

        public void Detach()
        {
            if (mediaPlayer == null) return;
            mediaPlayer.Playing -= OnPlaying;
            mediaPlayer.PositionChanged -= OnPositionChanged;
            mediaPlayer.EncounteredError -= OnEncounteredError;
            mediaPlayer = null;
            LogInfo("Detached from MediaPlayer.");
        }

        public void SetPitch(float value)   => pitch   = Clamp(value, 0.5f, 2.0f);
        public void SetFormant(float value) => formant = Clamp(value, 0.8f, 1.5f);
        public void SetGrit(float value)    => grit    = Clamp(value, 0f, 1f);
        public void SetBreath(float value)  => breath  = Clamp(value, 0f, 1f);

        public async Task<bool> ExtractBeatAsync(CancellationToken ct = default)
        {
            if (!TryResolveCurrentMediaPath(out string inputPath))
            {
                LogInfo("ExtractBeat failed: media path unavailable.");
                return false;
            }
            return await RunWithTimeoutAsync("ExtractBeat", async opCt =>
            {
                try
                {
                    opCt.ThrowIfCancellationRequested();
                    var result = ExtractStemsInternal(inputPath);
                    LogInfo(result ? "Beat extracted." : "Beat extract failed.");
                    if (result) extractBeatCount++;
                    return result;
                }
                catch (Exception ex) { LogError("ExtractBeat exception.", ex); return false; }
            }, ct, ms => extractBeatMs += ms);
        }

        public async Task<bool> ExtractVocalsAsync(CancellationToken ct = default)
        {
            if (!TryResolveCurrentMediaPath(out string inputPath))
            {
                LogInfo("ExtractVocals failed: media path unavailable.");
                return false;
            }
            return await RunWithTimeoutAsync("ExtractVocals", async opCt =>
            {
                try
                {
                    opCt.ThrowIfCancellationRequested();
                    var result = ExtractStemsInternal(inputPath);
                    LogInfo(result ? "Vocals extracted." : "Vocals extract failed.");
                    if (result) extractVocalsCount++;
                    return result;
                }
                catch (Exception ex) { LogError("ExtractVocals exception.", ex); return false; }
            }, ct, ms => extractVocalsMs += ms);
        }

        public async Task<bool> ApplyMorphAsync(CancellationToken ct = default)
        {
            if (mediaPlayer == null) { LogInfo("ApplyMorph failed: no MediaPlayer."); return false; }

            if (string.IsNullOrWhiteSpace(lastVocalsPath) || string.IsNullOrWhiteSpace(lastBeatPath) ||
                !File.Exists(lastVocalsPath) || !File.Exists(lastBeatPath))
            {
                if (!await ExtractVocalsAsync(ct)) return false;
            }

            return await RunWithTimeoutAsync("ApplyMorph", async opCt =>
            {
                try
                {
                    opCt.ThrowIfCancellationRequested();
                    ProcessAndRemixInternal();
                    if (string.IsNullOrWhiteSpace(lastMorphedPath) || !File.Exists(lastMorphedPath))
                    {
                        LogInfo("ApplyMorph failed: morphed file missing.");
                        return false;
                    }
                    using var media = new Media(libVlc, new Uri(lastMorphedPath));
                    media.AddOption(":file-caching=150");
                    nativeBridgeAttached = false;
                    if (nativeBridgeEnabled &&
                        nativeBridge.IsAvailable() &&
                        nativeBridge.IsAbiCompatible(NativeBridgeContract.ExpectedAbiVersion) &&
                        nativeBridge.TryAttachToPlayback())
                    {
                        media.AddOption(":audio-filter=" + nativeBridge.FilterName());
                        nativeBridgeAttached = true;
                    }
                    mediaPlayer.Media = media;
                    var ok = mediaPlayer.Play();
                    LogInfo(ok ? "Morphed output routed back to VLC." : "VLC failed to play morphed output.");
                    if (ok) applyMorphCount++;
                    return ok;
                }
                catch (Exception ex) { LogError("ApplyMorph exception.", ex); return false; }
            }, ct, ms => applyMorphMs += ms);
        }

        private bool ExtractStemsInternal(string inputPath)
        {
            var timestamp  = DateTime.UtcNow.ToString("yyyyMMdd_HHmmss_fff");
            var vocalsPath = Path.Combine(tempRoot, $"vocals_{timestamp}.wav");
            var beatPath   = Path.Combine(tempRoot, $"beat_{timestamp}.wav");

            using var reader   = new AudioFileReader(inputPath);
            var sr       = reader.WaveFormat.SampleRate;
            var channels = reader.WaveFormat.Channels;
            var source   = ReadAllFloat(reader);
            var mono     = DownmixToMono(source, channels);

            const int fftSize = 1024;
            const int hop     = 256;
            var vocals = StftMaskSplit(mono, sr, fftSize, hop, StemSplitMode.VocalsHighBand);
            var beat   = StftMaskSplit(mono, sr, fftSize, hop, StemSplitMode.BeatLowBand);

            SaveFloatMonoWav(vocalsPath, vocals, sr);
            SaveFloatMonoWav(beatPath,   beat,   sr);

            lock (stateLock)
            {
                lastSourcePath = inputPath;
                lastVocalsPath = vocalsPath;
                lastBeatPath   = beatPath;
            }
            return true;
        }

        private void ProcessAndRemixInternal()
        {
            if (string.IsNullOrWhiteSpace(lastVocalsPath) || string.IsNullOrWhiteSpace(lastBeatPath))
                throw new InvalidOperationException("Stems are unavailable.");

            using var vocalsReader = new AudioFileReader(lastVocalsPath);
            using var beatReader   = new AudioFileReader(lastBeatPath);

            var sr     = vocalsReader.WaveFormat.SampleRate;
            var vocals = ReadAllFloat(vocalsReader);
            var beat   = ReadAllFloat(beatReader);

            var warped = AudioMorphProcessor.Apply(vocals, new AudioMorphSettings
            {
                Pitch = pitch, Formant = formant, Grit = grit, Breath = breath
            });

            var mixLen = Math.Max(warped.Length, beat.Length);
            var mix    = new float[mixLen];
            for (var i = 0; i < mixLen; i++)
            {
                var v  = i < warped.Length ? warped[i] : 0f;
                var b  = i < beat.Length   ? beat[i]   : 0f;
                mix[i] = Clamp(v * 0.85f + b * 0.9f, -1f, 1f);
            }

            var timestamp  = DateTime.UtcNow.ToString("yyyyMMdd_HHmmss_fff");
            var outputPath = Path.Combine(tempRoot, $"morphed_{timestamp}.wav");
            SaveFloatMonoWav(outputPath, mix, sr);
            lastMorphedPath = outputPath;
        }

        private static float[] StftMaskSplit(float[] input, int sampleRate, int fftSize, int hop, StemSplitMode splitMode)
        {
            if (input.Length == 0) return Array.Empty<float>();

            var output    = new float[input.Length + fftSize];
            var window    = BuildHann(fftSize);
            var frame     = new NAudio.Dsp.Complex[fftSize];
            var recon     = new NAudio.Dsp.Complex[fftSize];
            var cutoffHz  = 1800f;
            var cutoffBin = (int)(cutoffHz * fftSize / sampleRate);

            for (var pos = 0; pos < input.Length; pos += hop)
            {
                Array.Clear(frame, 0, frame.Length);
                for (var i = 0; i < fftSize; i++)
                {
                    var idx = pos + i;
                    frame[i].X = idx < input.Length ? input[idx] * window[i] : 0f;
                    frame[i].Y = 0f;
                }
                FastFourierTransform.FFT(true, (int)Math.Log2(fftSize), frame);
                Array.Copy(frame, recon, fftSize);

                for (var k = 0; k < fftSize / 2; k++)
                {
                    var keep = splitMode switch
                    {
                        StemSplitMode.VocalsHighBand => k >= cutoffBin,
                        StemSplitMode.BeatLowBand    => k <= cutoffBin,
                        _                            => true
                    };
                    if (!keep)
                    {
                        recon[k].X = 0f; recon[k].Y = 0f;
                        var mirror = (fftSize - k) % fftSize;
                        recon[mirror].X = 0f; recon[mirror].Y = 0f;
                    }
                }
                FastFourierTransform.FFT(false, (int)Math.Log2(fftSize), recon);
                for (var i = 0; i < fftSize; i++)
                {
                    var idx = pos + i;
                    if (idx < output.Length)
                        output[idx] += (recon[i].X / fftSize) * window[i];
                }
            }
            if (output.Length > input.Length) Array.Resize(ref output, input.Length);
            return output;
        }

        private bool TryResolveCurrentMediaPath(out string path)
        {
            path = string.Empty;
            if (mediaPlayer?.Media == null) return false;
            var mrl = mediaPlayer.Media.Mrl;
            if (string.IsNullOrWhiteSpace(mrl)) return false;
            try
            {
                path = mrl.StartsWith("file://", StringComparison.OrdinalIgnoreCase)
                    ? new Uri(mrl).LocalPath : mrl;
                return File.Exists(path);
            }
            catch { return false; }
        }

        private void OnPlaying(object? sender, EventArgs e)
        {
            if (controlsInjected) return;
            controlsInjected = true;
            LogInfo("OnPlaying: control hook requested.");
            LogInfo("Note: Qt bottom-bar injection is host-app responsibility in LibVLCSharp.");
        }

        private void OnPositionChanged(object? sender, MediaPlayerPositionChangedEventArgs e) { }

        private void OnEncounteredError(object? sender, EventArgs e) =>
            LogInfo("VLC playback error (possible buffer underrun/filter mismatch).");

        private static float[] ReadAllFloat(AudioFileReader reader)
        {
            var rented = ArrayPool<float>.Shared.Rent(reader.WaveFormat.SampleRate * reader.WaveFormat.Channels);
            try
            {
                using var ms = new MemoryStream();
                using var bw = new BinaryWriter(ms);
                int read;
                while ((read = reader.Read(rented, 0, rented.Length)) > 0)
                    for (var i = 0; i < read; i++) bw.Write(rented[i]);
                bw.Flush(); ms.Position = 0;
                using var br = new BinaryReader(ms);
                var count  = (int)(ms.Length / sizeof(float));
                var result = new float[count];
                for (var i = 0; i < count; i++) result[i] = br.ReadSingle();
                return result;
            }
            finally { ArrayPool<float>.Shared.Return(rented); }
        }

        private static float[] DownmixToMono(float[] interleaved, int channels)
        {
            if (channels <= 1) return interleaved;
            var len  = interleaved.Length / channels;
            var mono = new float[len];
            for (var i = 0; i < len; i++)
            {
                var sum = 0f;
                for (var ch = 0; ch < channels; ch++) sum += interleaved[i * channels + ch];
                mono[i] = sum / channels;
            }
            return mono;
        }

        private static void SaveFloatMonoWav(string path, float[] samples, int sampleRate)
        {
            var format = WaveFormat.CreateIeeeFloatWaveFormat(sampleRate, 1);
            using var writer = new WaveFileWriter(path, format);
            writer.WriteSamples(samples, 0, samples.Length);
        }

        private static float[] BuildHann(int n)
        {
            var w = new float[n];
            for (var i = 0; i < n; i++)
                w[i] = (float)(0.5 * (1 - Math.Cos(2 * Math.PI * i / (n - 1))));
            return w;
        }

        private static float Clamp(float v, float min, float max) => Math.Max(min, Math.Min(max, v));

        public void Dispose()
        {
            Detach();
            LogInfo($"Summary | ExtractBeat count={extractBeatCount} totalMs={extractBeatMs} | " +
                    $"ExtractVocals count={extractVocalsCount} totalMs={extractVocalsMs} | " +
                    $"ApplyMorph count={applyMorphCount} totalMs={applyMorphMs}");
            ExportTelemetrySnapshot();
        }

        private void LogInfo(string message)  => logger.Info("[VlcMorphPlugin] " + message);

        private void LogError(string message, Exception ex)
        {
            lock (telemetryLock)
            {
                errorCount++;
                recentErrors.Add(new PluginErrorEvent
                {
                    Utc = DateTime.UtcNow, Message = message,
                    Exception = ex.GetType().Name, Detail = ex.Message
                });
                TrimTail(recentErrors, 64);
            }
            logger.Error("[VlcMorphPlugin] " + message, ex);
        }

        private async Task<bool> RunWithTimeoutAsync(string operationName,
            Func<CancellationToken, Task<bool>> action,
            CancellationToken externalToken,
            Action<long> durationSink)
        {
            using var timeoutCts = new CancellationTokenSource(operationTimeout);
            using var linked     = CancellationTokenSource.CreateLinkedTokenSource(externalToken, timeoutCts.Token);
            var sw = Stopwatch.StartNew();
            var success    = false;
            var completion = "ok";
            try
            {
                success = await action(linked.Token);
                return success;
            }
            catch (OperationCanceledException) when (timeoutCts.IsCancellationRequested)
            {
                completion = "timeout";
                LogInfo($"{operationName} cancelled due to timeout ({operationTimeout.TotalSeconds:F0}s).");
                return false;
            }
            catch (OperationCanceledException)
            {
                completion = "cancelled";
                throw;
            }
            finally
            {
                sw.Stop();
                durationSink(sw.ElapsedMilliseconds);
                RecordOperation(operationName, success, sw.ElapsedMilliseconds, completion);
                ExportTelemetrySnapshot();
            }
        }

        private void RecordOperation(string operationName, bool success, long elapsedMs, string completion)
        {
            lock (telemetryLock)
            {
                operationEvents.Add(new PluginOperationEvent
                {
                    Utc = DateTime.UtcNow, Operation = operationName,
                    Success = success, Completion = completion, DurationMs = elapsedMs
                });
                TrimTail(operationEvents, 128);
            }
        }

        private void ExportTelemetrySnapshot()
        {
            try
            {
                PluginTelemetrySnapshot snapshot;
                lock (telemetryLock)
                {
                    var abiVersion    = nativeBridge.AbiVersion();
                    var abiCompatible = nativeBridge.IsAbiCompatible(NativeBridgeContract.ExpectedAbiVersion);
                    snapshot = new PluginTelemetrySnapshot
                    {
                        SchemaVersion   = TelemetryContract.CurrentSchemaVersion,
                        SchemaSignature = TelemetryContract.SignatureFor(TelemetryContract.CurrentSchemaVersion),
                        GeneratedUtc    = DateTime.UtcNow,
                        TempRoot        = tempRoot,
                        LastSourcePath  = lastSourcePath,
                        LastVocalsPath  = lastVocalsPath,
                        LastBeatPath    = lastBeatPath,
                        LastMorphedPath = lastMorphedPath,
                        Settings        = new MorphSettingsSnapshot { Pitch = pitch, Formant = formant, Grit = grit, Breath = breath },
                        Metrics         = new MetricsSnapshot
                        {
                            ExtractBeatCount    = extractBeatCount,
                            ExtractVocalsCount  = extractVocalsCount,
                            ApplyMorphCount     = applyMorphCount,
                            ExtractBeatTotalMs  = extractBeatMs,
                            ExtractVocalsTotalMs= extractVocalsMs,
                            ApplyMorphTotalMs   = applyMorphMs,
                            ErrorCount          = errorCount
                        },
                        NativeBridge = new NativeBridgeSnapshot
                        {
                            Enabled            = nativeBridgeEnabled,
                            Available          = nativeBridge.IsAvailable(),
                            AttachedToPlayback = nativeBridgeAttached,
                            FilterName         = nativeBridge.FilterName(),
                            AbiVersion         = abiVersion,
                            ExpectedAbiVersion = NativeBridgeContract.ExpectedAbiVersion,
                            AbiCompatible      = abiCompatible,
                            ProbeMessage       = nativeBridge.LastProbeMessage(),
                            LibraryPath        = nativeBridge.ResolvedLibraryPath()
                        },
                        RecentOperations = operationEvents.ToArray(),
                        RecentErrors     = recentErrors.ToArray()
                    };
                }
                var json        = JsonSerializer.Serialize(snapshot, new JsonSerializerOptions { WriteIndented = true });
                var timestamp   = DateTime.UtcNow.ToString("yyyyMMdd_HHmmss_fff");
                var archivePath = Path.Combine(tempRoot, $"telemetry_{timestamp}.json");
                File.WriteAllText(archivePath, json);
                File.WriteAllText(telemetryLatestPath, json);
            }
            catch (Exception ex) { logger.Error("[VlcMorphPlugin] Failed to export telemetry snapshot.", ex); }
        }

        private static void TrimTail<T>(List<T> entries, int maxCount)
        {
            if (entries.Count > maxCount)
                entries.RemoveRange(0, entries.Count - maxCount);
        }

        private enum StemSplitMode { VocalsHighBand, BeatLowBand }

        // INativeBridgeControl
        public bool   NativeBridgeEnabled     => nativeBridgeEnabled;
        public bool   NativeBridgeAvailable   => nativeBridge.IsAvailable();
        public string NativeBridgeFilterName  => nativeBridge.FilterName();
        public string NativeBridgeProbeStatus => nativeBridge.LastProbeMessage();
        public void SetNativeBridgeEnabled(bool enabled)
        {
            nativeBridgeEnabled = enabled;
            LogInfo($"Native bridge enabled={nativeBridgeEnabled} available={nativeBridge.IsAvailable()} " +
                    $"abi={nativeBridge.AbiVersion()}/{NativeBridgeContract.ExpectedAbiVersion} " +
                    $"compatible={nativeBridge.IsAbiCompatible(NativeBridgeContract.ExpectedAbiVersion)} " +
                    $"filter={nativeBridge.FilterName()} probe='{nativeBridge.LastProbeMessage()}'");
            ExportTelemetrySnapshot();
        }
    }
}
