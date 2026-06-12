---
name: AudioSkill
description: Master Audio Skill — stem separation, transcription, voice cloning/cloning/training, Piper TTS, MIDI/music theory, lyric engine, mixing/remixing, audio DSP, noise cancellation, music video generation. USE WHEN audio, sound, music, speech, transcription, voice cloning, TTS, synthesize, remix, separate stems, noise cancel, lyrics, MIDI, melody, beat, vocal, podcast, recording, mix, master.
how_to: Invoke via IPC `audio:*` or directly from Python `from master_skills.audioSkill import AudioSkill`
version: 1.0.0
mergedProjects: 31
countPublicMethods: 107
countLineNumbers: 1520
---

# AudioSkill

Master audio skill aggregating 31 projects. Use the AudioSkill class for any audio operation.

## Capabilities (22)

| Capability | Methods | Description |
|---|---|---|
| Stem Separation | `separate_stems`, `separate_vocals` | Demucs-based 4-stem separation |
| Transcription | `transcribe` | Whisper-based speech-to-text |
| Voice Cloning | `clone_voice`, `train_clone` | ECAPA-TDNN speaker embedding |
| TTS | `synthesize`, `synthesize_batch`, `list_voices` | Piper TTS inference |
| MIDI | `midi_to_notes`, `notes_to_midi`, `midi_info` | MIDI parsing and conversion |
| Music Theory | `analyze_chord`, `key_detection`, `bpm_detect` | Key, chord, BPM analysis |
| Lyrics | `generate_lyrics`, `align_lyrics` | Lyric generation and alignment |
| Mixing | `mix_stems`, `remix`, `apply_effect` | Stem mixing and effects |
| Music Video | `generate_music_video`, `visualize_audio` | Audio visualization to video |
| DSP | `apply_eq`, `compress`, `reverb`, `delay` | Audio DSP effects |
| Noise Cancel | `reduce_noise`, `remove_silence` | Noise and silence removal |
| Batch | `batch_process` | Batch audio processing |
| Info | `get_capabilities`, `list_models`, `get_meta` | Introspection |

## Usage

```python
from master_skills.audioSkill import AudioSkill

skill = AudioSkill()
stems = skill.separate_stems(Path('song.mp3'))
text = skill.transcribe(Path('vocals.wav'))
skill.synthesize('Hello world', Path('model.onnx'), Path('output.wav'))
skill.remix(Path('track.mp3'), Path('remix.wav'), style='club')
```

## IPC Channels

- `audio:transcribe` — Transcribe audio file
- `audio:separate-stems` — Separate audio into stems
- `audio:synthesize` — Text-to-speech synthesis
- `audio:analyze` — Audio analysis (BPM, key, etc.)
- `audio:clone-voice` — Clone a voice from sample
- `audio:remix` — Remix audio tracks
- `audio:info` — Get skill metadata
