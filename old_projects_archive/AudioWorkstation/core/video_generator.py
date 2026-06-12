"""Music video generator using MoviePy."""

import os
from pathlib import Path
from typing import List, Dict, Optional
from PySide6.QtCore import QThread, Signal
from moviepy.editor import (
    AudioFileClip, ImageClip, CompositeVideoClip,
    concatenate_videoclips
)
from PIL import Image


class VideoGenerator(QThread):
    """Thread for generating music videos."""
    
    progress = Signal(str)  # Progress message
    finished = Signal(Path)  # Path to output video
    error = Signal(str)  # Error message
    
    def __init__(
        self,
        audio_path: Path,
        lyrics_data: List[Dict],
        images_dir: Path,
        output_path: Path,
        duration: Optional[float] = None
    ):
        super().__init__()
        self.audio_path = Path(audio_path)
        self.lyrics_data = lyrics_data
        self.images_dir = Path(images_dir)
        self.output_path = Path(output_path)
        self.duration = duration
        self._cancelled = False
    
    def cancel(self):
        """Cancel the processing."""
        self._cancelled = True
    
    def run(self):
        """Generate the music video."""
        try:
            # Load audio
            self.progress.emit("Loading audio...")
            audio_clip = AudioFileClip(str(self.audio_path))
            video_duration = self.duration or audio_clip.duration
            
            # Get available images
            image_files = sorted(list(self.images_dir.glob("*.png")) + 
                               list(self.images_dir.glob("*.jpg")) +
                               list(self.images_dir.glob("*.jpeg")))
            
            if not image_files:
                self.error.emit("No images found in videoImages directory")
                return
            
            self.progress.emit(f"Found {len(image_files)} images. Creating video clips...")
            
            # Create video clips for each lyric line
            video_clips = []
            image_index = 0
            
            for i, lyric_entry in enumerate(self.lyrics_data):
                if self._cancelled:
                    return
                
                start_time = lyric_entry.get("start", 0.0)
                end_time = lyric_entry.get("end", start_time + 2.0)
                
                # Ensure end_time doesn't exceed video duration
                if end_time > video_duration:
                    end_time = video_duration
                
                if start_time >= video_duration:
                    break
                
                # Select image (cycle through available images)
                image_path = image_files[image_index % len(image_files)]
                image_index += 1
                
                # Create image clip with crossfade
                clip_duration = end_time - start_time
                
                try:
                    img_clip = ImageClip(str(image_path), duration=clip_duration)
                    img_clip = img_clip.set_start(start_time).set_position("center")
                    img_clip = img_clip.resize(height=1080)  # Standard HD height
                    
                    video_clips.append(img_clip)
                except Exception as e:
                    self.progress.emit(f"Warning: Could not load image {image_path}: {e}")
                    continue
            
            if not video_clips:
                self.error.emit("No valid video clips created")
                return
            
            self.progress.emit("Compositing video...")
            
            # Composite all clips
            final_video = CompositeVideoClip(video_clips, size=(1920, 1080))
            final_video = final_video.set_audio(audio_clip)
            final_video = final_video.set_duration(video_duration)
            
            # Ensure output directory exists
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.progress.emit("Rendering video (this may take several minutes)...")
            
            # Render video
            final_video.write_videofile(
                str(self.output_path),
                fps=24,
                codec='libx264',
                audio_codec='aac',
                preset='medium',
                threads=4
            )
            
            # Clean up
            audio_clip.close()
            final_video.close()
            for clip in video_clips:
                clip.close()
            
            self.progress.emit("Video generation complete!")
            self.finished.emit(self.output_path)
            
        except Exception as e:
            self.error.emit(f"Video generation error: {str(e)}")
