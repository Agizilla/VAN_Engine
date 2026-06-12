using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace GechoShift.Contracts
{
    // ════════════════════════════════════════════════════════════════════
    // IMorphPlugin
    //   Core plugin interface — extract stems, apply morph, set DSP params.
    // ════════════════════════════════════════════════════════════════════
    public interface IMorphPlugin : IDisposable
    {
        void  SetPitch(float value);
        void  SetFormant(float value);
        void  SetGrit(float value);
        void  SetBreath(float value);

        Task<bool> ExtractBeatAsync(CancellationToken ct = default);
        Task<bool> ExtractVocalsAsync(CancellationToken ct = default);
        Task<bool> ApplyMorphAsync(CancellationToken ct = default);
    }

    // ════════════════════════════════════════════════════════════════════
    // INativeBridgeControl
    //   Exposes native filter bridge state to the host UI.
    // ════════════════════════════════════════════════════════════════════
    public interface INativeBridgeControl
    {
        bool   NativeBridgeEnabled     { get; }
        bool   NativeBridgeAvailable   { get; }
        string NativeBridgeFilterName  { get; }
        string NativeBridgeProbeStatus { get; }
        void   SetNativeBridgeEnabled(bool enabled);
    }

    // ════════════════════════════════════════════════════════════════════
    // INativeFilterBridge
    //   Abstraction over the optional native VLC audio-filter module.
    // ════════════════════════════════════════════════════════════════════
    public interface INativeFilterBridge
    {
        bool   IsAvailable();
        bool   IsAbiCompatible(int expectedVersion);
        bool   TryAttachToPlayback();
        string FilterName();
        int    AbiVersion();
        string LastProbeMessage();
        string ResolvedLibraryPath();
    }

    // ════════════════════════════════════════════════════════════════════
    // ITaskLogger
    // ════════════════════════════════════════════════════════════════════
    public interface ITaskLogger
    {
        void Info(string message);
        void Error(string message, Exception? ex = null);
    }

    // ════════════════════════════════════════════════════════════════════
    // NativeBridgeContract
    //   Version constants for ABI compatibility checks.
    // ════════════════════════════════════════════════════════════════════
    public static class NativeBridgeContract
    {
        public const int ExpectedAbiVersion = 1;
    }

    // ════════════════════════════════════════════════════════════════════
    // TelemetryContract
    //   Schema versioning for the telemetry JSON snapshots.
    // ════════════════════════════════════════════════════════════════════
    public static class TelemetryContract
    {
        public const string CurrentSchemaVersion = "1.0";

        public static string SignatureFor(string version) =>
            $"gechoshift-telemetry-{version}";
    }

    // ════════════════════════════════════════════════════════════════════
    // Snapshot record types  (serialised to telemetry_latest.json)
    // ════════════════════════════════════════════════════════════════════
    public sealed class PluginTelemetrySnapshot
    {
        public string              SchemaVersion      { get; set; } = "";
        public string              SchemaSignature    { get; set; } = "";
        public DateTime            GeneratedUtc       { get; set; }
        public string?             TempRoot           { get; set; }
        public string?             LastSourcePath     { get; set; }
        public string?             LastVocalsPath     { get; set; }
        public string?             LastBeatPath       { get; set; }
        public string?             LastMorphedPath    { get; set; }
        public MorphSettingsSnapshot Settings         { get; set; } = new();
        public MetricsSnapshot     Metrics            { get; set; } = new();
        public NativeBridgeSnapshot NativeBridge      { get; set; } = new();
        public PluginOperationEvent[] RecentOperations { get; set; } = Array.Empty<PluginOperationEvent>();
        public PluginErrorEvent[]  RecentErrors       { get; set; } = Array.Empty<PluginErrorEvent>();
    }

    public sealed class MorphSettingsSnapshot
    {
        public float Pitch   { get; set; }
        public float Formant { get; set; }
        public float Grit    { get; set; }
        public float Breath  { get; set; }
    }

    public sealed class MetricsSnapshot
    {
        public int  ExtractBeatCount      { get; set; }
        public int  ExtractVocalsCount    { get; set; }
        public int  ApplyMorphCount       { get; set; }
        public long ExtractBeatTotalMs    { get; set; }
        public long ExtractVocalsTotalMs  { get; set; }
        public long ApplyMorphTotalMs     { get; set; }
        public int  ErrorCount            { get; set; }
    }

    public sealed class NativeBridgeSnapshot
    {
        public bool   Enabled             { get; set; }
        public bool   Available           { get; set; }
        public bool   AttachedToPlayback  { get; set; }
        public string FilterName         { get; set; } = "";
        public int    AbiVersion          { get; set; }
        public int    ExpectedAbiVersion  { get; set; }
        public bool   AbiCompatible       { get; set; }
        public string ProbeMessage        { get; set; } = "";
        public string LibraryPath         { get; set; } = "";
    }

    public sealed class PluginOperationEvent
    {
        public DateTime Utc         { get; set; }
        public string   Operation   { get; set; } = "";
        public bool     Success     { get; set; }
        public string   Completion  { get; set; } = "";
        public long     DurationMs  { get; set; }
    }

    public sealed class PluginErrorEvent
    {
        public DateTime Utc       { get; set; }
        public string   Message   { get; set; } = "";
        public string   Exception { get; set; } = "";
        public string   Detail    { get; set; } = "";
    }
}
