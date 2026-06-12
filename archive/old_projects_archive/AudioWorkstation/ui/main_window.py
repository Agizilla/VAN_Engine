"""Main window with QStackedWidget for three states."""

import os
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QListWidget, QListWidgetItem, QLabel,
    QMessageBox, QProgressDialog, QDialog
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QIcon
from ui.import_widget import ImportWidget
from ui.studio_widget import StudioWidget
from ui.remix_widget import RemixWidget
from core.demucs_processor import DemucsProcessor
from core.whisper_processor import WhisperProcessor
from core.video_generator import VideoGenerator
from utils.file_manager import FileManager
from utils.training_estimator import get_training_estimate
from utils.audio_slicer import slice_vocals_for_training
import shutil
from moviepy.editor import VideoFileClip


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.current_artist = None
        self.current_song = None
        self.vocals_artist = None
        self.vocals_song = None
        self.beat_artist = None
        self.beat_song = None
        self.init_ui()
        self.refresh_library()
    
    def init_ui(self):
        """Initialize the UI."""
        self.setWindowTitle("Audio Workstation")
        self.setMinimumSize(1200, 800)
        
        # Central widget with horizontal layout
        central_widget = QWidget()
        main_layout = QHBoxLayout()
        
        # Sidebar (Library browser)
        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar, 1)  # 1/4 width
        
        # Main content area (StackedWidget)
        self.stacked_widget = QStackedWidget()
        
        # Import widget
        self.import_widget = ImportWidget()
        self.import_widget.import_requested.connect(self.on_import_requested)
        self.stacked_widget.addWidget(self.import_widget)
        
        # Studio widget
        self.studio_widget = StudioWidget()
        self.studio_widget.vocals_changed.connect(self.on_vocals_changed)
        self.studio_widget.beat_changed.connect(self.on_beat_changed)
        self.studio_widget.training_requested.connect(self.on_training_requested)
        self.stacked_widget.addWidget(self.studio_widget)
        
        # Remix widget
        self.remix_widget = RemixWidget()
        self.remix_widget.video_requested.connect(self.on_video_requested)
        self.stacked_widget.addWidget(self.remix_widget)
        
        main_layout.addWidget(self.stacked_widget, 3)  # 3/4 width
        
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # Apply dark theme
        self.apply_dark_theme()
        
        # Start on import screen
        self.stacked_widget.setCurrentIndex(0)
    
    def create_sidebar(self):
        """Create the library sidebar."""
        sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout()
        
        # Title
        title = QLabel("Library")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        sidebar_layout.addWidget(title)
        
        # Search box (placeholder for future)
        # For now, just show list
        
        # Library list
        self.library_list = QListWidget()
        self.library_list.itemDoubleClicked.connect(self.on_library_item_selected)
        sidebar_layout.addWidget(self.library_list)
        
        # Refresh button
        refresh_btn = QLabel("Double-click to open")
        refresh_btn.setStyleSheet("font-size: 10px; color: #888; padding: 5px;")
        sidebar_layout.addWidget(refresh_btn)
        
        sidebar_widget.setLayout(sidebar_layout)
        sidebar_widget.setMaximumWidth(300)
        return sidebar_widget
    
    def apply_dark_theme(self):
        """Apply dark theme to the application."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QListWidget {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
            }
            QListWidgetItem {
                padding: 5px;
            }
            QListWidgetItem:hover {
                background-color: #3d3d3d;
            }
            QListWidgetItem:selected {
                background-color: #0078d4;
            }
            QLineEdit {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 5px;
            }
            QTextEdit {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
            }
            QProgressBar {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
            }
        """)
    
    def refresh_library(self):
        """Refresh the library list."""
        self.library_list.clear()
        
        artists = FileManager.get_all_artists()
        for artist in artists:
            songs = FileManager.get_all_songs(artist)
            for song in songs:
                item_text = f"{artist} - {song}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, (artist, song))
                self.library_list.addItem(item)
    
    def on_library_item_selected(self, item: QListWidgetItem):
        """Handle library item selection."""
        artist, song = item.data(Qt.ItemDataRole.UserRole)
        self.current_artist = artist
        self.current_song = song
        
        # Switch to studio mode
        self.stacked_widget.setCurrentIndex(1)
        self.studio_widget.load_song(artist, song)
    
    def on_import_requested(self, artist_name: str, song_name: str, file_path: Path):
        """Handle import request."""
        self.current_artist = artist_name
        self.current_song = song_name
        
        # Ensure directory structure exists
        song_path = FileManager.ensure_song_structure(artist_name, song_name)
        
        # Load media into player for preview
        self.import_widget.load_media(file_path)
        
        # Check if file is video or audio
        is_video = file_path.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv']
        
        # Create progress dialog
        progress = QProgressDialog("Processing...", "Cancel", 0, 0, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setCancelButton(None)  # Don't allow cancel for now
        progress.show()
        
        # Extract audio if video
        audio_path = file_path
        if is_video:
            self.import_widget.add_status("Extracting audio from video...")
            audio_path = song_path / "audio.wav"
            try:
                video = VideoFileClip(str(file_path))
                video.audio.write_audiofile(str(audio_path), verbose=False, logger=None)
                video.close()
                
                # Sample frames for video images
                self.import_widget.add_status("Sampling video frames...")
                frames_dir = FileManager.get_video_images_path(artist_name, song_name)
                frames_dir.mkdir(parents=True, exist_ok=True)
                
                # Sample every 2 seconds
                video = VideoFileClip(str(file_path))
                duration = video.duration
                frame_count = 0
                for t in range(0, int(duration), 2):
                    frame = video.get_frame(t)
                    from PIL import Image
                    img = Image.fromarray(frame)
                    img.save(frames_dir / f"frame_{frame_count:04d}.jpg")
                    frame_count += 1
                video.close()
                
                self.import_widget.add_status(f"Extracted {frame_count} frames.")
            except Exception as e:
                progress.close()
                QMessageBox.critical(self, "Error", f"Failed to extract audio: {str(e)}")
                return
        else:
            # For audio files, copy to song directory
            final_audio_path = song_path / "audio.wav"
            try:
                shutil.copy2(file_path, final_audio_path)
                audio_path = final_audio_path
            except Exception as e:
                progress.close()
                QMessageBox.critical(self, "Error", f"Failed to copy audio file: {str(e)}")
                return
        
        # Process with Demucs
        self.import_widget.add_status("Starting stem separation...")
        self.import_widget.set_progress(True, 0, 100)
        
        stems_dir = song_path / "stems"
        demucs_processor = DemucsProcessor(audio_path, stems_dir)
        demucs_processor.progress.connect(self.import_widget.add_status)
        demucs_processor.finished.connect(lambda stems: self.on_demucs_finished(artist_name, song_name, audio_path, progress))
        demucs_processor.error.connect(lambda msg: self.on_processing_error(msg, progress))
        demucs_processor.start()
    
    def on_demucs_finished(self, artist_name: str, song_name: str, audio_path: Path, progress: QProgressDialog):
        """Handle Demucs completion."""
        # Process with Whisper
        self.import_widget.add_status("Starting lyrics extraction...")
        
        whisper_processor = WhisperProcessor(audio_path)
        whisper_processor.progress.connect(self.import_widget.add_status)
        whisper_processor.finished.connect(lambda lyrics: self.on_whisper_finished(artist_name, song_name, lyrics, progress))
        whisper_processor.error.connect(lambda msg: self.on_processing_error(msg, progress))
        whisper_processor.start()
    
    def on_whisper_finished(self, artist_name: str, song_name: str, lyrics_data: list, progress: QProgressDialog):
        """Handle Whisper completion."""
        # Save lyrics
        FileManager.save_lyrics(artist_name, song_name, lyrics_data)
        self.import_widget.add_status(f"Saved {len(lyrics_data)} lyric segments.")
        
        progress.close()
        self.import_widget.set_progress(False)
        self.import_widget.add_status("Processing complete! Switching to Studio mode...")
        
        # Refresh library and switch to studio
        self.refresh_library()
        self.current_artist = artist_name
        self.current_song = song_name
        self.stacked_widget.setCurrentIndex(1)
        self.studio_widget.load_song(artist_name, song_name)
        
        QMessageBox.information(self, "Complete", "Song imported and processed successfully!")
    
    def on_processing_error(self, message: str, progress: QProgressDialog):
        """Handle processing errors."""
        progress.close()
        self.import_widget.set_progress(False)
        QMessageBox.critical(self, "Processing Error", message)
    
    def on_vocals_changed(self, artist_name: str, song_name: str):
        """Handle vocals source change."""
        self.vocals_artist = artist_name
        self.vocals_song = song_name
        
        # Check if we should enter remix mode
        if self.beat_artist and (self.vocals_artist != self.beat_artist or self.vocals_song != self.beat_song):
            self.stacked_widget.setCurrentIndex(2)
            self.remix_widget.set_vocals_source(artist_name, song_name)
            if self.beat_artist:
                self.remix_widget.set_beat_source(self.beat_artist, self.beat_song)
    
    def on_beat_changed(self, artist_name: str, song_name: str):
        """Handle beat source change."""
        self.beat_artist = artist_name
        self.beat_song = song_name
        
        # Check if we should enter remix mode
        if self.vocals_artist and (self.vocals_artist != self.beat_artist or self.vocals_song != self.beat_song):
            self.stacked_widget.setCurrentIndex(2)
            self.remix_widget.set_beat_source(artist_name, song_name)
            if self.vocals_artist:
                self.remix_widget.set_vocals_source(self.vocals_artist, self.vocals_song)
    
    def on_training_requested(self, artist_name: str, song_name: str):
        """Handle training data preparation request."""
        from utils.file_manager import FileManager
        
        # Load lyrics
        lyrics_data = FileManager.load_lyrics(artist_name, song_name)
        if not lyrics_data:
            QMessageBox.warning(self, "No Lyrics", "No lyrics data found. Please process the song first.")
            return
        
        # Get estimate
        estimate = get_training_estimate(artist_name, song_name, lyrics_data)
        
        if estimate.get("error"):
            QMessageBox.warning(self, "Error", estimate["error"])
            return
        
        # Show estimate dialog
        msg = f"""Training Data Estimate:

Total Vocal Duration: {estimate['total_duration']:.1f} seconds
Estimated Slices: {estimate['estimated_slices']}
Estimated Training Time: {estimate['estimated_training_time']:.1f} minutes
Estimated Dataset Size: {estimate['dataset_size_mb']:.2f} MB

Would you like to prepare the training dataset now?"""
        
        reply = QMessageBox.question(self, "Training Estimate", msg, 
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            # Prepare dataset
            vocals_path = FileManager.get_stem_path(artist_name, song_name, "vocals")
            if not vocals_path.exists():
                QMessageBox.warning(self, "No Vocals", "Vocals stem not found.")
                return
            
            output_dir = FileManager.get_training_data_path(artist_name, song_name)
            
            progress = QProgressDialog("Preparing training data...", None, 0, 0, self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.show()
            
            try:
                slices = slice_vocals_for_training(vocals_path, lyrics_data, output_dir)
                progress.close()
                QMessageBox.information(self, "Complete", 
                                      f"Training dataset prepared!\n{len(slices)} slices created in:\n{output_dir}")
            except Exception as e:
                progress.close()
                QMessageBox.critical(self, "Error", f"Failed to prepare dataset: {str(e)}")
    
    def on_video_requested(self, artist_name: str, song_name: str):
        """Handle music video generation request."""
        from utils.file_manager import FileManager
        
        # Check if we have a preview mix
        if not self.remix_widget.preview_path or not self.remix_widget.preview_path.exists():
            reply = QMessageBox.question(self, "No Preview", 
                                       "No preview mix found. Would you like to create one first?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.remix_widget.update_preview()
                return
        
        # Get lyrics
        lyrics_data = FileManager.load_lyrics(artist_name, song_name)
        if not lyrics_data:
            QMessageBox.warning(self, "No Lyrics", "No lyrics data found.")
            return
        
        # Get images directory
        images_dir = FileManager.get_video_images_path(artist_name, song_name)
        if not images_dir.exists() or not any(images_dir.glob("*")):
            QMessageBox.warning(self, "No Images", "No images found in videoImages directory.")
            return
        
        # Get output path
        remixes_dir = FileManager.get_remixes_path(artist_name, song_name)
        output_path = remixes_dir / f"{artist_name}_{song_name}_video.mp4"
        
        # Create progress dialog
        progress = QProgressDialog("Generating music video...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()
        
        # Generate video
        video_generator = VideoGenerator(
            self.remix_widget.preview_path,
            lyrics_data,
            images_dir,
            output_path
        )
        video_generator.progress.connect(lambda msg: progress.setLabelText(msg))
        video_generator.finished.connect(lambda path: self.on_video_finished(path, progress))
        video_generator.error.connect(lambda msg: self.on_video_error(msg, progress))
        video_generator.start()
    
    def on_video_finished(self, output_path: Path, progress: QProgressDialog):
        """Handle video generation completion."""
        progress.close()
        QMessageBox.information(self, "Complete", f"Music video generated!\n{output_path}")
    
    def on_video_error(self, message: str, progress: QProgressDialog):
        """Handle video generation errors."""
        progress.close()
        QMessageBox.critical(self, "Error", message)
