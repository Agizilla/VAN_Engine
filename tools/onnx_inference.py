#!/usr/bin/env python3
"""ONNX Runtime inference for StyleTTS 2 voices. Lightweight, no PyTorch required."""

import numpy as np
import onnxruntime as ort
import json
from pathlib import Path
import argparse


class StyleTTS2ONNX:
    def __init__(self, model_dir: str = "Models/LJSpeech/lora"):
        self.model_dir = Path(model_dir)
        self.sessions = {}
        self.metadata = {}
        self._load_models()

    def _load_models(self):
        for onnx_file in self.model_dir.glob("*.onnx"):
            voice_name = onnx_file.stem
            print(f"[ONNX] Loading {voice_name} voice...")
            session = ort.InferenceSession(str(onnx_file), providers=['CPUExecutionProvider'])
            self.sessions[voice_name] = session
            json_file = self.model_dir / f"{voice_name}.json"
            if json_file.exists():
                with open(json_file) as f:
                    self.metadata[voice_name] = json.load(f)
        print(f"[ONNX] Loaded {len(self.sessions)} voices")

    def synthesize(self, text: str, voice_name: str = "male") -> np.ndarray:
        if voice_name not in self.sessions:
            raise ValueError(f"Voice '{voice_name}' not found. Available: {list(self.sessions.keys())}")
        session = self.sessions[voice_name]
        phonemes = self._text_to_phonemes(text)
        inputs = {session.get_inputs()[0].name: self._prepare_input(phonemes)}
        return session.run(None, inputs)[0]

    def _text_to_phonemes(self, text: str) -> np.ndarray:
        vocab = {c: i for i, c in enumerate("abcdefghijklmnopqrstuvwxyz ")}
        ids = [vocab.get(c, 0) for c in text.lower()[:200]]
        max_len = 200
        if len(ids) < max_len:
            ids += [0] * (max_len - len(ids))
        return np.array(ids, dtype=np.int64).reshape(1, -1)

    def _prepare_input(self, phonemes):
        return phonemes

    def list_voices(self):
        for name in self.sessions.keys():
            meta = self.metadata.get(name, {})
            print(f"  - {name}: {meta.get('created', 'unknown')}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true", help="List available voices")
    parser.add_argument("--voice", default="male", help="Voice to use")
    parser.add_argument("--text", help="Text to synthesize")
    parser.add_argument("--output", default="output.wav", help="Output file")
    parser.add_argument("--model-dir", default="Models/LJSpeech/lora", help="Model directory")
    args = parser.parse_args()
    tts = StyleTTS2ONNX(args.model_dir)
    if args.list:
        print("Available voices:")
        tts.list_voices()
    elif args.text:
        audio = tts.synthesize(args.text, args.voice)
        import soundfile as sf
        sf.write(args.output, audio, 24000)
        print(f"Saved to {args.output}")

if __name__ == "__main__":
    main()
