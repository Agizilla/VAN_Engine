# Proposed Project Catalog Schema

```json
{
  "catalogVersion": "1.0.0",
  "lastUpdated": "2026-06-07",
  "projects": [
    {
      "id": "music-studio",
      "name": "Music Studio",
      "path": "C:\\Users\\User\\Documents\\!ClaudeSonnet36\\Music Studio",
      "status": "merged",           // merged | active | archived | future | pending
      "category": "audio",          // audio | image | video | text | prd | other
      "fileCount": 227,
      "totalSizeKB": 850992,
      "masterSkill": "audioSkill.py",
      "featuresContributed": [
        "StemSeparation::separate_stems",
        "Transcription::transcribe",
        "MusicTheory::analyze"
      ],
      "sourceFiles": [
        "music_studio.py",
        "stem_remix_tab.py"
      ],
      "description": "Full music production studio with DAW-like interface",
      "discovered": "2026-06-07",
      "tags": ["music", "daw", "production"]
    }
  ],
  "masterSkills": [
    {
      "name": "audioSkill.py",
      "path": "ClawDia/src/tools/master_skills/audioSkill.py",
      "version": "1.0.0",
      "methods": 107,
      "lines": 1520,
      "mergedProjects": 31,
      "capabilities": ["StemSeparation", "Transcription", ...],
      "features": [
        {
          "name": "StemSeparation",
          "methods": ["separate_stems", "separate_vocals"],
          "sourceProjects": [
            {"name": "Music Studio", "files": ["music_studio.py", "demucsInstaller.py"]},
            {"name": "AUDIO_STUDIO", "files": ["main.py"]}
          ],
          "description": "Demucs-based 4-stem separation"
        }
      ]
    }
  ],
  "_comment": "Status values: merged=absorbed into master skill, active=standalone/current, archived=dead, future=planned, pending=waiting"
}
```

---

## Proposed Project Catalog: AUDIO (31 projects, sorted by size)

| # | Project | Files | Size (KB) | Status | Key Files | Master Skill |
|---|---------|-------|-----------|--------|-----------|-------------|
| 1 | Music Studio | 227 | 850,992 | **merged** | music_studio.py, demucsInstaller.py, stem_remix_tab.py | audioSkill.py |
| 2 | AUDIO_STUDIO | 300 | 102,353 | **merged** | (numerous .py) | audioSkill.py |
| 3 | autoRapper / AutoRapper | 67+60 | 74,689+438 | **merged** | main.py, autoBeat.py, vocal_vessel.py | audioSkill.py |
| 4 | Mute | 2,091 | 86,012 | **merged** | audio_processor.py, dream_processor.py | audioSkill.py |
| 5 | VoiceAdapterStudio | 35 | 203 | **merged** | adapter.py, main.py | audioSkill.py |
| 6 | AudioWorkstation | 22 | 8,745 | **merged** | main.py | audioSkill.py |
| 7 | PhoneController | 20 | 135 | **merged** | (audio-related) | audioSkill.py |
| 8 | VirtualDrums | 11 | 1,904 | **merged** | DrumTest.html | audioSkill.py |
| 9 | Song Mixer | 6 | 19,585 | **merged** | song_mixer.py | audioSkill.py |
| 10 | VoiceMash | 20 | 47,223 | **merged** | VoiceMash.py, merge_vids.py | audioSkill.py |
| 11 | LyricalStoryBoard | 7 | 34,013 | **merged** | make_video.py | audioSkill.py |
| 12 | VoiceClone | 3 | 43 | **merged** | voice_cloner_tool.py | audioSkill.py |
| 13 | VoiceHash | 2 | 4 | **merged** | main.py | audioSkill.py |
| 14 | VoicePaperclip | 2 | 6 | **merged** | AraLocal.py | audioSkill.py |
| 15 | AudioToImage | 4 | 12,024 | **merged** | app.py | audioSkill.py |
| 16 | DeepSeekAudioMorph | 91 | 513 | **merged** | (audio morphing) | audioSkill.py |
| 17 | OfflineSongWriter | 35 | 196 | **merged** | (songwriting) | audioSkill.py |
| 18 | LyricToMelodyPlusVoice | 27 | 128 | **merged** | (lyric-to-melody) | audioSkill.py |
| 19 | DirtyTalker (Grok) | 30 | 13,661 | **merged** | app.py | audioSkill.py |
| 20 | GechoShift | 16 | 187 | **merged** | (audio shift) | audioSkill.py |
| 21 | LismaAdapter | 7 | 16,344 | **merged** | Lisma.py | audioSkill.py |
| 22 | Song Style Extractor | 2 | 13 | **merged** | (style extraction) | audioSkill.py |
| 23 | VLC_AudioStudio | 13 | 133 | **merged** | (VLC integration) | audioSkill.py |
| 24 | VLC-Tools | 7 | 56 | **merged** | (VLC tools) | audioSkill.py |
| 25 | VibeVoice | 95 | 417 | **merged** | (voice) | audioSkill.py |
| 26 | labeled_sounds | 15 | 1,376 | **merged** | (sound files) | audioSkill.py |
| 27 | audio_input_30 HipHip | 30 | 295,750 | **raw_data** | (audio files) | audioSkill.py |
| 28 | audio_outputs | 68 | 2,248,445 | **raw_data** | (generated audio) | audioSkill.py |
| 29 | UVR-MDX-NET-Inst_HQ_3 | 8 | 38,352 | **raw_data** | (UVR output) | audioSkill.py |
| 30 | Song Mixer (!Web) | 6 | 19,585 | **merged** | song_mixer.py | audioSkill.py |
| 31 | LARA LOCAL | 15 | 253 | **merged** | voice_v2.py, stt_engine.py | audioSkill.py |

## Proposed Project Catalog: IMAGE (11 projects)

| # | Project | Files | Size (KB) | Status | Key Files | Master Skill |
|---|---------|-------|-----------|--------|-----------|-------------|
| 1 | PhotoAnimate | 264 | 137,182 | **merged** | run.py (PhotoAnimate) | imageSkill.py |
| 2 | faceMeshBuilder | 9 | 42 | **merged** | face_avatar_3d.py | imageSkill.py |
| 3 | AI-Photo-Editing | 12 | 86 | **merged** | app.py, config.json | imageSkill.py |
| 4 | FaceMash | 24 | 23,657 | **merged** | facemash.py, smile.py | imageSkill.py |
| 5 | FaceSwap | 6 | 11,949 | **merged** | face_swap_v*.html | imageSkill.py |
| 6 | ScreenClipOCR | 17 | 110 | **merged** | main.py, config.json | imageSkill.py |
| 7 | WebTextCapture | 25 | 9,173 | **merged** | content.js, tesseract | imageSkill.py |
| 8 | 3D-Character-Pipeline | 26 | 177 | **merged** | main.py | imageSkill.py |
| 9 | IMAGEtoCAD | 43 | 11,732 | **merged** | main.py | imageSkill.py |
| 10 | PersonErasor | 35 | 641 | **merged** | inpainting tools | imageSkill.py |
| 11 | FaceLandmarks | 2 | 3 | **merged** | run.py | imageSkill.py |

## Proposed Project Catalog: VIDEO (5 projects)

| # | Project | Files | Size (KB) | Status | Key Files | Master Skill |
|---|---------|-------|-----------|--------|-----------|-------------|
| 1 | Video Frame | 12 | 22,062 | **merged** | Frame.py, blink_counter_app.py | videoSkill.py |
| 2 | TalkingAvatar | 12 | 21,793 | **merged** | app.py, app2.py–app5.py | videoSkill.py |
| 3 | MovieDirector | 2 | 1,406 | **merged** | (director tools) | videoSkill.py |
| 4 | Video Blink Counter | 0 | 0 | **merged** | (empty project) | videoSkill.py |
| 5 | YoutubeDL GUI | 1 | 5 | **merged** | ytdlp_gui.py | videoSkill.py |

---

## Feature Map: audioSkill.py (107 methods, 22 capability groups)

| Capability | Methods | Source Projects (with file paths) |
|---|---|---|
| **StemSeparation** | `separate_stems`, `separate_vocals`, `save_stems` | Music Studio: `!ClaudeSonnet36/Music Studio/music_studio.py`, `!ClaudeSonnet36/Music Studio/demucsInstaller.py`, `!ClaudeSonnet36/Music Studio/stem_remix_tab.py` |
| **Transcription** | `transcribe`, `batch_transcribe` | Music Studio: `!ClaudeSonnet36/Music Studio/music_studio.py`, `!ClaudeSonnet36/Music Studio/transcript_editor_tab.py`, AUDIO_STUDIO: `ALL-PROJECTS/PROJECTS/AUDIO_STUDIO/main.py` |
| **VoiceAnalysis** | `analyze` | Music Studio, Mute: `!ClaudeSonnet36/Mute/audio_processor.py` |
| **VoiceCloning** | `clone_voice`, `train_voice` | VoiceClone: `!Python Scripts/VoiceClone/voice_cloner_tool.py`, VoiceAdapterStudio: `!ClaudeSonnet36/VoiceAdapterStudio/adapter.py` |
| **VoiceTransformation** | `apply` (VoiceAdapter) | VoiceAdapterStudio: `!ClaudeSonnet36/VoiceAdapterStudio/adapter.py` |
| **PiperTTS** | `synthesize`, `list_models` | PersonaBuilder: `!AntiGravity/PersonaBuilder/build_piper_metadata.py` |
| **VoiceTraining** | `train` (voice clone) | VoiceClone, VoiceAdapterStudio |
| **NoiseCancellation** | `reduce_noise`, `adaptive_filter`, `spectral_gate`, `generate_anti_sound` | Mute: `!ClaudeSonnet36/Mute/audio_processor.py`, Music Studio |
| **MIDIEncoder** | `encode`, `load`, `save`, `quantize` | AUDIO_STUDIO: `ALL-PROJECTS/PROJECTS/AUDIO_STUDIO/`, VirtualDrums: `!Android/VirtualDrums/DrumTest.html` |
| **MusicTheory** | `analyze`, `key_detection`, `bpm_detect`, `get_note` | Music Studio: `!ClaudeSonnet36/Music Studio/music_studio.py`, AUDIO_STUDIO |
| **LyricGeneration** | `generate_lyrics`, `enhance`, `segment`, `train` (lyrics) | autoRapper: `!Codex/AutoRapper/main.py`, `!Codex/AutoRapper/vocal_vessel.py`, OfflineSongWriter: `ALL-PROJECTS/PROJECTS/OfflineSongWriter/` |
| **RhymeScoring** | `score`, `match`, `suggest` | autoRapper: `!Codex/AutoRapper/vocal_vessel.py` |
| **ForcedAlignment** | `align`, `align_lyrics` | Music Studio, Mute |
| **PhonemeMatching** | `match` (phonemes) | autoRapper, Mute |
| **WavToMidi** | `detect` (pitch), `track` (pitch), `save` (midi) | AUDIO_STUDIO, VirtualDrums |
| **DrumGeneration** | `generate` (drum sequence) | VirtualDrums: `!Android/VirtualDrums/DrumTest.html` |
| **AudioEffects** | `apply_eq`, `compress`, `reverb`, `delay`, `flanger`, `chorus` | Music Studio, Song Mixer: `!Web/Song Mixer/song_mixer.py`, AudioWorkstation: `!Cursor/AudioWorkstation/main.py` |
| **RemixPipeline** | `remix`, `mix`, `batch_stem_separate` | Music Studio: `!ClaudeSonnet36/Music Studio/music_studio.py`, Song Mixer, autoRapper: `!Codex/AutoRapper/battle_mix.py` |
| **BatchProcessing** | `process_files`, `batch_stem_separate`, `batch_transcribe` | Music Studio, autoRapper |
| **MusicVideoGeneration** | `generate_music_video`, `generate` (video from audio) | LyricalStoryBoard: `!AI STUDIO/LyricalStoryBoard/make_video.py`, VoiceMash: `!Python Scripts/VoiceMash/VoiceMash.py`, AudioToImage: `!Python Scripts/AudioToImage/app.py` |
| **AudioIO** | `save_stems`, `get_separator`, `get_pitch_tracker` | All audio projects |

## Feature Map: imageSkill.py (52 methods, 14 capability groups)

| Capability | Methods | Source Projects (with file paths) |
|---|---|---|
| **FaceDetection** | `detect_faces`, `extract_face`, `detect` | PhotoAnimate: `ALL-PROJECTS/PROJECTS/PhotoAnimate/run.py`, FaceMash: `!Python Scripts/FaceMash/facemash.py` |
| **FaceLandmarks** | `get_face_landmarks`, `modify_landmarks`, `landmark_detector` | PhotoAnimate, faceMeshBuilder: `!Claude/faceMeshBuilder/face_avatar_3d.py`, FaceLandmarks: `!Python Scripts/FaceLandmarks/run.py` |
| **FaceAnimation** | `animate_face`, `create_animation`, `animator` | PhotoAnimate: `ALL-PROJECTS/PROJECTS/PhotoAnimate/run.py` |
| **FaceMesh3D** | `build_mesh`, `build` (texture atlas) | faceMeshBuilder: `!Claude/faceMeshBuilder/face_avatar_3d.py` |
| **ImageSegmentation** | `segment`, `segment_auto`, `segment_with_points` | AI-Photo-Editing: `ALL-PROJECTS/PROJECTS/AI-Photo-Editing-with-Inpainting/app.py` |
| **Inpainting** | `inpaint`, `fill_background`, `fill_subject`, `replace_background`, `replace_subject` | AI-Photo-Editing, PersonErasor: `ALL-PROJECTS/PROJECTS/PersonErasor/` |
| **ImageWarping** | `warp`, `warp_points`, `compute_warp_map`, `warper` | PhotoAnimate: `ALL-PROJECTS/PROJECTS/PhotoAnimate/run.py` |
| **TextureAtlas** | `build` (atlas) | faceMeshBuilder: `!Claude/faceMeshBuilder/face_avatar_3d.py` |
| **FaceAveraging** | `average_faces`, `add_face`, `get_best_faces`, `calculate_quality` | FaceMash: `!Python Scripts/FaceMash/facemash.py` |
| **FaceSwapping** | `swap` (faces) | FaceSwap: `!Python Scripts/FaceSwap/face_swap_v*.html` |
| **OCR** | `ocr`, `ocr_image`, `extract_from_region` | ScreenClipOCR: `ALL-PROJECTS/PROJECTS/ScreenClipOCR/main.py`, WebTextCapture: `ALL-PROJECTS/PROJECTS/WebTextCapture/content.js` |
| **ScreenCapture** | `capture_screen` | ScreenClipOCR |
| **ImageEffects** | `apply_effect`, `cartoonize`, `sepia`, `sketch`, `oil_paint`, `flip`, `rotate`, `adjust_brightness`, `adjust_contrast` | FaceMash, PhotoAnimate, multiple |
| **Cartoonization** | `cartoonize` | FaceMash: `!Python Scripts/FaceMash/facemash.py` |

## Feature Map: videoSkill.py (60 methods, 15 capability groups)

| Capability | Methods | Source Projects (with file paths) |
|---|---|---|
| **FaceDetection** | `detect_faces_in_video`, `detect_faces_in_frame`, `detect_faces`, `detector` | Video Frame: `!Python Scripts/Video Frame/Face and eye detect using haar cascade.py` |
| **EyeDetection** | `detect_eyes` | Video Frame, Video Blink Counter |
| **BlinkDetection** | `detect_blinks`, `blink`, `eye_aspect_ratio`, `total_blinks` | Video Frame: `!Python Scripts/Video Frame/blink_counter_app.py`, Video Blink Counter |
| **FrameExtraction** | `extract_frames`, `extract_all`, `extract_every_n`, `extract_at_timestamps` | Video Frame: `!Python Scripts/Video Frame/Frame.py` |
| **TalkingAvatar** | `avatar`, `process_avatar`, `detect_mouth_open`, `get_mouth_coords`, `extract_mouth_frames` | TalkingAvatar: `!Python Scripts/TalkingAvatar/app.py` |
| **MouthTracking** | `get_mouth_coords`, `detect_mouth_open` | TalkingAvatar: `!Python Scripts/TalkingAvatar/app*.py` |
| **VideoTrimming** | `trim_video`, `trim` | MovieDirector: `ALL-PROJECTS/PROJECTS/MovieDirector/` |
| **VideoConcat** | `concat_videos`, `concat` | MovieDirector |
| **VideoDownload** | `download_video`, `download`, `get_info` | YoutubeDL GUI: `!Python Scripts/YoutubeDL GUI/ytdlp_gui.py` |
| **GIFCreation** | `make_gif`, `from_images` | Video Frame, TalkingAvatar |
| **MusicVideoGeneration** | `make_music_video`, `with_lyrics` | VoiceMash: `!Python Scripts/VoiceMash/VoiceMash.py`, LyricalStoryBoard |
| **WebcamCapture** | `capture_webcam`, `record_webcam`, `capture_frame`, `read`, `write`, `release` | Video Frame, TalkingAvatar |
| **VideoEffects** | `apply_effect`, `_pixelate`, `apply_to_frame`, `apply_to_video` | MovieDirector, VF: `!Web/VF/index.html` |
| **SpeedChange** | `change_speed`, `speed_change` | MovieDirector |
| **AudioExtraction** | `extract_audio`, `add_audio_to_video` | MovieDirector, VoiceMash |
