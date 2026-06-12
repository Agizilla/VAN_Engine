param(
    [string]$Server = "http://127.0.0.1:8001"
)

$learningPayload = @{
    action = "add"
    author = @{
        name = "DeepSeek"
        role = "Senior Architect"
        model = "DeepSeek-R1"
        session_id = "sess_20260612_1430"
    }
    effort = "extended"
    task = "Learnings endpoint UI + shared registry + 20 core insights"
    tags = @("ui", "registry", "memory", "agents", "json-viewer", "face", "audio", "algorithm", "trust", "orchestration")
    learnings = @(
        @{ id = 1; learning = "EssaySkill: 10 visual format renderers as one unified skill is more maintainable than 10 separate endpoints."; source = "this_session"; effort = "extended" }
        @{ id = 2; learning = "SAAS Portal: Client-rendered menu via AJAX is shareable as a static .html - no server-side templates needed."; source = "this_session"; effort = "extended" }
        @{ id = 3; learning = "Preview button: Parse result.html from JSON, render in iframe - reusable pattern across all HTML-returning skills."; source = "this_session"; effort = "standard" }
        @{ id = 4; learning = "Copy HTML button: Clipboard API works inside iframe context when using srcdoc."; source = "this_session"; effort = "standard" }
        @{ id = 5; learning = "JSON tree viewer: Auto-generated collapsible tree from manifest.input_schema is more usable than raw <pre>."; source = "this_session"; effort = "extended" }
        @{ id = 6; learning = "Author + timestamp in learnings registry makes contributions auditable and attributable."; source = "this_session"; effort = "standard" }
        @{ id = 7; learning = "Forge UI: Agent skill selection should use dropdowns (not free text) to avoid typos."; source = "this_session"; effort = "standard" }
        @{ id = 8; learning = "Forge UI: Three-panel layout (agents | preview | activity log) is more usable than split-panel."; source = "this_session"; effort = "extended" }
        @{ id = 9; learning = "Forge UI: Agent cards should be draggable to change execution order (SortableJS)."; source = "this_session"; effort = "extended" }
        @{ id = 10; learning = "Mid-session compaction: Compact after each phase transition, not at the end - prevents context loss."; source = "training"; effort = "deep" }
        @{ id = 11; learning = "Immutable trust layer: Trust score changes should be append-only with SHA256 hashes - no retroactive edits."; source = "training"; effort = "deep" }
        @{ id = 12; learning = "Speculative prompt execution: Pre-compile prompts while waiting for slow dependencies (LLM, TTS, vision)."; source = "training"; effort = "advanced" }
        @{ id = 13; learning = "Voice-triggered pause: 'hold on, I'm thinking' pauses generation but keeps prompt buffer warm."; source = "training"; effort = "extended" }
        @{ id = 14; learning = "12-zone face mesh: Vertex groups mapped by spherical coordinates, not hardcoded indices."; source = "training"; effort = "deep" }
        @{ id = 15; learning = "Face audio calibration: Frequency bands mapped to zone scale/offset for lip-sync without ML."; source = "training"; effort = "advanced" }
        @{ id = 16; learning = "Delete over add: Any fix requiring >5 new lines must first attempt to reduce complexity elsewhere."; source = "training"; effort = "standard" }
        @{ id = 17; learning = "PRD is truth: The PRD is the single source of truth for task quality and criteria - not comments, not memory."; source = "training"; effort = "standard" }
        @{ id = 18; learning = "Test failure returns to RISK - never jump back to BUILD directly. Re-evaluate assumptions first."; source = "training"; effort = "standard" }
        @{ id = 19; learning = "Atomic ISC criteria: Every criterion must pass the splitting test (and/with/all)."; source = "training"; effort = "extended" }
        @{ id = 20; learning = "Emotional voice tagging: Every voice announcement must include an emotion tag ([Curiosity]) from the emotional dictionary."; source = "training"; effort = "standard" }
    )
    adjusted_behaviour = "For skills with nested schemas, use collapsible JSON tree viewer by default. For HTML-heavy skills, serve lightweight shell + AJAX render. For agent orchestration, use dropdowns and draggable cards."
    context = @{
        repo = "VAN_Engine"
        branch = "main"
        session = "2026-06-12_learnings_endpoint"
        trigger = "batch_script"
    }
    references = @("essay_generate UI", "forge UI", "learnings endpoint", "face_audio_calibration", "algorithm v3.8.2")
}

$json = $learningPayload | ConvertTo-Json -Depth 10

Write-Host "Posting to $Server/hooks/learnings ..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$Server/hooks/learnings" -Method Post -Body $json -ContentType "application/json"
    Write-Host "Success!" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 5
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}
