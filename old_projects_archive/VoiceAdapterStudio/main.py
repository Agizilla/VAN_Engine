#!/usr/bin/env python3
"""
VoiceAdapter Studio - Main Entry Point
Auto-installs dependencies and launches CLI by default.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple


class DependencyManager:
    """Manages dependency checking and installation."""
    
    def __init__(self):
        self.requirements_file = Path("requirements.txt")
        self.missing_packages = []
        
    def check_dependencies(self) -> Tuple[bool, List[str]]:
        """
        Check if all required packages are installed.
        
        Returns:
            Tuple of (all_installed, missing_packages)
        """
        if not self.requirements_file.exists():
            print("⚠️  requirements.txt not found!")
            return True, []
        
        print("🔍 Checking dependencies...")
        
        # Read requirements
        with open(self.requirements_file, 'r', encoding='utf-8') as f:
            requirements = [
                line.strip() 
                for line in f 
                if line.strip() and not line.startswith('#')
            ]
        
        # Check each package
        missing = []
        for requirement in requirements:
            # Parse package name (handle >=, ==, etc.)
            pkg_name = requirement.split('>=')[0].split('==')[0].split('[')[0].strip()
            
            try:
                __import__(pkg_name.replace('-', '_'))
            except ImportError:
                missing.append(requirement)
        
        self.missing_packages = missing
        
        if missing:
            print(f"❌ Missing {len(missing)} package(s):")
            for pkg in missing:
                print(f"   - {pkg}")
            return False, missing
        else:
            print("✅ All dependencies installed!")
            return True, []
    
    def install_dependencies(self) -> bool:
        """
        Install missing dependencies.
        
        Returns:
            True if installation successful, False otherwise
        """
        if not self.missing_packages:
            return True
        
        print("\n📦 Installing missing dependencies...")
        print("This may take a few minutes...\n")
        
        try:
            # Install using pip
            subprocess.check_call([
                sys.executable,
                "-m",
                "pip",
                "install",
                "--upgrade",
                *self.missing_packages
            ])
            
            print("\n✅ Dependencies installed successfully!")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Installation failed: {e}")
            print("\nTry installing manually:")
            print(f"   pip install -r {self.requirements_file}")
            return False
    
    def ensure_dependencies(self) -> bool:
        """
        Check and install dependencies if needed.
        
        Returns:
            True if all dependencies are ready, False otherwise
        """
        all_installed, missing = self.check_dependencies()
        
        if all_installed:
            return True
        
        # Prompt user
        print("\nWould you like to install missing dependencies now?")
        response = input("Install? (y/n): ").strip().lower()
        
        if response == 'y':
            return self.install_dependencies()
        else:
            print("\n⚠️  Some features may not work without required dependencies.")
            print(f"To install later, run: pip install -r {self.requirements_file}")
            return False


class TaskManager:
    """Manages TASKS.md reading and updating."""
    
    def __init__(self):
        self.tasks_file = Path("TASKS.md")
    
    def read_status(self):
        """Read and display current project status from TASKS.md."""
        if not self.tasks_file.exists():
            print("⚠️  TASKS.md not found. Project status unavailable.")
            return
        
        print("\n" + "="*60)
        print("PROJECT STATUS (from TASKS.md)")
        print("="*60)
        
        # FIX: Explicitly specify utf-8 encoding
        try:
            with open(self.tasks_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            # Fallback for older files or different encodings
            with open(self.tasks_file, 'r', encoding='latin-1') as f:
                lines = f.readlines()
        
        # Count completed vs total tasks
        total_tasks = 0
        completed_tasks = 0
        
        for line in lines:
            if line.strip().startswith('- ['):
                total_tasks += 1
                if '[x]' in line or '[X]' in line:
                    completed_tasks += 1
        
        if total_tasks > 0:
            completion_rate = (completed_tasks / total_tasks) * 100
            print(f"\n📊 Overall Progress: {completed_tasks}/{total_tasks} tasks complete ({completion_rate:.1f}%)")
        
        # Show current sprint (completed items)
        print("\n✅ Recently Completed:")
        in_completed = False
        for line in lines:
            if "## 🎯 Current Sprint" in line:
                in_completed = True
            elif in_completed and "### ✅ Completed" in line:
                continue
            elif in_completed and line.strip().startswith('- [x]'):
                # Print completed task
                task = line.strip()[6:].strip()  # Remove '- [x] '
                print(f"   • {task}")
            elif in_completed and (line.startswith('## ') or line.startswith('---')):
                break
        
        print("\n" + "="*60 + "\n")


def setup_directories():
    """Create necessary directories."""
    directories = [
        "models",
        "adapters", 
        "outputs",
        "marketplace_data"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)


def show_startup_banner():
    """Display startup banner."""
    banner = """
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║          VoiceAdapter Studio - Starting Up               ║
║                                                          ║
║     Cross-Platform Voice Adapter Creation Suite          ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """
    print(banner)
    print("Version 1.0.0 | Local Processing | February 2026\n")


def main():
    """Main entry point."""
    # Show banner
    show_startup_banner()
    
    # Setup directories
    setup_directories()
    
    # Check and install dependencies
    dep_manager = DependencyManager()
    
    if not dep_manager.ensure_dependencies():
        print("\n⚠️  Continuing with limited functionality...")
        print("Some features may not work correctly.\n")
        
        response = input("Continue anyway? (y/n): ").strip().lower()
        if response != 'y':
            print("Exiting. Please install dependencies and try again.")
            sys.exit(1)
    
    # Read and display project status
    task_manager = TaskManager()
    task_manager.read_status()
    
    # Parse command-line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--gui":
            print("🚀 Launching GUI mode...\n")
            from gui import launch
            launch()
            return
        elif sys.argv[1] == "--status":
            # Already displayed above
            return
        elif sys.argv[1] == "--help":
            print_help()
            return
    
    # Default: Launch CLI
    print("🚀 Launching CLI mode...\n")
    print("(Use 'python main.py --gui' to launch web interface)\n")
    
    try:
        from cli import main as cli_main
        cli_main()
    except KeyboardInterrupt:
        print("\n\nShutdown requested. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nFor help, run: python main.py --help")
        sys.exit(1)


def print_help():
    """Print help message."""
    help_text = """
VoiceAdapter Studio - Command Line Options

USAGE:
    python main.py [OPTIONS]

OPTIONS:
    (none)      Launch CLI menu (default)
    --gui       Launch Gradio web interface
    --status    Show project status from TASKS.md
    --help      Show this help message

EXAMPLES:
    python main.py                  # Start CLI
    python main.py --gui            # Start web GUI
    python main.py --status         # Check project status

FEATURES:
    • Train voice adapters from audio samples
    • Apply adapters to generate synthesized audio
    • Browse marketplace of pre-made adapters
    • Manage and organize your adapter library

For detailed documentation, see README.md

PROJECT STRUCTURE:
    cli.py          - Command-line interface
    gui.py          - Gradio web interface
    adapter.py      - Training and inference engine
    marketplace.py  - Adapter marketplace functionality
    main.py         - This file (entry point)

DIRECTORIES:
    models/         - Base ONNX models
    adapters/       - Trained adapters (.pth files)
    outputs/        - Generated audio files
    marketplace_data/ - Marketplace catalog

SUPPORT:
    • Check TASKS.md for development roadmap
    • See README.md for troubleshooting
    • Submit issues on GitHub

VERSION: 1.0.0
LICENSE: MIT
    """
    print(help_text)


if __name__ == "__main__":
    main()
