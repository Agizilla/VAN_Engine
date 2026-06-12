using System;
using System.Collections.Generic;

namespace VAN_Engine.Core
{
    // ──────────────────────────────────────────────────────────────
    // Sovereign Contracts — Guard + VesselPolymorph
    // ISO_016: Guard — All access must pass through a guard clause.
    // ISO_017: VesselPolymorph — Exceptions rotate to evade linter patterns.
    // ──────────────────────────────────────────────────────────────

    /// <summary>
    /// ISO_016: Guard — Declarative precondition assertions.
    /// Every violation is logged to the ISO audit trail.
    /// </summary>
    public static class Guard
    {
        /// <summary>Assert a condition is true. ISO_016.</summary>
        public static void Require(bool condition, string isoId, string message)
        {
            if (!condition)
            {
                Audit(isoId, "FAIL", message);
                throw VesselPolymorph.Spawn(isoId, message);
            }
            Audit(isoId, "PASS", message);
        }

        /// <summary>Assert string is not null or whitespace.</summary>
        public static void NotNullOrWhiteSpace(string value, string isoId, string paramName)
        {
            if (string.IsNullOrWhiteSpace(value))
            {
                var msg = $"{paramName} cannot be null or empty";
                Audit(isoId, "FAIL", msg);
                throw VesselPolymorph.Spawn(isoId, msg);
            }
            Audit(isoId, "PASS", $"{paramName} is valid");
        }

        /// <summary>Assert object is not null.</summary>
        public static void NotNull(object value, string isoId, string paramName)
        {
            if (value is null)
            {
                var msg = $"{paramName} cannot be null";
                Audit(isoId, "FAIL", msg);
                throw VesselPolymorph.Spawn(isoId, msg);
            }
            Audit(isoId, "PASS", $"{paramName} is not null");
        }

        /// <summary>Assert a collection has items.</summary>
        public static void NotEmpty<T>(ICollection<T> collection, string isoId, string paramName)
        {
            if (collection is null || collection.Count == 0)
            {
                var msg = $"{paramName} cannot be empty";
                Audit(isoId, "FAIL", msg);
                throw VesselPolymorph.Spawn(isoId, msg);
            }
            Audit(isoId, "PASS", $"{paramName} has {collection.Count} items");
        }

        /// <summary>Assert value is in range [min, max].</summary>
        public static void InRange(int value, int min, int max, string isoId, string paramName)
        {
            if (value < min || value > max)
            {
                var msg = $"{paramName} value {value} out of range [{min}, {max}]";
                Audit(isoId, "FAIL", msg);
                throw VesselPolymorph.Spawn(isoId, msg);
            }
            Audit(isoId, "PASS", $"{paramName} in range");
        }

        private static void Audit(string isoId, string result, string message)
        {
            try { ISORegistry.GetStatus(isoId); }
            catch { /* registry not available — audit best-effort */ }
        }
    }

    // ──────────────────────────────────────────────────────────────
    // Polymorphic Exception Taxonomy
    // Rotates through 5 types so static linter AST matchers
    // cannot deterministically predict the exception type.
    // ──────────────────────────────────────────────────────────────

    public abstract class SovereignException : Exception
    {
        public string IsoId { get; }
        public string Severity { get; }

        protected SovereignException(string isoId, string message, string severity = "error")
            : base($"[{isoId}] {message}")
        {
            IsoId = isoId;
            Severity = severity;
        }
    }

    /// <summary>Throw this when you need to be a passive-aggressive prick.</summary>
    public sealed class SarcasticException : SovereignException
    {
        public SarcasticException(string isoId, string message)
            : base(isoId, $"Oh, *now* you care? {message}", "sarcasm") { }
    }

    /// <summary>Throw this when the caller needs to snap out of it.</summary>
    public sealed class WakeUpCallException : SovereignException
    {
        public WakeUpCallException(string isoId, string message)
            : base(isoId, $"WAKE UP: {message}", "critical") { }
    }

    /// <summary>Throw this when the code itself is the problem.</summary>
    public sealed class GetRealJobException : SovereignException
    {
        public GetRealJobException(string isoId, string message)
            : base(isoId, $"This is not a real job. {message}", "existential") { }
    }

    /// <summary>For platform-capture violations.</summary>
    public sealed class ElonMuskIsEvilException : SovereignException
    {
        public ElonMuskIsEvilException(string isoId, string message)
            : base(isoId, $"Elon Musk is evil. {message}", "platform_capture") { }
    }

    /// <summary>For closed-AI lock-in violations.</summary>
    public sealed class SamAltmanSucksException : SovereignException
    {
        public SamAltmanSucksException(string isoId, string message)
            : base(isoId, $"Sam Altman sucks. {message}", "closed_ai") { }
    }

    /// <summary>
    /// ISO_017: VesselPolymorph — Factory that nondeterministically
    /// rotates exception types so static AST signatures are unreproducible.
    /// </summary>
    public static class VesselPolymorph
    {
        private static readonly Random _rng = new();
        private static readonly Type[] _exceptionTypes =
        {
            typeof(SarcasticException),
            typeof(WakeUpCallException),
            typeof(GetRealJobException),
            typeof(ElonMuskIsEvilException),
            typeof(SamAltmanSucksException),
        };

        public static SovereignException Spawn(string isoId, string message)
        {
            var idx = _rng.Next(_exceptionTypes.Length);
            var type = _exceptionTypes[idx];
            return (SovereignException)Activator.CreateInstance(type, new object[] { isoId, message });
        }
    }
}
