#!/usr/bin/env python3
"""Complete voice training pipeline: ONNX + LoRA from .wav + transcription"""

import argparse
from pathlib import Path
import json


def train_voice(voice_name: str, wav_path: str, transcript: str):
    print(f"""
Training Voice: {voice_name}
    """)
    wav_file = Path(wav_path)
    if not wav_file.exists():
        print(f" Audio file not found: {wav_path}")
        return False
    if not transcript.strip():
        print(" Transcription is empty")
        return False
    print(f"  Audio: {wav_file.name} ({wav_file.stat().st_size / 1024:.1f} KB)")
    print(f"  Transcript: {transcript[:100]}...")

    print(" Training LoRA adapter...")
    from voice_cloner import StyleTTS2LoRA
    cloner = StyleTTS2LoRA()
    try:
        cloner.train_lora(voice_name, wav_path, transcript, epochs=50)
    except Exception as e:
        print(f" Training failed: {e}")
        return False

    print(" Exporting to ONNX...")
    try:
        cloner.export_to_onnx(voice_name)
    except Exception as e:
        print(f" ONNX export failed: {e}")

    print(f"""
Voice '{voice_name}' trained successfully

Test with:
    python voice_cloner.py --synthesize "Hello world" --voice {voice_name}
    python onnx_inference.py --voice {voice_name} --text "Hello world"
    """)
    return True


def batch_train(config_file: str):
    with open(config_file, 'r') as f:
        config = json.load(f)
    for voice in config.get("voices", []):
        train_voice(voice["name"], voice["wav"], voice["text"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", help="Voice name")
    parser.add_argument("--wav", help="Path to .wav file")
    parser.add_argument("--text", help="Transcription text")
    parser.add_argument("--batch", help="Batch config JSON file")
    args = parser.parse_args()
    if args.batch:
        batch_train(args.batch)
    elif args.name and args.wav and args.text:
        train_voice(args.name, args.wav, args.text)
    else:
        print(__doc__)
