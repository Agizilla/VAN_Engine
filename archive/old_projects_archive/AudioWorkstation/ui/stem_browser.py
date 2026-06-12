"""Stem browser dialog for selecting stems from library."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QMessageBox
)
from PySide6.QtCore import Qt
from utils.file_manager import FileManager


class StemBrowser(QDialog):
    """Dialog for browsing and selecting stems from the library."""
    
    def __init__(self, parent=None, stem_type="vocals"):
        super().__init__(parent)
        self.stem_type = stem_type
        self.selected_artist = None
        self.selected_song = None
        self.init_ui()
        self.populate_tree()
    
    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel(f"Select {self.stem_type.capitalize()} from Library")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # Tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Artist", "Song"])
        self.tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.tree)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.select_button = QPushButton("Select")
        self.select_button.clicked.connect(self.on_select)
        buttons_layout.addWidget(self.select_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)
        
        self.setWindowTitle(f"Select {self.stem_type.capitalize()}")
        self.resize(600, 400)
    
    def populate_tree(self):
        """Populate the tree with available stems."""
        self.tree.clear()
        
        artists = FileManager.get_all_artists()
        for artist in artists:
            artist_item = QTreeWidgetItem(self.tree, [artist])
            artist_item.setExpanded(True)
            
            songs = FileManager.get_all_songs(artist)
            for song in songs:
                # Check if the required stem exists
                if self.stem_type == "vocals":
                    stem_path = FileManager.get_stem_path(artist, song, "vocals")
                elif self.stem_type == "beat":
                    stem_path = FileManager.get_stem_path(artist, song, "beat")
                    if not stem_path.exists():
                        stem_path = FileManager.get_stem_path(artist, song, "instrumental")
                else:
                    stem_path = FileManager.get_stem_path(artist, song, self.stem_type)
                
                if stem_path.exists():
                    song_item = QTreeWidgetItem(artist_item, [song])
                    song_item.setData(0, Qt.ItemDataRole.UserRole, artist)
                    song_item.setData(1, Qt.ItemDataRole.UserRole, song)
    
    def on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle double-click on item."""
        if item.parent():  # It's a song item
            self.on_select()
    
    def on_select(self):
        """Handle select button click."""
        current_item = self.tree.currentItem()
        if current_item and current_item.parent():  # Song item
            self.selected_artist = current_item.data(0, Qt.ItemDataRole.UserRole)
            self.selected_song = current_item.text(0)
            self.accept()
        else:
            QMessageBox.warning(self, "No Selection", "Please select a song.")
    
    def get_selection(self):
        """Get the selected artist and song."""
        return self.selected_artist, self.selected_song
