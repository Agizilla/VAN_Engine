import shutil
import tempfile
from pathlib import Path
from typing import Any, Optional

from .base import BaseSkill, register_skill

_audio_instance = None
_whisper_model = None
_demucs_model = None


def _get_audio():
    global _audio_instance
    if _audio_instance is None:
        from ..tools.master_skills.audioSkill import AudioSkill
        _audio_instance = AudioSkill()
    return _audio_instance


def _load_whisper():
    global _whisper_model
    if _whisper_model is None:
        import whisper
        _whisper_model = whisper.load_model("base")
    return _whisper_model


def _load_demucs():
    global _demucs_model
    if _demucs_model is None:
        from ..tools.master_skills.audioSkill import DemucsSeparator
        _demucs_model = DemucsSeparator()
    return _demucs_model


def _resample_to_16khz(input_path: str, tmpdir: str) -> str:
    import librosa
    import soundfile as sf
    y, sr = librosa.load(input_path, sr=None, mono=True)
    if sr != 16000:
        y = librosa.resample(y, orig_sr=sr, target_sr=16000)
        out = str(Path(tmpdir) / f"resampled_{Path(input_path).name}")
        sf.write(out, y, 16000)
        return out
    return input_path


@register_skill("audio_transcribe", "audio")
class AudioTranscribeSkill(BaseSkill):
    name = "audio_transcribe"
    description = "Transcribe audio to text using Whisper"
    category = "audio"
    def execute(self, **kwargs) -> dict:
        path = Path(kwargs.get("path", ""))
        if not path.exists():
            return {"error": f"File not found: {path}"}
        tmpdir = tempfile.mkdtemp()
        try:
            self.publish("progress", {"type": "progress", "current": 0, "total": 1})
            audio_path = _resample_to_16khz(str(path), tmpdir)
            result = _get_audio().transcribe(audio_path, word_timestamps=True)
            self.publish("progress", {"type": "progress", "current": 1, "total": 1})
            return {"result": {"text": result["text"], "segments": result["segments"]}}
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


@register_skill("audio_separate_stems", "audio")
class AudioSeparateStemsSkill(BaseSkill):
    name = "audio_separate_stems"
    description = "Separate audio into vocal/beat/bass/drum stems using Demucs"
    category = "audio"
    def execute(self, **kwargs) -> dict:
        path = Path(kwargs.get("path", ""))
        if not path.exists():
            return {"error": f"File not found: {path}"}
        output_dir = Path(kwargs.get("output_dir", "")) if kwargs.get("output_dir") else None
        tmpdir = tempfile.mkdtemp() if output_dir is None else None
        try:
            target_dir = output_dir or Path(tmpdir)
            _load_demucs()
            self.publish("progress", {"type": "progress", "current": 0, "total": 4})
            stems = _get_audio().separate_stems(path, target_dir)
            self.publish("progress", {"type": "progress", "current": 4, "total": 4})
            return {"result": {k: str(v) for k, v in stems.items()}}
        finally:
            if tmpdir is not None:
                shutil.rmtree(tmpdir, ignore_errors=True)


@register_skill("audio_analyze", "audio")
class AudioAnalyzeSkill(BaseSkill):
    name = "audio_analyze"
    description = "Analyze audio: BPM, key, duration, MFCC profile"
    category = "audio"
    def execute(self, **kwargs) -> dict:
        path = Path(kwargs.get("path", ""))
        if not path.exists():
            return {"error": f"File not found: {path}"}
        self.publish("progress", {"type": "progress", "current": 0, "total": 1})
        analysis = _get_audio().analyze(path)
        self.publish("progress", {"type": "progress", "current": 1, "total": 1})
        return {"result": analysis}


@register_skill("audio_voice_clone", "audio")
class AudioVoiceCloneSkill(BaseSkill):
    name = "audio_voice_clone"
    description = "Clone voice from source to target audio using ECAPA-TDNN embeddings"
    category = "audio"
    def execute(self, **kwargs) -> dict:
        src = Path(kwargs.get("source", ""))
        tgt = Path(kwargs.get("target", ""))
        if not src.exists() or not tgt.exists():
            return {"error": "Source or target file not found"}
        self.publish("progress", {"type": "progress", "current": 0, "total": 1})
        out = _get_audio().clone_voice(src, tgt)
        self.publish("progress", {"type": "progress", "current": 1, "total": 1})
        return {"result": {"clone_path": str(out)}}


@register_skill("audio_synthesize", "audio")
class AudioSynthesizeSkill(BaseSkill):
    name = "audio_synthesize"
    description = "Synthesize speech from text using Piper TTS"
    category = "audio"
    def execute(self, **kwargs) -> dict:
        text = kwargs.get("text", "")
        if not text:
            return {"error": "No text provided"}
        model_path = Path(kwargs.get("model", "")) if kwargs.get("model") else None
        out = _get_audio().synthesize(text, model_path)
        return {"result": {"path": str(out)}}


@register_skill("audio_remix", "audio")
class AudioRemixSkill(BaseSkill):
    name = "audio_remix"
    description = "Remix audio: mix vocals from one source with beats from another"
    category = "audio"
    def execute(self, **kwargs) -> dict:
        path = Path(kwargs.get("path", ""))
        if not path.exists():
            return {"error": f"File not found: {path}"}
        out = _get_audio().remix(path)
        return {"result": {"path": str(out)}}


@register_skill("audio_mix_stems", "audio")
class AudioMixStemsSkill(BaseSkill):
    name = "audio_mix_stems"
    description = "Mix multiple stem WAV files into one with adjustable volumes"
    category = "audio"
    def execute(self, **kwargs) -> dict:
        stem_paths = [Path(p) for p in kwargs.get("stems", [])]
        if not stem_paths:
            return {"error": "No stem paths provided"}
        volumes = kwargs.get("volumes")
        out = _get_audio().mix(stem_paths, volumes=volumes)
        return {"result": {"path": str(out)}}


@register_skill("audio_lyrics", "audio")
class AudioLyricsSkill(BaseSkill):
    name = "audio_lyrics"
    description = "Generate lyrics using Markov chain from training corpus"
    category = "audio"
    def execute(self, **kwargs) -> dict:
        corpus = kwargs.get("corpus")
        seed = kwargs.get("seed")
        length = kwargs.get("length", 20)
        lyrics = _get_audio().generate_lyrics(corpus, seed, length)
        return {"result": {"lyrics": lyrics}}


@register_skill("audio_align", "audio")
class AudioAlignSkill(BaseSkill):
    name = "audio_align"
    description = "Force-align lyrics text to audio using DTW"
    category = "audio"
    def execute(self, **kwargs) -> dict:
        path = Path(kwargs.get("path", ""))
        text = kwargs.get("text", "")
        if not path.exists() or not text:
            return {"error": "File or text missing"}
        alignment = _get_audio().align_lyrics(path, text)
        return {"result": {
            "words": [{"word": w.word, "start": w.start, "end": w.end} for w in alignment.words],
            "duration": alignment.duration
        }}


@register_skill("audio_music_video", "audio")
class AudioMusicVideoSkill(BaseSkill):
    name = "audio_music_video"
    description = "Generate a music video from audio + images"
    category = "audio"
    def execute(self, **kwargs) -> dict:
        audio_path = Path(kwargs.get("audio", ""))
        images = [Path(p) for p in kwargs.get("images", [])]
        if not audio_path.exists() or not images:
            return {"error": "Audio file or images missing"}
        out = _get_audio().generate_music_video(audio_path, images)
        return {"result": {"path": str(out)}}


@register_skill("audio_noise_cancel", "audio")
class AudioNoiseCancelSkill(BaseSkill):
    name = "audio_noise_cancel"
    description = "Apply noise cancellation / spectral gating to audio"
    category = "audio"
    def execute(self, **kwargs) -> dict:
        path = Path(kwargs.get("path", ""))
        if not path.exists():
            return {"error": "File not found"}
        from ..tools.master_skills.audioSkill import NoiseCanceller, load_audio, save_audio
        y, sr = load_audio(path)
        canceller = NoiseCanceller()
        cleaned = canceller.spectral_gate(y, sr, kwargs.get("threshold", -40))
        output = Path(kwargs.get("output", "")) if kwargs.get("output") else path.parent / f"denoised_{path.name}"
        save_audio(output, cleaned, sr)
        return {"result": {"path": str(output)}}


@register_skill("audio_batch_process", "audio")
class AudioBatchProcessSkill(BaseSkill):
    name = "audio_batch_process"
    description = "Batch process multiple audio files through stem separation"
    category = "audio"
    def execute(self, **kwargs) -> dict:
        files = [Path(p) for p in kwargs.get("files", [])]
        if not files:
            return {"error": "No files provided"}
        from ..tools.master_skills.audioSkill import BatchProcessor
        processor = BatchProcessor()
        total = len(files)
        self.publish("progress", {"type": "progress", "current": 0, "total": total})
        results = processor.batch_stem_separate(files)
        self.publish("progress", {"type": "progress", "current": total, "total": total})
        return {"result": {str(k): {sk: str(sp) for sk, sp in v.items()} for k, v in results.items()}}


@register_skill("audio_list_models", "audio")
class AudioListModelsSkill(BaseSkill):
    name = "audio_list_models"
    description = "List available TTS models and voice clones"
    category = "audio"
    def execute(self, **kwargs) -> dict:
        models = _get_audio().list_models()
        return {"result": models}


@register_skill("audio_info", "audio")
class AudioInfoSkill(BaseSkill):
    name = "audio_info"
    description = "Get audio skill metadata and capabilities"
    category = "audio"
    def execute(self, **kwargs) -> dict:
        from ..tools.master_skills.audioSkill import __meta__
        return {"result": __meta__}
