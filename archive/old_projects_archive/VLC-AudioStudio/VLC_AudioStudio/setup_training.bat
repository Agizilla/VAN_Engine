@echo off
REM VLC_AudioStudio Training Pipeline Setup Script
REM This script sets up the Python environment with all required dependencies

echo.
echo ========================================
echo VLC_AudioStudio Training Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

echo [✓] Python is installed
python --version

REM Create virtual environment
echo.
echo Creating Python virtual environment...
if exist "venv" (
    echo Virtual environment already exists. Skipping creation.
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [✓] Virtual environment created
)

REM Activate virtual environment
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

echo [✓] Virtual environment activated

REM Upgrade pip and install setuptools
echo.
echo Upgrading pip and installing setuptools...
python -m pip install --upgrade pip setuptools wheel --quiet
if errorlevel 1 (
    echo WARNING: Failed to upgrade pip. Continuing anyway...
)
echo [✓] Pip and setuptools upgraded

REM Install requirements
echo.
echo Installing Python dependencies...
echo This may take 10-15 minutes on first install...
echo.

pip install -r python_scripts/requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    echo Try running manually:
    echo   venv\Scripts\activate
    echo   pip install -r python_scripts/requirements.txt
    pause
    exit /b 1
)

echo.
echo [✓] All dependencies installed

REM Verify installations
echo.
echo Verifying installations...
python -c "import torch; print('✓ PyTorch:', torch.__version__)" || echo ✗ PyTorch installation failed
python -c "import whisper; print('✓ Whisper installed')" || echo ✗ Whisper installation failed
python -c "import librosa; print('✓ librosa installed')" || echo ✗ librosa installation failed
python -c "import torchaudio; print('✓ torchaudio installed')" || echo ✗ torchaudio installation failed

REM Create necessary directories
echo.
echo Creating directories...
if not exist "training_data" mkdir training_data
if not exist "training_data\artist_samples" mkdir training_data\artist_samples
if not exist "trained_models" mkdir trained_models
if not exist "models" mkdir models

echo [✓] Directories created

REM Summary
echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Place your artist's audio samples in: training_data\artist_samples\
echo    (Use .wav format, 10-30 seconds each, preferably singing)
echo.
echo 2. Review the training config: song_configs\training_config.json
echo.
echo 3. Run training from VLC_AudioStudio UI or manually:
echo    python python_scripts/train_voice_model.py --config song_configs/training_config.json
echo.
echo 4. After training, use the trained model for voice cloning
echo.
echo Virtual environment is still active. To deactivate:
echo    deactivate
echo.
echo To reactivate later:
echo    venv\Scripts\activate.bat
echo.
pause
