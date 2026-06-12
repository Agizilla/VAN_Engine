# VoiceAdapter Studio - Deployment Guide

## Package Contents

You have received the complete VoiceAdapter Studio application. This guide will help you deploy and run it on your system.

## What's Included

```
voiceadapter_studio.tar.gz (32 KB)
├── Core Application Files
│   ├── main.py              - Entry point with auto-install
│   ├── cli.py               - Command-line interface
│   ├── gui.py               - Gradio web interface
│   ├── adapter.py           - Training and inference engine
│   ├── marketplace.py       - Marketplace functionality
│   ├── demo.py              - Interactive demonstration
│   └── test_installation.py - Installation verification
│
├── Documentation
│   ├── README.md           - Comprehensive documentation
│   ├── QUICKSTART.md       - 5-minute quick start guide
│   ├── PROJECT_OVERVIEW.md - Technical architecture
│   ├── TASKS.md            - Development roadmap
│   └── DEPLOYMENT.md       - This file
│
├── Configuration
│   ├── requirements.txt    - Python dependencies
│   ├── LICENSE             - MIT License
│   └── .gitignore          - Git ignore rules
│
└── Directories
    ├── models/             - Base ONNX models (empty)
    ├── adapters/           - Trained adapters (empty)
    ├── outputs/            - Generated audio (empty)
    └── marketplace_data/   - Marketplace catalog (auto-generated)
```

## System Requirements

### Minimum Requirements
- **OS**: Windows 10+, macOS 10.15+, Linux (Ubuntu 20.04+)
- **Python**: 3.8 or higher
- **RAM**: 4 GB
- **Storage**: 1 GB free space
- **Internet**: Required for first-time dependency installation

### Recommended Requirements
- **OS**: Windows 11, macOS 13+, Linux (Ubuntu 22.04+)
- **Python**: 3.10 or higher
- **RAM**: 8 GB
- **Storage**: 5 GB free space (for models and adapters)
- **GPU**: CUDA-capable GPU for Pro mode (optional)

## Installation Steps

### Step 1: Extract the Archive

**On Linux/macOS:**
```bash
tar -xzf voiceadapter_studio.tar.gz
cd voiceadapter_studio
```

**On Windows:**
- Right-click `voiceadapter_studio.tar.gz`
- Select "Extract All..."
- Open the extracted folder in Command Prompt or PowerShell

### Step 2: Verify Python Installation

```bash
python --version
# or
python3 --version
```

If Python is not installed:
- **Windows**: Download from python.org
- **macOS**: `brew install python` or download from python.org
- **Linux**: `sudo apt install python3 python3-pip`

### Step 3: Run the Application

The application will automatically install dependencies on first run:

```bash
python main.py
```

You'll see:
1. Startup banner
2. Dependency check
3. Auto-installation prompt (if needed)
4. Project status display
5. CLI menu

**First-time installation may take 2-5 minutes** depending on your internet speed.

### Step 4: Verify Installation (Optional)

```bash
python test_installation.py
```

This runs a comprehensive test suite that verifies:
- File structure
- Directory structure
- Python dependencies
- Module imports
- Marketplace functionality
- Adapter module functionality

## Running the Application

### Option 1: Command-Line Interface (Default)

```bash
python main.py
```

Navigate using the menu:
- `1` - Train new adapter
- `2` - Apply adapter to generate audio
- `3` - List available adapters
- `4` - Launch web GUI
- `5` - Exit

### Option 2: Web Interface

```bash
python main.py --gui
```

The web interface will open in your default browser at `http://127.0.0.1:7860`

**Three tabs available:**
- **Train**: Upload audio and create adapters
- **Apply**: Generate audio with adapters
- **Marketplace**: Browse and discover adapters

### Option 3: Demo Mode

```bash
python demo.py
```

Interactive demonstrations without requiring audio files or models.

## Quick Start Example

### 1. Create Your First Adapter (Demo)

Since you won't have audio files immediately, try the demo:

```bash
python demo.py
# Select option 1 or 2 to see how it works
```

### 2. When Ready with Real Audio

**Via CLI:**
```bash
python main.py
# Select: 1) Train Adapter
# Enter: your_audio.wav
# Name: MyFirstStyle
# Accept defaults
# Wait for training...
```

**Via GUI:**
```bash
python main.py --gui
# Go to Train tab
# Upload your_audio.wav
# Enter name: MyFirstStyle
# Click "Start Training"
```

### 3. Generate Audio

**Via CLI:**
```bash
python main.py
# Select: 2) Apply Adapter
# Choose: MyFirstStyle
# Enter lyrics: "Testing my voice adapter"
# Wait for generation...
# Output in: outputs/output.wav
```

**Via GUI:**
```bash
python main.py --gui
# Go to Apply tab
# Select adapter: MyFirstStyle
# Enter lyrics: "Testing my voice adapter"
# Click "Generate Audio"
# Play or download result
```

## Command Reference

```bash
# Start CLI (default)
python main.py

# Start web GUI
python main.py --gui

# Show project status
python main.py --status

# Show help
python main.py --help

# Run demo
python demo.py

# Test installation
python test_installation.py
```

## Configuration

### Modes

The application has two operational modes:

**Ordinary Mode (Default)**
- CPU-only processing
- Faster setup, slower training
- Best for: Quick tests, casual users
- Training time: ~5 minutes

**Pro Mode**
- GPU-accelerated (if available)
- More control over parameters
- Best for: Professional use, high-quality results
- Training time: ~2 minutes (with GPU)

Select mode during training or in GUI settings.

### File Locations

```
voiceadapter_studio/
├── adapters/        - Your trained adapters
├── outputs/         - Generated audio files
├── models/          - Base ONNX models (add your own)
└── marketplace_data/- Marketplace catalog
```

## Troubleshooting

### Issue: Dependencies Won't Install

**Solution:**
```bash
# Try manual installation
pip install -r requirements.txt

# Or install individually
pip install gradio torch onnxruntime soundfile librosa numpy scipy tqdm pyyaml pillow
```

### Issue: "Module not found" errors

**Solution:**
```bash
# Verify installation
python test_installation.py

# Check Python path
python -c "import sys; print(sys.path)"

# Reinstall specific package
pip install --upgrade <package-name>
```

### Issue: Out of Memory During Training

**Solution:**
- Use Ordinary mode (lower memory)
- Reduce training epochs
- Close other applications
- Use smaller audio files (<2 minutes)

### Issue: GUI Won't Launch

**Solution:**
```bash
# Check Gradio installation
pip install --upgrade gradio

# Try launching GUI directly
python gui.py

# Check firewall settings (allow port 7860)
```

### Issue: Audio File Not Recognized

**Solution:**
- Convert to WAV format (16-bit, 44.1kHz recommended)
- Use Audacity or FFmpeg for conversion:
  ```bash
  ffmpeg -i input.mp3 -ar 44100 -ac 1 output.wav
  ```

### Issue: CUDA/GPU Not Detected (Pro Mode)

**Solution:**
```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# Install CUDA-enabled PyTorch
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

## Platform-Specific Notes

### Windows
- Use Command Prompt or PowerShell
- May need to install Visual C++ Redistributable
- Add Python to PATH during installation
- Firewall may block Gradio (allow when prompted)

### macOS
- Use Terminal
- Install Xcode Command Line Tools: `xcode-select --install`
- Apple Silicon: PyTorch has native MPS support
- Allow Python in Security & Privacy settings

### Linux
- Install system dependencies:
  ```bash
  sudo apt-get update
  sudo apt-get install python3-pip libsndfile1 ffmpeg
  ```
- For GPU support, install CUDA toolkit
- Use Python 3.10+ for best results

## Performance Tips

### Training
1. Use high-quality audio (clean, minimal noise)
2. Start with Ordinary mode to test
3. Increase epochs for better quality (but slower)
4. Pro mode with GPU is 2-3x faster

### Inference
1. Pre-load adapters for batch processing
2. Use CPU for single generations
3. GPU only beneficial for batch jobs (10+ files)

### Storage
1. Compress old adapters to save space
2. Delete unused output files regularly
3. Base models can be shared across projects

## Security Considerations

### Data Privacy
- All processing is local (no cloud uploads)
- No telemetry or analytics
- Your audio never leaves your device

### Best Practices
- Keep adapters private unless intended for sharing
- Review marketplace adapters before use
- Back up important adapters regularly

## Updating

### Check for Updates
```bash
python main.py --status
# Check TASKS.md for latest version info
```

### Manual Update
1. Download new version
2. Extract to new folder
3. Copy `adapters/` and `outputs/` from old version
4. Run `python main.py`

## Support Resources

### Documentation
- `README.md` - Comprehensive guide
- `QUICKSTART.md` - Quick start tutorial
- `PROJECT_OVERVIEW.md` - Technical details
- `TASKS.md` - Development roadmap

### Getting Help
1. Check troubleshooting section above
2. Run `python main.py --help`
3. Read error messages carefully
4. Check `TASKS.md` for known issues
5. Submit GitHub issue (if applicable)

## Next Steps

After successful installation:

1. ✅ Run `python test_installation.py` to verify setup
2. ✅ Try `python demo.py` to see features
3. ✅ Read `QUICKSTART.md` for tutorials
4. ✅ Start with `python main.py --gui` for easiest experience
5. ✅ Create your first adapter!

## Uninstallation

To remove VoiceAdapter Studio:

```bash
# Remove Python packages
pip uninstall gradio torch onnxruntime soundfile librosa numpy scipy tqdm pyyaml pillow

# Delete project folder
rm -rf voiceadapter_studio/  # Linux/macOS
# or manually delete folder on Windows
```

## License

VoiceAdapter Studio is licensed under the MIT License.
See `LICENSE` file for details.

---

**Version**: 1.0.0  
**Release Date**: February 2026  
**Support**: Check README.md for contact info

**Enjoy creating with VoiceAdapter Studio!** 🎵
