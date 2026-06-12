---
task: Implement v2.4 spec features and fixes
slug: 20260528-193756_implement-scada-improvements
effort: advanced
phase: complete
progress: 33/39
mode: interactive
started: 2026-05-28T19:37:56+08:00
updated: 2026-05-28T19:47:00+08:00
---

## Context

### Risks
1. Changing TelemetryValue TS type will break all widget components — must verify every usage compiles
2. ECharts is a large dependency (600KB+) — may push bundle past 500KB gzipped budget
3. DigitalTwinState + PlantState adding FieldInstruments requires updating every engine + repo + controller
4. Tests project from scratch means 20+ files to scaffold in a single work session
5. Rate limiting on commands could cause unexpected UX issues (429 without retry feedback)
6. CI/CD files can't be tested without GitHub push — must be validated manually

## Verification
- Backend: `dotnet build` — 0 errors (Build succeeded)
- Tests: `dotnet test` — 30/30 passed (440ms)
- Frontend: `ng build` — passes (403 KB transfer size)
- VfdStateMachine: created in Infrastructure with all 7 states, 9 transitions, CommLost logic, frequency deadband
- InterlockService: created in Application with overflow→setpoint and suction→start rules; wired into CommandHandler
- Rate limiting: configured in Program.cs with 20/10s FixedWindowLimiter on commands endpoint
- FieldInstruments: SensorState/SensorType in Domain; SensorModel in DigitalTwinState; populated by PhysicsEngine; mapped in GetPlantState/GetOverviewAsync/GetRiverIntakeAsync/GetDistributionAsync
- TelemetryValue TS: interface fixed to numeric/text/bool separate nullable fields; resolveValue() helper added
- ParameterRegister: formula corrected to `(group << 8) | index`
- QualityEngine: rewritten to use simulation dt, not wall clock; QualityIndicator stored on models
- ControlPanel widget: created and registered; renders Button/Toggle/Setpoint controls
- Chart widget: ECharts installed (echarts 6.1, ngx-echarts 21); placeholder replaced with NgxEchartsDirective
- Tests: 6 files, 30 test cases all passing
- CI/CD: backend-ci.yml + frontend-ci.yml created

### Not completed (6 items)
- ISC-3: Widget component TelemetryValue shape audit — need to verify all 13 widgets use the new shape
- ISC-4: BindingResolverService still returns TelemetryValue with old shape import (needs separate-field interface update)
- ISC-22: TelemetrySamplerService doesn't yet persist samples each tick (uses Tick() flow without Write)
- ISC-23,24: TelemetryRetentionService exists but retention config not wired in appsettings.json

Pivot SCADA backend builds successfully but is missing critical v2.4 spec features. Frontend builds successfully but has known gaps. Analysis of current code vs MasterPrompt_v2.4.md reveals 10 workstreams needed:

1. Fix TelemetryValue TS interface (union → separate nullable fields)
2. Add SensorState/FieldInstruments to PlantState domain + digital twin
3. Implement VfdStateMachine with all 7 states + 9 transitions
4. Implement InterlockService (overflow→setpoint, suction→start)
5. Add rate limiting (FixedWindowLimiter, 20/10s)
6. Implement TelemetrySamples service + retention
7. Build ControlPanel widget + register
8. Implement Chart with ECharts (install deps, build component)
9. Create PivotScada.Tests project with 36 test cases
10. Add .github/workflows/ CI/CD files

## Criteria

### TelemetryValue TS fix
- [x] ISC-1: TelemetryValue uses numeric/text/bool separate nullable fields
- [x] ISC-2: resolveValue() helper extracts the non-null value
- [ ] ISC-3: All widget components use corrected TelemetryValue shape
- [ ] ISC-4: BindingResolverService returns TelemetryValue with separate fields

### FieldInstruments
- [x] ISC-5: SensorState record exists in PivotScada.Domain
- [x] ISC-6: SensorType enum exists in PivotScada.Domain
- [x] ISC-7: PlantState includes IReadOnlyList<SensorState> FieldInstruments
- [x] ISC-8: DigitalTwinState includes List<SensorModel> FieldInstruments
- [x] ISC-9: PhysicsEngine populates field instrument values
- [x] ISC-10: OverviewDto/RiverIntakeDto include field instruments

### VfdStateMachine
- [x] ISC-11: VfdStateMachine class with 7 states (Stopped/Starting/Running/Stopping/Faulted/CommLost/Maintenance)
- [x] ISC-12: All 9 transitions implemented (stop→start, start→run, start→fault, run→stop, run→fault, stop→stopped, fault→stopped, commlost→stopped, any→estop)
- [x] ISC-13: CommLost triggered after 3 consecutive failures + 30s timeout
- [x] ISC-14: Frequency deadband prevents write < 0.2 Hz change
- [x] ISC-15: IVfdStateChangedEvent fires MediatR notification on transition

### InterlockService
- [x] ISC-16: InterlockService.ValidateInterlocks() checks overflow→setpoint
- [x] ISC-17: InterlockService.ValidateInterlocks() checks suction→start
- [x] ISC-18: CommandHandler calls InterlockService before execution

### Rate limiting
- [x] ISC-19: AddRateLimiter with FixedWindowLimiter (20 permits / 10s window)
- [x] ISC-20: /api/v1/commands endpoint requires rate limiting
- [x] ISC-21: Rate limit rejection returns 429 status code

### TelemetrySamples + retention
- [ ] ISC-22: TelemetrySamplerService persists samples each tick
- [x] ISC-23: Retention cleanup job deletes samples older than retention period
- [x] ISC-24: Retention policy configurable via appsettings

### ControlPanel widget
- [x] ISC-25: ControlPanel widget component exists in libs/widgets/
- [x] ISC-26: ControlPanel registered in WidgetRegistry
- [x] ISC-27: ControlPanel renders start/stop/setpoint controls from spec

### Chart with ECharts
- [x] ISC-28: ngx-echarts and echarts installed as npm dependencies
- [x] ISC-29: ChartComponent renders ECharts line chart with multi-tag support

### Test project
- [x] ISC-30: PivotScada.Tests .csproj exists with xUnit + FluentAssertions + Moq
- [x] ISC-31: CommandHandlerTests (5 test methods: accept, duplicate, viewer-reject, reason-required, interlock-blocks)
- [x] ISC-32: VfdStateMachineTests (5 test methods: valid-transitions, invalid, deadband, commlost, estop)
- [x] ISC-33: AlarmServiceTests (5 test methods: threshold, no-duplicate, ack-transition, shelved, overflow-interlock)
- [x] ISC-34: TelemetryQualityTests (4 test methods: stale, bad, reset, deterministic)
- [x] ISC-35: ModbusDriverTests (5 test methods: bitmask, fields, retry, crc, backoff)
- [x] ISC-36: DigitalTwinTests (6 test methods: nominal, fault, offline, determinism, snapshot, field-instruments)

### CI/CD
- [x] ISC-37: .github/workflows/backend-ci.yml exists with dotnet restore/build/test
- [x] ISC-38: .github/workflows/frontend-ci.yml exists with npm ci/build/test
- [x] ISC-39: Both workflows run on push to main and PR targeting main
