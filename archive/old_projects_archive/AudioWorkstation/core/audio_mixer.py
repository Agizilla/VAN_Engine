"""Real-time audio mixing utilities."""

from pathlib import Path
from pydub import AudioSegment
from typing import Optional


def mix_audio(
    vocals_path: Path,
    beat_path: Path,
    output_path: Path,
    vocal_volume: float = 0.0,  # dB adjustment
    beat_volume: float = 0.0,   # dB adjustment
    master_volume: float = 0.0  # dB adjustment
) -> Path:
    """
    Mix vocals and beat with volume adjustments.
    
    Args:
        vocals_path: Path to vocals audio file
        beat_path: Path to beat/instrumental audio file
        output_path: Path to save mixed audio
        vocal_volume: Volume adjustment for vocals in dB
        beat_volume: Volume adjustment for beat in dB
        master_volume: Master volume adjustment in dB
    
    Returns:
        Path to the output file
    """
    # Load audio files
    vocals = AudioSegment.from_wav(str(vocals_path))
    beat = AudioSegment.from_wav(str(beat_path))
    
    # Adjust volumes
    vocals = vocals + vocal_volume
    beat = beat + beat_volume
    
    # Align lengths (use the longer one)
    max_length = max(len(vocals), len(beat))
    vocals = vocals[:max_length]
    beat = beat[:max_length]
    
    # Mix
    mixed = vocals.overlay(beat)
    
    # Apply master volume
    mixed = mixed + master_volume
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Export
    mixed.export(str(output_path), format="wav")
    
    return output_path
