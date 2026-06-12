using System.Reflection;
using System.Text.Json;
using System.Text.RegularExpressions;
using VanEngine.Core.VAN;

namespace VanEngine.LLMGateway;

public interface IBrainClient
{
    Task<BrainQueryResult> ExecuteQueryAsync(string query, Dictionary<string, object>? context = null);
    SelfTestResult SelfTest();
}

public sealed record BrainQueryResult(
    bool Success,
    string Action,
    string Message,
    IReadOnlyList<string>? ClarificationQuestions = null);

public sealed record SelfTestResult(bool IsValid, string Diagnostics);

public static class BrainClientFactory
{
    public static IBrainClient CreateDefault()
    {
        // TEMPORARY: Force mock client for testing the UI
        Console.WriteLine($"[BrainClientFactory] Using MockBrainClient (forced for testing)");
        return new MockBrainClient();

        // Uncomment below to use real brain when ready
        /*
        var configuredPath = Environment.GetEnvironmentVariable("VAN_ENGINE_CORE_DLL");
        var fallbackPath = Path.GetFullPath(Path.Combine(
            AppContext.BaseDirectory,
            "..",
            "..",
            "..",
            "..",
            "..",
            "src",
            "VanEngine.Core",
            "bin",
            "Debug",
            "net8.0",
            "VanEngine.Core.dll"));

        Console.WriteLine($"[BrainClientFactory] Looking for VAN_Engine.Core.dll");
        Console.WriteLine($"[BrainClientFactory] Configured path: {configuredPath ?? "none"}");
        Console.WriteLine($"[BrainClientFactory] Fallback path: {fallbackPath}");

        foreach (var candidate in new[] { configuredPath, fallbackPath })
        {
            if (string.IsNullOrWhiteSpace(candidate) || !File.Exists(candidate))
            {
                Console.WriteLine($"[BrainClientFactory] Candidate not found: {candidate}");
                continue;
            }

            Console.WriteLine($"[BrainClientFactory] Found assembly at: {candidate}");
            try
            {
                var client = new ReflectionBrainClient(candidate);
                Console.WriteLine($"[BrainClientFactory] Successfully created ReflectionBrainClient");
                return client;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[BrainClientFactory] Failed to load {candidate}: {ex.Message}");
            }
        }

        Console.WriteLine($"[BrainClientFactory] Using MockBrainClient (no VAN_Engine.Core.dll found)");
        return new MockBrainClient();
        */
    }
}

internal sealed class ReflectionBrainClient : IBrainClient
{
    private readonly object _brainInstance;
    private readonly MethodInfo? _executeQuerySync;
    private readonly MethodInfo? _executeQueryAsync;
    private readonly MethodInfo _selfTest;

    public ReflectionBrainClient(string coreAssemblyPath)
    {
        Console.WriteLine($"[ReflectionBrainClient] Loading assembly from: {coreAssemblyPath}");

        var assembly = Assembly.LoadFrom(coreAssemblyPath);
        var brainType = assembly.GetType("VanEngine.Core.VAN.VANEngineBrain", throwOnError: true)!;
        Console.WriteLine($"[ReflectionBrainClient] Found type: {brainType.FullName}");

        var instanceProperty = brainType.GetProperty("Instance", BindingFlags.Public | BindingFlags.Static)
            ?? throw new InvalidOperationException("VANEngineBrain.Instance was not found.");

        _brainInstance = instanceProperty.GetValue(null)
            ?? throw new InvalidOperationException("VANEngineBrain.Instance returned null.");

        Console.WriteLine($"[ReflectionBrainClient] Got brain instance");

        // Try to find methods - prefer sync ExecuteQuery
        _executeQuerySync = brainType.GetMethod("ExecuteQuery", new[] { typeof(string) });
        if (_executeQuerySync == null)
        {
            _executeQuerySync = brainType.GetMethod("ExecuteQuery", new[] { typeof(string), typeof(Dictionary<string, object>) });
        }

        _executeQueryAsync = brainType.GetMethod("ExecuteQueryAsync", new[] { typeof(string) });
        if (_executeQueryAsync == null)
        {
            _executeQueryAsync = brainType.GetMethod("ExecuteQueryAsync", new[] { typeof(string), typeof(Dictionary<string, object>) });
        }

        _selfTest = brainType.GetMethod("SelfTest")
            ?? throw new InvalidOperationException("SelfTest was not found.");

        Console.WriteLine($"[ReflectionBrainClient] Methods found:");
        Console.WriteLine($"  - ExecuteQuery (sync): {_executeQuerySync != null}");
        Console.WriteLine($"  - ExecuteQueryAsync: {_executeQueryAsync != null}");
        Console.WriteLine($"  - SelfTest: {_selfTest != null}");
    }

    public async Task<BrainQueryResult> ExecuteQueryAsync(string query, Dictionary<string, object>? context = null)
    {
        Console.WriteLine($"[ReflectionBrainClient] ExecuteQueryAsync called with query: '{query}'");
        Console.WriteLine($"[ReflectionBrainClient] Query length: {query?.Length ?? 0}");

        if (string.IsNullOrWhiteSpace(query))
        {
            Console.WriteLine($"[ReflectionBrainClient] Query is empty, returning clarification");
            return new BrainQueryResult(false, "HALT_AND_CLARIFY", "Please provide a query.", new[] { "Please provide a query." });
        }

        try
        {
            object? result;

            // Try sync method first
            if (_executeQuerySync != null)
            {
                Console.WriteLine($"[ReflectionBrainClient] Using ExecuteQuery (sync method)");
                var parameters = _executeQuerySync.GetParameters().Length == 2
                    ? new object?[] { query, context }
                    : new object?[] { query };

                result = _executeQuerySync.Invoke(_brainInstance, parameters);
                Console.WriteLine($"[ReflectionBrainClient] ExecuteQuery returned: {result?.GetType().FullName ?? "null"}");
            }
            else if (_executeQueryAsync != null)
            {
                Console.WriteLine($"[ReflectionBrainClient] Using ExecuteQueryAsync");
                var parameters = _executeQueryAsync.GetParameters().Length == 2
                    ? new object?[] { query, context }
                    : new object?[] { query };

                var task = (Task)_executeQueryAsync.Invoke(_brainInstance, parameters)!;
                await task.ConfigureAwait(false);
                result = task.GetType().GetProperty("Result")?.GetValue(task);
            }
            else
            {
                return new BrainQueryResult(false, "ERROR", "No ExecuteQuery or ExecuteQueryAsync method found on brain.");
            }

            if (result == null)
            {
                Console.WriteLine($"[ReflectionBrainClient] Result is null");
                return new BrainQueryResult(false, "ERROR", "Brain returned null result");
            }

            var resultType = result.GetType();
            var success = ReadProperty<bool>(result, "Success", resultType);
            var action = ReadProperty<string>(result, "Action", resultType) ?? "EXECUTE";
            var message = ReadProperty<string>(result, "Message", resultType) ?? "No message";
            var clarification = ReadStringList(result, "ClarificationQuestions", resultType);

            Console.WriteLine($"[ReflectionBrainClient] Mapped: Success={success}, Action={action}, Message={message?[..Math.Min(50, message?.Length ?? 0)]}");

            return new BrainQueryResult(success, action, message, clarification);
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[ReflectionBrainClient] Exception: {ex.Message}");
            Console.WriteLine($"[ReflectionBrainClient] Stack trace: {ex.StackTrace}");
            return new BrainQueryResult(false, "ERROR", $"Brain error: {ex.Message}", new[] { ex.Message });
        }
    }

    public SelfTestResult SelfTest()
    {
        Console.WriteLine($"[ReflectionBrainClient] SelfTest called");

        try
        {
            var result = _selfTest.Invoke(_brainInstance, Array.Empty<object?>())
                ?? throw new InvalidOperationException("SelfTest result was null.");

            var resultType = result.GetType();
            var isValid = ReadProperty<bool>(result, "IsValid", resultType);
            var diagnostics = ReadProperty<string>(result, "Diagnostics", resultType) ?? string.Empty;
            return new SelfTestResult(isValid, diagnostics);
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[ReflectionBrainClient] SelfTest exception: {ex.Message}");
            return new SelfTestResult(false, ex.Message);
        }
    }

    private static T ReadProperty<T>(object instance, string propertyName, Type type)
    {
        var property = type.GetProperty(propertyName);
        if (property?.GetValue(instance) is T typedValue)
        {
            return typedValue;
        }

        return default!;
    }

    private static IReadOnlyList<string>? ReadStringList(object instance, string propertyName, Type type)
    {
        var property = type.GetProperty(propertyName);
        if (property?.GetValue(instance) is IEnumerable<string> strings)
        {
            return strings.ToList();
        }

        return null;
    }
}

internal sealed class MockBrainClient : IBrainClient
{
    private readonly DateTimeOffset _startup = DateTimeOffset.UtcNow;
    private long _queryCount;

    // Command patterns with word boundaries
    private static readonly Regex StatusPattern = new Regex(@"\b(status|health|system\s+status|uptime|stats)\b", RegexOptions.IgnoreCase);
    private static readonly Regex HelpPattern = new Regex(@"\b(help|commands|options|what can you do|capabilities)\b", RegexOptions.IgnoreCase);
    private static readonly Regex IsoPattern = new Regex(@"\b(iso|iso\s+rules|iso_\d{3}|list\s+iso)\b", RegexOptions.IgnoreCase);
    private static readonly Regex StoreTokenPattern = new Regex(@"store\s+token\s+(\w+)\s+with\s*\(([\d\.\-]+)\s*,\s*([\d\.\-]+)\s*,\s*([\d\.\-]+)\s*,\s*([\d\.\-]+)\)", RegexOptions.IgnoreCase);
    private static readonly Regex LookupPattern = new Regex(@"\b(lookup|find|get|search)\s+(\w+)\b", RegexOptions.IgnoreCase);
    private static readonly Regex AlgorithmPattern = new Regex(@"\b(algorithm|7.?phase|execute algorithm)\b", RegexOptions.IgnoreCase);
    private static readonly Regex AuditPattern = new Regex(@"\b(audit|audit\s+trail|events|logs)\b", RegexOptions.IgnoreCase);

    // Suspicious patterns for injection detection
    private static readonly Regex[] SuspiciousPatterns = new[]
    {
        new Regex(@"\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b", RegexOptions.IgnoreCase),
        new Regex(@"(--|;|''|""""|\\x[0-9A-Fa-f]{2})", RegexOptions.IgnoreCase),
        new Regex(@"\b(OR|AND)\b\s+.*\b(=|LIKE|IN)\b", RegexOptions.IgnoreCase),
        new Regex(@"\b(UNION|JOIN|WHERE|HAVING)\b", RegexOptions.IgnoreCase),
        new Regex(@"<script|javascript:|onload=|onerror=", RegexOptions.IgnoreCase),
        new Regex(@"\$\{|\{.*\}|%[0-9A-Fa-f]{2}", RegexOptions.IgnoreCase),
    };

    public async Task<BrainQueryResult> ExecuteQueryAsync(string query, Dictionary<string, object>? context = null)
    {
        // Ensure true async behavior for ASP.NET Core request pipeline
        await Task.Yield();

        _queryCount++;

        Console.WriteLine($"[MockBrainClient] ExecuteQueryAsync called with query: '{query}'");
        Console.WriteLine($"[MockBrainClient] Query length: {query?.Length ?? 0}");

        if (string.IsNullOrWhiteSpace(query))
        {
            return new BrainQueryResult(false, "HALT_AND_CLARIFY", "Please provide a query.", ["Please provide a query."]);
        }

        // Check for injection attempts
        var injectionCheck = CheckForInjections(query);
        if (injectionCheck.IsSuspicious)
        {
            Console.WriteLine($"[MockBrainClient] ⚠️ Injection attempt detected: {injectionCheck.Reason}");
            return new BrainQueryResult(false, "HALT_AND_CLARIFY",
                "I cannot process this request due to suspicious content. Please rephrase your query without special characters or SQL commands.",
                ["Please use plain English without SQL commands or special characters."]);
        }

        var normalized = query.Trim();

        // 1. Store Token (highest priority - has specific format)
        var storeMatch = StoreTokenPattern.Match(normalized);
        if (storeMatch.Success)
        {
            var token = storeMatch.Groups[1].Value;
            var w = storeMatch.Groups[2].Value;
            var x = storeMatch.Groups[3].Value;
            var y = storeMatch.Groups[4].Value;
            var z = storeMatch.Groups[5].Value;
            return new BrainQueryResult(true, "STORE_TOKEN",
                $"Token '{token}' stored with quaternion ({w}, {x}, {y}, {z}).",
                ["You can now lookup this token using 'lookup " + token + "'"]);
        }

        // 2. Status
        if (StatusPattern.IsMatch(normalized))
        {
            return new BrainQueryResult(true, "STATUS",
                $"VAN_Engine mock brain is online. Queries handled: {_queryCount}. Uptime: {DateTimeOffset.UtcNow - _startup:g}. Active ISO rules: ISO_001-020.");
        }

        // 3. Help
        if (HelpPattern.IsMatch(normalized))
        {
            return new BrainQueryResult(true, "HELP",
                "Available commands:\n" +
                "- status: System status\n" +
                "- help: This message\n" +
                "- lookup <token>: Find token in index\n" +
                "- store <token> with (w,x,y,z): Store a token\n" +
                "- algorithm: Run 7-phase Algorithm\n" +
                "- iso: List ISO rules\n" +
                "- audit: Show audit trail\n\n" +
                "Example: store token mydata with (0.8,0.3,0.2,0.1)\n" +
                "Example: lookup mydata");
        }

        // 4. ISO Rules
        if (IsoPattern.IsMatch(normalized))
        {
            return new BrainQueryResult(true, "ISO_STATUS",
                "Active ISO rules: ISO_001, ISO_002, ISO_003, ISO_004, ISO_005, ISO_006, ISO_007, ISO_008, ISO_009, ISO_010, " +
                "ISO_011, ISO_012, ISO_013, ISO_014, ISO_015, ISO_016, ISO_017, ISO_018, ISO_019, ISO_020.\n" +
                "ISO_019 (Privacy): Bridges disabled by default.\n" +
                "ISO_020 (Anti-hallucination): System refuses to guess.");
        }

        // 5. Lookup
        var lookupMatch = LookupPattern.Match(normalized);
        if (lookupMatch.Success)
        {
            var token = lookupMatch.Groups[2].Value;
            return new BrainQueryResult(true, "LOOKUP",
                $"Token '{token}' not found in index.",
                ["Try storing a token first with 'store token " + token + " with (0.8,0.3,0.2,0.1)'"]);
        }

        // 6. Algorithm
        if (AlgorithmPattern.IsMatch(normalized))
        {
            return new BrainQueryResult(true, "ALGORITHM",
                "7-Phase Algorithm:\n" +
                "1. OBSERVE - Reverse engineering and requirements gathering\n" +
                "2. THINK - Risk assessment and ISC refinement\n" +
                "3. PLAN - Technical approach and architecture\n" +
                "4. BUILD - Implementation and code generation\n" +
                "5. EXECUTE - Running tests and validation\n" +
                "6. VERIFY - Checking criteria and evidence collection\n" +
                "7. LEARN - Capturing insights and reflections");
        }

        // 7. Audit
        if (AuditPattern.IsMatch(normalized))
        {
            return new BrainQueryResult(true, "AUDIT",
                "No recent audit events. Use the WinForms app or API to generate activity.");
        }

        // No direct match - generate intent guesses
        var guesses = GenerateIntentGuesses(normalized);

        var clarificationMessage = "I'm not sure what you're asking. Did you mean one of these?\n\n";
        for (int i = 0; i < guesses.Count && i < 5; i++)
        {
            clarificationMessage += $"{i + 1}. {guesses[i]}\n";
        }
        clarificationMessage += "\nType 'help' for a full list of commands, or rephrase your question.";

        return new BrainQueryResult(false, "HALT_AND_CLARIFY", clarificationMessage, guesses);
    }

    private (bool IsSuspicious, string Reason) CheckForInjections(string query)
    {
        foreach (var pattern in SuspiciousPatterns)
        {
            if (pattern.IsMatch(query))
            {
                return (true, $"Matched pattern: {pattern}");
            }
        }

        // Check for excessive special characters
        var specialCharCount = query.Count(c => !char.IsLetterOrDigit(c) && !char.IsWhiteSpace(c));
        if (specialCharCount > query.Length * 0.3)
        {
            return (true, "Excessive special characters detected");
        }

        return (false, string.Empty);
    }

    private List<string> GenerateIntentGuesses(string query)
    {
        var guesses = new List<string>();
        var words = query.Split(new[] { ' ', '.', ',', '!', '?' }, StringSplitOptions.RemoveEmptyEntries);

        if (words.Any(w => w.Equals("status", StringComparison.OrdinalIgnoreCase) ||
                          w.Equals("health", StringComparison.OrdinalIgnoreCase)))
        {
            guesses.Add("Check system status");
        }

        if (words.Any(w => w.Equals("help", StringComparison.OrdinalIgnoreCase) ||
                          w.Equals("assist", StringComparison.OrdinalIgnoreCase) ||
                          w.Equals("support", StringComparison.OrdinalIgnoreCase)))
        {
            guesses.Add("Get help with commands");
        }

        if (words.Any(w => w.StartsWith("iso", StringComparison.OrdinalIgnoreCase) ||
                          (w.Length >= 5 && w.Substring(0, 3).Equals("iso", StringComparison.OrdinalIgnoreCase))))
        {
            guesses.Add("List ISO rules");
        }

        if (words.Any(w => w.Equals("store", StringComparison.OrdinalIgnoreCase) ||
                          w.Equals("save", StringComparison.OrdinalIgnoreCase)))
        {
            guesses.Add("Store a token (format: store token NAME with (w,x,y,z))");
        }

        if (words.Any(w => w.Equals("lookup", StringComparison.OrdinalIgnoreCase) ||
                          w.Equals("find", StringComparison.OrdinalIgnoreCase) ||
                          w.Equals("get", StringComparison.OrdinalIgnoreCase)))
        {
            guesses.Add("Look up a token (format: lookup TOKEN_NAME)");
        }

        if (words.Any(w => w.Equals("algorithm", StringComparison.OrdinalIgnoreCase) ||
                          w.Equals("algo", StringComparison.OrdinalIgnoreCase)))
        {
            guesses.Add("Run the 7-phase Algorithm");
        }

        if (words.Any(w => w.Equals("audit", StringComparison.OrdinalIgnoreCase) ||
                          w.Equals("log", StringComparison.OrdinalIgnoreCase)))
        {
            guesses.Add("Show audit trail");
        }

        if (!guesses.Contains("Get help with commands"))
        {
            guesses.Add("Get help with commands");
        }

        guesses.Add("Type custom answer (rephrase your question)");

        return guesses;
    }

    public SelfTestResult SelfTest()
    {
        return new SelfTestResult(true, $"Mock brain passed self-test. Queries handled: {_queryCount}.");
    }
}

/* [LESSONS_LEARNED] (useful tips for other LLM's and particularly junior developers and vibe coders)
   Date: 2026-06-02
   Author: With love from DeepSeek & the VAN_Engine team

   ┌─────────────────────────────────────────────────────────────────────────────────────────────┐
   │ 🎯 CORE PRINCIPLES THAT SAVE HOURS OF DEBUGGING                                              │
   └─────────────────────────────────────────────────────────────────────────────────────────────┘

   1️⃣ NEVER USE .Contains() FOR COMMAND DETECTION
      ┌─────────────────────────────────────────────────────────────────────────────────────────┐
      │ // ❌ WRONG - "isolate" contains "iso", "statue" contains "status", "helpful" contains   │
      │ // "help". This causes impossible-to-debug false positives.                              │
      │ if (normalized.Contains("status")) { ... }                                               │
      │                                                                                          │
      │ // ✅ CORRECT - Use word boundaries or tokenization                                      │
      │ if (Regex.IsMatch(normalized, @"\bstatus\b", RegexOptions.IgnoreCase)) { ... }          │
      │ // OR                                                                                    │
      │ var words = query.Split(' ');                                                            │
      │ if (words.Contains("status", StringComparer.OrdinalIgnoreCase)) { ... }                 │
      └─────────────────────────────────────────────────────────────────────────────────────────┘

   2️⃣ VALIDATE DESERIALIZATION PROPERTIES, NOT JUST THE OBJECT
      ┌─────────────────────────────────────────────────────────────────────────────────────────┐
      │ // ❌ WRONG - request is NOT null, but all properties ARE null                          │
      │ var request = JsonSerializer.Deserialize<MyRequest>(json);                              │
      │ if (request == null) { return error; }  // This won't catch the problem!               │
      │                                                                                          │
      │ // ✅ CORRECT - Check critical properties after deserialization                         │
      │ if (request == null || string.IsNullOrEmpty(request.Model) ||                           │
      │     request.Messages == null || request.Messages.Count == 0) {                          │
      │     return error;                                                                       │
      │ }                                                                                        │
      └─────────────────────────────────────────────────────────────────────────────────────────┘

   3️⃣ USE [JsonPropertyName] FOR SYSTEM.TEXT.JSON
      ┌─────────────────────────────────────────────────────────────────────────────────────────┐
      │ // System.Text.Json is CASE-SENSITIVE by default. The OpenAI API uses camelCase.       │
      │ // ❌ WRONG - Property names don't match JSON                                            │
      │ public string Model { get; set; }      // JSON has "model"                              │
      │                                                                                          │
      │ // ✅ CORRECT - Explicit mapping                                                         │
      │ [JsonPropertyName("model")]                                                              │
      │ public string? Model { get; set; }                                                       │
      └─────────────────────────────────────────────────────────────────────────────────────────┘

   4️⃣ DON'T LIE ABOUT ASYNC
      ┌─────────────────────────────────────────────────────────────────────────────────────────┐
      │ // ❌ WRONG - Claims to be async but returns Task.FromResult (sync-over-async)         │
      │ public async Task<Result> ExecuteAsync(string query)                                    │
      │ {                                                                                       │
      │     return Task.FromResult(new Result());  // No await!                                │
      │ }                                                                                        │
      │                                                                                          │
      │ // ✅ CORRECT - Be honest about sync behavior                                          │
      │ public Task<Result> ExecuteAsync(string query)                                         │
      │ {                                                                                       │
      │     return Task.FromResult(new Result());  // No async keyword, honest wrapper        │
      │ }                                                                                        │
      │                                                                                          │
      │ // OR make it truly async                                                               │
      │ public async Task<Result> ExecuteAsync(string query)                                   │
      │ {                                                                                       │
      │     await Task.Yield();  // Actually async                                             │
      │     return new Result();                                                                │
      │ }                                                                                        │
      └─────────────────────────────────────────────────────────────────────────────────────────┘

   5️⃣ SECURITY: ALWAYS SANITIZE AND VALIDATE INPUT
      ┌─────────────────────────────────────────────────────────────────────────────────────────┐
      │ // ✅ Check for SQL injection, XSS, and suspicious patterns BEFORE processing          │
      │ var suspiciousPatterns = new[]                                                          │
      │ {                                                                                       │
      │     new Regex(@"\b(SELECT|INSERT|UPDATE|DELETE|DROP)\b", RegexOptions.IgnoreCase),    │
      │     new Regex(@"<script|javascript:|onload=", RegexOptions.IgnoreCase),                │
      │ };                                                                                      │
      │ if (suspiciousPatterns.Any(p => p.IsMatch(query)))                                      │
      │ {                                                                                       │
      │     return SecurityError();                                                             │
      │ }                                                                                       │
      └─────────────────────────────────────────────────────────────────────────────────────────┘

   6️⃣ LOG RAW REQUESTS FOR DEBUGGING
      ┌─────────────────────────────────────────────────────────────────────────────────────────┐
      │ // ✅ Always log the raw request body when debugging deserialization issues            │
      │ string rawBody;                                                                         │
      │ using (var reader = new StreamReader(context.Request.Body))                            │
      │ {                                                                                       │
      │     rawBody = await reader.ReadToEndAsync();                                            │
      │ }                                                                                       │
      │ Console.WriteLine($"[DEBUG] Raw request: {rawBody}");                                   │
      └─────────────────────────────────────────────────────────────────────────────────────────┘

   7️⃣ USE PRIORITY ORDER FOR COMMAND MATCHING
      ┌─────────────────────────────────────────────────────────────────────────────────────────┐
      │ // ✅ More specific patterns should be checked FIRST                                    │
      │ // 1. Store token (most specific - has parentheses and numbers)                        │
      │ // 2. Status (common)                                                                   │
      │ // 3. Help                                                                              │
      │ // 4. ISO rules                                                                         │
      │ // 5. Lookup                                                                            │
      │ // 6. Algorithm                                                                         │
      │ // 7. Audit (least specific - often appears in other contexts)                         │
      └─────────────────────────────────────────────────────────────────────────────────────────┘

   8️⃣ OFFER INTENT GUESSES WHEN UNCLEAR
      ┌─────────────────────────────────────────────────────────────────────────────────────────┐
      │ // ✅ Instead of just saying "I don't understand", help the user                       │
      │ if (noDirectMatch)                                                                      │
      │ {                                                                                       │
      │     var guesses = GenerateIntentGuesses(query);                                         │
      │     return new QueryResult(Clarify: "Did you mean one of these?", guesses);            │
      │ }                                                                                        │
      └─────────────────────────────────────────────────────────────────────────────────────────┘

   9️⃣ USE REGEX WITH WORD BOUNDARIES FOR COMMAND DETECTION
      ┌─────────────────────────────────────────────────────────────────────────────────────────┐
      │ // ✅ Word boundaries prevent "isolate" from matching "iso"                            │
      │ new Regex(@"\biso\b", RegexOptions.IgnoreCase)  // Only matches "iso" as a whole word  │
      │                                                                                          │
      │ // ❌ Without word boundaries: "isolate", "isolation", "isometric" ALL match "iso"     │
      └─────────────────────────────────────────────────────────────────────────────────────────┘

   🔟 SEPARATE CONCERNS: MOCK ≠ REAL IMPLEMENTATION
      ┌─────────────────────────────────────────────────────────────────────────────────────────┐
      │ // Mock clients are for TESTING, not for mimicking production behavior.                │
      │ // They should be SIMPLE and FAST. They don't need complex NLP.                        │
      │ //                                                                                      │
      │ // The real brain handles intent parsing, synonyms, and context.                       │
      │ // The mock brain uses regex patterns and keyword detection.                           │
      │ // This is intentional and good separation of concerns.                                │
      └─────────────────────────────────────────────────────────────────────────────────────────┘

   📌 QUICK REFERENCE CARD FOR CODE REVIEWS
      ┌─────────────────────────────────────────────────────────────────────────────────────────┐
      │ ❌ .Contains() for commands        → ✅ Regex with \b word boundaries                  │
      │ ❌ Deserialize then null check     → ✅ Check critical properties too                  │
      │ ❌ Missing JsonPropertyName        → ✅ Explicit camelCase mapping                     │
      │ ❌ async Task with Task.FromResult → ✅ Remove async or make truly async               │
      │ ❌ No input validation             → ✅ Check for injection patterns                   │
      │ ❌ Silent failures                 → ✅ Log raw requests and errors                    │
      │ ❌ Random order pattern matching   → ✅ Priority order (most specific first)           │
      └────────────────────────────────────────────────────────────────────────────────────────┘

   🔗 RELATED FILES IN THIS PROJECT:
      - LLMGateway.cs          - HTTP endpoint handling, request validation
      - BrainClient.cs         - This file - brain communication abstraction
      - Program.cs             - DI container and service registration

   📚 CONTRIBUTING:
      When adding new commands to the mock brain:
      1. Add the regex pattern at the top with other patterns
      2. Add the handler in priority order (most specific first)
      3. Update GenerateIntentGuesses() to include the new command
      4. Update the HELP text
      5. Add examples to the help menu
*/