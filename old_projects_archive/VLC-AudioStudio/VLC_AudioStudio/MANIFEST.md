# VLC_AudioStudio - Project Manifest & Architecture

## 📦 Complete File List

```
VLC_AudioStudio/
│
├── VLC_AudioStudio.csproj          [Project Configuration File]
│   └── Defines build settings, target framework (.NET 6.0), and NuGet dependencies
│       Dependencies: NAudio 2.2.1, NAudio.Vorbis 1.5.0
│
├── App.xaml                         [Application Resources]
│   └── Root XAML for the WPF application
│       Defines: Application entry point and global resources
│
├── App.xaml.cs                      [Application Code-Behind]
│   └── Application startup logic
│       Contains: Standard WPF app initialization
│
├── MainWindow.xaml                  [UI Definition - 700+ lines]
│   └── Complete user interface layout and styling
│       Contains:
│       - Menu bar (File, Edit, View, Playback, Tools, Help)
│       - Toolbar (file operations, Audio Tools button)
│       - Main content area (media viewer or Audio Tools tabs)
│       - Progress bar with time display
│       - Playback controls (volume, play/pause, stop, prev/next)
│       - Audio Tools tabbed interface:
│         * Persona Management tab
│         * Demucs Tools tab
│         * Piper TTS tab
│         * Lyrics Tools tab
│       - Resource definitions (brushes, styles, templates)
│
├── MainWindow.xaml.cs               [Main Logic - Audio Playback]
│   └── Audio playback functionality and event handlers
│       Contains:
│       - NAudio initialization (WaveOutEvent, AudioFileReader)
│       - File open dialog
│       - Play/Pause/Stop logic
│       - Volume control
│       - Progress tracking and UI updates
│       - Audio Tools panel toggle
│       - Time formatting
│       - Resource cleanup on close
│
├── Properties/
│   └── AssemblyInfo.cs              [Assembly Metadata]
│       Contains: Version, title, company info
│
├── README.md                        [Full Documentation]
│   └── Comprehensive guide including:
│       - Project overview
│       - Requirements and setup
│       - Feature list
│       - Code components explanation
│       - Build and run instructions
│       - Troubleshooting guide
│       - Extending the project
│
├── QUICKSTART.md                    [5-Minute Setup Guide]
│   └── Step-by-step quick start including:
│       - Opening in Visual Studio
│       - Restoring packages
│       - Building and running
│       - Testing playback
│       - Common issues and fixes
│
├── .gitignore                       [Git Configuration]
│   └── Excludes build output, temporary files, IDE settings
│
└── MANIFEST.md                      [This File]
    └── Complete file listing and architecture overview
```

## 🏗️ Architecture Overview

### Layers

```
┌─────────────────────────────────────────┐
│          UI Layer (XAML)                │
│  - MainWindow.xaml                      │
│  - Styles, brushes, controls            │
│  - Data binding (where used)            │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│    Code-Behind & Event Handlers         │
│  - MainWindow.xaml.cs                   │
│  - Button click events                  │
│  - Timer updates                        │
│  - UI state management                  │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      Audio Engine (NAudio)              │
│  - WaveOutEvent (playback device)       │
│  - AudioFileReader (file loading)       │
│  - Supports: MP3, WAV, FLAC, AAC        │
└─────────────────────────────────────────┘
```

### Data Flow - Playback

```
User clicks "Open" 
    ↓
OpenFileDialog opens
    ↓
User selects file (e.g., song.mp3)
    ↓
LoadAudioFile() called
    ↓
AudioFileReader loads file
    ↓
WaveOutEvent initializes
    ↓
UI updates (track name, total time)
    ↓
User clicks Play
    ↓
PlayPauseButton_Click() called
    ↓
WaveOutEvent.Play()
    ↓
Timer.Start() begins
    ↓
Timer_Tick() fires every 500ms
    ↓
Updates: current time, progress bar
    ↓
Song finishes (or user clicks Stop)
    ↓
StopButton_Click() called
    ↓
Reset playback state
```

## 🎨 UI Components

### Main Sections

1. **Menu Bar** (32px height)
   - File, Edit, View, Playback, Tools, Help
   - Currently non-functional (ready for implementation)

2. **Toolbar** (48px height)
   - Open File button
   - Open Directory button
   - Open Network Stream button
   - Fullscreen/Playlist buttons
   - Loop/Shuffle buttons
   - Effects button
   - **Audio Tools button** (toggles Audio Tools panel)
   - Current track label
   - Visual feedback with emoji icons

3. **Main Content Area** (flexible)
   - Media Viewer: Shows "♫" icon when no audio loaded
   - Audio Tools Panel: Tabbed interface with 4 tabs
   - Toggle between them with Audio Tools button

4. **Progress Bar** (auto)
   - Visual progress indicator (orange)
   - Current time / Total time display
   - Ready for click-to-seek (not yet implemented)

5. **Playback Controls** (64px height)
   - Volume icon + Volume slider
   - Previous button (with icon ⏮️)
   - **Play/Pause button** (▶️/⏸️ - toggles)
   - **Stop button** (⏹️)
   - Next button (with icon ⏭️)
   - Speed, Subtitles, Audio Track buttons
   - All styled in VLC orange (#FF9500)

### Audio Tools Tabs

Each tab contains a scrollable panel with controls:

#### Tab 1: Persona Management
- Create new persona (name + description)
- Load/Delete buttons
- List of existing personas

#### Tab 2: Demucs Tools
- Model selection dropdown (HTDemucs variants)
- Stem selection checkboxes (Vocals, Drums, Bass, Other)
- GPU acceleration toggle
- WAV export toggle
- Split Audio button
- Status display

#### Tab 3: Piper TTS
- ONNX model file picker
- Config file picker
- Text input area
- Speaking rate slider
- Pitch slider
- Training section (audio file + lyrics)
- Generate Speech button

#### Tab 4: Lyrics Tools
- Left panel: Lyrics editor (view/edit current track)
- Right panel: Lyrics generator
  - Persona lexicon selector
  - Topic/theme input
  - Mood/style dropdowns
  - Song structure checkboxes
  - Lines per section slider
  - Generate button

## 🎯 Key Classes & Methods

### MainWindow.cs

| Method | Purpose |
|--------|---------|
| `InitializePlayer()` | Creates WaveOutEvent and timer |
| `AttachEventHandlers()` | Wires up all button click events |
| `OpenFileButton_Click()` | Opens file dialog |
| `LoadAudioFile()` | Loads file into NAudio |
| `PlayPauseButton_Click()` | Toggle play/pause state |
| `StopButton_Click()` | Stop and reset playback |
| `VolumeSlider_ValueChanged()` | Real-time volume adjustment |
| `Timer_Tick()` | Update UI every 500ms |
| `AudioToolsButton_Click()` | Toggle Audio Tools panel |
| `FormatTime()` | Convert TimeSpan to MM:SS |
| `OnClosed()` | Clean up resources on exit |

### Fields

| Field | Type | Purpose |
|-------|------|---------|
| `_wavePlayer` | IWavePlayer | NAudio playback device |
| `_audioFileReader` | AudioFileReader | Loaded audio file |
| `_timer` | DispatcherTimer | UI update timer |
| `_currentFilePath` | string | Path to loaded file |
| `_isPlaying` | bool | Playback state flag |

## 🛠️ Technologies Used

| Technology | Version | Purpose |
|------------|---------|---------|
| .NET | 6.0+ | Framework |
| WPF | Windows Desktop | UI framework |
| NAudio | 2.2.1 | Audio playback |
| NAudio.Vorbis | 1.5.0 | Ogg support |
| C# | 9.0+ | Programming language |
| XAML | W3C standard | UI markup |

## 📊 Build Configuration

**Project File**: VLC_AudioStudio.csproj

```xml
<PropertyGroup>
  <OutputType>WinExe</OutputType>
  <TargetFramework>net6.0-windows</TargetFramework>
  <UseWPF>true</UseWPF>
</PropertyGroup>
```

**NuGet Packages**:
- NAudio 2.2.1 (Audio playback)
- NAudio.Vorbis 1.5.0 (Ogg Vorbis codec)

**Supported Audio Formats**:
- MP3 (via Windows Media Feature Pack)
- WAV (PCM, ADPCM)
- FLAC (via NAudio plugin)
- AAC (via Windows Media Feature Pack)

## 🔄 State Management

### Playback States

```
┌─────────────────┐
│   No File       │ ← Initial state
│   Loaded        │
└────────┬────────┘
         │ LoadAudioFile()
         ↓
┌─────────────────┐
│   File Loaded   │ ← Ready to play
│   Stopped       │
└────────┬────────┘
         │ Play()
         ↓
┌─────────────────┐
│   Playing       │ ← Timer updates UI
│   In Progress   │
└────────┬────────┘
         │ Pause() or end reached
         ↓
┌─────────────────┐
│   File Loaded   │
│   Paused        │
└─────────────────┘
```

## ✨ Features at a Glance

### Functional (Working Now)
✅ Audio file loading (MP3, WAV, etc.)
✅ Play / Pause / Stop
✅ Volume control
✅ Progress tracking
✅ Time display
✅ Audio Tools toggle

### UI Ready (Need Implementation)
⏳ Persona Management
⏳ Demucs Tools
⏳ Piper TTS
⏳ Lyrics Tools
⏳ Playlist (Next/Previous)
⏳ Menu actions
⏳ Seek on progress click

## 📝 Code Statistics

| File | Lines | Purpose |
|------|-------|---------|
| MainWindow.xaml | ~710 | UI definition + styles |
| MainWindow.xaml.cs | ~195 | Audio logic + handlers |
| App.xaml | ~5 | App resources |
| App.xaml.cs | ~13 | App startup |
| VLC_AudioStudio.csproj | ~15 | Project config |
| AssemblyInfo.cs | ~45 | Assembly metadata |
| **Total** | **~985** | **Complete project** |

## 🚀 Quick Reference

**To run**: Press F5 in Visual Studio or `dotnet run`
**To build**: Ctrl+Shift+B or `dotnet build`
**To debug**: F5 → breakpoints work in MainWindow.xaml.cs
**To extend**: Add button click handlers in MainWindow.xaml.cs

---

**Project Created**: 2024
**Target Framework**: .NET 6.0 Windows Desktop
**Status**: Fully functional audio player with Audio Tools UI skeleton
