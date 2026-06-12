"""Audio slicing utilities for voice training dataset preparation."""

import os
from pathlib import Path
from typing import List, Dict, Optional
from pydub import AudioSegment
import json


def slice_vocals_for_training(
    vocals_path: Path,
    lyrics_data: List[Dict],
    output_dir: Path,
    slice_length: float = 3.0,
    overlap: float = 0.5,
    min_slice_length: float = 1.0
) -> List[Path]:
    """
    Slice vocals into training segments based on lyrics timestamps.
    
    Args:
        vocals_path: Path to the vocals WAV file
        lyrics_data: List of dicts with 'start' and 'end' keys
        output_dir: Directory to save slices
        slice_length: Target length of each slice in seconds
        overlap: Overlap between slices in seconds
        min_slice_length: Minimum slice length to keep
    
    Returns:
        List of paths to created slice files
    """
    if not vocals_path.exists():
        raise FileNotFoundError(f"Vocals file not found: {vocals_path}")
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load audio
    audio = AudioSegment.from_wav(str(vocals_path))
    sample_rate = audio.frame_rate
    
    # Create slices
    slices = []
    slice_index = 0
    
    # Process each lyric segment
    for entry in lyrics_data:
        if not isinstance(entry, dict):
            continue
        
        start_time = entry.get("start", 0.0)
        end_time = entry.get("end", start_time)
        
        # Convert to milliseconds
        start_ms = int(start_time * 1000)
        end_ms = int(end_time * 1000)
        
        # Extract segment
        segment = audio[start_ms:end_ms]
        
        # Create overlapping slices from this segment
        segment_duration = len(segment) / 1000.0  # seconds
        
        if segment_duration < min_slice_length:
            continue
        
        # Slice this segment
        step_ms = int((slice_length - overlap) * 1000)
        slice_length_ms = int(slice_length * 1000)
        
        current_start = 0
        while current_start + slice_length_ms <= len(segment):
            slice_audio = segment[current_start:current_start + slice_length_ms]
            
            # Save slice
            slice_filename = f"slice_{slice_index:04d}.wav"
            slice_path = output_dir / slice_filename
            slice_audio.export(str(slice_path), format="wav")
            slices.append(slice_path)
            
            slice_index += 1
            current_start += step_ms
        
        # Handle remaining audio at the end
        remaining = segment[current_start:]
        if len(remaining) / 1000.0 >= min_slice_length:
            slice_filename = f"slice_{slice_index:04d}.wav"
            slice_path = output_dir / slice_filename
            remaining.export(str(slice_path), format="wav")
            slices.append(slice_path)
            slice_index += 1
    
    return slices
