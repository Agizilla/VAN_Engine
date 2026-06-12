---
name: VideoSkill
description: Master Video Skill — Haar cascade face/eye detection, blink detection (EAR), talking avatar mouth tracking, frame extraction, video trim/concat, yt-dlp download, GIF creation, video effects (sepia, grayscale, edge, invert, pixelate, blur, cartoon, glitch). USE WHEN video, face detection, blink detection, talking avatar, trim video, concat video, download video, create GIF, video effects, frame extraction, webcam capture, screen record.
how_to: Invoke via IPC `video:*` or directly from Python `from master_skills.videoSkill import VideoSkill`
version: 1.0.0
mergedProjects: 5
countPublicMethods: 60
countLineNumbers: 912
---

# VideoSkill

Master video skill aggregating 5 projects. Use the VideoSkill class for any video operation.

## Capabilities (15)

| Capability | Methods | Description |
|---|---|---|
| Face Detection | `detect_faces_in_video`, `detect_eyes` | Haar cascade face/eye detection |
| Blink Detection | `detect_blinks` | EAR-based blink detection |
| Avatar | `animate_avatar_mouth` | MediaPipe mouth tracking |
| Frame Extraction | `extract_frames`, `extract_frame_at` | Frame extraction from video |
| Trimming | `trim_video`, `split_video` | Video trimming and splitting |
| Concatenation | `concat_videos` | Video concatenation |
| Download | `download_video`, `download_audio` | yt-dlp download |
| GIF | `make_gif`, `optimize_gif` | GIF creation and optimization |
| Music Video | `create_music_video` | Audio-driven video generation |
| Effects | `apply_effect` | Sepia, grayscale, edge, invert, pixelate, blur, cartoon, glitch |
| Speed | `change_speed` | Video speed adjustment |
| Webcam | `capture_webcam`, `record_webcam` | Webcam capture |
| Audio | `add_audio_to_video`, `extract_audio` | Audio track management |
| Scene Detection | `detect_scenes` | Scene change detection |
| Info | `get_capabilities`, `get_meta` | Introspection |

## Usage

```python
from master_skills.videoSkill import VideoSkill

skill = VideoSkill()
faces = skill.detect_faces_in_video(Path('video.mp4'))
skill.trim_video(Path('video.mp4'), start=10, end=30, output=Path('clip.mp4'))
skill.make_gif(Path('video.mp4'), output=Path('out.gif'))
skill.apply_effect(Path('video.mp4'), effect='sepia', output=Path('sepia.mp4'))
```

## IPC Channels

- `video:detect-faces` — Detect faces in video
- `video:trim` — Trim video
- `video:concat` — Concatenate videos
- `video:gif` — Create GIF from video
- `video:download` — Download video
- `video:effects` — Apply video effects
- `video:info` — Get skill metadata
