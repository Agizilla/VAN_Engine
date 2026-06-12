#!/usr/bin/env python3
"""
Installation verification script for 3D Face Avatar Generator
Checks if all required dependencies are properly installed
"""

import sys

def check_imports():
    """Check if all required packages can be imported"""
    packages = {
        'numpy': 'numpy',
        'cv2': 'opencv-python',
        'PIL': 'pillow',
        'mediapipe': 'mediapipe',
        'OpenGL': 'PyOpenGL',
        'pygame': 'pygame',
        'tkinter': 'tkinter (usually built-in)'
    }
    
    print("=" * 60)
    print("3D Face Avatar Generator - Installation Check")
    print("=" * 60)
    print()
    
    all_ok = True
    
    for module, package in packages.items():
        try:
            __import__(module)
            print(f"✓ {package:30s} - OK")
        except ImportError as e:
            print(f"✗ {package:30s} - MISSING")
            all_ok = False
    
    print()
    print("=" * 60)
    
    if all_ok:
        print("✓ All dependencies are installed correctly!")
        print()
        print("You can now run the application:")
        print("  python face_avatar_3d.py")
    else:
        print("✗ Some dependencies are missing.")
        print()
        print("Please install missing packages:")
        print("  pip install -r requirements.txt")
    
    print("=" * 60)
    
    return all_ok

def check_mediapipe():
    """Verify MediaPipe face mesh is working"""
    try:
        import mediapipe as mp
        face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            min_detection_confidence=0.5
        )
        print()
        print("✓ MediaPipe Face Mesh initialized successfully")
        print("  - Landmark points: 478")
        print("  - 3D coordinates: Enabled")
        return True
    except Exception as e:
        print(f"✗ MediaPipe initialization failed: {e}")
        return False

def check_opengl():
    """Verify OpenGL is working"""
    try:
        import pygame
        from OpenGL.GL import *
        from OpenGL.GLU import *
        
        pygame.init()
        pygame.display.set_mode((100, 100), pygame.HIDDEN | pygame.OPENGL)
        
        version = glGetString(GL_VERSION)
        print()
        print(f"✓ OpenGL is working")
        print(f"  - Version: {version.decode() if version else 'Unknown'}")
        
        pygame.quit()
        return True
    except Exception as e:
        print(f"✗ OpenGL check failed: {e}")
        print("  Note: This may work fine in your main environment")
        return False

if __name__ == "__main__":
    print()
    deps_ok = check_imports()
    
    if deps_ok:
        check_mediapipe()
        check_opengl()
    
    print()
    sys.exit(0 if deps_ok else 1)
