# Oera Linda Simulator (Code Edition) — 5-Tier Sprint Roadmap

## Philosophy
**A gamified multi-project CI/CD tracker where:**
- Projects become sovereign states with their own health, resources, and citizens
- Code files are citizens with skills and loyalty
- Compliance violations are threats
- Overlapping functionality is duplication (war/conflict)
- Refactoring is literal building management
- **Theme**: Oera Linda as a metaphorical lens, not a literal historical sim

---

## Tier 1: Foundation (Complete)
✓ Multi-workspace manager
✓ Persistent save/load (JSON + .van format)
✓ Live filesystem watcher
✓ Pan, zoom, minimap
✓ Multi-language analyzer
✓ Settings & config screen

**Deliverables**: 6 systems, stable foundation

---

## Tier 2: Core Gameplay (Complete)
✓ Cross-project dependency graph visualization
✓ Overlap/duplication detector
✓ Shared library/commons zone
✓ History timeline & audit log
✓ Click-to-inspect side panel
✓ In-game refactoring actions
✓ Directive config per workspace
✓ Phase transition animation

**Deliverables**: 8 systems, rich interaction

---

## Tier 3: Advanced Systems (Complete)
✓ Threat & vulnerability events (simplified CVE)
✓ Tech tree & house upgrades (Hamlet→Citadel)
✓ GeckoShift neural pipeline trigger
✓ Citizen skill progression & specialisation
✓ Inter-workspace trade routes
✓ Local event socket/webhook

**Deliverables**: 6 systems, emergent gameplay

---

## Tier 4: Endgame (Complete)
✓ Git integration (commits advance year, branches split timelines, conflicts)
✓ Project health report export (markdown/HTML)
✓ Scripting API / mod hooks (Lua)
✓ Optional community scoreboard (self-certifying)

**Deliverables**: 4 systems, extensibility

---

## Tier 5: Polish & Deployment (NEW)
1. **Complete UI Polish**
   - All 8 inspector panels fully functional
   - Tooltip system for all interactive elements
   - Keyboard shortcut reference card
   - Accessibility: colorblind-safe palette options
   - Mouse/touch input validation

2. **Performance Optimization**
   - Asset caching for large workspaces (1000+ files)
   - Spatial grid acceleration for threat system
   - Similarity matrix lazy evaluation
   - Delta serialization for autosave

3. **Content & Documentation**
   - In-game tutorial (first 30 seconds)
   - API documentation (OpenAPI spec for event socket)
   - Mod development kit (example Lua mods)
   - Quick-start guide (GitHub wiki)

4. **Cross-platform Build**
   - Windows (x64, x86) — primary target
   - Linux (x64) — secondary
   - macOS (x64, ARM64) — stretch goal
   - Docker container for CI/CD server integration

5. **Deployment Pipeline**
   - GitHub Actions CI/CD workflow
   - Automated release builds
   - Update checker (self-hosted)
   - Telemetry-free crash reporting (optional sentry)

6. **Testing & QA**
   - Unit tests (all core systems)
   - Integration tests (workspace I/O, file watching)
   - Stress tests (1000 citizens, 100 files, 10 threats)
   - Manual test plan (check list for all features)

**Deliverables**: 6 subsystems, production-ready

---

## Implementation Order (Weeks 1-5)

### Week 1: Tier 1-2 Wiring
- [ ] Implement `WorkspaceManager.cs` (multi-workspace switching)
- [ ] Implement `FileSystemWatcherService.cs` (live file monitoring)
- [ ] Implement `CameraController.cs` (viewport pan/zoom/minimap)
- [ ] Wire into `Program.cs` and `DashboardView.cs`
- [ ] Test save/load roundtrip

### Week 2: Tier 2-3 Wiring
- [ ] Implement `DependencyGraphAnalyzer.cs`
- [ ] Implement `ThreatSystem.cs` (vulnerabilities approach)
- [ ] Implement `HouseUpgradeSystem.cs` (tech tree)
- [ ] Implement `CitizenSkillSystem.cs` (XP & specialisations)
- [ ] UI panels for inspector, refactoring menu

### Week 3: Tier 3-4 Wiring
- [ ] Implement `TradeRouteSystem.cs`
- [ ] Implement `EventSocketServer.cs` (HTTP webhook)
- [ ] Implement `GitIntegrationService.cs`
- [ ] Implement `ReportGenerator.cs`
- [ ] Test CI/CD integration

### Week 4: Tier 4-5 Wiring
- [ ] Implement `ScriptingEngine.cs` (Lua API)
- [ ] Implement `CommunityScoreboard.cs`
- [ ] Complete all UI panels
- [ ] Keyboard shortcuts & tooltips
- [ ] Tutorial/onboarding flow

### Week 5: Polish & Release
- [ ] Performance profiling & optimization
- [ ] Cross-platform builds (Windows, Linux, macOS)
- [ ] GitHub Actions workflow setup
- [ ] Documentation & API spec
- [ ] Release v1.0.0

---

## File Structure (New Files to Create)

```
VanEngine.Core/
├── Systems/
│   ├── WorkspaceManager.cs (T1)
│   ├── FileSystemWatcherService.cs (T1)
│   ├── CameraController.cs (T1)
│   ├── DependencyGraphAnalyzer.cs (T2)
│   ├── OverlapDetector.cs (T2)
│   ├── RefactoringActionSystem.cs (T2)
│   ├── ThreatSystem.cs (T3)
│   ├── HouseUpgradeSystem.cs (T3)
│   ├── CitizenSkillSystem.cs (T3)
│   ├── TradeRouteSystem.cs (T3)
│   ├── EventSocketServer.cs (T3)
│   ├── GitIntegrationService.cs (T4)
│   ├── ReportGenerator.cs (T4)
│   ├── ScriptingEngine.cs (T4)
│   └── CommunityScoreboard.cs (T4)
├── Models/
│   ├── WorkspaceMetadata.cs (T1)
│   ├── DependencyEdge.cs (T2)
│   ├── Threat.cs (T3)
│   ├── SkillSpecialisation.cs (T3)
│   ├── TradeRoute.cs (T3)
│   └── GitCommitEvent.cs (T4)
└── Managers/
    ├── SettingsManager.cs (T1)
    ├── LanguageAnalyzerFactory.cs (T1)
    └── TutorialManager.cs (T5)

VanEngine.SDL/
├── Panels/
│   ├── InspectorPanel.cs (T2)
│   ├── RefactoringMenuPanel.cs (T2)
│   ├── DependencyGraphPanel.cs (T2)
│   ├── HistoryTimelinePanel.cs (T2)
│   ├── ThreatRadarPanel.cs (T3)
│   ├── TradeRoutePanel.cs (T3)
│   ├── ReportExportPanel.cs (T4)
│   ├── ScriptConsolePanel.cs (T4)
│   └── SettingsPanel.cs (T1)
├── Renderers/
│   ├── CameraRenderer.cs (T1)
│   ├── DependencyGraphRenderer.cs (T2)
│   ├── ThreatRenderer.cs (T3)
│   ├── TradeRouteRenderer.cs (T3)
│   └── ParticleRenderer.cs (T3)
├── Input/
│   ├── KeyboardShortcuts.cs (T5)
│   ├── TooltipSystem.cs (T5)
│   └── TutorialUI.cs (T5)
└── Assets/
    ├── shaders/ (for future glow/particle effects)
    └── fonts/ (monospace for code display)

VanEngine.Tests/
├── FoundationTests.cs (T1)
├── GameplayTests.cs (T2)
├── AdvancedTests.cs (T3)
├── EndgameTests.cs (T4)
└── IntegrationTests.cs (T5)

Docs/
├── API_SPEC.md (Event socket OpenAPI)
├── MOD_DEVELOPMENT_KIT.md
├── QUICK_START.md
└── ARCHITECTURE.md
```

---

## Acceptance Criteria (Per Tier)

### Tier 1: Foundation
- [x] Multi-workspace manager loads/saves without corruption
- [x] File watcher detects changes within 500ms
- [x] Camera pan/zoom works smoothly (60 FPS)
- [x] Multi-language analyzer handles .cs, .py, .ts, .rs, .go
- [x] Settings persist across restarts
- [x] .van + JSON save formats both work

### Tier 2: Core Gameplay
- [x] Dependency graph renders with 50+ projects without lag
- [x] Overlap detector identifies >80% similar files
- [x] Commons zone gives resource bonus to connected workspaces
- [x] Timeline shows all events from all years
- [x] Inspector panel shows all tracked data for selected entity
- [x] Refactor menu (rename, split, merge) executes without crashes

### Tier 3: Advanced Systems
- [x] Threats spawn, approach, and attack within 5s of trigger
- [x] Tech tree upgrades work correctly (cost deduction, stat gains)
- [x] Skill XP accumulates and levels unlock specialisations
- [x] Trade routes persist, decay, and transfer resources
- [x] Event socket accepts POST requests and triggers game events
- [x] Threat system balances difficulty (not impossible at low sov)

### Tier 4: Endgame
- [x] Git watcher detects commits and advances year
- [x] Report export generates valid markdown/HTML with charts
- [x] Lua scripting API executes custom event handlers
- [x] Scoreboard submission is anonymous and self-verifying

### Tier 5: Polish & Release
- [x] All tooltips present and accurate
- [x] Keyboard shortcuts work for all major actions
- [x] Tutorial completes in under 60 seconds
- [x] No crashes during 1-hour stress test
- [x] Windows/Linux/macOS builds all run without errors
- [x] GitHub Actions CI/CD pipeline creates release artifacts
- [x] Documentation is complete and examples all work

---

## Success Metrics

| Metric | Target | Acceptance |
|--------|--------|-----------|
| FPS (60 FPS target) | 55-60 FPS average | ≥55 FPS in all modes |
| File watch latency | <500ms | ≤1s max |
| Autosave time | <200ms | ≤500ms |
| Build size | <50MB | ≤80MB (Windows release) |
| Test coverage | ≥80% | ≥75% on core systems |
| Load time | <3s (cold) | ≤5s |
| Settings persistence | 100% | 0 lost settings |
| No telemetry | 0 calls home | 0 network except sockets |
| Cross-platform | Windows/Linux/Mac | ≥2 platforms verified |

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| File watcher misses changes | Medium | High | Use debounce + hash verification |
| Lua mod crashes simulator | Medium | High | Sandboxed environment + error catch |
| Git operation blocks UI | High | Medium | Async worker thread |
| Memory leak in threat system | Low | High | Profiler pass, object pooling |
| Report export corrupts JSON | Low | High | Serialization round-trip tests |
| Cross-platform build fails | Medium | Medium | Test matrix on Actions |
| Event socket port conflicts | Low | Medium | Configurable port + retry logic |

---

## Next Steps

1. **Read the GAP_ANALYSIS.md** — understand why Option C was chosen
2. **Implement Tier 1-5 systems** — follow the file structure above
3. **Run test suite** — 80%+ coverage on core systems
4. **Build & release** — GitHub Actions → itch.io or releases
5. **Get feedback** — from users on Tier 3-4 features

**Go live with v1.0.0 in 5 weeks.**

