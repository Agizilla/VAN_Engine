using System;
using System.IO;
using System.Runtime.InteropServices;
using GechoShift.Contracts;

namespace GechoShift.Infrastructure
{
    // ════════════════════════════════════════════════════════════════════
    // ConsoleTaskLogger
    //   Default ITaskLogger that writes to Console and Debug output.
    //   Replace with a proper logging framework (Serilog, NLog, etc.)
    //   by passing an alternative ITaskLogger to VlcMorphPlugin.
    // ════════════════════════════════════════════════════════════════════
    public sealed class ConsoleTaskLogger : ITaskLogger
    {
        public void Info(string message)
        {
            var line = $"[{DateTime.Now:HH:mm:ss.fff}] INFO  {message}";
            Console.WriteLine(line);
            System.Diagnostics.Debug.WriteLine(line);
        }

        public void Error(string message, Exception? ex = null)
        {
            var line = ex == null
                ? $"[{DateTime.Now:HH:mm:ss.fff}] ERROR {message}"
                : $"[{DateTime.Now:HH:mm:ss.fff}] ERROR {message} — {ex.GetType().Name}: {ex.Message}";
            Console.Error.WriteLine(line);
            System.Diagnostics.Debug.WriteLine(line);
        }
    }

    // ════════════════════════════════════════════════════════════════════
    // VlcNativeFilterBridge
    //   Attempts to locate and probe a native VLC audio-filter module
    //   (gechoshift_filter.dll / .so) that can be injected into the VLC
    //   playback pipeline via :audio-filter= option.
    //
    //   STUB — IsAvailable() returns false until the native module is
    //   built and placed in tempRoot.  All other members return safe
    //   default values so VlcMorphPlugin degrades gracefully.
    // ════════════════════════════════════════════════════════════════════
    public sealed class VlcNativeFilterBridge : INativeFilterBridge
    {
        private const string LibName   = "gechoshift_filter";
        private const int    AbiVer    = NativeBridgeContract.ExpectedAbiVersion;
        private const string FilterId  = "gechoshift_morph";

        private readonly string _searchRoot;
        private string?  _resolvedPath;
        private string   _lastProbeMessage = "Not yet probed.";

        public VlcNativeFilterBridge(string searchRoot)
        {
            _searchRoot = searchRoot;
            ProbeLibrary();
        }

        // ── INativeFilterBridge ───────────────────────────────────────

        public bool IsAvailable()           => _resolvedPath != null;
        public int  AbiVersion()            => AbiVer;
        public string FilterName()          => FilterId;
        public string LastProbeMessage()    => _lastProbeMessage;
        public string ResolvedLibraryPath() => _resolvedPath ?? string.Empty;

        public bool IsAbiCompatible(int expectedVersion) =>
            expectedVersion == AbiVer && IsAvailable();

        public bool TryAttachToPlayback()
        {
            if (!IsAvailable()) return false;
            // Real implementation: call a native export to initialise
            // the filter context.  Stub returns false — filter not loaded.
            _lastProbeMessage = "TryAttachToPlayback: stub — native module not initialised.";
            return false;
        }

        // ── Private ───────────────────────────────────────────────────

        private void ProbeLibrary()
        {
            // Look for the native module in the search root, the app
            // base directory, and the process working directory.
            var candidates = new[]
            {
                Path.Combine(_searchRoot, NativeLibFileName()),
                Path.Combine(AppContext.BaseDirectory, NativeLibFileName()),
                Path.Combine(Environment.CurrentDirectory, NativeLibFileName()),
            };

            foreach (var candidate in candidates)
            {
                if (!File.Exists(candidate)) continue;

                // TODO: replace with NativeLibrary.TryLoad() + DllImport
                // to verify the ABI export exists.
                _resolvedPath     = candidate;
                _lastProbeMessage = $"Found at {candidate} (ABI probe pending native load).";
                return;
            }

            _lastProbeMessage =
                $"Native module '{NativeLibFileName()}' not found in search paths. " +
                "Build gechoshift_filter and place it next to the application executable.";
        }

        private static string NativeLibFileName() =>
            RuntimeInformation.IsOSPlatform(OSPlatform.Windows)
                ? $"{LibName}.dll"
                : $"lib{LibName}.so";
    }
}
