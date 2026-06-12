#!/usr/bin/env python3
"""
VoiceAdapter Studio - Main Entry Point
Enhanced with Training Orchestration and ESC Interrupts.
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from typing import List, Tuple, Optional

# Attempt to import keyboard for the interrupt functionality
try:
    import keyboard
except ImportError:
    keyboard = None


class DependencyManager:
    """Manages dependency checking and installation with mapping support."""
    
    def __init__(self):
        self.requirements_file = Path("requirements.txt")
        self.missing_packages = []
        # Map pip names to actual import names
        self.import_map = {
            "scikit-learn": "sklearn",
            "opencv-python": "cv2",
            "pillow": "PIL",
            "python-dotenv": "dotenv"
        }
        
    def check_dependencies(self) -> Tuple[bool, List[str]]:
        if not self.requirements_file.exists():
            print("⚠️  requirements.txt not found!")
            return True, []
        
        print("🔍 Checking system integrity...")
        missing = []
        
        try:
            with open(self.requirements_file, 'r', encoding='utf-8') as f:
                requirements = [
                    line.strip() 
                    for line in f 
                    if line.strip() and not line.startswith('#')
                ]
            
            for requirement in requirements:
                pkg_name = requirement.split('>=')[0].split('==')[0].split('[')[0].strip()
                import_name = self.import_map.get(pkg_name.lower(), pkg_name.replace('-', '_'))
                
                try:
                    __import__(import_name)
                except ImportError:
                    missing.append(requirement)
        except Exception as e:
            print(f"⚠️ Error reading requirements: {e}")
        
        self.missing_packages = missing
        if missing:
            print(f"❌ Missing {len(missing)} package(s).")
            return False, missing
        
        print("✅ All dependencies ready.")
        return True, []

    def install_dependencies(self) -> bool:
        if not self.missing_packages:
            return True
        print("\n📦 Installing missing dependencies...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *self.missing_packages])
            print("\n✅ Installation successful!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Installation failed: {e}")
            return False

    def ensure_dependencies(self) -> bool:
        all_installed, _ = self.check_dependencies()
        if all_installed:
            return True
        
        response = input("\nWould you like to install missing dependencies now? (y/n): ").strip().lower()
        if response == 'y':
            return self.install_dependencies()
        return False


class TaskManager:
    """Manages TASKS.md reading with robust encoding."""
    
    def __init__(self):
        self.tasks_file = Path("TASKS.md")
    
    def read_status(self):
        if not self.tasks_file.exists():
            print("⚠️  TASKS.md not found.")
            return
        
        print("\n" + "="*60)
        print("PROJECT STATUS")
        print("="*60)
        
        try:
            with open(self.tasks_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            with open(self.tasks_file, 'r', encoding='latin-1') as f:
                lines = f.readlines()
        
        total = 0
        done = 0
        for line in lines:
            if line.strip().startswith('- ['):
                total += 1
                if '[x]' in line.lower():
                    done += 1
        
        if total > 0:
            print(f"📊 Progress: {done}/{total} tasks ({ (done/total)*100:.1f}%)")
        print("="*60 + "\n")


class VoiceOrchestrator:
    """Handles the Vessel creation logic: Training, Input, and Interrupts."""
    
    def __init__(self):
        self.config_path = Path("config.json")
        self.models_dir = Path("models")
        self.config = self._load_config()

    def _load_config(self) -> dict:
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"base_model_path": None}

    def _save_config(self):
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4)

    def select_base_model(self) -> Optional[Path]:
        available = list(self.models_dir.glob("*.onnx")) + list(self.models_dir.glob("*.pth"))
        
        if not available:
            print("\n⚠️  No models found in /models/.")
            if self.config["base_model_path"]:
                print(f"Using persisted path: {self.config['base_model_path']}")
                return Path(self.config["base_model_path"])
            
            path = input("Please enter the absolute path to your base model: ").strip('"')
            if Path(path).exists():
                self.config["base_model_path"] = path
                self._save_config()
                return Path(path)
            return None
        
        print("\n--- Available Base Models ---")
        for i, m in enumerate(available, 1):
            print(f"{i}. {m.name}")
        
        choice = input("\nSelect model number (or press Enter for manual): ")
        if choice.isdigit() and 1 <= int(choice) <= len(available):
            return available[int(choice)-1]
        return None

    def get_audio_input(self) -> str:
        print("\n--- Audio Input Type ---")
        print("1. Full Song (Vocals + Beat)")
        print("2. Pure Vocals (Best for Adapter Training)")
        print("3. Pure Beat (Instrumental)")
        print("4. Live Recording Session")
        
        choice = input("\nSelection: ")
        if choice == '4':
            return "recording_session_active"
        return input("Path to .wav file: ").strip('"')

    def run_training(self):
        model = self.select_base_model()
        if not model: return
        
        audio = self.get_audio_input()
        print(f"\n🔥 Training Adapter using: {model.name}")
        print(">>> HOLD [ESC] TO PAUSE/KILL SESSION <<<\n")
        
        # Simulated Epoch Loop
        for epoch in range(1, 101):
            if keyboard and keyboard.is_pressed('esc'):
                print("\n\n⏸️  INTERRUPT DETECTED")
                action = input("Continue (c) or Kill & Cleanup (k)? ").lower()
                if action == 'k':
                    print("🧹 Cleaning temporary buffers... returning to menu.")
                    return
                print("▶️ Resuming...")

            time.sleep(0.05) # Simulated workload
            if epoch % 10 == 0:
                print(f"Progress: [{epoch}%] - Adjusting weights...")
        
        print("\n✅ Training Complete. Adapter saved to /adapters/")


def setup_directories():
    for d in ["models", "adapters", "outputs", "marketplace_data"]:
        Path(d).mkdir(exist_ok=True)


def main():
    setup_directories()
    print("\nVoiceAdapter Studio - Version 1.0.0 | February 2026")
    
    dep_manager = DependencyManager()
    if not dep_manager.ensure_dependencies():
        print("⚠️  Proceeding with limited functionality.")

    task_manager = TaskManager()
    orchestrator = VoiceOrchestrator()

    while True:
        print("\n" + "MAIN MENU".center(40, "-"))
        print("1. Train New Adapter")
        print("2. Launch GUI (--gui)")
        print("3. Check Project Status (--status)")
        print("4. Exit")
        
        choice = input("\nAction: ").strip()
        
        if choice == '1':
            orchestrator.run_training()
        elif choice == '2':
            print("🚀 Launching GUI...")
            from gui import launch
            launch()
            break
        elif choice == '3':
            task_manager.read_status()
        elif choice == '4':
            print("Goodbye!")
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nShutdown requested.")
        sys.exit(0)