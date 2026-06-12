# VLC_AudioStudio

A WPF audio player application inspired by VLC with advanced audio tools including Demucs audio separation, Piper TTS, and lyrics management.

## Project Structure

```
VLC_AudioStudio/
├── VLC_AudioStudio.csproj          # Project file with NuGet dependencies
├── App.xaml                         # Application resources
├── App.xaml.cs                      # Application code-behind
├── MainWindow.xaml                  # Main UI definition
├── MainWindow.xaml.cs               # Audio playback logic and event handlers
└── Properties/
    └── AssemblyInfo.cs              # Assembly metadata
```

## Requirements

- **.NET 6.0 SDK or later** with Windows Desktop support
- **Visual Studio 2022** (or later) with WPF development tools
- Windows 10/11

## NuGet Dependencies

The project automatically includes:
- **NAudio** (2.2.1) - Audio playback library for MP3, WAV, FLAC, AAC
- **NAudio.Vorbis** (1.5.0) - Ogg Vorbis support

These are defined in the `.csproj` file and will be restored automatically.

## Setup Instructions

### Option 1: Using Visual Studio

1. **Open the solution:**
   - File → Open → Folder → Select the `VLC_AudioStudio` folder
   - Visual Studio will auto-detect and open the project

2. **Restore NuGet packages:**
   - Tools → NuGet Package Manager → Manage NuGet Packages for Solution
   - Or: Right-click project → Restore NuGet Packages
   - Or run in Package Manager Console: `Update-Package -Reinstall`

3. **Build the project:**
   - Build → Build Solution (Ctrl+Shift+B)
   - Output will be in: `bin/Debug/net6.0-windows/`

4. **Run the application:**
   - Press F5 or Debug → Start Debugging
   - Or double-click the `.exe` in the build output folder

### Option 2: Using Command Line

```bash
cd VLC_AudioStudio

# Restore packages
dotnet restore

# Build
dotnet build

# Run
dotnet run
```

## Features

### Audio Playback (Functional)
- ✅ **Open Files**: Support for MP3, WAV, FLAC, AAC, MP4
- ✅ **Playback Controls**: Play, Pause, Stop, Previous, Next
- ✅ **Volume Control**: Volume slider with real-time adjustment
- ✅ **Progress Bar**: Visual feedback with current/total time
- ✅ **Keyboard Shortcuts**: Can be added to button handlers

### Audio Tools (UI Only - Ready for Implementation)

#### 1. **Persona Management**
   - Create and manage voice personas
   - Store persona metadata and settings
   - Load/delete personas from database

#### 2. **Demucs Tools**
   - Audio source separation (vocals, drums, bass, other)
   - Multiple model selection (HTDemucs, Demucs v3, etc.)
   - GPU acceleration option
   - WAV export format

#### 3. **Piper TTS** (Text-to-Speech)
   - Load ONNX models and config files
   - Text synthesis with adjustable parameters
   - Speaking rate and pitch control
   - Training interface for custom voice models

#### 4. **Lyrics Tools**
   - View and edit current track lyrics
   - Generate new lyrics based on persona lexicon
   - Customizable mood, style, and song structure
   - Integration with persona voice settings

## Key Code Components

### MainWindow.xaml.cs - Playback Logic

**Audio Playback:**
- `InitializePlayer()` - Sets up NAudio WaveOutEvent and timer
- `LoadAudioFile()` - Opens file dialog and loads selected file
- `PlayPauseButton_Click()` - Toggle play/pause state
- `StopButton_Click()` - Stop playback and reset position
- `VolumeSlider_ValueChanged()` - Real-time volume adjustment
- `Timer_Tick()` - Updates UI with current playback time and progress

**Audio Tools:**
- `AudioToolsButton_Click()` - Toggles between media viewer and Audio Tools panel

### MainWindow.xaml - UI Definition

**Styles:**
- `ToolbarButtonStyle` - Standard toolbar buttons
- `ControlButtonStyle` - Playback control buttons (orange themed)
- `AudioToolsButtonStyle` - Primary action buttons
- `AudioToolsTabItemStyle` - Tab styling with orange underline on selection

**Sections:**
- Menu bar (File, Edit, View, etc.)
- Toolbar (file operations, view options, Audio Tools button)
- Main content area (media viewer or Audio Tools tabs)
- Progress bar with time display
- Playback controls (volume, play/pause, stop, etc.)

## Building and Running

### Visual Studio
1. Open the project folder as a folder in VS 2022
2. Build → Build Solution
3. Press F5 to run

### Command Line
```bash
dotnet build
dotnet run
```

## Extending the Project

To add functionality to the Audio Tools tabs:

1. **Persona Management**: Connect to a database (SQLite recommended)
2. **Demucs**: Integrate Demucs Python library via IronPython or subprocess calls
3. **Piper TTS**: Use Piper's C# bindings or integrate via subprocess
4. **Lyrics**: Add LyricFind API or local lyrics database

Each tab's UI is ready - just wire up the button click handlers and data bindings.

## Troubleshooting

### NAudio not found
- Run: `dotnet restore`
- Or in Visual Studio: Tools → NuGet Package Manager → Manage NuGet Packages for Solution → Restore

### Windows Media Player codec issues
- NAudio relies on Windows built-in codecs
- For MP3 support, ensure Windows Media Feature Pack is installed
- For FLAC, may need additional libraries

### Build fails on .NET version
- Ensure you have .NET 6.0 or later SDK installed
- Check: `dotnet --version`
- Download from: https://dotnet.microsoft.com/download

## License

This project is provided as-is for educational and development purposes.

## Next Steps

1. Test audio playback with MP3/WAV files
2. Implement Audio Tools tab functionality
3. Add database for persona storage
4. Integrate Demucs, Piper TTS APIs
5. Add playlist functionality
6. Implement keyboard shortcuts
