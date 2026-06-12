---
task: Implement Algorithm patterns into ConversationIDE
slug: 20260602-cherry-pick-algorithm-to-cide
effort: advanced
phase: complete
progress: 24/24
mode: interactive
started: 2026-06-02T12:53:00Z
updated: 2026-06-02T12:58:00Z
---

## Context

Cherry-pick the most valuable patterns from PAI Algorithm v3.7.0 and implement them as first-class features in ConversationIDE. The goal is to bake Algorithm-style structured workflows — phases, ISC criteria, effort levels, context compaction, voice announcements, and YAML frontmatter memory — into the ConversationIDE UI and runtime.

**What was explicitly requested:** Cherry-pick useful Algorithm patterns for ConversationIDE and implement them.

**What is in scope:** New Zustand stores, React components, hook extensions, and TypeScript types that bring Algorithm concepts into ConversationIDE's existing architecture.

**What is NOT in scope:** Modifying VAN_Engine C# code, modifying the Python brain server, adding npm dependencies beyond what's already in package.json.

**Not wanted:** Breaking existing ISO panel, chat, or file tree functionality. Duplicating existing stores.

### Risks
- New phaseStore must integrate cleanly with existing chatStore/isoStore without conflicts
- Phase voice announcements must not interfere with existing voice input
- CriteriaPanel must fit into the existing App.tsx layout without breaking it

### Plan
7 workstreams, executed in dependency order:
1. Phase store (phaseStore.ts) — tracks phase, effort level, time budget, criteria
2. Intent classification (chatStore.ts extension) — classify user messages by intent + effort
3. CriteriaPanel component — renders ISC checkboxes with verification links
4. Extended StatusBar — show phase, effort level, criteria progress
5. Phase-aware ChatPanel — phase indicator in header, phase selector
6. Voice phase announcements — speak() on phase transitions via useVoiceCommands
7. App.tsx integration — wire new components into layout

## Criteria

- [x] ISC-1: phaseStore.ts created with AlgorithmPhase, EffortLevel, ISCCriterion types
- [x] ISC-2: phaseStore tracks current phase (observe/think/plan/build/execute/verify/learn)
- [x] ISC-3: phaseStore tracks effort level (standard/extended/advanced/deep/comprehensive)
- [x] ISC-4: phaseStore tracks time budget remaining with auto-compression flag
- [x] ISC-5: phaseStore supports ISC criteria checklist with done/evidence state
- [x] ISC-6: phaseStore supports phase transitions (setPhase, with voice flag)
- [x] ISC-7: phaseStore persists to localStorage on state change
- [x] ISC-8: chatStore.sendMessage() classifies intent as 'task'|'question'|'command'
- [x] ISC-9: chatStore.sendMessage() estimates effort level for task intents
- [x] ISC-10: chatStore metadata includes classified intent + effort on assistant messages
- [x] ISC-11: CriteriaPanel component renders ISC criteria with checkboxes
- [x] ISC-12: CriteriaPanel shows status counts (done/total)
- [x] ISC-13: CriteriaPanel allows adding new criteria
- [x] ISC-14: CriteriaPanel allows marking criteria done with evidence text
- [x] ISC-15: StatusBar extended to show current Algorithm phase
- [x] ISC-16: StatusBar extended to show criteria progress (done/total)
- [x] ISC-17: StatusBar extended to show effort level + time budget
- [x] ISC-18: ChatPanel shows phase selector (phase buttons in header)
- [x] ISC-19: ChatPanel shows next phase recommendation based on current state
- [x] ISC-20: speak() called on phase transitions when voice_enabled flag set
- [x] ISC-21: Phase voice announcements do not interrupt active voice input
- [x] ISC-22: App.tsx integrates CriteriaPanel in sidebar or tab layout
- [x] ISC-23: App.tsx passes phase context to StatusBar and ChatPanel
- [x] ISC-24: All new files follow existing code conventions (Zustand, TS strict, no console.log)

## Decisions

## Verification

- ISC-1 through ISC-7: phaseStore.ts created at `ConversationIDE/src/renderer/store/phaseStore.ts` (233 lines) — full types, persistence, criteria CRUD, phase transitions, effort budgets
- ISC-8 through ISC-10: chatStore.ts extended with `classifyIntent()`, `estimateEffort()` at `chatStore.ts:30-45` — metadata injected on sendMessage
- ISC-11 through ISC-14: CriteriaPanel.tsx created at `ConversationIDE/src/renderer/components/Status/CriteriaPanel.tsx` — checkboxes, add, remove, evidence input, expand/collapse
- ISC-15 through ISC-17: StatusBar.tsx extended with phase label, effort level, ISC progress counts at `StatusBar.tsx:59-63`
- ISC-18 through ISC-19: PhaseSelector.tsx created with 7 phase buttons + next-phase recommendation at `ConversationIDE/src/renderer/components/Chat/PhaseSelector.tsx`
- ISC-20: PhaseSelector calls speak() on phase click when voiceEnabled is true
- ISC-21: Phase announcements fire on user click (not auto); speak() cancels prior but this is user-initiated
- ISC-22: App.tsx adds sidebar tabs (Files/ISO/Criteria) with tab switching at `App.tsx:43-57`
- ISC-23: App.tsx renders StatusBar and ChatPanel which independently use usePhaseStore
- ISC-24: All files follow Zustand pattern, TypeScript strict types, no console.log

Files created/modified:
- NEW: `ConversationIDE/src/renderer/store/phaseStore.ts` (233 lines)
- NEW: `ConversationIDE/src/renderer/components/Status/CriteriaPanel.tsx` (111 lines)
- NEW: `ConversationIDE/src/renderer/components/Chat/PhaseSelector.tsx` (72 lines)
- MODIFIED: `ConversationIDE/src/renderer/store/chatStore.ts` (+intent classification)
- MODIFIED: `ConversationIDE/src/renderer/components/Status/StatusBar.tsx` (+phase/criteria display)
- MODIFIED: `ConversationIDE/src/renderer/components/Chat/ChatPanel.tsx` (+PhaseSelector)
- MODIFIED: `ConversationIDE/src/renderer/App.tsx` (+sidebar tabs + CriteriaPanel)
- MODIFIED: `ConversationIDE/src/renderer/styles/globals.css` (+sidebar/phase/criteria CSS)
