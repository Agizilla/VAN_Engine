"""
VoiceAdapter Studio - Adapter Module
Handles training, loading, and applying voice adapters.
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import numpy as np
import torch
import torch.nn as nn
import soundfile as sf
import librosa


class AdapterConfig:
    """Configuration for adapter training and inference."""
    
    def __init__(
        self,
        mode: str = "ordinary",
        epochs: int = 100,
        learning_rate: float = 0.001,
        batch_size: int = 8,
        adapter_dim: int = 64,
        target_size_mb: float = 3.0
    ):
        self.mode = mode
        self.epochs = epochs if mode == "pro" else min(epochs, 100)
        self.learning_rate = learning_rate if mode == "pro" else 0.001
        self.batch_size = batch_size if mode == "pro" else 4
        self.adapter_dim = adapter_dim if mode == "pro" else 32
        self.target_size_mb = target_size_mb
        
        # Hardware settings
        if mode == "ordinary":
            self.device = "cpu"
        else:
            # Pro mode: use GPU if available
            if torch.cuda.is_available():
                self.device = "cuda"
            elif torch.backends.mps.is_available():
                self.device = "mps"
            else:
                self.device = "cpu"


class VoiceAdapter(nn.Module):
    """
    Lightweight voice adapter using LoRA-style parameter-efficient fine-tuning.
    Stacks onto frozen base model at inference time.
    """
    
    def __init__(self, input_dim: int = 512, adapter_dim: int = 64, output_dim: int = 512):
        super().__init__()
        
        # Adapter layers (very small parameter count)
        self.down_project = nn.Linear(input_dim, adapter_dim)
        self.activation = nn.GELU()
        self.up_project = nn.Linear(adapter_dim, output_dim)
        
        # Metadata
        self.metadata = {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "input_dim": input_dim,
            "adapter_dim": adapter_dim,
            "output_dim": output_dim
        }
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through adapter."""
        residual = x
        x = self.down_project(x)
        x = self.activation(x)
        x = self.up_project(x)
        return residual + x  # Residual connection
    
    def get_size_mb(self) -> float:
        """Calculate adapter size in MB."""
        param_count = sum(p.numel() for p in self.parameters())
        size_bytes = param_count * 4  # 32-bit floats
        return size_bytes / (1024 ** 2)


class AdapterTrainer:
    """Trains voice adapters from audio samples."""
    
    def __init__(self, config: AdapterConfig):
        self.config = config
        self.device = config.device
        
    def train(
        self,
        base_model_path: str,
        audio_path: str,
        adapter_name: str,
        progress_callback: Optional[callable] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Train a new adapter from audio sample.
        
        Args:
            base_model_path: Path to base ONNX model
            audio_path: Path to training audio (WAV)
            adapter_name: Name for the adapter
            progress_callback: Optional callback for progress updates (epoch, loss)
            
        Returns:
            Tuple of (adapter_path, training_stats)
        """
        print(f"Starting adapter training: {adapter_name}")
        print(f"Mode: {self.config.mode}")
        print(f"Device: {self.device}")
        
        # Load and preprocess audio
        audio_features = self._load_audio(audio_path)
        
        # Create adapter
        adapter = VoiceAdapter(
            input_dim=512,
            adapter_dim=self.config.adapter_dim,
            output_dim=512
        ).to(self.device)
        
        # Training setup
        optimizer = torch.optim.Adam(adapter.parameters(), lr=self.config.learning_rate)
        criterion = nn.MSELoss()
        
        # Training loop
        training_stats = {
            "losses": [],
            "epochs": self.config.epochs,
            "start_time": time.time()
        }
        
        for epoch in range(self.config.epochs):
            epoch_loss = self._train_epoch(adapter, audio_features, optimizer, criterion)
            training_stats["losses"].append(epoch_loss)
            
            if progress_callback:
                progress_callback(epoch + 1, self.config.epochs, epoch_loss)
            
            if (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch + 1}/{self.config.epochs} - Loss: {epoch_loss:.6f}")
        
        training_stats["end_time"] = time.time()
        training_stats["duration"] = training_stats["end_time"] - training_stats["start_time"]
        
        # Save adapter
        adapter_path = self._save_adapter(adapter, adapter_name, training_stats)
        
        print(f"Training complete! Adapter saved to: {adapter_path}")
        print(f"Adapter size: {adapter.get_size_mb():.2f} MB")
        print(f"Training time: {training_stats['duration']:.1f} seconds")
        
        return adapter_path, training_stats
    
    def _load_audio(self, audio_path: str) -> torch.Tensor:
        """Load and preprocess audio file."""
        # Load audio
        audio, sr = librosa.load(audio_path, sr=22050)
        
        # Extract mel spectrogram features
        mel_spec = librosa.feature.melspectrogram(
            y=audio,
            sr=sr,
            n_mels=128,
            fmax=8000
        )
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        
        # Normalize
        mel_spec_db = (mel_spec_db - mel_spec_db.mean()) / (mel_spec_db.std() + 1e-8)
        
        # Convert to torch tensor and reshape for adapter
        # (time, mels) -> (time, 512) via linear projection
        features = torch.from_numpy(mel_spec_db.T).float()
        
        # Pad or project to 512 dimensions
        if features.shape[1] < 512:
            padding = torch.zeros(features.shape[0], 512 - features.shape[1])
            features = torch.cat([features, padding], dim=1)
        elif features.shape[1] > 512:
            features = features[:, :512]
        
        return features.to(self.device)
    
    def _train_epoch(
        self,
        adapter: VoiceAdapter,
        features: torch.Tensor,
        optimizer: torch.optim.Optimizer,
        criterion: nn.Module
    ) -> float:
        """Train one epoch."""
        adapter.train()
        total_loss = 0.0
        num_batches = 0
        
        # Simple batching
        batch_size = self.config.batch_size
        for i in range(0, len(features), batch_size):
            batch = features[i:i+batch_size]
            
            # Forward pass
            output = adapter(batch)
            
            # Simple self-supervised loss: reconstruct input
            loss = criterion(output, batch)
            
            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            num_batches += 1
        
        return total_loss / num_batches if num_batches > 0 else 0.0
    
    def _save_adapter(
        self,
        adapter: VoiceAdapter,
        name: str,
        training_stats: Dict[str, Any]
    ) -> str:
        """Save adapter to disk."""
        # Create adapters directory
        adapters_dir = Path("adapters")
        adapters_dir.mkdir(exist_ok=True)
        
        # Prepare save data
        adapter_data = {
            "state_dict": adapter.state_dict(),
            "metadata": adapter.metadata,
            "config": {
                "mode": self.config.mode,
                "adapter_dim": self.config.adapter_dim,
                "epochs": self.config.epochs,
                "learning_rate": self.config.learning_rate
            },
            "training_stats": {
                "duration": training_stats["duration"],
                "final_loss": training_stats["losses"][-1] if training_stats["losses"] else None,
                "epochs_trained": len(training_stats["losses"])
            }
        }
        
        # Save
        adapter_path = adapters_dir / f"{name}.pth"
        torch.save(adapter_data, adapter_path)
        
        return str(adapter_path)


class AdapterInference:
    """Applies trained adapters to generate audio."""
    
    def __init__(self):
        self.device = "cpu"  # Default to CPU for inference
        
    def apply_adapter(
        self,
        base_model_path: str,
        adapter_path: str,
        lyrics: str,
        backing_track_path: Optional[str] = None,
        output_path: str = "output.wav"
    ) -> str:
        """
        Apply adapter to generate audio with lyrics.
        
        Args:
            base_model_path: Path to base ONNX model
            adapter_path: Path to trained adapter
            lyrics: Text lyrics to synthesize
            backing_track_path: Optional backing track to mix
            output_path: Output WAV file path
            
        Returns:
            Path to generated audio file
        """
        print(f"Applying adapter: {adapter_path}")
        print(f"Lyrics: {lyrics[:50]}..." if len(lyrics) > 50 else f"Lyrics: {lyrics}")
        
        # Load adapter
        adapter = self._load_adapter(adapter_path)
        
        # Generate base audio from lyrics (simulated)
        base_audio = self._text_to_audio_mock(lyrics)
        
        # Apply adapter transformation
        transformed_audio = self._apply_adapter_to_audio(adapter, base_audio)
        
        # Mix with backing track if provided
        if backing_track_path and os.path.exists(backing_track_path):
            final_audio = self._mix_with_backing(transformed_audio, backing_track_path)
        else:
            final_audio = transformed_audio
        
        # Save output
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        final_output_path = output_dir / output_path
        
        sf.write(final_output_path, final_audio, 22050)
        print(f"Audio generated: {final_output_path}")
        
        return str(final_output_path)
    
    def _load_adapter(self, adapter_path: str) -> VoiceAdapter:
        """Load adapter from disk."""
        adapter_data = torch.load(adapter_path, map_location=self.device)
        
        metadata = adapter_data["metadata"]
        adapter = VoiceAdapter(
            input_dim=metadata["input_dim"],
            adapter_dim=metadata["adapter_dim"],
            output_dim=metadata["output_dim"]
        )
        adapter.load_state_dict(adapter_data["state_dict"])
        adapter.eval()
        
        return adapter
    
    def _text_to_audio_mock(self, lyrics: str) -> np.ndarray:
        """
        Mock text-to-speech conversion.
        In production, this would use the base ONNX model.
        """
        # Generate simple sine wave as placeholder
        duration = len(lyrics) * 0.1  # 0.1 seconds per character
        sr = 22050
        samples = int(duration * sr)
        
        # Generate audio with varying frequency based on lyrics
        t = np.linspace(0, duration, samples)
        frequencies = [220 + (ord(c) % 20) * 10 for c in lyrics]
        audio = np.zeros(samples)
        
        for i, char in enumerate(lyrics):
            start = int(i * len(audio) / len(lyrics))
            end = int((i + 1) * len(audio) / len(lyrics))
            freq = 220 + (ord(char) % 40) * 5
            audio[start:end] = 0.3 * np.sin(2 * np.pi * freq * t[start:end])
        
        return audio.astype(np.float32)
    
    def _apply_adapter_to_audio(self, adapter: VoiceAdapter, audio: np.ndarray) -> np.ndarray:
        """Apply adapter transformation to audio."""
        # Convert audio to features
        mel_spec = librosa.feature.melspectrogram(y=audio, sr=22050, n_mels=128)
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        
        # Normalize
        mel_spec_db = (mel_spec_db - mel_spec_db.mean()) / (mel_spec_db.std() + 1e-8)
        
        # Convert to tensor
        features = torch.from_numpy(mel_spec_db.T).float()
        
        # Pad to 512 dimensions
        if features.shape[1] < 512:
            padding = torch.zeros(features.shape[0], 512 - features.shape[1])
            features = torch.cat([features, padding], dim=1)
        elif features.shape[1] > 512:
            features = features[:, :512]
        
        # Apply adapter
        with torch.no_grad():
            transformed_features = adapter(features)
        
        # Convert back to audio (simplified)
        transformed_features_np = transformed_features.cpu().numpy()[:, :128].T
        
        # Inverse mel spectrogram (approximation)
        # In production, use proper vocoder
        transformed_audio = librosa.feature.inverse.mel_to_audio(
            librosa.db_to_power(transformed_features_np),
            sr=22050
        )
        
        # Match original length
        if len(transformed_audio) < len(audio):
            transformed_audio = np.pad(transformed_audio, (0, len(audio) - len(transformed_audio)))
        else:
            transformed_audio = transformed_audio[:len(audio)]
        
        return transformed_audio.astype(np.float32)
    
    def _mix_with_backing(self, vocal: np.ndarray, backing_path: str) -> np.ndarray:
        """Mix vocal with backing track."""
        backing, sr = librosa.load(backing_path, sr=22050)
        
        # Match lengths
        min_len = min(len(vocal), len(backing))
        vocal = vocal[:min_len]
        backing = backing[:min_len]
        
        # Mix (80% backing, 20% vocal)
        mixed = 0.8 * backing + 0.2 * vocal
        
        # Normalize
        mixed = mixed / np.max(np.abs(mixed))
        
        return mixed


def list_adapters() -> list:
    """List all available adapters with metadata."""
    adapters_dir = Path("adapters")
    if not adapters_dir.exists():
        return []
    
    adapters = []
    for adapter_file in adapters_dir.glob("*.pth"):
        try:
            adapter_data = torch.load(adapter_file, map_location="cpu")
            metadata = adapter_data.get("metadata", {})
            training_stats = adapter_data.get("training_stats", {})
            
            size_mb = adapter_file.stat().st_size / (1024 ** 2)
            created = metadata.get("created_at", "Unknown")
            
            adapters.append({
                "name": adapter_file.stem,
                "path": str(adapter_file),
                "size_mb": size_mb,
                "created_at": created,
                "training_stats": training_stats
            })
        except Exception as e:
            print(f"Error loading {adapter_file}: {e}")
            continue
    
    return sorted(adapters, key=lambda x: x["created_at"], reverse=True)


if __name__ == "__main__":
    # Example usage
    print("VoiceAdapter Module - Example Usage")
    
    # Example: Train adapter
    config = AdapterConfig(mode="ordinary", epochs=50)
    trainer = AdapterTrainer(config)
    
    # Example: Apply adapter
    inference = AdapterInference()
    # output = inference.apply_adapter(
    #     "models/base.onnx",
    #     "adapters/my_style.pth",
    #     "Test lyrics for voice synthesis"
    # )
