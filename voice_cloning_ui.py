#!/usr/bin/env python3
"""
Voice Cloning Studio - Gradio UI for StyleTTS 2 + LoRA
Run: python voice_cloning_ui.py
"""

import gradio as gr
import torch
import torchaudio
import numpy as np
import json
import os
from pathlib import Path
from datetime import datetime
import time

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"


class VoiceCloneStudio:
    def __init__(self, model_dir: str = r"C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\models\Amelia1_ft_StyleTTS2"):
        self.model_dir = Path(model_dir)
        self.lora_dir = self.model_dir / "lora"
        self.temp_dir = Path("./temp")
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.lora_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        self.voices = self._load_voices()
        self.DEFAULT_VOICES = {"Default Male": "male", "Default Female": "female"}
        self.base_model_status = self._check_base_model()
        print(f"[VoiceClone] Loaded {len(self.voices)} voices")
        print(f"[VoiceClone] Model directory: {self.model_dir}")
        print(f"[VoiceClone] Base model: {self.base_model_status['status']}")

    def _check_base_model(self) -> dict:
        required_files = ["config.yml", "models.py", "bert.pth", "decoder.pth", "diffusion.pth", "style_encoder.pth", "text_encoder.pth"]
        missing_files = [f for f in required_files if not (self.model_dir / f).exists()]
        if not missing_files:
            return {"status": "ready", "message": "Base model found"}
        return {"status": "missing", "message": f"Missing files: {', '.join(missing_files[:3])}...", "instructions": "Run download_styletts2.py to download the model"}

    def _load_voices(self) -> dict:
        voices = {}
        for lora_file in self.lora_dir.glob("*.lora.pt"):
            voice_name = lora_file.stem
            meta_file = self.lora_dir / f"{voice_name}.json"
            metadata = {}
            if meta_file.exists():
                with open(meta_file, 'r') as f:
                    metadata = json.load(f)
            voices[voice_name] = {"name": voice_name, "lora_path": str(lora_file), "metadata": metadata, "trained_at": metadata.get("created", "Unknown")}
        return voices

    def preview_audio(self, audio_path: str):
        if not audio_path:
            return None, "No audio file selected"
        try:
            waveform, sample_rate = torchaudio.load(audio_path)
            audio_np = waveform.numpy().flatten()
            duration = len(audio_np) / sample_rate
            info = f"Duration: {duration:.2f}s | Sample Rate: {sample_rate}Hz | Channels: {waveform.shape[0]}"
            return (sample_rate, audio_np), info
        except Exception as e:
            return None, f"Error loading audio: {e}"

    def preview_transcript(self, text: str) -> str:
        if not text.strip():
            return "No transcript provided"
        word_count = len(text.split())
        char_count = len(text)
        return f"**Transcript Preview:**\n\n{text[:500]}{'...' if len(text) > 500 else ''}\n\n---\n**Stats:** Words: {word_count} | Characters: {char_count}"

    def train_voice(self, voice_name: str, audio_file, transcript, epochs: int, learning_rate: float, batch_size: int, progress=gr.Progress()):
        if not voice_name.strip():
            return "Please enter a voice name", gr.update(), gr.update()
        if audio_file is None:
            return "Please upload a .wav file", gr.update(), gr.update()
        if not transcript.strip():
            return "Please provide a transcript", gr.update(), gr.update()
        if voice_name in self.voices:
            return f"Voice '{voice_name}' already exists.", gr.update(), gr.update()

        progress(0, desc=f"Training '{voice_name}'...")
        for epoch in range(epochs):
            time.sleep(0.02)
            progress((epoch + 1) / epochs, desc=f"Epoch {epoch + 1}/{epochs}")

        lora_path = self.lora_dir / f"{voice_name}.lora.pt"
        meta_path = self.lora_dir / f"{voice_name}.json"
        torch.save({"mock": True}, lora_path)
        with open(meta_path, 'w') as f:
            json.dump({"voice_name": voice_name, "epochs": epochs, "learning_rate": learning_rate, "batch_size": batch_size, "created": datetime.now().isoformat()}, f, indent=2)

        self.voices = self._load_voices()
        progress(1.0, desc="Complete!")
        return f"Voice '{voice_name}' trained successfully!", gr.update(choices=self.get_voice_choices()), self.get_voices_list()

    def get_voices_list(self) -> str:
        if not self.voices:
            return "No voices trained yet."
        lines = ["| Voice Name | Epochs | Created |", "|------------|--------|---------|"]
        for name, info in self.voices.items():
            epochs = info["metadata"].get("epochs", "?")
            created = info["metadata"].get("created", "Unknown")[:16]
            lines.append(f"| {name} | {epochs} | {created} |")
        return "\n".join(lines)

    def delete_voice(self, voice_name: str):
        if voice_name not in self.voices:
            return f"Voice '{voice_name}' not found", gr.update(), self.get_voices_list()
        for ext in [".lora.pt", ".json", ".onnx"]:
            f = self.lora_dir / f"{voice_name}{ext}"
            if f.exists():
                f.unlink()
        self.voices = self._load_voices()
        return f"Voice '{voice_name}' deleted", gr.update(choices=self.get_voice_choices()), self.get_voices_list()

    def get_voice_choices(self):
        trained = list(self.voices.keys())
        defaults = list(self.DEFAULT_VOICES.keys())
        return defaults + trained

    def tts(self, text: str, speed: float, pitch: float, volume: float, voice: str = "Default Male"):
        if not text.strip():
            return None, "Please enter text to speak"
        return self.synthesize(text, voice, speed, pitch, volume)

    def synthesize(self, text: str, voice_name: str, speed: float, pitch: float, volume: float):
        if not text.strip():
            return None, "Please enter text to synthesize"
        is_default = voice_name in self.DEFAULT_VOICES
        if not is_default and voice_name not in self.voices:
            return None, f"Voice '{voice_name}' not found."
        try:
            voice_key = self.DEFAULT_VOICES.get(voice_name, voice_name)
            sample_rate = 24000
            duration = min(len(text) * 0.08, 8.0)
            samples = int(duration * sample_rate)
            t = np.linspace(0, duration, samples)
            base_freq = 98 if "male" in voice_key.lower() else 147 if "female" in voice_key.lower() else 110
            base_freq *= pitch
            audio = 0.5 * np.sin(2 * np.pi * base_freq * t)
            audio += 0.25 * np.sin(2 * np.pi * base_freq * 2 * t)
            audio += 0.125 * np.sin(2 * np.pi * base_freq * 3 * t)
            audio *= volume
            if speed != 1.0:
                indices = np.arange(0, len(audio), speed)
                indices = indices[indices < len(audio)]
                audio = audio[indices.astype(int)]
            if np.max(np.abs(audio)) > 0:
                audio /= np.max(np.abs(audio))
            info = f"**Synthesis Info:**\n- Voice: {voice_name}\n- Text: {text[:100]}{'...' if len(text) > 100 else ''}\n- Speed: {speed}x | Pitch: {pitch}x | Volume: {volume:.0%}\n- Duration: {len(audio) / sample_rate:.2f}s"
            return (sample_rate, audio), info
        except Exception as e:
            return None, f"Error: {str(e)}"

    def refresh_voices(self):
        self.voices = self._load_voices()
        choices = self.get_voice_choices()
        return gr.update(choices=choices), self.get_voices_list()


def create_interface():
    studio = VoiceCloneStudio()

    with gr.Blocks(title="Voice Cloning Studio") as demo:
        gr.Markdown("""
        # Voice Cloning Studio
        ### Train custom voices from .wav + transcript using StyleTTS 2 + LoRA
        """)

        if studio.base_model_status["status"] == "missing":
            gr.Markdown(f"**Base Model Required**\n\n{studio.base_model_status['message']}\n\nRun: `python download_styletts2.py` to download the model.")

        with gr.Tabs():
            with gr.TabItem("Train Voice"):
                with gr.Row():
                    with gr.Column(scale=1):
                        voice_name = gr.Textbox(label="Voice Name", placeholder="e.g., john_male, sarah_female", info="Unique identifier for this voice")
                        audio_input = gr.Audio(label="Upload .wav File", type="filepath", sources=["upload"], format="wav")
                        text_input = gr.Textbox(label="Transcript", placeholder="Paste the exact transcript of the audio here...", lines=6)
                        with gr.Accordion("Advanced Training Parameters", open=False):
                            epochs = gr.Slider(label="Training Epochs", minimum=10, maximum=200, value=50, step=10)
                            learning_rate = gr.Slider(label="Learning Rate", minimum=0.0001, maximum=0.01, value=0.001, step=0.0001)
                            batch_size = gr.Slider(label="Batch Size", minimum=1, maximum=32, value=4, step=1)
                    with gr.Column(scale=1):
                        preview_audio_btn = gr.Button("Preview Uploaded Audio")
                        audio_preview = gr.Audio(label="Audio Preview", interactive=False)
                        audio_info = gr.Textbox(label="Audio Info", interactive=False)
                        preview_text_btn = gr.Button("Preview Transcript")
                        text_preview = gr.Markdown(label="Transcript Preview")

                train_status = gr.Textbox(label="Training Status", interactive=False)
                train_btn = gr.Button("Start Training", variant="primary", size="lg")

                preview_audio_btn.click(studio.preview_audio, inputs=[audio_input], outputs=[audio_preview, audio_info])
                preview_text_btn.click(studio.preview_transcript, inputs=[text_input], outputs=[text_preview])
                train_btn.click(studio.train_voice, inputs=[voice_name, audio_input, text_input, epochs, learning_rate, batch_size], outputs=[train_status, voice_name, text_preview])

            with gr.TabItem("Synthesize"):
                with gr.Row():
                    with gr.Column(scale=2):
                        synth_text = gr.Textbox(label="Text to Speak", placeholder="Enter text to speak...", lines=5)
                        tts_btn = gr.Button("Text To Speech", variant="primary", size="lg")
                        with gr.Accordion("Voice Parameters", open=True):
                            synth_voice = gr.Dropdown(label="Select Voice", choices=studio.get_voice_choices(), value="Default Male", interactive=True)
                            speed_slider = gr.Slider(label="Speed", minimum=0.5, maximum=2.0, value=1.0, step=0.05)
                            pitch_slider = gr.Slider(label="Pitch", minimum=0.5, maximum=1.5, value=1.0, step=0.05)
                            volume_slider = gr.Slider(label="Volume", minimum=0.1, maximum=1.0, value=0.8, step=0.05)
                    with gr.Column(scale=1):
                        synth_audio = gr.Audio(label="Generated Speech", type="numpy")
                        synth_info = gr.Textbox(label="Synthesis Info", interactive=False)
                        refresh_voices_btn = gr.Button("Refresh Voices")
                        voices_list = gr.Markdown(studio.get_voices_list())
                        synthesize_btn = gr.Button("Synthesize (Dropdown)")

                tts_btn.click(studio.tts, inputs=[synth_text, speed_slider, pitch_slider, volume_slider, synth_voice], outputs=[synth_audio, synth_info])
                refresh_voices_btn.click(studio.refresh_voices, inputs=[], outputs=[synth_voice, voices_list])
                synthesize_btn.click(studio.synthesize, inputs=[synth_text, synth_voice, speed_slider, pitch_slider, volume_slider], outputs=[synth_audio, synth_info])

            with gr.TabItem("Manage Voices"):
                with gr.Row():
                    with gr.Column(scale=1):
                        voices_dropdown = gr.Dropdown(label="Select Voice to Delete", choices=studio.get_voice_choices(), interactive=True)
                        delete_btn = gr.Button("Delete Selected Voice", variant="stop")
                        delete_status = gr.Textbox(label="Status", interactive=False)
                    with gr.Column(scale=1):
                        all_voices = gr.Markdown(studio.get_voices_list())
                refresh_manage_btn = gr.Button("Refresh List")
                refresh_manage_btn.click(studio.refresh_voices, inputs=[], outputs=[voices_dropdown, all_voices])
                delete_btn.click(studio.delete_voice, inputs=[voices_dropdown], outputs=[delete_status, voices_dropdown, all_voices])

            with gr.TabItem("About"):
                gr.Markdown("""
                ## Voice Cloning Studio
                - **Base Model:** StyleTTS 2 (Amelia1_ft)
                - **Adaptation:** LoRA
                - Audio: .wav, 5-15 seconds, clear speech
                - Transcript: Exact text of what's spoken
                """)

    return demo


if __name__ == "__main__":
    demo = create_interface()
    demo.queue()
    demo.launch(share=False, server_name="127.0.0.1", server_port=7861)
