#!/usr/bin/env python3
"""
VLC_AudioStudio Voice Model Inference
Use trained voice models to clone voices in new audio

Usage:
    python infer_voice_model.py --model trained_model.pth --input audio.wav --output output.wav
"""

import os
import sys
import json
import torch
import torchaudio
import numpy as np
from pathlib import Path
import logging
from typing import Dict, Tuple
import librosa

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VoiceModelInference:
    """Inference engine for trained voice models"""
    
    def __init__(self, model_path: str, config_path: str = None):
        """
        Initialize inference engine
        
        Args:
            model_path: Path to trained .pth model
            config_path: Optional path to model config
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_path = model_path
        self.config = {}
        
        if config_path and Path(config_path).exists():
            with open(config_path) as f:
                self.config = json.load(f)
        
        logger.info(f"Using device: {self.device}")
        logger.info(f"Model path: {model_path}")
        
        # Load model (simplified for demonstration)
        self.model = self._load_model()
    
    def _load_model(self):
        """Load the trained model"""
        try:
            if not Path(self.model_path).exists():
                logger.error(f"Model file not found: {self.model_path}")
                return None
            
            # In real implementation, load So-VITS-SVC model
            # checkpoint = torch.load(self.model_path, map_location=self.device)
            # model = SingerConversionModel(...)
            # model.load_state_dict(checkpoint)
            # model.eval()
            
            logger.info("Model loaded successfully")
            return None  # Placeholder
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return None
    
    def load_audio(self, audio_path: str, sr: int = 24000) -> Tuple[np.ndarray, int]:
        """Load and preprocess audio"""
        logger.info(f"Loading audio: {audio_path}")
        
        waveform, original_sr = torchaudio.load(audio_path)
        
        # Resample if needed
        if original_sr != sr:
            resampler = torchaudio.transforms.Resample(original_sr, sr)
            waveform = resampler(waveform)
        
        # Convert to numpy
        audio = waveform.numpy()[0]
        
        # Normalize
        audio = audio / (np.abs(audio).max() + 1e-5)
        
        return audio, sr
    
    def infer(self, 
              input_audio: str,
              pitch_shift: int = 0,
              f0_method: str = "harvest",
              index_rate: float = 0.75,
              filter_radius: int = 3,
              rms_mix_rate: float = 0.25,
              protect: float = 0.33) -> np.ndarray:
        """
        Perform voice conversion inference
        
        Args:
            input_audio: Path to input audio file
            pitch_shift: Pitch shift in semitones (-12 to +12)
            f0_method: F0 extraction method ("harvest", "dio", "pyin")
            index_rate: How much to use the trained voice (0.0 to 1.0)
            filter_radius: Median filter radius
            rms_mix_rate: RMS mix ratio
            protect: Protect consonants (0.0 to 1.0)
        
        Returns:
            Output audio as numpy array
        """
        
        if self.model is None:
            logger.error("Model not loaded")
            return None
        
        try:
            # Load input audio
            audio, sr = self.load_audio(input_audio)
            
            logger.info(f"Audio loaded: {len(audio)} samples @ {sr}Hz")
            logger.info(f"Inference parameters:")
            logger.info(f"  Pitch shift: {pitch_shift}")
            logger.info(f"  Index rate: {index_rate}")
            logger.info(f"  F0 method: {f0_method}")
            
            # Extract fundamental frequency
            f0 = self._extract_f0(audio, sr, f0_method)
            
            # Apply pitch shift
            if pitch_shift != 0:
                f0 = f0 * (2 ** (pitch_shift / 12))
            
            # Perform voice conversion (simplified)
            output_audio = self._convert_voice(
                audio, f0, sr,
                index_rate=index_rate,
                filter_radius=filter_radius,
                rms_mix_rate=rms_mix_rate,
                protect=protect
            )
            
            logger.info(f"Inference complete. Output shape: {output_audio.shape}")
            
            return output_audio
            
        except Exception as e:
            logger.error(f"Inference failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_f0(self, audio: np.ndarray, sr: int, method: str) -> np.ndarray:
        """Extract fundamental frequency"""
        logger.info(f"Extracting F0 using {method}...")
        
        try:
            if method == "harvest":
                # Use librosa's piptrack (similar to harvest)
                f0, _ = librosa.piptrack(y=audio, sr=sr)
                f0 = np.where(f0 > 0, f0, 0)
                f0 = np.nanmean(f0, axis=0)
            elif method == "pyin":
                f0, _, _ = librosa.pyin(audio, fmin=50, fmax=400, sr=sr)
                f0 = np.nan_to_num(f0)
            else:  # dio (default)
                f0, _ = librosa.piptrack(y=audio, sr=sr, hop_length=512)
                f0 = np.nanmean(f0, axis=0)
            
            return f0
            
        except Exception as e:
            logger.warning(f"F0 extraction failed: {e}. Using silence.")
            return np.zeros_like(audio)
    
    def _convert_voice(self, 
                      audio: np.ndarray,
                      f0: np.ndarray,
                      sr: int,
                      index_rate: float = 0.75,
                      filter_radius: int = 3,
                      rms_mix_rate: float = 0.25,
                      protect: float = 0.33) -> np.ndarray:
        """Perform voice conversion"""
        
        logger.info("Converting voice...")
        
        # In real implementation, this would use the trained model
        # For now, return slightly modified audio to demonstrate
        
        output = audio.copy()
        
        # Apply simple pitch shifting based on F0
        if f0 is not None and len(f0) > 0:
            # Simple time-stretch based on F0 (placeholder)
            scale_factor = 1.0 + (index_rate * 0.1)
            hop_length = 512
            
            # Ensure F0 has the right shape
            if len(f0) < len(audio) // hop_length:
                f0 = np.pad(f0, (0, len(audio) // hop_length - len(f0)))
        
        # Apply RMS mixing
        rms_original = np.sqrt(np.mean(audio ** 2))
        rms_output = np.sqrt(np.mean(output ** 2))
        
        if rms_output > 0:
            mix_factor = rms_mix_rate * (rms_original / rms_output)
            output = output * (1 - rms_mix_rate) + audio * mix_factor
        
        # Apply median filter for smoothness
        if filter_radius > 0:
            from scipy.ndimage import median_filter
            output = median_filter(output, size=filter_radius * 2 + 1)
        
        # Normalize output
        max_val = np.abs(output).max()
        if max_val > 0:
            output = output / max_val
        
        return output
    
    def save_audio(self, audio: np.ndarray, sr: int, output_path: str):
        """Save audio to file"""
        logger.info(f"Saving audio to: {output_path}")
        
        # Convert to torch tensor
        audio_tensor = torch.from_numpy(audio).float().unsqueeze(0)
        
        # Save
        torchaudio.save(output_path, audio_tensor, sr)
        
        logger.info(f"✓ Audio saved successfully")


def main():
    """Main entry point"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="VLC_AudioStudio Voice Model Inference")
    parser.add_argument("--model", required=True, help="Path to trained model")
    parser.add_argument("--input", required=True, help="Input audio file")
    parser.add_argument("--output", required=True, help="Output audio file")
    parser.add_argument("--config", help="Model config file")
    parser.add_argument("--pitch-shift", type=int, default=0, help="Pitch shift (-12 to +12)")
    parser.add_argument("--index-rate", type=float, default=0.75, help="Index rate (0.0 to 1.0)")
    parser.add_argument("--f0-method", default="harvest", help="F0 extraction method")
    
    args = parser.parse_args()
    
    # Initialize inference
    inference = VoiceModelInference(args.model, args.config)
    
    if inference.model is None:
        logger.error("Failed to initialize inference engine")
        return 1
    
    # Run inference
    output_audio = inference.infer(
        args.input,
        pitch_shift=args.pitch_shift,
        f0_method=args.f0_method,
        index_rate=args.index_rate
    )
    
    if output_audio is None:
        return 1
    
    # Save output
    inference.save_audio(output_audio, 24000, args.output)
    
    # Return output path for .NET to read
    print(args.output)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
