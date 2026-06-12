using System.Diagnostics;
using System.Text;
using SovereignIDE.Core.Exceptions;
using SovereignIDE.Core.Models;
using SovereignIDE.Core.Validation;

namespace SovereignIDE.Core.Execution;

/// <summary>
/// Manages command queue with approval workflow.
/// </summary>
public class CommandQueue
{
    private readonly List<CommandEntry> _queue = new();
    private readonly string _sessionId;

    public event EventHandler<CommandEntry>? CommandAdded;
    public event EventHandler<CommandEntry>? CommandApproved;
    public event EventHandler<CommandEntry>? CommandRejected;
    public event EventHandler<CommandEntry>? CommandExecuted;

    public IReadOnlyList<CommandEntry> Pending => _queue.Where(c => c.Status == CommandStatus.Pending).ToList();
    public IReadOnlyList<CommandEntry> All => _queue.AsReadOnly();

    public CommandQueue(string sessionId)
    {
        _sessionId = sessionId;
    }

    /// <summary>
    /// Adds command to queue.
    /// Contract: Dangerous commands MUST require approval.
    /// </summary>
    public void Add(CommandEntry command)
    {
        ArgumentNullException.ThrowIfNull(command);

        // Validate command
        CommandValidator.ValidateCommand(command, _sessionId);

        // Force approval for dangerous commands
        if (CommandValidator.IsDangerousCommand(command.Command))
        {
            command = command with { RequiresApproval = true };
        }

        _queue.Add(command);
        CommandAdded?.Invoke(this, command);

        Console.WriteLine($"📋 Queued: {command.Command}");
    }

    /// <summary>
    /// Approves a pending command.
    /// </summary>
    public void Approve(string commandId, string approvedBy)
    {
        var command = _queue.FirstOrDefault(c => c.Id == commandId);
        if (command == null)
            throw new ExecutionException($"Command {commandId} not found", "Approving command", _sessionId);

        var updated = command with
        {
            Status = CommandStatus.Approved,
            ApprovedBy = approvedBy
        };

        var index = _queue.IndexOf(command);
        _queue[index] = updated;

        CommandApproved?.Invoke(this, updated);
        Console.WriteLine($"✅ Approved: {command.Command}");
    }

    /// <summary>
    /// Rejects a pending command.
    /// </summary>
    public void Reject(string commandId)
    {
        var command = _queue.FirstOrDefault(c => c.Id == commandId);
        if (command == null)
            throw new ExecutionException($"Command {commandId} not found", "Rejecting command", _sessionId);

        var updated = command with { Status = CommandStatus.Rejected };

        var index = _queue.IndexOf(command);
        _queue[index] = updated;

        CommandRejected?.Invoke(this, updated);
        Console.WriteLine($"❌ Rejected: {command.Command}");
    }

    /// <summary>
    /// Marks command as executed.
    /// </summary>
    public void MarkExecuted(string commandId, int exitCode, string output)
    {
        var command = _queue.FirstOrDefault(c => c.Id == commandId);
        if (command == null)
            return;

        var status = exitCode == 0 ? CommandStatus.Executed : CommandStatus.Failed;

        var updated = command with
        {
            Status = status,
            ExitCode = exitCode,
            Output = output,
            ExecutedDate = DateTime.UtcNow
        };

        var index = _queue.IndexOf(command);
        _queue[index] = updated;

        CommandExecuted?.Invoke(this, updated);
    }

    /// <summary>
    /// Clears completed commands.
    /// </summary>
    public void ClearCompleted()
    {
        _queue.RemoveAll(c => c.Status is CommandStatus.Executed or CommandStatus.Rejected);
    }
}

/// <summary>
/// Executes commands safely with timeout and output capture.
/// </summary>
public class CommandExecutor
{
    private readonly int _timeoutSeconds;

    public CommandExecutor(int timeoutSeconds = 60)
    {
        _timeoutSeconds = timeoutSeconds;
    }

    /// <summary>
    /// Executes command and returns result.
    /// Contract: MUST timeout after configured seconds.
    /// </summary>
    public async Task<ExecutionResult> ExecuteAsync(CommandEntry command, CancellationToken cancellationToken = default)
    {
        var startInfo = new ProcessStartInfo
        {
            FileName = GetShell(command.Type),
            Arguments = GetArguments(command),
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true
        };

        var output = new StringBuilder();
        var error = new StringBuilder();

        try
        {
            using var process = new Process { StartInfo = startInfo };

            process.OutputDataReceived += (s, e) =>
            {
                if (e.Data != null)
                    output.AppendLine(e.Data);
            };

            process.ErrorDataReceived += (s, e) =>
            {
                if (e.Data != null)
                    error.AppendLine(e.Data);
            };

            process.Start();
            process.BeginOutputReadLine();
            process.BeginErrorReadLine();

            // Wait with timeout
            using var cts = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
            cts.CancelAfter(TimeSpan.FromSeconds(_timeoutSeconds));

            await process.WaitForExitAsync(cts.Token);

            var combined = output.ToString() + (error.Length > 0 ? "\n" + error.ToString() : "");

            return new ExecutionResult
            {
                ExitCode = process.ExitCode,
                Output = combined,
                TimedOut = false
            };
        }
        catch (OperationCanceledException)
        {
            return new ExecutionResult
            {
                ExitCode = -1,
                Output = $"Command timed out after {_timeoutSeconds} seconds",
                TimedOut = true
            };
        }
        catch (Exception ex)
        {
            return new ExecutionResult
            {
                ExitCode = -1,
                Output = $"Execution failed: {ex.Message}",
                TimedOut = false
            };
        }
    }

    private string GetShell(CommandType type)
    {
        return type switch
        {
            CommandType.PowerShell => "powershell.exe",
            CommandType.Cmd => "cmd.exe",
            CommandType.Bash => "bash",
            _ => OperatingSystem.IsWindows() ? "cmd.exe" : "bash"
        };
    }

    private string GetArguments(CommandEntry command)
    {
        return command.Type switch
        {
            CommandType.PowerShell => $"-Command \"{command.Command}\"",
            CommandType.Cmd => $"/C \"{command.Command}\"",
            CommandType.Bash => $"-c \"{command.Command}\"",
            _ => OperatingSystem.IsWindows() ? $"/C \"{command.Command}\"" : $"-c \"{command.Command}\""
        };
    }
}

public record ExecutionResult
{
    public required int ExitCode { get; init; }
    public required string Output { get; init; }
    public required bool TimedOut { get; init; }
}

/// <summary>
/// Auto-executor with pause button logic.
/// The heart of the "human-in-loop" system.
/// </summary>
public class AutoExecutor
{
    private bool _paused = true; // Default: paused (safe)
    private readonly CommandQueue _commandQueue;
    private readonly CommandExecutor _executor;

    public event EventHandler<bool>? PausedChanged;

    public bool Paused
    {
        get => _paused;
        set
        {
            if (_paused != value)
            {
                _paused = value;
                PausedChanged?.Invoke(this, _paused);
                Console.WriteLine(_paused ? "⏸️  PAUSED" : "▶️  AUTO");
            }
        }
    }

    public AutoExecutor(CommandQueue commandQueue, CommandExecutor? executor = null)
    {
        _commandQueue = commandQueue;
        _executor = executor ?? new CommandExecutor();
    }

    /// <summary>
    /// Processes a command based on pause state and approval requirements.
    /// 
    /// Contract:
    /// - If paused: ALWAYS queue for approval
    /// - If not paused AND requires approval: queue
    /// - If not paused AND doesn't require approval: execute
    /// </summary>
    public async Task ProcessCommandAsync(CommandEntry command)
    {
        if (Paused)
        {
            _commandQueue.Add(command);
            return;
        }

        if (command.RequiresApproval)
        {
            _commandQueue.Add(command);
            return;
        }

        // Auto-execute
        await ExecuteCommandAsync(command);
    }

    /// <summary>
    /// Executes an approved command.
    /// </summary>
    public async Task ExecuteCommandAsync(CommandEntry command)
    {
        Console.WriteLine($"🚀 Executing: {command.Command}");

        var result = await _executor.ExecuteAsync(command);

        _commandQueue.MarkExecuted(command.Id, result.ExitCode, result.Output);

        if (result.ExitCode == 0)
        {
            Console.WriteLine($"✅ Success: {command.Command}");
        }
        else
        {
            Console.WriteLine($"❌ Failed (exit {result.ExitCode}): {command.Command}");
            Console.WriteLine($"Output: {result.Output}");

            // Auto-pause on failure
            Paused = true;
            Console.WriteLine("⏸️  Auto-paused due to command failure");
        }
    }

    /// <summary>
    /// Executes all approved commands in queue.
    /// </summary>
    public async Task ExecuteAllApprovedAsync()
    {
        var approved = _commandQueue.All
            .Where(c => c.Status == CommandStatus.Approved)
            .ToList();

        foreach (var command in approved)
        {
            await ExecuteCommandAsync(command);

            // Stop if paused (e.g., due to failure)
            if (Paused)
                break;
        }
    }
}
