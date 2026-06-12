# Installation Troubleshooting for Python 3.13

## The Problem

You're getting this error:
```
AttributeError: _ARRAY_API not found
```

This happens because **OpenCV doesn't fully support Python 3.13 yet** with older versions.

## Quick Fix (Automatic)

Run this script to automatically fix the issue:

```bash
python fix_python313.py
```

This will:
1. Uninstall old OpenCV versions
2. Install compatible numpy (1.26+)
3. Install latest OpenCV (4.10+)
4. Install all other dependencies
5. Test that everything works

## Manual Fix Options

### Option 1: Update OpenCV (Easiest)

```bash
# Uninstall old versions
py -m pip uninstall -y opencv-python opencv-contrib-python opencv-python-headless

# Install latest compatible versions
py -m pip install --upgrade numpy>=1.26.0
py -m pip install --upgrade opencv-python>=4.10.0.84
py -m pip install --upgrade pillow mediapipe PyOpenGL pygame
```

### Option 2: Use Python 3.11 or 3.12 (Recommended)

Python 3.13 is very new. For best compatibility:

1. Download Python 3.11 or 3.12 from https://www.python.org/downloads/
2. Install it (keep Python 3.13 if you want both)
3. Use it specifically for this project:

```bash
# If you have multiple Python versions
py -3.11 -m pip install -r requirements.txt
py -3.11 face_avatar_3d.py
```

### Option 3: Virtual Environment (Clean Install)

```bash
# Create fresh environment
py -m venv face_env

# Activate it
# On Windows:
face_env\Scripts\activate
# On Mac/Linux:
source face_env/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run the app
python face_avatar_3d.py
```

### Option 4: Conda (If you have Anaconda/Miniconda)

```bash
conda create -n face3d python=3.11
conda activate face3d
pip install -r requirements.txt
python face_avatar_3d.py
```

## Verify Installation

After trying any fix, verify it worked:

```bash
python verify_installation.py
```

You should see all green checkmarks (✓).

## Still Not Working?

### Check Your Python Version

```bash
python --version
```

If it shows Python 3.13, and you installed Python 3.11/3.12, use:

```bash
py -3.11 --version  # Should show 3.11.x
py -3.12 --version  # Should show 3.12.x
```

### Check Installed Packages

```bash
pip list | findstr opencv
pip list | findstr numpy
```

You should see:
- `numpy` version 1.26.0 or higher
- `opencv-python` version 4.10.0 or higher

### Nuclear Option: Complete Reinstall

```bash
# Remove everything
py -m pip uninstall -y numpy opencv-python pillow mediapipe PyOpenGL pygame

# Clear pip cache
py -m pip cache purge

# Reinstall fresh
py -m pip install --no-cache-dir -r requirements.txt
```

## Understanding the Error

The `_ARRAY_API not found` error occurs because:

1. **Python 3.13 changed internal APIs** that numpy relies on
2. **Older OpenCV versions** were built against older numpy versions
3. **Version mismatch** causes the import to fail

The solution is ensuring you have:
- `numpy >= 1.26.0` (has Python 3.13 support)
- `opencv-python >= 4.10.0` (compatible with new numpy)

## Recommended Setup for This Project

**Best compatibility:**
```
Python: 3.11 or 3.12
numpy: 1.26.0+
opencv-python: 4.10.0+
```

**Also works (newest):**
```
Python: 3.13
numpy: 1.26.4+
opencv-python: 4.10.0.84+
```

## Quick Commands Reference

```bash
# See your Python version
python --version

# See installed package versions
pip list

# Update a specific package
pip install --upgrade PACKAGE_NAME

# Install from requirements
pip install -r requirements.txt

# Create virtual environment
py -m venv myenv

# Activate virtual environment (Windows)
myenv\Scripts\activate

# Activate virtual environment (Mac/Linux)
source myenv/bin/activate

# Deactivate virtual environment
deactivate
```

## After Successful Installation

Run the app:
```bash
python face_avatar_3d.py
```

You should see the GUI window with 4 buttons!

## Need More Help?

1. Run `python fix_python313.py` for automatic fixing
2. Run `python verify_installation.py` to check what's installed
3. Check the error message carefully - it often tells you what's missing
4. Make sure you're using the right Python interpreter if you have multiple versions

Good luck! 🚀
