@echo off
REM Launch Audio Transcriber UI (Gradio)
echo Starting Audio Transcriber UI...
echo Open http://127.0.0.1:7860 in your browser.
py "%~dp0transcribe\transcribe_ui.py"
