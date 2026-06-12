# VoiceAdapter Studio

**VoiceAdapter Studio** is a cross-platform desktop application that empowers both ordinary users and professional artists to create, apply, and share voice adapters for music production and voice synthesis.

## Purpose

VoiceAdapter Studio enables you to:
- **Train lightweight voice adapters** from audio samples
- **Apply adapters** to transform vocals with custom styles
- **Share and discover** adapters through a built-in marketplace
- **Work offline** - everything runs locally, no cloud services required

Perfect for music producers, content creators, voice actors, and AI enthusiasts who want full control over their voice synthesis pipeline.

## Features

### Two User Modes
- **Ordinary Mode**: Simple defaults, CPU-only, optimized for quick results
- **Pro Mode**: Full control over training parameters, batch processing, model management

### Core Capabilities
- Train custom voice adapters (≤5 MB each)
- Apply adapters to lyrics with backing tracks
- Browse and manage adapter marketplace
- Cross-platform: Windows, macOS, Linux
- Future-ready for Android deployment

## Quick Start

### Installation

1. Clone or download this repository
2. Run the main script - it will auto-install dependencies:

```bash
python main.py
```

On first run, the app will check `requirements.txt` and install any missing packages automatically.

### System Requirements

- Python 3.8 or higher
- 4 GB RAM minimum (8 GB recommended for Pro mode)
- 1 GB free disk space for models and adapters

## CLI Usage

When you run `main.py`, you'll see the CLI menu:

```
=== VoiceAdapter Studio CLI ===
1) Train Adapter
2) Apply Adapter
3) List Adapters
4) Launch GUI
5) Exit
```

### CLI Examples

#### 1. Train a New Adapter

```bash
Select option: 1
Enter base model path (or press Enter for default): 
Enter input WAV path: /path/to/vocals.wav
Enter adapter name: MyStyle
Enter number of epochs (default 100): 150
Training mode [ordinary/pro] (default: ordinary): pro
```

This creates a new adapter file: `adapters/MyStyle.pth`

#### 2. Apply Adapter to Generate Audio

```bash
Select option: 2
Enter base model path: models/base_model.onnx
Enter adapter path: adapters/MyStyle.pth
Enter backing track WAV: /path/to/beat.wav
Enter lyrics: "This is my custom song with adapted vocals"
Output file (default: output.wav): my_song.wav
```

Generates: `outputs/my_song.wav`

#### 3. List Available Adapters

```bash
Select option: 3

Available Adapters:
- MyStyle.pth (2.3 MB) - Created: 2024-02-27
- Jazz_Smooth.pth (1.8 MB) - Created: 2024-02-26
- Rock_Gritty.pth (3.1 MB) - Created: 2024-02-25
```

#### 4. Launch GUI

```bash
Select option: 4
Launching Gradio GUI...
Running on local URL:  http://127.0.0.1:7860
```

## GUI Launch

Start the Gradio web interface:

```bash
python main.py
# Then select option 4, or run directly:
python gui.py
```

The GUI opens in your default browser with three tabs:

### Train Tab
- Upload base model (ONNX format)
- Upload training audio (WAV)
- Set adapter name and parameters
- Progress bar shows training status
- Download trained adapter

### Apply Tab
- Select base model
- Choose adapter
- Upload backing track
- Enter lyrics
- Generate and download output

### Marketplace Tab
- Browse adapter categories (Genre, Mood, Artist Style)
- Preview adapter details
- Mock "Buy" buttons (payment integration coming soon)
- Search and filter adapters
- View ratings and descriptions

## Adapter Format

VoiceAdapter Studio uses lightweight adapter files:
- **Format**: PyTorch state_dict (.pth)
- **Size**: Typically 1-5 MB per adapter
- **Structure**: Only trainable parameters, no full model weights
- **Loading**: Stacks onto frozen base model at inference time
- **Portability**: Share adapters independently of base models

## Project Self-Management

VoiceAdapter Studio maintains its own development roadmap:

### Tasks.md
The app reads and updates `Tasks.md` on startup to track:
- Feature backlog
- Current development status
- Completed tasks
- Known issues

### Auto-Install
`main.py` automatically:
- Checks `requirements.txt`
- Installs missing dependencies
- Validates installation
- Reports any issues

## Directory Structure

```
voiceadapter_studio/
├── main.py              # Entry point with auto-install
├── cli.py               # Command-line interface
├── gui.py               # Gradio web interface
├── adapter.py           # Adapter training and inference
├── marketplace.py       # Marketplace mock functionality
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── TASKS.md            # Development roadmap
├── models/             # Base ONNX models
├── adapters/           # Trained adapters
├── outputs/            # Generated audio files
└── marketplace_data/   # Marketplace catalog
```

## Portability & Future Android Support

### Current: Pure Python
- No OS-specific system calls
- Works on Windows, macOS, Linux
- Minimal external dependencies

### Future: Android Deployment

The codebase is designed for easy Android porting:

**Option 1: Kivy**
```python
# Future: Replace Gradio with Kivy UI
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
# ... adapter integration remains the same
```

**Option 2: Gradio WebView**
```python
# Future: Embed Gradio in Android WebView
# Use termux or python-for-android
# Gradio server runs locally, native WebView displays UI
```

**Considerations for Android:**
- ONNX Runtime has Android support
- PyTorch Mobile for on-device inference
- Optimize adapter sizes (target <2 MB)
- Use quantization for models
- Background service for long training tasks

See `TASKS.md` for detailed Android migration roadmap.

## Marketplace Mock-up

The current marketplace is a **demonstration/prototype**:

### Available Categories
- **Genre**: Pop, Rock, Jazz, Hip-Hop, Classical, Electronic
- **Mood**: Energetic, Melancholic, Romantic, Aggressive, Chill
- **Artist Style**: Famous vocalist emulations (for practice/education)

### Features
- Static grid layout with adapter cards
- "Buy" buttons (no real payment processing)
- Ratings and download counts
- Adapter descriptions and audio previews (simulated)

### Future Marketplace
- Real payment integration (Stripe/PayPal)
- User uploads and reviews
- License management (commercial vs. personal use)
- Blockchain-based ownership tracking
- Revenue sharing for adapter creators

## Modes Explained

### Ordinary Mode (Default)
- **Target**: Casual users, content creators
- **Hardware**: CPU-only, 4 GB RAM
- **Training**: 50-100 epochs, ~5 minutes
- **Adapter Size**: 1-3 MB
- **Interface**: Simplified, minimal options

### Pro Mode
- **Target**: Professional artists, ML engineers
- **Hardware**: GPU-accelerated (CUDA/MPS), 8+ GB RAM
- **Training**: Custom epochs, learning rate, batch size
- **Adapter Size**: Up to 5 MB
- **Interface**: Full parameter control, batch processing
- **Features**:
  - Base model management
  - Batch audition (apply adapter to multiple inputs)
  - Advanced monitoring (loss curves, spectrograms)
  - Export formats (ONNX, TorchScript)

Switch modes in GUI settings or CLI prompts.

## Technical Details

### Adapter Architecture
- Lightweight parameter-efficient fine-tuning (PEFT)
- LoRA-style adapter layers
- Frozen base model + trainable adapter weights
- Fast inference: <100ms latency per second of audio

### Supported Formats
- **Input Audio**: WAV, MP3, FLAC, OGG
- **Base Models**: ONNX format
- **Adapters**: PyTorch state_dict (.pth)
- **Output**: WAV (16-bit, 44.1 kHz)

## Troubleshooting

### Missing Dependencies
If auto-install fails, manually install:
```bash
pip install -r requirements.txt
```

### ONNX Runtime Issues
For GPU support (optional):
```bash
pip uninstall onnxruntime
pip install onnxruntime-gpu
```

### Audio Library Conflicts
On Linux, install system dependencies:
```bash
sudo apt-get install libsndfile1 ffmpeg
```

### Low Memory
- Use Ordinary mode
- Reduce batch size in Pro mode
- Close other applications during training

## Contributing

VoiceAdapter Studio is self-managing but welcomes contributions:
1. Check `TASKS.md` for open tasks
2. Fork the repository
3. Create feature branch
4. Submit pull request

## License

MIT License - See LICENSE file for details

## Acknowledgments

- ONNX Runtime for cross-platform inference
- Gradio for rapid UI development
- PyTorch for adapter training
- Librosa for audio processing

---

**Version**: 1.0.0  
**Status**: Production Ready  
**Last Updated**: February 2026

For issues and feature requests, check `TASKS.md` or submit a GitHub issue.
