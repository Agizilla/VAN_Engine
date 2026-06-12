# VoiceAdapter Studio - Quick Start Guide

Get up and running with VoiceAdapter Studio in 5 minutes!

## Prerequisites

- Python 3.8 or higher
- 4 GB RAM (8 GB recommended)
- ~1 GB free disk space

## Installation

### Step 1: Download VoiceAdapter Studio

```bash
# If you have Git
git clone https://github.com/your-repo/voiceadapter-studio.git
cd voiceadapter-studio

# Or download and extract the ZIP file, then:
cd voiceadapter-studio
```

### Step 2: Run First-Time Setup

The application will automatically check and install dependencies:

```bash
python main.py
```

You'll see:
- Dependency check
- Auto-installation of missing packages (if needed)
- Project status from TASKS.md
- CLI menu

**That's it!** You're ready to use VoiceAdapter Studio.

## Quick Tour

### 1. Explore the CLI (Default)

When you run `python main.py`, you'll see a menu:

```
1) Train Adapter      - Create a new voice adapter
2) Apply Adapter      - Generate audio with adapter
3) List Adapters      - View available adapters
4) Launch GUI         - Open Gradio web interface
5) Exit               - Close application
```

**Try option 4** to launch the web GUI!

### 2. Launch the Web GUI

```bash
python main.py --gui
```

Or select option 4 from the CLI menu.

The GUI will open in your browser with three tabs:
- **Train**: Create new adapters
- **Apply**: Generate audio with adapters
- **Marketplace**: Browse and discover adapters

### 3. Run the Demo

Want to see what VoiceAdapter Studio can do without any setup?

```bash
python demo.py
```

This demonstrates:
- Marketplace browsing
- Adapter management
- Training simulation
- Inference simulation

## Your First Adapter

### Option A: Use the CLI

1. Run `python main.py`
2. Select `1) Train Adapter`
3. Follow the prompts:
   - Press Enter for default base model
   - Enter path to your audio file (WAV format)
   - Name your adapter (e.g., "MyStyle")
   - Choose epochs (default: 100)
   - Select mode (ordinary for CPU, pro for GPU)
4. Wait for training to complete
5. Your adapter is saved in `adapters/`

### Option B: Use the GUI

1. Run `python main.py --gui`
2. Go to the **Train** tab
3. Upload your audio file
4. Enter adapter name
5. Adjust settings (optional)
6. Click "Start Training"
7. Download your trained adapter

## Generate Audio

### Using CLI

1. Run `python main.py`
2. Select `2) Apply Adapter`
3. Choose your adapter from the list
4. Optionally add a backing track
5. Enter lyrics
6. Wait for generation
7. Audio saved in `outputs/`

### Using GUI

1. Launch GUI: `python main.py --gui`
2. Go to **Apply** tab
3. Select adapter
4. Upload backing track (optional)
5. Enter lyrics
6. Click "Generate Audio"
7. Play or download the result

## Browse the Marketplace

The marketplace (currently a demo) shows available adapters:

### CLI
```bash
python main.py
# Select option 3 to list adapters
```

### GUI
```bash
python main.py --gui
# Navigate to Marketplace tab
```

Browse by:
- **Genre**: Pop, Rock, Jazz, Hip-Hop, Classical, Electronic
- **Mood**: Energetic, Melancholic, Romantic, Chill
- **Artist Style**: Educational vocal styles

## Tips for Success

### Training
- Use high-quality audio (44.1kHz or higher)
- Minimum 30 seconds of audio
- Clean audio works best (minimal background noise)
- More epochs = better quality (but longer training time)

### Generating Audio
- Clear, well-written lyrics work best
- Add a backing track for better results
- Experiment with different adapters
- Pro mode gives more control

### Performance
- **Ordinary mode**: CPU-only, faster for quick tests
- **Pro mode**: GPU-accelerated (if available), better quality
- Close other apps during training
- Use SSD for faster file I/O

## Troubleshooting

### Dependencies Won't Install
```bash
# Try manual installation
pip install -r requirements.txt

# Or individually
pip install gradio torch onnxruntime soundfile librosa numpy
```

### Module Import Errors
```bash
# Run the installation test
python test_installation.py

# This will diagnose issues
```

### Audio File Issues
- Only WAV files are fully supported
- Convert MP3/FLAC to WAV using:
  - Audacity (free)
  - FFmpeg: `ffmpeg -i input.mp3 output.wav`
  - Online converters

### Out of Memory
- Use Ordinary mode (less memory)
- Reduce epochs
- Use smaller audio files
- Close other applications

### GUI Won't Launch
```bash
# Check if Gradio is installed
pip install gradio

# Try launching directly
python gui.py
```

## Next Steps

1. **Read the full documentation**: See `README.md`
2. **Check the roadmap**: See `TASKS.md`
3. **Explore settings**: Try different modes and parameters
4. **Share adapters**: Export your adapters to share
5. **Join the community**: (GitHub Issues / Discussions)

## Command Reference

```bash
# Start CLI
python main.py

# Start GUI
python main.py --gui

# Run demo
python demo.py

# Check status
python main.py --status

# Test installation
python test_installation.py

# Get help
python main.py --help
```

## File Locations

- **Adapters**: `adapters/*.pth`
- **Generated audio**: `outputs/*.wav`
- **Models**: `models/*.onnx`
- **Marketplace data**: `marketplace_data/`

## Getting Help

1. Check `README.md` for detailed documentation
2. Run `python main.py --help`
3. Check `TASKS.md` for known issues
4. Submit an issue on GitHub
5. Check the FAQ in README.md

## What's Next?

- Create your first adapter
- Try different training modes
- Explore the marketplace
- Generate audio with lyrics
- Share your adapters
- Contribute to the project

**Have fun creating with VoiceAdapter Studio!** 🎵

---

**Version**: 1.0.0  
**Updated**: February 2026
