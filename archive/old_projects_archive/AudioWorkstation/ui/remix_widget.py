"""Remix state widget."""

from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QFileDialog, QMessageBox, QLineEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from ui.studio_widget import AudioPlayer


class RemixWidget(QWidget):
    """Widget for remix mode with live preview."""
    
    save_requested = Signal(str, str, Path)  # artist_name, song_name, output_path
    video_requested = Signal(str, str)  # artist_name, song_name
    
    def __init__(self):
        super().__init__()
        self.vocals_artist = None
        self.vocals_song = None
        self.beat_artist = None
        self.beat_song = None
        self.preview_path = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Remix")
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # Info label
        self.info_label = QLabel("Mix vocals and beat from different songs")
        self.info_label.setStyleSheet("font-size: 12px; color: #888; padding: 5px;")
        layout.addWidget(self.info_label)
        
        # Four players layout
        players_layout = QHBoxLayout()
        
        # Player A: Original (vocals source)
        self.player_a = AudioPlayer("Vocals Source")
        players_layout.addWidget(self.player_a)
        
        # Player B: Beat source
        self.player_b = AudioPlayer("Beat Source")
        players_layout.addWidget(self.player_b)
        
        # Player C: Combined preview
        preview_layout = QVBoxLayout()
        self.player_c = AudioPlayer("Live Preview")
        preview_layout.addWidget(self.player_c)
        
        self.update_preview_btn = QPushButton("Update Preview")
        self.update_preview_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.update_preview_btn.clicked.connect(self.update_preview)
        preview_layout.addWidget(self.update_preview_btn)
        
        preview_widget = QWidget()
        preview_widget.setLayout(preview_layout)
        players_layout.addWidget(preview_widget)
        
        layout.addLayout(players_layout)
        
        # Volume controls
        volume_layout = QVBoxLayout()
        volume_title = QLabel("Volume Controls")
        volume_title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        volume_layout.addWidget(volume_title)
        
        # Vocal volume
        vocal_vol_layout = QHBoxLayout()
        vocal_vol_layout.addWidget(QLabel("Vocal Volume:"))
        self.vocal_volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.vocal_volume_slider.setRange(-20, 20)
        self.vocal_volume_slider.setValue(0)
        self.vocal_volume_slider.valueChanged.connect(self.on_volume_changed)
        vocal_vol_layout.addWidget(self.vocal_volume_slider)
        self.vocal_volume_label = QLabel("0 dB")
        self.vocal_volume_label.setMinimumWidth(50)
        vocal_vol_layout.addWidget(self.vocal_volume_label)
        volume_layout.addLayout(vocal_vol_layout)
        
        # Beat volume
        beat_vol_layout = QHBoxLayout()
        beat_vol_layout.addWidget(QLabel("Beat Volume:"))
        self.beat_volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.beat_volume_slider.setRange(-20, 20)
        self.beat_volume_slider.setValue(0)
        self.beat_volume_slider.valueChanged.connect(self.on_volume_changed)
        beat_vol_layout.addWidget(self.beat_volume_slider)
        self.beat_volume_label = QLabel("0 dB")
        self.beat_volume_label.setMinimumWidth(50)
        beat_vol_layout.addWidget(self.beat_volume_label)
        volume_layout.addLayout(beat_vol_layout)
        
        # Master volume
        master_vol_layout = QHBoxLayout()
        master_vol_layout.addWidget(QLabel("Master Volume:"))
        self.master_volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.master_volume_slider.setRange(-20, 20)
        self.master_volume_slider.setValue(0)
        self.master_volume_slider.valueChanged.connect(self.on_volume_changed)
        master_vol_layout.addWidget(self.master_volume_slider)
        self.master_volume_label = QLabel("0 dB")
        self.master_volume_label.setMinimumWidth(50)
        master_vol_layout.addWidget(self.master_volume_label)
        volume_layout.addLayout(master_vol_layout)
        
        layout.addLayout(volume_layout)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        
        self.video_btn = QPushButton("Generate Music Video")
        self.video_btn.setStyleSheet("""
            QPushButton {
                background-color: #E91E63;
                color: white;
                font-weight: bold;
                padding: 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c2185b;
            }
        """)
        self.video_btn.clicked.connect(self.on_generate_video)
        actions_layout.addWidget(self.video_btn)
        
        self.save_btn = QPushButton("Save Remix")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        self.save_btn.clicked.connect(self.on_save_remix)
        actions_layout.addWidget(self.save_btn)
        
        layout.addLayout(actions_layout)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def set_vocals_source(self, artist_name: str, song_name: str):
        """Set the vocals source."""
        from utils.file_manager import FileManager
        
        self.vocals_artist = artist_name
        self.vocals_song = song_name
        
        vocals_path = FileManager.get_stem_path(artist_name, song_name, "vocals")
        self.player_a.load_file(vocals_path)
        
        self.update_info()
    
    def set_beat_source(self, artist_name: str, song_name: str):
        """Set the beat source."""
        from utils.file_manager import FileManager
        
        self.beat_artist = artist_name
        self.beat_song = song_name
        
        beat_path = FileManager.get_stem_path(artist_name, song_name, "beat")
        if not beat_path.exists():
            beat_path = FileManager.get_stem_path(artist_name, song_name, "instrumental")
        self.player_b.load_file(beat_path)
        
        self.update_info()
    
    def update_info(self):
        """Update the info label."""
        if self.vocals_artist and self.beat_artist:
            info = f"Vocals: {self.vocals_artist} - {self.vocals_song} | "
            info += f"Beat: {self.beat_artist} - {self.beat_song}"
            self.info_label.setText(info)
    
    def on_volume_changed(self):
        """Handle volume slider changes."""
        vocal_db = self.vocal_volume_slider.value()
        beat_db = self.beat_volume_slider.value()
        master_db = self.master_volume_slider.value()
        
        self.vocal_volume_label.setText(f"{vocal_db} dB")
        self.beat_volume_label.setText(f"{beat_db} dB")
        self.master_volume_label.setText(f"{master_db} dB")
    
    def update_preview(self):
        """Update the live preview mix."""
        if not self.vocals_artist or not self.beat_artist:
            QMessageBox.warning(self, "Missing Sources", "Please select both vocals and beat sources.")
            return
        
        from utils.file_manager import FileManager
        from core.audio_mixer import mix_audio
        
        # Get paths
        vocals_path = FileManager.get_stem_path(self.vocals_artist, self.vocals_song, "vocals")
        beat_path = FileManager.get_stem_path(self.beat_artist, self.beat_song, "beat")
        if not beat_path.exists():
            beat_path = FileManager.get_stem_path(self.beat_artist, self.beat_song, "instrumental")
        
        if not vocals_path.exists() or not beat_path.exists():
            QMessageBox.warning(self, "Files Not Found", "Could not find vocals or beat files.")
            return
        
        # Create temporary preview file
        import tempfile
        temp_dir = Path(tempfile.gettempdir())
        self.preview_path = temp_dir / "remix_preview.wav"
        
        # Mix audio
        try:
            mix_audio(
                vocals_path,
                beat_path,
                self.preview_path,
                vocal_volume=self.vocal_volume_slider.value(),
                beat_volume=self.beat_volume_slider.value(),
                master_volume=self.master_volume_slider.value()
            )
            self.player_c.load_file(self.preview_path)
            QMessageBox.information(self, "Preview Updated", "Preview mix has been updated.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create preview: {str(e)}")
    
    def on_generate_video(self):
        """Handle music video generation request."""
        if not self.vocals_artist or not self.beat_artist:
            QMessageBox.warning(self, "Missing Sources", "Please select both vocals and beat sources.")
            return
        
        # Use vocals source for video (or could use a combined name)
        self.video_requested.emit(self.vocals_artist, self.vocals_song)
    
    def on_save_remix(self):
        """Handle save remix request."""
        if not self.vocals_artist or not self.beat_artist:
            QMessageBox.warning(self, "Missing Sources", "Please select both vocals and beat sources.")
            return
        
        if not self.preview_path or not self.preview_path.exists():
            QMessageBox.warning(self, "No Preview", "Please update the preview first.")
            return
        
        # Get save location
        from utils.file_manager import FileManager
        
        # Create a remix name
        remix_name = f"{self.vocals_artist}_{self.vocals_song}_x_{self.beat_artist}_{self.beat_song}"
        remixes_dir = FileManager.get_remixes_path(self.vocals_artist, self.vocals_song)
        default_path = remixes_dir / f"{remix_name}.wav"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Remix",
            str(default_path),
            "Audio Files (*.wav *.mp3);;All Files (*)"
        )
        
        if file_path:
            # Copy preview to final location
            import shutil
            shutil.copy2(self.preview_path, file_path)
            QMessageBox.information(self, "Saved", f"Remix saved to {file_path}")
