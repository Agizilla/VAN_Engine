"""Demucs stem separation processor.

Note: The Demucs API may vary between versions. If you encounter import errors,
you may need to adjust the imports or use an alternative approach such as:
- Using torchaudio's HDEMUCS_HIGH_MUSDB_PLUS pipeline
- Using demucs via subprocess call
- Using demucs.separate() function directly

Current implementation uses demucs.pretrained.get_model() which should work
with demucs >= 4.0.0.
"""

import os
from pathlib import Path
from typing import Dict, Optional
from PySide6.QtCore import QThread, Signal
import torch
import torchaudio
try:
    from demucs.pretrained import get_model
    from demucs.audio import convert_audio, save_audio
    DEMUCS_AVAILABLE = True
except ImportError:
    DEMUCS_AVAILABLE = False
import soundfile as sf
import numpy as np


class DemucsProcessor(QThread):
    """Thread for running Demucs stem separation."""
    
    progress = Signal(str)  # Progress message
    finished = Signal(dict)  # Dict of stem_name -> path
    error = Signal(str)  # Error message
    
    def __init__(self, input_path: Path, output_dir: Path):
        super().__init__()
        self.input_path = Path(input_path)
        self.output_dir = Path(output_dir)
        self._cancelled = False
    
    def cancel(self):
        """Cancel the processing."""
        self._cancelled = True
    
    def run(self):
        """Run the stem separation."""
        try:
            if not DEMUCS_AVAILABLE:
                self.error.emit("Demucs library not available. Please install: pip install demucs")
                return
            
            self.progress.emit("Initializing Demucs model...")
            
            # Load model
            model = get_model("htdemucs")
            model.eval()
            
            if self._cancelled:
                return
            
            self.progress.emit("Loading audio file...")
            
            # Load audio
            wav, sr = torchaudio.load(str(self.input_path))
            wav = convert_audio(wav, sr, model.sample_rate, model.chin)
            
            if self._cancelled:
                return
            
            self.progress.emit("Separating stems (this may take a few minutes)...")
            
            # Separate
            with torch.no_grad():
                ref, wav = wav.mean(0), wav - wav.mean(0)
                sources = model(wav[None])[0]
                sources = sources * ref.std() + ref.mean()
            
            if self._cancelled:
                return
            
            # Demucs returns: [drums, bass, other, vocals]
            stems = {
                "drums": sources[0].cpu().numpy(),
                "bass": sources[1].cpu().numpy(),
                "other": sources[2].cpu().numpy(),
                "vocals": sources[3].cpu().numpy()
            }
            
            # Save stems
            self.progress.emit("Saving stems...")
            stem_paths = {}
            
            # Ensure output directory exists
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save individual stems
            for stem_name, audio_data in stems.items():
                if self._cancelled:
                    return
                
                stem_path = self.output_dir / f"{stem_name}.wav"
                save_audio(audio_data, str(stem_path), model.sample_rate)
                stem_paths[stem_name] = stem_path
            
            # Create instrumental (drums + bass + other combined)
            self.progress.emit("Creating instrumental mix...")
            instrumental = stems["drums"] + stems["bass"] + stems["other"]
            instrumental_path = self.output_dir / "instrumental.wav"
            save_audio(instrumental, str(instrumental_path), model.sample_rate)
            stem_paths["instrumental"] = instrumental_path
            
            # Also create "beat" alias (same as instrumental)
            beat_path = self.output_dir / "beat.wav"
            save_audio(instrumental, str(beat_path), model.sample_rate)
            stem_paths["beat"] = beat_path
            
            self.progress.emit("Stem separation complete!")
            self.finished.emit(stem_paths)
            
        except Exception as e:
            import traceback
            self.error.emit(f"Demucs processing error: {str(e)}\n{traceback.format_exc()}")
