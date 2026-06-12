# PRD: Clawdia Master Skills — Audio, Image, Video

**Date:** 2026-06-07
**Status:** Complete
**Project:** VAN Engine / ClawDia / ConversationIDE

---

## 1. Goal

Merge all audio, image, and video capabilities scattered across ~47 projects in `C:\Users\User\Documents\` into three unified master skill Python modules, register them as ClawDia skills, and wire them into ConversationIDE at every integration layer.

---

## 2. Spec

### 2.1 Master Skill Files

| File | Lines | Methods | Merged Projects | Location |
|------|-------|---------|----------------|----------|
| `audioSkill.py` | 1520 | 107 | 31 | `ClawDia/src/tools/master_skills/` |
| `imageSkill.py` | 768 | 52 | 11 | `ClawDia/src/tools/master_skills/` |
| `videoSkill.py` | 912 | 60 | 5 | `ClawDia/src/tools/master_skills/` |

### 2.2 Architecture

```
ClawDia/src/tools/master_skills/
├── audioSkill.py      # AudioSkill class — 22 capabilities
├── imageSkill.py      # ImageSkill class — 14 capabilities
└── videoSkill.py      # VideoSkill class — 15 capabilities

ClawDia/src/skills/
├── audio_skills.py    # 14 registered BaseSkill subclasses
├── vision_skills.py   # 10 registered BaseSkill subclasses
└── video_skills.py    # 13 registered BaseSkill subclasses

ConversationIDE/
├── src/main/ipc/
│   ├── audio.ts       # 4 IPC channels
│   ├── image.ts       # 4 IPC channels
│   └── video.ts       # 4 IPC channels
├── src/preload/index.ts          # Bridge exposure
├── src/renderer/types/electron.d.ts  # TypeScript interfaces
├── src/VanEngine.Core/VAN/
│   ├── runtime.py     # VanFunctionRegistry entries
│   └── brain.py       # Component registration
└── .cide/skills/MasterSkills/
    ├── AudioSkill.md
    ├── ImageSkill.md
    ├── VideoSkill.md
    ├── audioSkill.py
    ├── imageSkill.py
    └── videoSkill.py
```

### 2.3 IPC Channels

| Domain | Channel | Params | Description |
|--------|---------|--------|-------------|
| **audio** | `audio:transcribe` | `{filePath}` | Whisper transcription |
| | `audio:separate-stems` | `{filePath}` | Demucs stem separation |
| | `audio:synthesize` | `{text, outputPath}` | Piper TTS |
| | `audio:info` | — | Metadata + capabilities |
| **image** | `image:detect` | `{filePath}` | Face detection |
| | `image:segment` | `{filePath, points?}` | SAM segmentation |
| | `image:ocr` | `{filePath}` | Text extraction |
| | `image:info` | — | Metadata + capabilities |
| **video** | `video:detect-faces` | `{filePath}` | Face detection |
| | `video:trim` | `{filePath, start, end, output?}` | Video trimming |
| | `video:gif` | `{filePath, output?}` | GIF creation |
| | `video:info` | — | Metadata + capabilities |

### 2.4 VAN Engine Registration

- `runtime.py`: 3 `self.Register()` calls — `Audio/MasterAudio`, `Image/MasterImage`, `Video/MasterVideo`
- `brain.py`: `_register_master_skills()` calls `RegisterComponent()` for all 3

---

## 3. Artifacts

### File: `ClawDia/src/tools/master_skills/audioSkill.py`
**Status:** Created ✓
**Description:** Master Audio Skill — 1520 lines, 107 methods, 22 capabilities across stem separation, transcription, voice cloning, TTS, MIDI, music theory, lyrics, mixing, music video, DSP, noise cancellation, batch processing.

### File: `ClawDia/src/tools/master_skills/imageSkill.py`
**Status:** Created ✓
**Description:** Master Image Skill — 768 lines, 52 methods, 14 capabilities across face detection/animation, 3D mesh, SAM segmentation, SD inpainting, face averaging/swapping, OCR, cartoonization, classification.

### File: `ClawDia/src/tools/master_skills/videoSkill.py`
**Status:** Created ✓
**Description:** Master Video Skill — 912 lines, 60 methods, 15 capabilities across face/eye detection, blink/EAR detection, talking avatar mouth, frame extraction, trim/concat, yt-dlp download, GIF, music video, effects (8 types), webcam, scene detection.

### File: `ClawDia/src/skills/audio_skills.py`
**Status:** Created ✓
**Description:** 14 registered skills (transcribe, separate_stems, analyze, voice_clone, synthesize, remix, mix_stems, lyrics, align, music_video, noise_cancel, batch_process, list_models, info). Uses `@register_skill` decorator, delegates to `AudioSkill`.

### File: `ClawDia/src/skills/vision_skills.py`
**Status:** Created ✓
**Description:** 10 registered skills (detect, classify, ocr, segment, inpaint, animate, effects, swap, info, helper). Uses `@register_skill` decorator, delegates to `ImageSkill`.

### File: `ClawDia/src/skills/video_skills.py`
**Status:** Created ✓
**Description:** 13 registered skills (trim, scenes, analyze, concat, download, gif, music_video, effects, speed, avatar, audio_add, webcam, info). Uses `@register_skill` decorator, delegates to `VideoSkill`.

### File: `ConversationIDE/src/main/ipc/audio.ts`
**Status:** Created ✓
**Description:** Electron IPC handler — 4 channels: transcribe, separate-stems, synthesize, info. Invokes Python via `execFile`, parses JSON result.

### File: `ConversationIDE/src/main/ipc/image.ts`
**Status:** Created ✓
**Description:** Electron IPC handler — 4 channels: detect, segment, ocr, info. Invokes Python via `execFile`, parses JSON result.

### File: `ConversationIDE/src/main/ipc/video.ts`
**Status:** Created ✓
**Description:** Electron IPC handler — 4 channels: detect-faces, trim, gif, info. Invokes Python via `execFile`, parses JSON result.

### File: `ConversationIDE/src/preload/index.ts`
**Status:** Modified ✓
**Description:** Added `audio`, `image`, `video` API sections to the preload bridge, exposing IPC channels to the renderer.

### File: `ConversationIDE/src/renderer/types/electron.d.ts`
**Status:** Modified ✓
**Description:** Added `AudioAPI`, `ImageAPI`, `VideoAPI` interfaces and wired them into the `ElectronAPI` interface.

### File: `ConversationIDE/src/main/index.ts`
**Status:** Modified ✓
**Description:** Added imports for `setupAudioHandlers`, `setupImageHandlers`, `setupVideoHandlers` and wired calls in `app.whenReady()`.

### File: `ConversationIDE/src/VanEngine.Core/VAN/runtime.py`
**Status:** Modified ✓
**Description:** Added 3 registered functions: `_master_audio`, `_master_image`, `_master_video` under their respective carriers.

### File: `ConversationIDE/src/VanEngine.Core/VAN/brain.py`
**Status:** Modified ✓
**Description:** Added `_register_master_skills()` method called during init, registering MasterAudio/MasterImage/MasterVideo components.

### File: `ConversationIDE/.cide/skills/MasterSkills/AudioSkill.md`
**Status:** Created ✓
**Description:** PAI SKILL.md definition with USE WHEN patterns, capabilities table, usage examples, IPC channel reference.

### File: `ConversationIDE/.cide/skills/MasterSkills/ImageSkill.md`
**Status:** Created ✓
**Description:** PAI SKILL.md definition with USE WHEN patterns, capabilities table, usage examples, IPC channel reference.

### File: `ConversationIDE/.cide/skills/MasterSkills/VideoSkill.md`
**Status:** Created ✓
**Description:** PAI SKILL.md definition with USE WHEN patterns, capabilities table, usage examples, IPC channel reference.

### File: `ConversationIDE/.cide/skills/skills.html`
**Status:** Modified ✓
**Description:** Added MasterSkills tab with full documentation of all 3 master skills, capability tables, usage examples, metadata.

### File: `ConversationIDE/.cide/skills/Media/SKILL.md`
**Status:** Modified ✓
**Description:** Added routing rows for Audio → AudioSkill.md, Image → ImageSkill.md, Video → VideoSkill.md.

---

## 4. Key Decisions

- **Base selection:** Music Studio (84 files, 1555 KB) for audio; PhotoAnimate (4 files, 57 KB) for image; Video Frame (6 files, 69 KB) for video — chosen by code volume and feature completeness
- **Architecture:** Master skills at `tools/master_skills/` as plain Python classes; registered skills at `skills/` as `BaseSkill` subclasses with `@register_skill` decorator — clean separation of concerns
- **IPC pattern:** Followed existing `meme_forge.ts` pattern — `execFile` invokes inline Python that imports from `tools.master_skills`, prints JSON to stdout
- **No structural changes:** Existing `base.py` (register_skill decorator + BaseSkill ABC) used as-is

---

## 5. Blocked Items

| Issue | Impact | Notes |
|-------|--------|-------|
| StyleTTS2 missing main checkpoint | Voice cloning TTS output is garbage | ONNX export uses random weights; needs `epoch_00000.pth` at root |
| Demucs/SAM/SD models not verified installed | Some capabilities may fail at runtime | Check `pip list` for `demucs`, `segment-anything`, `diffusers` |

---

## 6. Stale Projects Flagged (5+ GB reclaimable)

| Project | Size | Reason |
|---------|------|--------|
| CypherApp | 1.0 GB | Dependencies bundled |
| CypherApp_by_Replit | 363 MB | Likely duplicate |
| OfflineCollaborator | 298 MB | Dead code |
| Pivot | 240 MB | Dead code |
| audio_outputs | 2.2 GB | Generated artifacts |
| audio_input | 289 MB | Raw data, likely stale |
