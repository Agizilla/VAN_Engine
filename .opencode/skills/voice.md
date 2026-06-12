---
description: Text-to-speech using local StyleTTS2 voice model (Amelia1) or Windows SAPI
---

# Voice TTS Skill

Speak text aloud using the configured TTS engine.

## Usage

### From the voice server (port 8888):
```powershell
# Health check
curl.exe -s http://localhost:8888/health

# Speak with auto engine selection
Invoke-RestMethod -Uri 'http://localhost:8888/notify' -Method Post -ContentType 'application/json' -Body '{"message":"Hello world","voice_id":"auto","voice_enabled":"true"}'

# Speak with local StyleTTS2 engine (Amelia1 model)
Invoke-RestMethod -Uri 'http://localhost:8888/notify' -Method Post -ContentType 'application/json' -Body '{"message":"Hello world","voice_id":"local","voice_enabled":"true"}'

# Speak with Windows SAPI only
Invoke-RestMethod -Uri 'http://localhost:8888/notify' -Method Post -ContentType 'application/json' -Body '{"message":"Hello world","voice_id":"sapi","voice_enabled":"true"}'
```

### Direct CLI:
```powershell
node voice-notify.mjs "Hello world" auto
node voice-notify.mjs "Hello world" local
node voice-notify.mjs "Hello world" sapi
```

### Voice IDs:
- `auto` - Try local → ElevenLabs → SAPI (default)
- `local` or `styletts2` - StyleTTS2 Amelia1 model
- `sapi` - Windows built-in SAPI
- `elevenlabs` - ElevenLabs cloud TTS (requires API key)

## Architecture

```
voice-server.mjs (port 8888)  ←  curl/Invoke-RestMethod
  ├── local  →  tts_local.py  →  StyleTTS2 (Amelia1_ft model)  →  speakers
  ├── elevenlabs → ElevenLabs API (optional, needs key)  →  speakers
  └── sapi   →  Windows System.Speech  →  speakers

voice-notify.mjs (direct CLI, same engine selection)
```

## Setup

Run the setup script to install Python dependencies and download model utilities:

```powershell
python tools\setup_tts.py
```

Or manually:

```powershell
# Install Python deps
pip install numpy soundfile onnxruntime scipy

# Clone StyleTTS2 repo
git clone https://github.com/yl4579/StyleTTS2.git

# Install PyTorch (CPU)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```
