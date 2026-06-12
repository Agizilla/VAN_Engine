@echo off
echo ========================================
echo Audio Workstation - Build Script
echo ========================================
echo.

REM Check if virtual environment exists
if not exist venv (
    echo ERROR: Virtual environment not found!
    echo Please run install.bat first.
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing PyInstaller if not already installed...
pip install pyinstaller

echo Cleaning previous build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist AudioWorkstation.spec del /q AudioWorkstation.spec

echo Building executable with PyInstaller...
pyinstaller --onefile ^
    --windowed ^
    --name "AudioWorkstation" ^
    --icon=NONE ^
    --add-data "ui;ui" ^
    --add-data "core;core" ^
    --add-data "utils;utils" ^
    --hidden-import=PySide6.QtCore ^
    --hidden-import=PySide6.QtGui ^
    --hidden-import=PySide6.QtWidgets ^
    --hidden-import=PySide6.QtMultimedia ^
    --hidden-import=demucs ^
    --hidden-import=whisper ^
    --hidden-import=pydub ^
    --hidden-import=moviepy ^
    --hidden-import=torch ^
    --hidden-import=torchaudio ^
    --hidden-import=librosa ^
    --hidden-import=soundfile ^
    main.py

if errorlevel 1 (
    echo.
    echo Build failed! Check the error messages above.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build complete!
echo ========================================
echo.
echo Executable location: dist\AudioWorkstation.exe
echo.
pause
