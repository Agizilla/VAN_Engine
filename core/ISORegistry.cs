using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;

namespace VAN_Engine.Core
{
    /// <summary>
    /// ISO_015: Immutable audit event for every registry query.
    /// </summary>
    public sealed record AuditEntry(
        string Timestamp,
        string QueryType,
        string QueryArg,
        string Result
    );

    /// <summary>
    /// ISO Registry — Single Source of Truth for ISO Rules.
    /// ISO_020: Never report unverified status. Query or clarify.
    /// ISO_015: Every query leaves an immutable audit trail.
    /// </summary>
    public static class ISORegistry
    {
        private static readonly Dictionary<string, Dictionary<string, JsonElement>> _rules = new();
        private static readonly List<AuditEntry> _auditLog = new();
        private static readonly object _lock = new();
        private static bool _loaded = false;

        /// <summary>
        /// Load rules from ISO_Rules.json.
        /// </summary>
        public static int Load(string path = null)
        {
            path ??= Path.Combine(
                AppDomain.CurrentDomain.BaseDirectory,
                "..", "..", "..", "..", "core", "ISO_Rules.json"
            );

            if (!File.Exists(path))
                throw new FileNotFoundException($"ISO_Rules.json not found at {path}");

            var json = File.ReadAllText(path);
            var data = JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(json);

            lock (_lock)
            {
                _rules.Clear();

                if (data.TryGetValue("rules", out var rulesElement))
                {
                    foreach (var rule in rulesElement.EnumerateArray())
                    {
                        var id = rule.GetProperty("id").GetString();
                        var dict = new Dictionary<string, JsonElement>();
                        foreach (var prop in rule.EnumerateObject())
                            dict[prop.Name] = prop.Value;
                        _rules[id] = dict;
                    }
                }

                _loaded = true;
            }

            return _rules.Count;
        }

        private static void Audit(string queryType, string queryArg, string result)
        {
            lock (_lock)
            {
                _auditLog.Add(new AuditEntry(
                    DateTime.UtcNow.ToString("o"),
                    queryType,
                    queryArg,
                    result
                ));
            }
        }

        /// <summary>
        /// Query a single rule's status. Never assumes.
        /// Returns "unknown" status if rule not found.
        /// </summary>
        public static Dictionary<string, string> GetStatus(string isoId)
        {
            if (!_loaded) Load();

            lock (_lock)
            {
                if (_rules.TryGetValue(isoId, out var rule))
                {
                    var result = new Dictionary<string, string>();
                    foreach (var kvp in rule)
                        result[kvp.Key] = kvp.Value.GetRawText().Trim('"');

                    Audit("get_status", isoId, result.GetValueOrDefault("status", "unknown"));
                    return result;
                }

                Audit("get_status", isoId, "unknown");
                return new Dictionary<string, string> { { "status", "unknown" } };
            }
        }

        /// <summary>
        /// Generate status report from actual data, not memory.
        /// </summary>
        public static string ReportAll()
        {
            if (!_loaded) Load();

            var lines = new List<string>();
            lock (_lock)
            {
                foreach (var isoId in _rules.Keys.OrderBy(k => k))
                {
                    var rule = _rules[isoId];
                    var name = rule.GetValueOrDefault("name", "").GetRawText().Trim('"');
                    var status = rule.GetValueOrDefault("status", "").GetRawText().Trim('"');
                    lines.Add($"{isoId} ({name}): {status}");
                }
            }

            var report = string.Join("\n", lines);
            Audit("report_all", "", $"{_rules.Count} rules reported");
            return report;
        }

        /// <summary>
        /// ISO_015: Return immutable audit trail.
        /// </summary>
        public static List<AuditEntry> GetAuditLog()
        {
            lock (_lock)
            {
                return new List<AuditEntry>(_auditLog);
            }
        }

        /// <summary>
        /// Number of loaded rules.
        /// </summary>
        public static int RuleCount()
        {
            if (!_loaded) Load();
            lock (_lock) { return _rules.Count; }
        }

        /// <summary>
        /// ISO_012: Self-validation — each rule checks its own integrity.
        /// </summary>
        public static List<string> ValidateAll()
        {
            if (!_loaded) Load();

            var errors = new List<string>();
            lock (_lock)
            {
                foreach (var (isoId, rule) in _rules)
                {
                    if (!rule.ContainsKey("status"))
                        errors.Add($"{isoId}: missing status");
                    else
                    {
                        var status = rule["status"].GetRawText().Trim('"');
                        if (status != "active" && status != "enforced")
                            errors.Add($"{isoId}: invalid status '{status}'");
                    }

                    if (!rule.ContainsKey("name"))
                        errors.Add($"{isoId}: missing name");
                }
            }

            Audit("validate_all", "", $"{errors.Count} errors");
            return errors;
        }
    }

    internal static class DictionaryExtensions
    {
        public static TValue GetValueOrDefault<TKey, TValue>(
            this Dictionary<TKey, TValue> dict, TKey key, TValue defaultValue)
        {
            return dict.TryGetValue(key, out var value) ? value : defaultValue;
        }
    }
}
