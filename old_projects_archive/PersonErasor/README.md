# Sovereign IDE

**AI-Human Collaborative Development Environment**

Version 1.0 | Built with C# .NET 8 + WinForms

---

## Overview

Sovereign IDE is a development environment designed for **co-evolution** between human developers and AI models. Unlike traditional AI coding assistants, Sovereign IDE:

- **Persists context** across sessions via manifest files
- **Gives humans control** with pause button and approval workflow
- **Is model-agnostic** - works with DeepSeek, Claude, Gemini, etc.
- **Is transparent** - all operations are visible and debuggable
- **Is sovereign** - runs locally, no vendor lock-in

---

## Quick Start

### Prerequisites

- **Windows 10/11** (WinForms application)
- **.NET 8 SDK** ([Download](https://dotnet.microsoft.com/download/dotnet/8.0))
- **Visual Studio 2022** (recommended) or VS Code with C# extension

### Build & Run

```bash
# Clone repository
git clone <your-repo-url>
cd SovereignIDE

# Restore dependencies
dotnet restore

# Build
dotnet build

# Run
dotnet run --project SovereignIDE.UI/SovereignIDE.UI.csproj
```

Or open `SovereignIDE.sln` in Visual Studio and press F5.

---

## Architecture

### Core Components

#### SovereignIDE.Core (Class Library)

**Models** (`Models/ManifestV4.cs`)
- Complete manifest schema as C# records
- File entries, commands, decisions, conversation history

**Validation** (`Validation/Validators.cs`)
- Path validation (blocks traversal attacks)
- State transition validation
- Command security (dangerous pattern detection)
- Content encoding validation

**Parsers** (`Parsers/ResponseParser.cs`)
- Extracts files, commands, decisions from AI responses
- Handles chatty format → structured data
- Infers filenames from context

**File System** (`FileSystem/FileManager.cs`)
- Safe file I/O with validation
- Batch operations with rollback
- Directory scanning

**Execution** (`Execution/CommandExecution.cs`)
- CommandQueue: approval workflow
- CommandExecutor: safe process execution
- AutoExecutor: pause button logic

**AI Integration** (`AI/AnthropicClient.cs`)
- Full Anthropic API client
- Streaming support
- Retry logic with exponential backoff

**Exceptions** (`Exceptions/SovereignExceptions.cs`)
- Copy-pasteable error messages
- Hierarchical exception types
- Error data capture

#### SovereignIDE.UI (WinForms Application)

**MainForm** - 3-panel layout
- Left: File Explorer (project tree)
- Center: Manifest Viewer (JSON + preview)
- Right: Command Queue (approval list)

**Controls**
- FileExplorerControl: tree view for browsing files
- ManifestViewerControl: displays manifest JSON and file previews
- CommandQueueControl: command approval interface

---

## Usage

### 1. Open a Project

**File → Open Project Folder**

Select your project root. Sovereign IDE will:
- Scan all files
- Create initial manifest
- Initialize session

### 2. Paste AI Response

**Ctrl+V or Edit → Paste Response**

Copy AI model output (DeepSeek, Claude, etc.) to clipboard, then paste. Sovereign IDE will:
- Extract code blocks
- Infer filenames from context
- Queue commands for approval
- Update manifest

### 3. Approve Commands

Commands appear in the **Command Queue** panel (right side).

- **Double-click** a pending command to approve/reject
- Dangerous commands (rm -rf, etc.) ALWAYS require approval
- Failed commands auto-pause execution

### 4. Toggle Auto-Execution

**Ctrl+Space or click Pause Button**

- 🔴 **PAUSED** (default): All actions require approval
- 🔵 **AUTO**: Non-dangerous commands execute automatically

### 5. Save Manifest

**File → Save Manifest**

Saves current project state (files, commands, decisions, history) to JSON.

**Why?** The manifest IS the memory. Load it in the next session to continue where you left off.

---

## Manifest Schema v4.0

The manifest is the **single source of truth** for project state.

### Structure

```json
{
  "version": "4.0",
  "context": {
    "model": "DeepSeek",
    "sessionId": "uuid",
    "owner": "YourName",
    "projectRoot": "C:\\Projects\\MyApp",
    "cumulativeTokens": 850000,
    "history": [
      {
        "timestamp": "2026-03-28T14:00:00Z",
        "agent": "Claude",
        "action": "Created Parser.cs",
        "filesPaths": ["src/Parser.cs"]
      }
    ]
  },
  "files": [
    {
      "path": "src/Parser.cs",
      "state": "created",
      "content": "using System;...",
      "language": "csharp",
      "modelName": "Claude"
    }
  ],
  "commands": [
    {
      "type": "dotnet",
      "command": "dotnet build",
      "status": "pending",
      "requiresApproval": false
    }
  ],
  "decisions": [
    {
      "timestamp": "2026-03-28T10:00:00Z",
      "agent": "Human",
      "decision": "Use C# over Python",
      "rationale": "Better debugging, Windows-native"
    }
  ]
}
```

### Key Concepts

**File States**
- `unchanged`: File exists, no changes
- `modified`: File was edited
- `created`: New file
- `deleted`: File removed

**Command Status**
- `pending`: Awaiting approval
- `approved`: Ready to execute
- `executed`: Successfully ran
- `failed`: Execution failed
- `rejected`: User declined

**History Growth**
- History grows indefinitely (by design)
- Monitor size: warnings at 10MB, critical at 50MB
- Archive old entries when needed (manual decision)

---

## Security

### Path Validation

ALL file paths are validated to prevent:
- Path traversal (`../../../etc/passwd`)
- Absolute paths (`C:\Windows\System32`)
- URL-encoded attacks (`%2e%2e/`)

### Command Validation

Dangerous commands ALWAYS require approval:
- `rm -rf`, `del /f /s`, `format`
- `shutdown`, `reboot`
- `chmod 777`, `sudo rm`
- Fork bombs

### Error Handling

Every error produces a **copy-pasteable** format:

```
=== SOVEREIGN IDE ERROR ===
Message: Path traversal not allowed
Context: File '../etc/passwd'
Time: 2026-03-28 14:30:00 UTC

Data:
  InvalidPath: ../etc/passwd
  Reason: Path contains '..'

Stack Trace:
...

[This error has been copied to clipboard]
```

Paste this into AI chat to debug.

---

## Philosophy

### The Pause Button

The **giant pause button** (top-right) is the philosophical center of Sovereign IDE.

- **Paused (default)**: You approve everything. You're in control.
- **Auto**: AI can execute safe operations. You still approve dangerous ones.
- **Ctrl+Space**: Toggle instantly.

**Why?** Trust, but verify. Let AI work fast, but keep the kill switch.

### The Manifest as Memory

Traditional AI assistants forget everything when you close the chat. Sovereign IDE's manifest IS the memory:

- Every file change
- Every command
- Every decision
- Complete conversation history

**Result:** AI agents can **grow with you**, not reset every session.

### Co-Evolution, Not Replacement

Sovereign IDE doesn't replace developers. It **augments** them:

- AI generates boilerplate
- Human makes architectural decisions
- AI enforces contracts (validators)
- Human debugs with breakpoints

**The end goal:** Faster iteration, better quality, permanent knowledge.

---

## Roadmap

### v1.1 (Next Sprint)
- [ ] WebView2 integration (embedded browser for AI chat)
- [ ] Clipboard watcher (auto-detect new responses)
- [ ] Terminal integration (embedded shell)
- [ ] Git integration (commit, push, pull from IDE)

### v1.2
- [ ] Line-level diffs (partial file edits)
- [ ] Undo/redo system
- [ ] File conflict resolution UI
- [ ] Model switcher (DeepSeek ↔ Claude ↔ Gemini)

### v2.0
- [ ] Multi-agent support (DeepSeek + Claude collaborate)
- [ ] Team mode (multiple humans, one manifest)
- [ ] Plugin system (extend with custom parsers)

---

## Contributing

This is a **sovereign project**. That means:

1. **No vendor dependencies** - runs offline if needed
2. **No telemetry** - your data stays local
3. **Full transparency** - every operation is visible
4. **Human in control** - pause button always works

If you want to contribute, honor these principles.

---

## License

MIT License - build whatever you want on top of this.

---

## Contact

Built by: **[Your Name]**  
Session: `[Session ID from manifest]`  
Date: 2026-03-28

---

**"Build tools that set you free, not lock you in."**
