# Quick Start Guide - VLC_AudioStudio

## 🚀 Get Started in 5 Minutes

### Step 1: Open the Project in Visual Studio

1. Open **Visual Studio 2022**
2. Select **"Open a folder"**
3. Navigate to and select the `VLC_AudioStudio` folder
4. Wait for VS to finish loading (you'll see status at the bottom)

### Step 2: Restore NuGet Packages

The NuGet packages (NAudio) will restore automatically. If not:
- Go to **Tools → NuGet Package Manager → Manage NuGet Packages for Solution**
- Or right-click the project → **Restore NuGet Packages**

### Step 3: Build the Project

- Press **Ctrl+Shift+B** or go to **Build → Build Solution**
- Wait for the build to complete (check Output window)
- You should see: "Build succeeded"

### Step 4: Run the Application

- Press **F5** or **Debug → Start Debugging**
- The audio player window will open

## 🎵 Testing Playback

1. Click the **📁 Open File** button (top-left toolbar)
2. Select an audio file from your computer:
   - **Supported formats**: MP3, WAV, FLAC, AAC
3. Click the **▶️ Play** button in the bottom controls
4. Adjust volume with the **🔊 Volume Slider**
5. Click **⏹️ Stop** to stop playback

## 🛠️ Testing Audio Tools

1. Load an audio file first (see above)
2. Click **Audio Tools** button in the toolbar
3. The main view will switch to show the Audio Tools tabs:
   - **Persona Management**: Create/manage voice personas
   - **Demucs Tools**: Audio source separation controls
   - **Piper TTS**: Text-to-speech interface
   - **Lyrics Tools**: View and generate song lyrics
4. Click **Audio Tools** again to return to the audio viewer

## 📁 File Structure

```
VLC_AudioStudio/
├── VLC_AudioStudio.csproj       ← Project configuration
├── App.xaml                      ← App resources
├── App.xaml.cs                   ← App startup
├── MainWindow.xaml               ← UI definition
├── MainWindow.xaml.cs            ← Audio logic & handlers
├── README.md                      ← Full documentation
├── QUICKSTART.md                 ← This file
├── .gitignore                    ← Git ignore rules
└── Properties/
    └── AssemblyInfo.cs           ← Assembly metadata
```

## ⚡ Common Issues & Fixes

### Build Fails - "SDK not found"
- Check: **Help → About Microsoft Visual Studio** → look for .NET version
- Required: **.NET 6.0 SDK or later**
- Download: https://dotnet.microsoft.com/download

### NAudio not found during build
```
Right-click Project → Restore NuGet Packages
```

### No sound when playing audio
- Check Windows volume is not muted
- Try a different audio file
- Check NAudio is properly installed (should be in obj/Debug/net6.0-windows folder)

### Audio file won't open
- Make sure the file format is supported: MP3, WAV, FLAC, AAC
- MP3 requires Windows Media Feature Pack (usually pre-installed on Win10/11)
- Try with a WAV file first as a test

## 💡 What's Already Working

✅ Open audio files  
✅ Play / Pause / Stop buttons  
✅ Previous / Next buttons (UI ready for playlist)  
✅ Volume control (real-time adjustment)  
✅ Progress bar (with current/total time)  
✅ Audio Tools toggle (shows/hides the tab panel)  

## 🔧 What's Not Wired Up Yet

The following UI elements are ready but need implementation:

- **Persona Management**: Database storage and retrieval
- **Demucs Tools**: Integration with Demucs Python library
- **Piper TTS**: Integration with ONNX models and synthesis
- **Lyrics Tools**: Lyrics database and generation API
- **Next/Previous buttons**: Playlist functionality
- **Menu items**: File menu actions

## 📝 Next Steps

1. **Test playback** with your own audio files
2. **Explore the code** in MainWindow.xaml.cs to understand the structure
3. **Start implementing** Audio Tools features as needed
4. **Add your own features** by wiring up the button handlers

## 🎓 Learning Resources

### Understanding the Code

The playback logic is in **MainWindow.xaml.cs**:

- `LoadAudioFile()` - Loads a file into NAudio
- `PlayPauseButton_Click()` - Handles play/pause toggle
- `Timer_Tick()` - Updates UI during playback
- `AudioToolsButton_Click()` - Toggles Audio Tools panel

### Modifying the UI

All UI is defined in **MainWindow.xaml**:

- Styles define button appearance (colors, hover effects)
- Tab controls in the Audio Tools panel
- Each tool has its own `<TabItem>`

### Adding Functionality

To add features:
1. Find the button in MainWindow.xaml.cs
2. Add your logic to the Click event handler
3. Update the UI with results

## 📞 Debugging Tips

### Enable logging
Add this to your button handlers:
```csharp
System.Diagnostics.Debug.WriteLine("Message here");
```

View in **Debug → Windows → Output** during runtime.

### Check audio device
NAudio uses the default Windows audio output device. To verify:
```csharp
var devices = NAudio.Wave.WaveOutEvent.DeviceCount;
// Should return > 0
```

### Verify file loading
Check the file path and format:
```csharp
string filePath = openFileDialog.FileName;
// filePath should be a valid absolute path
```

## ✨ You're Ready!

You now have a fully functional audio player with:
- Professional VLC-like UI
- Working playback controls
- Audio Tools interface ready for integration
- Clean, documented code

**Happy coding!** 🎉

For more details, see **README.md**
