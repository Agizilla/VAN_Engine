"""Training time estimation for voice cloning."""

import os
from pathlib import Path
from typing import Dict, Optional
import json


def get_training_estimate(
    artist_name: str,
    song_name: str,
    lyrics_data: Optional[list] = None
) -> Dict[str, any]:
    """
    Estimate training time and dataset size for voice cloning.
    
    Args:
        artist_name: Artist name
        song_name: Song name
        lyrics_data: Optional lyrics data (will load from file if not provided)
    
    Returns:
        Dictionary with:
        - total_duration: Total vocal duration in seconds
        - estimated_slices: Number of slices that will be created
        - estimated_training_time: Estimated training time in minutes
        - dataset_size_mb: Estimated dataset size in MB
    """
    from utils.file_manager import FileManager
    
    # Load lyrics if not provided
    if lyrics_data is None:
        lyrics_data = FileManager.load_lyrics(artist_name, song_name)
    
    if not lyrics_data:
        return {
            "total_duration": 0.0,
            "estimated_slices": 0,
            "estimated_training_time": 0.0,
            "dataset_size_mb": 0.0,
            "error": "No lyrics data available"
        }
    
    # Calculate total vocal duration from lyrics timestamps
    total_duration = 0.0
    for entry in lyrics_data:
        if isinstance(entry, dict):
            start = entry.get("start", 0.0)
            end = entry.get("end", start)
            duration = end - start
            total_duration += duration
    
    # Estimate slices: aim for 2-5 second slices with 0.5s overlap
    # This gives us more training data
    slice_length = 3.0  # seconds
    overlap = 0.5  # seconds
    step = slice_length - overlap
    
    if total_duration > 0:
        estimated_slices = int((total_duration - slice_length) / step) + 1
        estimated_slices = max(1, estimated_slices)  # At least 1 slice
    else:
        estimated_slices = 0
    
    # Estimate training time
    # Rough estimate: ~1 minute per 10 seconds of audio for basic training
    # This is a conservative estimate for lightweight training
    base_time_per_second = 0.1  # minutes per second of audio
    estimated_training_time = total_duration * base_time_per_second
    
    # Minimum training time
    if estimated_training_time < 5.0:
        estimated_training_time = 5.0
    
    # Estimate dataset size
    # Assuming 16kHz mono WAV, ~192KB per second
    bytes_per_second = 192 * 1024
    dataset_size_mb = (estimated_slices * slice_length * bytes_per_second) / (1024 * 1024)
    
    return {
        "total_duration": round(total_duration, 2),
        "estimated_slices": estimated_slices,
        "estimated_training_time": round(estimated_training_time, 1),
        "dataset_size_mb": round(dataset_size_mb, 2),
        "error": None
    }
