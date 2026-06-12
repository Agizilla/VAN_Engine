"""File management utilities for the Library structure."""

import os
import json
from pathlib import Path
from typing import Optional, Dict, List, Tuple


class FileManager:
    """Manages the dynamic Library file structure."""
    
    LIBRARY_ROOT = "./Library"
    
    @staticmethod
    def get_song_path(artist_name: str, song_name: str) -> Path:
        """Get the full path to a song's directory."""
        return Path(FileManager.LIBRARY_ROOT) / artist_name / song_name
    
    @staticmethod
    def ensure_song_structure(artist_name: str, song_name: str) -> Path:
        """Create the full directory structure for a song if it doesn't exist."""
        song_path = FileManager.get_song_path(artist_name, song_name)
        
        # Create all subdirectories
        (song_path / "stems").mkdir(parents=True, exist_ok=True)
        (song_path / "trainingData").mkdir(parents=True, exist_ok=True)
        (song_path / "videoImages").mkdir(parents=True, exist_ok=True)
        (song_path / "remixes").mkdir(parents=True, exist_ok=True)
        
        return song_path
    
    @staticmethod
    def get_stem_path(artist_name: str, song_name: str, stem_name: str) -> Path:
        """Get path to a specific stem file."""
        return FileManager.get_song_path(artist_name, song_name) / "stems" / f"{stem_name}.wav"
    
    @staticmethod
    def get_lyrics_path(artist_name: str, song_name: str) -> Path:
        """Get path to lyrics.json file."""
        return FileManager.get_song_path(artist_name, song_name) / "lyrics.json"
    
    @staticmethod
    def save_lyrics(artist_name: str, song_name: str, lyrics_data: List[Dict]) -> None:
        """Save lyrics data to JSON file."""
        lyrics_path = FileManager.get_lyrics_path(artist_name, song_name)
        with open(lyrics_path, 'w', encoding='utf-8') as f:
            json.dump(lyrics_data, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def load_lyrics(artist_name: str, song_name: str) -> Optional[List[Dict]]:
        """Load lyrics data from JSON file."""
        lyrics_path = FileManager.get_lyrics_path(artist_name, song_name)
        if lyrics_path.exists():
            with open(lyrics_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    @staticmethod
    def get_all_artists() -> List[str]:
        """Get list of all artist names in the library."""
        library_path = Path(FileManager.LIBRARY_ROOT)
        if not library_path.exists():
            return []
        return [d.name for d in library_path.iterdir() if d.is_dir()]
    
    @staticmethod
    def get_all_songs(artist_name: str) -> List[str]:
        """Get list of all song names for an artist."""
        artist_path = Path(FileManager.LIBRARY_ROOT) / artist_name
        if not artist_path.exists():
            return []
        return [d.name for d in artist_path.iterdir() if d.is_dir()]
    
    @staticmethod
    def get_all_stems(artist_name: str, song_name: str) -> Dict[str, Path]:
        """Get all available stems for a song."""
        stems_path = FileManager.get_song_path(artist_name, song_name) / "stems"
        if not stems_path.exists():
            return {}
        
        stems = {}
        for stem_file in stems_path.glob("*.wav"):
            stem_name = stem_file.stem
            stems[stem_name] = stem_file
        
        return stems
    
    @staticmethod
    def get_video_images_path(artist_name: str, song_name: str) -> Path:
        """Get path to videoImages directory."""
        return FileManager.get_song_path(artist_name, song_name) / "videoImages"
    
    @staticmethod
    def get_training_data_path(artist_name: str, song_name: str) -> Path:
        """Get path to trainingData directory."""
        return FileManager.get_song_path(artist_name, song_name) / "trainingData"
    
    @staticmethod
    def get_remixes_path(artist_name: str, song_name: str) -> Path:
        """Get path to remixes directory."""
        return FileManager.get_song_path(artist_name, song_name) / "remixes"
