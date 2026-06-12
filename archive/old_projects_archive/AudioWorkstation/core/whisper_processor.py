"""Whisper lyrics extraction processor."""

import os
from pathlib import Path
from typing import List, Dict, Optional
from PySide6.QtCore import QThread, Signal
import whisper


class WhisperProcessor(QThread):
    """Thread for running Whisper transcription."""
    
    progress = Signal(str)  # Progress message
    finished = Signal(list)  # List of dicts with start, end, text
    error = Signal(str)  # Error message
    
    def __init__(self, audio_path: Path, model_size: str = "base"):
        super().__init__()
        self.audio_path = Path(audio_path)
        self.model_size = model_size
        self._cancelled = False
    
    def cancel(self):
        """Cancel the processing."""
        self._cancelled = True
    
    def run(self):
        """Run the transcription."""
        try:
            self.progress.emit(f"Loading Whisper model ({self.model_size})...")
            model = whisper.load_model(self.model_size)
            
            if self._cancelled:
                return
            
            self.progress.emit("Transcribing audio (this may take a few minutes)...")
            result = model.transcribe(
                str(self.audio_path),
                word_timestamps=True,
                language="en"  # Can be made configurable
            )
            
            if self._cancelled:
                return
            
            # Convert to our format: list of dicts with start, end, text
            lyrics_data = []
            for segment in result.get("segments", []):
                lyrics_data.append({
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"].strip()
                })
            
            self.progress.emit("Transcription complete!")
            self.finished.emit(lyrics_data)
            
            # Store lyrics data for later retrieval
            self._lyrics_data = lyrics_data
            
        except Exception as e:
            self.error.emit(f"Whisper processing error: {str(e)}")
