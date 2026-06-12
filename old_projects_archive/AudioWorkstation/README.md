# Audio Workstation

A beautiful, responsive PySide6 desktop application for AI-powered music remixing, voice cloning, and music video creation.

![Audio Workstation](screenshots/main.png)

## Features

### 🎵 Core Capabilities
- **Audio/Video Import**: Import audio or video files and automatically extract stems
- **AI Stem Separation**: Powered by Demucs - separate vocals, drums, bass, and other instruments
- **Lyrics Extraction**: Automatic timestamped lyrics extraction using OpenAI Whisper
- **Remix Studio**: Mix vocals from one song with beats from another in real-time
- **Voice Training Data Prep**: Prepare clean datasets for voice cloning with time estimates
- **Music Video Generator**: Create music videos from audio and images with lyric-synced timing

### 🎨 User Interface
- Modern dark theme with premium feel
- Three-state workflow: Import → Studio → Remix
- Sidebar library browser for easy navigation
- Real-time audio preview with multiple players
- Responsive design that stays smooth during processing

## Installation

### Prerequisites
- Windows 10/11 (primary support)
- Python 3.10 or higher
- NVIDIA GPU with CUDA support (recommended for faster processing)

### Quick Install
1. Run `install.bat` - this will:
   - Create a virtual environment
   - Install all dependencies with CUDA support
   - Set up PyTorch with CUDA 12.1

2. Activate the virtual environment:
   ```batch
   venv\Scripts\activate.bat
   ```

3. Run the application:
   ```batch
   python main.py
   ```

## Building Standalone Executable

Run `build.bat` to create a single `.exe` file:
- Output: `dist\AudioWorkstation.exe`
- Includes all dependencies
- No installation required for end users

## Usage

### 1. Import & Process
- Enter Artist Name and Song Name
- Click "Import & Process" and select an audio or video file
- The app will:
  - Extract audio from video (if applicable)
  - Sample video frames to `videoImages/` folder
  - Separate stems using Demucs (vocals, instrumental, drums, bass, other)
  - Extract timestamped lyrics using Whisper
  - Save everything to `Library/{ArtistName}/{SongName}/`

### 2. Studio Mode
- View three players:
  - **Player A**: Original full track
  - **Player B**: Vocals stem (with "Change Vocals" button)
  - **Player C**: Beat/Instrumental stem (with "Change Beat" button)
- Click "Change Vocals" or "Change Beat" to browse and select stems from your library
- Click "Prepare Training Data & Estimate" to prepare voice cloning dataset

### 3. Remix Mode
- Automatically enters when vocals and beat come from different songs
- **Player D**: Live combined preview of the remix
- Adjust volumes with sliders:
  - Vocal Volume
  - Beat Volume
  - Master Volume
- Click "Generate Music Video" to create a video from images and lyrics
- Click "Save Remix" to export the final mix

## Project Structure

```
AudioWorkstation/
├── main.py                 # Application entry point
├── ui/                     # UI widgets and components
│   ├── __init__.py
│   ├── main_window.py     # Main window with QStackedWidget
│   ├── import_widget.py   # Import state UI
│   ├── studio_widget.py   # Studio state UI
│   └── remix_widget.py    # Remix state UI
├── core/                   # Business logic
│   ├── __init__.py
│   ├── demucs_processor.py    # Stem separation
│   ├── whisper_processor.py   # Lyrics extraction
│   ├── video_generator.py     # Music video creation
│   └── audio_mixer.py         # Real-time audio mixing
├── utils/                  # Utilities
│   ├── __init__.py
│   ├── file_manager.py    # Library file management
│   ├── training_estimator.py  # Voice training time estimates
│   └── audio_slicer.py    # Vocal slicing for training
├── Library/                # User's music library (created at runtime)
│   └── {ArtistName}/
│       └── {SongName}/
│           ├── stems/
│           ├── trainingData/
│           ├── videoImages/
│           ├── remixes/
│           └── lyrics.json
├── requirements.txt
├── install.bat
├── build.bat
└── README.md
```

## Technical Details

### Dependencies
- **PySide6**: Modern Qt-based GUI framework
- **Demucs**: State-of-the-art source separation
- **OpenAI Whisper**: Accurate speech recognition and transcription
- **MoviePy**: Video editing and composition
- **PyTorch**: Deep learning backend with CUDA support
- **Pydub**: Audio manipulation and processing

### Architecture
- **Threading**: All heavy processing runs on QThread to keep GUI responsive
- **Signals/Slots**: Qt signals for progress updates and state changes
- **Dynamic Paths**: No hardcoded paths - all file operations use dynamic library structure
- **Error Handling**: Comprehensive error handling with user-friendly messages

## License

This project is provided as-is for educational and personal use.

## Credits

- Demucs by Facebook Research
- OpenAI Whisper
- PySide6 by The Qt Company
- MoviePy community

---

**Note**: This application requires significant computational resources, especially for stem separation and video generation. An NVIDIA GPU with CUDA support is highly recommended for optimal performance.
