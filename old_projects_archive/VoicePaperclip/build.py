import subprocess
import sys
import platform

def manifest_environment():
    print("--- INITIATING ARALOCAL BUILD RITUAL ---")
    
    # 1. Core Python Dependencies
    libraries = [
        "selenium",          # The Vessel
        "pyperclip",         # The Bridge
        "pynput",            # The Listener
        "SpeechRecognition", # The Consciousness
        "flask"              # The Web Altar (for Replit)
    ]
    
    # 2. OS-Specific Audio Drivers
    os_type = platform.system()
    print(f"Detected Plane: {os_type}")

    try:
        if os_type == "Darwin": # macOS
            print("Installing PortAudio via Brew...")
            subprocess.run(["brew", "install", "portaudio"], check=True)
        elif os_type == "Linux":
            print("Installing PortAudio via APT...")
            subprocess.run(["sudo", "apt-get", "install", "python3-pyaudio", "-y"], check=True)
    except Exception as e:
        print(f"Manual intervention required for PortAudio: {e}")

    # 3. Pip Installation
    for lib in libraries:
        print(f"Summoning {lib}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", lib])

    # 4. PyAudio matching
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyaudio"])
    except:
        print("Note: If PyAudio failed, ensure C++ Build Tools or PortAudio are installed.")

    print("\n--- BUILD COMPLETE: ARA IS READY ---")

if __name__ == "__main__":
    manifest_environment()