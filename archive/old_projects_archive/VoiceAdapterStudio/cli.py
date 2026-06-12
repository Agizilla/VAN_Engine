"""
VoiceAdapter Studio - CLI Module
Command-line interface with menu-driven interaction.
"""

import os
import sys
from pathlib import Path
from typing import Optional

from adapter import AdapterConfig, AdapterTrainer, AdapterInference, list_adapters
from marketplace import Marketplace, format_adapter_card


class CLI:
    """Command-line interface for VoiceAdapter Studio."""
    
    def __init__(self):
        self.marketplace = Marketplace()
        self.running = True
        
    def run(self):
        """Main CLI loop."""
        self.show_welcome()
        
        while self.running:
            self.show_menu()
            choice = input("\nSelect option (1-5): ").strip()
            
            if choice == "1":
                self.train_adapter()
            elif choice == "2":
                self.apply_adapter()
            elif choice == "3":
                self.list_adapters()
            elif choice == "4":
                self.launch_gui()
            elif choice == "5":
                self.exit_cli()
            else:
                print("Invalid option. Please enter 1-5.")
            
            if self.running:
                input("\nPress Enter to continue...")
                self.clear_screen()
    
    def show_welcome(self):
        """Display welcome banner."""
        banner = """
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║          VoiceAdapter Studio - CLI Edition               ║
║                                                          ║
║     Create, Apply, and Share Voice Adapters              ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
        """
        print(banner)
        print("Version 1.0.0 | Cross-platform | Local Processing\n")
    
    def show_menu(self):
        """Display main menu."""
        menu = """
═══════════════════════════════════════════════════════════
                    MAIN MENU
═══════════════════════════════════════════════════════════

1) Train Adapter      - Create a new voice adapter
2) Apply Adapter      - Generate audio with adapter
3) List Adapters      - View available adapters
4) Launch GUI         - Open Gradio web interface
5) Exit               - Close application

═══════════════════════════════════════════════════════════
        """
        print(menu)
    
    def train_adapter(self):
        """Train a new adapter."""
        print("\n" + "="*60)
        print("TRAIN NEW ADAPTER")
        print("="*60 + "\n")
        
        # Get inputs
        base_model = input("Enter base model path (or press Enter for default): ").strip()
        if not base_model:
            base_model = "models/base_model.onnx"
            print(f"Using default: {base_model}")
        
        audio_path = input("Enter input WAV path: ").strip()
        if not audio_path or not os.path.exists(audio_path):
            print("❌ Invalid audio file path.")
            return
        
        adapter_name = input("Enter adapter name: ").strip()
        if not adapter_name:
            print("❌ Adapter name required.")
            return
        
        # Get training parameters
        try:
            epochs_input = input("Enter number of epochs (default 100): ").strip()
            epochs = int(epochs_input) if epochs_input else 100
        except ValueError:
            print("❌ Invalid epoch count. Using default: 100")
            epochs = 100
        
        mode = input("Training mode [ordinary/pro] (default: ordinary): ").strip().lower()
        if mode not in ["ordinary", "pro"]:
            mode = "ordinary"
        
        print(f"\n📊 Training Configuration:")
        print(f"   Mode: {mode}")
        print(f"   Epochs: {epochs}")
        print(f"   Audio: {audio_path}")
        print(f"   Adapter name: {adapter_name}")
        
        confirm = input("\nProceed with training? (y/n): ").strip().lower()
        if confirm != 'y':
            print("Training cancelled.")
            return
        
        # Create trainer and train
        print("\n🚀 Starting training...\n")
        
        config = AdapterConfig(mode=mode, epochs=epochs)
        trainer = AdapterTrainer(config)
        
        def progress_callback(epoch, total, loss):
            """Display training progress."""
            progress = (epoch / total) * 100
            bar_length = 40
            filled = int(bar_length * epoch / total)
            bar = "█" * filled + "░" * (bar_length - filled)
            print(f"\rEpoch {epoch}/{total} |{bar}| {progress:.1f}% - Loss: {loss:.6f}", end="")
        
        try:
            adapter_path, stats = trainer.train(
                base_model_path=base_model,
                audio_path=audio_path,
                adapter_name=adapter_name,
                progress_callback=progress_callback
            )
            
            print("\n\n✅ Training complete!")
            print(f"📁 Adapter saved: {adapter_path}")
            print(f"⏱️  Duration: {stats['duration']:.1f} seconds")
            print(f"📉 Final loss: {stats['losses'][-1]:.6f}" if stats['losses'] else "")
            
        except Exception as e:
            print(f"\n❌ Training failed: {e}")
    
    def apply_adapter(self):
        """Apply adapter to generate audio."""
        print("\n" + "="*60)
        print("APPLY ADAPTER")
        print("="*60 + "\n")
        
        # Show available adapters
        adapters = list_adapters()
        if not adapters:
            print("❌ No adapters available. Train one first!")
            return
        
        print("Available Adapters:")
        for i, adapter in enumerate(adapters, 1):
            print(f"  {i}) {adapter['name']} ({adapter['size_mb']:.2f} MB)")
        
        # Select adapter
        try:
            adapter_idx = int(input("\nSelect adapter number: ").strip()) - 1
            if adapter_idx < 0 or adapter_idx >= len(adapters):
                print("❌ Invalid selection.")
                return
            selected_adapter = adapters[adapter_idx]
        except ValueError:
            print("❌ Invalid input.")
            return
        
        # Get other inputs
        base_model = input("Enter base model path (or press Enter for default): ").strip()
        if not base_model:
            base_model = "models/base_model.onnx"
            print(f"Using default: {base_model}")
        
        backing_track = input("Enter backing track WAV (optional, press Enter to skip): ").strip()
        if backing_track and not os.path.exists(backing_track):
            print("⚠️  Backing track not found. Proceeding without it.")
            backing_track = None
        
        lyrics = input("Enter lyrics: ").strip()
        if not lyrics:
            print("❌ Lyrics required.")
            return
        
        output_file = input("Output filename (default: output.wav): ").strip()
        if not output_file:
            output_file = "output.wav"
        
        # Apply adapter
        print(f"\n🎵 Generating audio with adapter: {selected_adapter['name']}\n")
        
        try:
            inference = AdapterInference()
            output_path = inference.apply_adapter(
                base_model_path=base_model,
                adapter_path=selected_adapter['path'],
                lyrics=lyrics,
                backing_track_path=backing_track,
                output_path=output_file
            )
            
            print(f"\n✅ Audio generated successfully!")
            print(f"📁 Output: {output_path}")
            
        except Exception as e:
            print(f"\n❌ Generation failed: {e}")
    
    def list_adapters(self):
        """List all available adapters."""
        print("\n" + "="*60)
        print("AVAILABLE ADAPTERS")
        print("="*60 + "\n")
        
        adapters = list_adapters()
        
        if not adapters:
            print("No adapters found. Train one using option 1!")
            return
        
        for adapter in adapters:
            print(f"📦 {adapter['name']}")
            print(f"   Path: {adapter['path']}")
            print(f"   Size: {adapter['size_mb']:.2f} MB")
            print(f"   Created: {adapter['created_at'][:10]}")
            
            if 'training_stats' in adapter and adapter['training_stats']:
                stats = adapter['training_stats']
                if 'duration' in stats:
                    print(f"   Training time: {stats['duration']:.1f} seconds")
                if 'final_loss' in stats and stats['final_loss']:
                    print(f"   Final loss: {stats['final_loss']:.6f}")
            
            print()
    
    def launch_gui(self):
        """Launch Gradio GUI."""
        print("\n" + "="*60)
        print("LAUNCHING GRADIO GUI")
        print("="*60 + "\n")
        
        print("Starting web interface...")
        print("The GUI will open in your default browser.")
        print("Press Ctrl+C in this terminal to stop the server.\n")
        
        try:
            import gui
            gui.launch()
        except KeyboardInterrupt:
            print("\n\nGUI server stopped.")
        except Exception as e:
            print(f"\n❌ Failed to launch GUI: {e}")
            print("Make sure all dependencies are installed.")
    
    def exit_cli(self):
        """Exit the CLI."""
        print("\n" + "="*60)
        print("Thank you for using VoiceAdapter Studio!")
        print("="*60 + "\n")
        self.running = False
    
    @staticmethod
    def clear_screen():
        """Clear terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')


def main():
    """CLI entry point."""
    try:
        cli = CLI()
        cli.run()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
