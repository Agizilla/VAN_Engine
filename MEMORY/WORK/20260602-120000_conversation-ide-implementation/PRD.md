---
task: Implement Conversation-IDE blueprint with VAN_Engine integration
slug: 20260602-120000_conversation-ide-implementation
effort: comprehensive
phase: build
progress: 0/64
mode: interactive
started: 2026-06-02T12:00:00Z
updated: 2026-06-02T12:00:00Z
---

## Context

Implement the Conversation-IDE blueprint as a standalone Electron+React+TypeScript application that integrates with VAN_Engine as a vessel (ISO_004 isolation). The application mounts under VAN_Engine/ConversationIDE/ and includes:

- Electron main process with IPC handlers for chat, files, build, and VAN_Engine bridge
- React renderer with Chat, Files, Status, and Config panels
- Python bridge to VAN_Engine's core (ISORegistry, quaternion index, audit log)
- Voice command support via Web Speech API
- Zustand state management for chat, file, and ISO stores
- Full ISO_004/010/015/019/020 compliance

**What was explicitly requested:** Complete implementation per the 16-section blueprint including all ~50 source files, Python bridge, IPC protocols, React components, voice commands, and config.

**What was NOT requested:** C# code changes (VAN_Engine's C# projects are separate), adding external dependencies not in the blueprint, cloud API integrations.

**Not wanted:** External API calls enabled by default (ISO_019), hallucinated or guessed state (ISO_020), cross-project mutations (ISO_004).

### Risks
- Python bridge requires VAN_Engine to exist at the expected path
- Voice commands require browser SpeechRecognition API (Chromium-only)
- Monaco editor in Electron can be large; verify bundle size

### Plan
The work is organized into 7 workstreams executed in parallel:
1. Directory scaffold + config files
2. Python VAN_Engine bridge (4 files)
3. Electron main process (9 files)  
4. Preload script
5. React components + hooks + stores (20 files)
6. Styles + build scripts
7. Project-level config (tsconfig, vite, package.json)

All files follow the exact structure from the blueprint. Python bridge connects to VAN_Engine's ISO_Rules.json, token_index.db, and audit log.

## Criteria

- [ ] ISC-1: package.json created with all blueprint dependencies
- [ ] ISC-2: electron.vite.config.ts created with proper build config
- [ ] ISC-3: tsconfig.json created for main process
- [ ] ISC-4: tsconfig.web.json created for renderer
- [ ] ISC-5: tailwind.config.js created with dark theme
- [ ] ISC-6: index.html created as renderer entry point
- [ ] ISC-7: config/default.json created with offline-first defaults
- [ ] ISC-8: config/projects.json created with VAN_Engine + ConversationIDE projects
- [ ] ISC-9: config/bridges.json created with all bridges disabled (ISO_019)
- [ ] ISC-10: Python bridge __init__.py created as package
- [ ] ISC-11: Python bridge client.py connects to VAN_Engine ISO_Rules.json
- [ ] ISC-12: Python bridge client.py connects to VAN_Engine token_index.db
- [ ] ISC-13: Python bridge client.py implements quaternion_lookup()
- [ ] ISC-14: Python bridge client.py implements quaternion_store()
- [ ] ISC-15: Python bridge client.py implements get_iso_rules()
- [ ] ISC-16: Python bridge client.py implements log_audit() (ISO_015)
- [ ] ISC-17: Python bridge client.py implements drift_gate() (ISO_010)
- [ ] ISC-18: Python bridge client.py implements _compute_drift()
- [ ] ISC-19: quaternion_client.py provides standalone quaternion operations
- [ ] ISC-20: iso_client.py provides ISO rule status queries
- [ ] ISC-21: audit_client.py provides audit log reading
- [ ] ISC-22: Python bridge uses singleton pattern via get_bridge()
- [ ] ISC-23: Windows UTF-8 encoding wrapper in all Python files
- [ ] ISC-24: Electron src/main/index.ts created as main entry point
- [ ] ISC-25: src/main/window.ts creates BrowserWindow with contextIsolation
- [ ] ISC-26: src/main/ipc/chat.ts handles chat send/receive IPC
- [ ] ISC-27: src/main/ipc/files.ts handles file read/write/tree IPC
- [ ] ISC-28: src/main/ipc/build.ts handles build pipeline IPC
- [ ] ISC-29: src/main/ipc/van_engine.ts handles quaternion/ISO/audit IPC
- [ ] ISC-30: src/main/ipc/van_engine.ts spawns Python bridge process
- [ ] ISC-31: src/main/services/fileWatcher.ts watches files for changes
- [ ] ISC-32: src/main/services/buildPipeline.ts orchestrates builds
- [ ] ISC-33: src/main/services/skillRouter.ts routes intents to skills
- [ ] ISC-34: src/preload/index.ts exposes contextBridge API
- [ ] ISC-35: src/renderer/index.tsx creates React root
- [ ] ISC-36: src/renderer/App.tsx composes all panels in layout
- [ ] ISC-37: src/renderer/styles/globals.css provides dark theme styles
- [ ] ISC-38: ChatPanel.tsx renders chat UI with connection status
- [ ] ISC-39: MessageList.tsx renders message bubbles with metadata
- [ ] ISC-40: InputArea.tsx provides text input with send button
- [ ] ISC-41: VoiceInput.tsx provides speech-to-text recording
- [ ] ISC-42: FileTree.tsx renders directory tree with expand/collapse
- [ ] ISC-43: Editor.tsx wraps Monaco editor for file editing
- [ ] ISC-44: DiffViewer.tsx shows file diff with before/after
- [ ] ISC-45: StatusBar.tsx shows connection and ISO status indicators
- [ ] ISC-46: ISOPanel.tsx displays ISO rule status grid from VAN_Engine
- [ ] ISC-47: AuditLog.tsx displays recent audit events (ISO_015)
- [ ] ISC-48: Settings.tsx provides UI config panel
- [ ] ISC-49: Bridges.tsx provides bridge enable/disable UI
- [ ] ISC-50: Projects.tsx provides project management UI
- [ ] ISC-51: useWebSocket.ts hook manages WebSocket connection
- [ ] ISC-52: useFileSystem.ts hook provides file operations
- [ ] ISC-53: useVoiceCommands.ts hook provides speech recognition + TTS
- [ ] ISC-54: chatStore.ts manages conversations and messages
- [ ] ISC-55: fileStore.ts manages file tree and watched files
- [ ] ISC-56: isoStore.ts manages ISO rule status and audit events
- [ ] ISC-57: scripts/build.js builds and packages the app
- [ ] ISC-58: scripts/deploy.js deploys to release directory
- [ ] ISC-59: ISO_004 enforced in file IPC (no cross-project access)
- [ ] ISC-60: ISO_019 enforced (all bridges disabled in default config)
- [ ] ISC-61: Context isolation enabled (nodeIntegration: false)
- [ ] ISC-62: ConversationIDE directory created under VAN_Engine root
- [ ] ISC-63: All Python files include sys.stdout UTF-8 wrapper on win32
- [ ] ISC-64: All React components use TypeScript strict typing

## Decisions

## Verification
