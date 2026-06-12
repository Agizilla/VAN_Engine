"""
Python 3.13 Compatibility Fixer
Resolves the OpenCV "_ARRAY_API not found" error
"""

import subprocess
import sys

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    return version.major, version.minor

def fix_opencv_python313():
    """Fix OpenCV for Python 3.13"""
    print("\n" + "="*60)
    print("OpenCV Python 3.13 Compatibility Fix")
    print("="*60 + "\n")
    
    major, minor = check_python_version()
    
    if major == 3 and minor >= 13:
        print("⚠ Python 3.13 detected - applying compatibility fixes...")
        print("\nStep 1: Uninstalling old OpenCV...")
        
        packages_to_remove = [
            'opencv-python',
            'opencv-contrib-python',
            'opencv-python-headless'
        ]
        
        for package in packages_to_remove:
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'uninstall', '-y', package],
                             capture_output=True)
            except:
                pass
        
        print("Step 2: Installing compatible versions...")
        
        # Install numpy first (required for OpenCV)
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'numpy>=1.26.0'])
        
        # Install latest OpenCV
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'opencv-python>=4.10.0'])
        
        # Install other dependencies
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade',
                       'pillow>=10.0.0',
                       'mediapipe>=0.10.14',
                       'PyOpenGL>=3.1.7',
                       'pygame>=2.6.0'])
        
        print("\n✓ Installation complete!")
        print("\nStep 3: Testing OpenCV import...")
        
        try:
            import cv2
            print(f"✓ OpenCV imported successfully! Version: {cv2.__version__}")
            return True
        except Exception as e:
            print(f"✗ OpenCV import failed: {e}")
            return False
    
    elif major == 3 and minor >= 8:
        print("✓ Python 3.8-3.12 detected - standard installation should work")
        print("\nInstalling dependencies...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        return True
    
    else:
        print("⚠ Python version too old. Please upgrade to Python 3.8+")
        return False

def provide_alternatives():
    """Provide alternative solutions if auto-fix fails"""
    print("\n" + "="*60)
    print("Alternative Solutions")
    print("="*60 + "\n")
    
    print("Option 1: Use Python 3.11 or 3.12 (Recommended)")
    print("-" * 60)
    print("Python 3.13 is very new and some packages aren't fully compatible yet.")
    print("Download Python 3.11 or 3.12 from: https://www.python.org/downloads/")
    print("Then run: py -3.11 -m pip install -r requirements.txt")
    print()
    
    print("Option 2: Manual Installation Commands")
    print("-" * 60)
    print("Run these commands one by one:")
    print("  py -m pip uninstall -y opencv-python opencv-contrib-python")
    print("  py -m pip install --upgrade numpy")
    print("  py -m pip install --upgrade opencv-python")
    print("  py -m pip install --upgrade pillow mediapipe PyOpenGL pygame")
    print()
    
    print("Option 3: Use a Virtual Environment")
    print("-" * 60)
    print("  py -m venv venv")
    print("  venv\\Scripts\\activate")
    print("  pip install --upgrade pip")
    print("  pip install -r requirements.txt")
    print()
    
    print("Option 4: Install from conda (if you have Anaconda)")
    print("-" * 60)
    print("  conda create -n face3d python=3.11")
    print("  conda activate face3d")
    print("  pip install -r requirements.txt")
    print()

if __name__ == "__main__":
    success = fix_opencv_python313()
    
    if not success:
        provide_alternatives()
        print("\n" + "="*60)
        print("After fixing, run: python face_avatar_3d.py")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("✓ Ready to use! Run: python face_avatar_3d.py")
        print("="*60)
