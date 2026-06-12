#!/usr/bin/env python3
"""
VoiceAdapter Studio - Demo Script
Demonstrates key functionality without requiring actual models or audio files.
"""

import sys
import time
from pathlib import Path


def demo_banner():
    """Show demo banner."""
    banner = """
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║          VoiceAdapter Studio - DEMO MODE                 ║
║                                                          ║
║     Demonstration of Core Features                       ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """
    print(banner)
    print("This demo shows VoiceAdapter Studio features without requiring")
    print("actual audio files or models.\n")


def demo_marketplace():
    """Demonstrate marketplace functionality."""
    print("\n" + "="*60)
    print("DEMO: Marketplace")
    print("="*60 + "\n")
    
    from marketplace import Marketplace, format_adapter_card
    
    marketplace = Marketplace()
    
    # Show categories
    print("📂 Available Categories:")
    for category in marketplace.get_categories():
        print(f"   • {category}")
    
    print("\n🎵 Featured Adapters:\n")
    
    # Show top 3 adapters
    top_adapters = marketplace.get_most_downloaded(3)
    for i, adapter in enumerate(top_adapters, 1):
        print(f"\n{i}. {adapter['name']}")
        print(f"   Author: {adapter['author']}")
        print(f"   Price: ${adapter['price']}")
        print(f"   Rating: {'⭐' * int(adapter['rating'])} ({adapter['rating']}/5)")
        print(f"   Downloads: {adapter['downloads']:,}")
        print(f"   {adapter['description'][:80]}...")
    
    print("\n" + "="*60)


def demo_adapter_list():
    """Demonstrate adapter listing."""
    print("\n" + "="*60)
    print("DEMO: Adapter Management")
    print("="*60 + "\n")
    
    # Create sample adapters directory
    adapters_dir = Path("adapters")
    adapters_dir.mkdir(exist_ok=True)
    
    # Create mock adapter files
    import torch
    from adapter import VoiceAdapter
    
    sample_adapters = [
        ("Pop_Style", 64),
        ("Jazz_Smooth", 48),
        ("Rock_Power", 56)
    ]
    
    print("Creating sample adapters...\n")
    
    for name, dim in sample_adapters:
        adapter = VoiceAdapter(adapter_dim=dim)
        adapter_path = adapters_dir / f"{name}.pth"
        
        if not adapter_path.exists():
            adapter_data = {
                "state_dict": adapter.state_dict(),
                "metadata": adapter.metadata,
                "config": {"adapter_dim": dim, "mode": "ordinary"},
                "training_stats": {"duration": 123.4, "final_loss": 0.0045}
            }
            torch.save(adapter_data, adapter_path)
            print(f"✅ Created: {name}.pth ({adapter.get_size_mb():.2f} MB)")
    
    # List adapters
    from adapter import list_adapters
    
    print("\n📦 Available Adapters:\n")
    adapters = list_adapters()
    
    for adapter in adapters:
        print(f"   • {adapter['name']}")
        print(f"     Size: {adapter['size_mb']:.2f} MB")
        print(f"     Created: {adapter['created_at'][:10]}")
        if 'training_stats' in adapter and adapter['training_stats']:
            stats = adapter['training_stats']
            print(f"     Training time: {stats.get('duration', 0):.1f}s")
        print()
    
    print("="*60)


def demo_training_simulation():
    """Simulate adapter training."""
    print("\n" + "="*60)
    print("DEMO: Training Simulation")
    print("="*60 + "\n")
    
    print("Simulating adapter training process...\n")
    
    epochs = 20
    for epoch in range(1, epochs + 1):
        loss = 1.0 - (epoch / epochs) * 0.95
        progress = (epoch / epochs) * 100
        
        bar_length = 40
        filled = int(bar_length * epoch / epochs)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        print(f"\rEpoch {epoch}/{epochs} |{bar}| {progress:.0f}% - Loss: {loss:.6f}", end="")
        time.sleep(0.1)
    
    print("\n\n✅ Training simulation complete!")
    print("📁 Adapter would be saved to: adapters/demo_adapter.pth")
    print("💾 Estimated size: 2.3 MB")
    print("⏱️  Estimated training time: 45.2 seconds\n")
    
    print("="*60)


def demo_inference_simulation():
    """Simulate adapter application."""
    print("\n" + "="*60)
    print("DEMO: Audio Generation Simulation")
    print("="*60 + "\n")
    
    print("Simulating audio generation with adapter...\n")
    
    lyrics = "This is a demo of VoiceAdapter Studio generating vocals"
    
    print(f"📝 Input Lyrics: {lyrics}")
    print(f"🎵 Selected Adapter: Pop_Style")
    print(f"🎹 Backing Track: demo_beat.wav")
    
    steps = [
        "Loading adapter...",
        "Processing lyrics...",
        "Generating base audio...",
        "Applying adapter transformation...",
        "Mixing with backing track...",
        "Finalizing output..."
    ]
    
    print("\n🎬 Generation Pipeline:\n")
    
    for i, step in enumerate(steps, 1):
        print(f"   [{i}/{len(steps)}] {step}")
        time.sleep(0.3)
    
    print("\n✅ Audio generation simulation complete!")
    print("📁 Output would be saved to: outputs/demo_output.wav")
    print("⏱️  Estimated generation time: 8.3 seconds\n")
    
    print("="*60)


def demo_menu():
    """Interactive demo menu."""
    while True:
        print("\n" + "="*60)
        print("DEMO MENU")
        print("="*60)
        print("\n1) Marketplace Demo")
        print("2) Adapter Management Demo")
        print("3) Training Simulation")
        print("4) Inference Simulation")
        print("5) Run All Demos")
        print("6) Exit Demo")
        
        choice = input("\nSelect demo (1-6): ").strip()
        
        if choice == "1":
            demo_marketplace()
        elif choice == "2":
            demo_adapter_list()
        elif choice == "3":
            demo_training_simulation()
        elif choice == "4":
            demo_inference_simulation()
        elif choice == "5":
            demo_marketplace()
            demo_adapter_list()
            demo_training_simulation()
            demo_inference_simulation()
        elif choice == "6":
            print("\nExiting demo. Thanks for exploring VoiceAdapter Studio!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-6.")
        
        input("\nPress Enter to continue...")


def main():
    """Main demo entry point."""
    demo_banner()
    
    print("What would you like to see?")
    print("\n1) Interactive Demo Menu")
    print("2) Quick Demo (run all demonstrations)")
    print("3) Exit")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == "1":
        demo_menu()
    elif choice == "2":
        demo_marketplace()
        input("\nPress Enter to continue...")
        demo_adapter_list()
        input("\nPress Enter to continue...")
        demo_training_simulation()
        input("\nPress Enter to continue...")
        demo_inference_simulation()
        print("\n✅ All demos complete!")
    elif choice == "3":
        print("Goodbye!")
    else:
        print("Invalid choice. Exiting.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted. Goodbye!")
        sys.exit(0)
