"""Import state widget."""

from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QProgressBar, QTextEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget


class ImportWidget(QWidget):
    """Widget for importing and processing audio/video files."""
    
    import_requested = Signal(str, str, Path)  # artist_name, song_name, file_path
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.current_file_path = None
    
    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Import & Process")
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # Media player section
        player_layout = QVBoxLayout()
        
        # Video widget (for video playback)
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(400)
        player_layout.addWidget(self.video_widget)
        
        # Media player
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        
        # Player controls
        controls_layout = QHBoxLayout()
        self.play_button = QPushButton("▶ Play")
        self.play_button.clicked.connect(self.toggle_playback)
        controls_layout.addWidget(self.play_button)
        controls_layout.addStretch()
        player_layout.addLayout(controls_layout)
        
        layout.addLayout(player_layout)
        
        # Form fields
        form_layout = QVBoxLayout()
        
        # Artist name
        artist_layout = QHBoxLayout()
        artist_layout.addWidget(QLabel("Artist Name:"))
        self.artist_input = QLineEdit()
        self.artist_input.setPlaceholderText("Enter artist name")
        artist_layout.addWidget(self.artist_input)
        form_layout.addLayout(artist_layout)
        
        # Song name
        song_layout = QHBoxLayout()
        song_layout.addWidget(QLabel("Song Name:"))
        self.song_input = QLineEdit()
        self.song_input.setPlaceholderText("Enter song name")
        song_layout.addWidget(self.song_input)
        form_layout.addLayout(song_layout)
        
        layout.addLayout(form_layout)
        
        # Import button
        self.import_button = QPushButton("Import & Process")
        self.import_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.import_button.clicked.connect(self.on_import_clicked)
        layout.addWidget(self.import_button)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status text
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(150)
        self.status_text.setReadOnly(True)
        self.status_text.setPlaceholderText("Status messages will appear here...")
        layout.addWidget(self.status_text)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def toggle_playback(self):
        """Toggle media playback."""
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.play_button.setText("▶ Play")
        else:
            self.media_player.play()
            self.play_button.setText("⏸ Pause")
    
    def on_import_clicked(self):
        """Handle import button click."""
        artist_name = self.artist_input.text().strip()
        song_name = self.song_input.text().strip()
        
        if not artist_name or not song_name:
            self.add_status("Please enter both artist name and song name.")
            return
        
        # Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Audio or Video File",
            "",
            "Media Files (*.mp3 *.wav *.mp4 *.avi *.mov *.mkv);;All Files (*)"
        )
        
        if file_path:
            self.current_file_path = Path(file_path)
            self.import_requested.emit(artist_name, song_name, self.current_file_path)
    
    def load_media(self, file_path: Path):
        """Load media file into player."""
        self.current_file_path = file_path
        self.media_player.setSource(str(file_path))
        self.play_button.setEnabled(True)
    
    def add_status(self, message: str):
        """Add a status message."""
        self.status_text.append(message)
    
    def set_progress(self, visible: bool, value: int = 0, maximum: int = 100):
        """Set progress bar visibility and value."""
        self.progress_bar.setVisible(visible)
        self.progress_bar.setValue(value)
        self.progress_bar.setMaximum(maximum)
    
    def set_processing(self, processing: bool):
        """Enable/disable UI during processing."""
        self.import_button.setEnabled(not processing)
        self.artist_input.setEnabled(not processing)
        self.song_input.setEnabled(not processing)
