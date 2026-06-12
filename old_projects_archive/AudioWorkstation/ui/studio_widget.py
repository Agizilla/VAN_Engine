"""Studio state widget."""

from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QMessageBox
)
from PySide6.QtCore import Signal
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput


class AudioPlayer(QWidget):
    """Reusable audio player widget."""
    
    def __init__(self, title: str):
        super().__init__()
        self.title = title
        self.init_ui()
    
    def init_ui(self):
        """Initialize the player UI."""
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel(self.title)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Media player
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        
        # Controls
        controls_layout = QHBoxLayout()
        self.play_button = QPushButton("▶ Play")
        self.play_button.clicked.connect(self.toggle_playback)
        controls_layout.addWidget(self.play_button)
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        self.setLayout(layout)
    
    def toggle_playback(self):
        """Toggle playback."""
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.play_button.setText("▶ Play")
        else:
            self.media_player.play()
            self.play_button.setText("⏸ Pause")
    
    def load_file(self, file_path: Path):
        """Load audio file."""
        if file_path and file_path.exists():
            self.media_player.setSource(str(file_path))
            self.play_button.setEnabled(True)
        else:
            self.play_button.setEnabled(False)
    
    def stop(self):
        """Stop playback."""
        self.media_player.stop()
        self.play_button.setText("▶ Play")


class StudioWidget(QWidget):
    """Widget for studio mode with three players."""
    
    vocals_changed = Signal(str, str)  # artist_name, song_name
    beat_changed = Signal(str, str)    # artist_name, song_name
    training_requested = Signal(str, str)  # artist_name, song_name
    
    def __init__(self):
        super().__init__()
        self.current_artist = None
        self.current_song = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Studio")
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # Three players side by side
        players_layout = QHBoxLayout()
        
        # Player A: Original
        self.player_a = AudioPlayer("Original Track")
        players_layout.addWidget(self.player_a)
        
        # Player B: Vocals
        vocals_layout = QVBoxLayout()
        self.player_b = AudioPlayer("Vocals")
        vocals_layout.addWidget(self.player_b)
        
        self.change_vocals_btn = QPushButton("Change Vocals")
        self.change_vocals_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        self.change_vocals_btn.clicked.connect(self.on_change_vocals)
        vocals_layout.addWidget(self.change_vocals_btn)
        vocals_widget = QWidget()
        vocals_widget.setLayout(vocals_layout)
        players_layout.addWidget(vocals_widget)
        
        # Player C: Beat
        beat_layout = QVBoxLayout()
        self.player_c = AudioPlayer("Beat/Instrumental")
        beat_layout.addWidget(self.player_c)
        
        self.change_beat_btn = QPushButton("Change Beat")
        self.change_beat_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
        """)
        self.change_beat_btn.clicked.connect(self.on_change_beat)
        beat_layout.addWidget(self.change_beat_btn)
        beat_widget = QWidget()
        beat_widget.setLayout(beat_layout)
        players_layout.addWidget(beat_widget)
        
        layout.addLayout(players_layout)
        
        # Training button
        training_layout = QHBoxLayout()
        training_layout.addStretch()
        self.training_btn = QPushButton("Prepare Training Data & Estimate")
        self.training_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #7b1fa2;
            }
        """)
        self.training_btn.clicked.connect(self.on_training_requested)
        training_layout.addWidget(self.training_btn)
        training_layout.addStretch()
        layout.addLayout(training_layout)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def load_song(self, artist_name: str, song_name: str):
        """Load a song into the studio."""
        from utils.file_manager import FileManager
        
        self.current_artist = artist_name
        self.current_song = song_name
        
        song_path = FileManager.get_song_path(artist_name, song_name)
        
        # Load original (if available, use first audio file found)
        # For now, we'll load the first stem as original
        stems = FileManager.get_all_stems(artist_name, song_name)
        if stems:
            # Try to find original or use vocals as placeholder
            original_path = stems.get("vocals") or list(stems.values())[0]
            self.player_a.load_file(original_path)
        
        # Load vocals
        vocals_path = FileManager.get_stem_path(artist_name, song_name, "vocals")
        self.player_b.load_file(vocals_path)
        
        # Load beat/instrumental
        beat_path = FileManager.get_stem_path(artist_name, song_name, "beat")
        if not beat_path.exists():
            beat_path = FileManager.get_stem_path(artist_name, song_name, "instrumental")
        self.player_c.load_file(beat_path)
    
    def on_change_vocals(self):
        """Open dialog to select vocals from library."""
        from ui.stem_browser import StemBrowser
        from utils.file_manager import FileManager
        
        dialog = StemBrowser(self, stem_type="vocals")
        if dialog.exec():
            artist, song = dialog.get_selection()
            if artist and song:
                vocals_path = FileManager.get_stem_path(artist, song, "vocals")
                if vocals_path.exists():
                    self.player_b.load_file(vocals_path)
                    self.vocals_changed.emit(artist, song)
    
    def on_change_beat(self):
        """Open dialog to select beat from library."""
        from ui.stem_browser import StemBrowser
        from utils.file_manager import FileManager
        
        dialog = StemBrowser(self, stem_type="beat")
        if dialog.exec():
            artist, song = dialog.get_selection()
            if artist and song:
                beat_path = FileManager.get_stem_path(artist, song, "beat")
                if not beat_path.exists():
                    beat_path = FileManager.get_stem_path(artist, song, "instrumental")
                if beat_path.exists():
                    self.player_c.load_file(beat_path)
                    self.beat_changed.emit(artist, song)
    
    def on_training_requested(self):
        """Handle training data preparation request."""
        if not self.current_artist or not self.current_song:
            QMessageBox.warning(self, "No Song Selected", "Please load a song first.")
            return
        self.training_requested.emit(self.current_artist, self.current_song)
