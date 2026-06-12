using VanEngine.Compiler.Runtime;
using VanEngine.Core.VAN;

namespace VanEngine.Compiler;

public static class ClawdiaHost
{
    public static async Task Main(string[] args)
    {
        using var cortex = new CortexRuntime();

        Console.WriteLine("=== Clawdia Cortex v1.0 — Sovereign Offline AI ===");
        Console.WriteLine("Direct-mapping VAN compiler. Zero GC. Zero reflection.");
        Console.WriteLine("Fryas Juul — 6-bit geometric tokenization.");
        Console.WriteLine($"Args: {(args.Length > 0 ? args[0] : "none")}");
        Console.WriteLine();

        if (args.Length > 0 && File.Exists(args[0]))
        {
            Console.WriteLine($"Loading {args[0]}...");
            await cortex.ExecuteFileAsync(args[0]);
            Console.WriteLine("Execution complete.");
            return;
        }

        Console.WriteLine("Interactive mode — type VAN blocks, 'test:juul', or 'exit':");
        while (true)
        {
            Console.Write("\n> ");
            var input = Console.ReadLine();
            if (string.IsNullOrWhiteSpace(input) || input == "exit")
                break;

            if (input == "test:juul")
            {
                RunJuulTest();
                continue;
            }

            try
            {
                var result = await cortex.ExecuteStringAsync(input);
                Console.WriteLine($"  => {System.Text.Json.JsonSerializer.Serialize(result)}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"  Error: {ex.Message}");
            }
        }
    }

    private static void RunJuulTest()
    {
        Console.WriteLine("Enter Fryas text (using the 34-character alphabet):");
        var fryasLine = Console.ReadLine();
        if (string.IsNullOrEmpty(fryasLine)) return;

        var lexer = new JuulLexer(fryasLine.AsSpan());
        Console.Write("Juul masks: ");
        while (lexer.ReadNextMask() is { } mask)
        {
            Console.Write($"{(byte)mask:X2} ");
        }
        Console.WriteLine();

        Console.Write("Character count: ");
        var chars = 0;
        var countLexer = new JuulLexer(fryasLine.AsSpan());
        while (countLexer.ReadNextMask() is { }) chars++;
        Console.WriteLine(chars);
    }
}
