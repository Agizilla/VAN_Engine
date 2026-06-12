#!/usr/bin/env python3
"""
Local TTS inference using StyleTTS2 fine-tuned model (Amelia1_ft_StyleTTS2).
Can also fall back to ONNX if available.

Usage:
  python tts_local.py --text "Hello world" --output output.wav
  python tts_local.py --text "Hello world" --play
"""

import argparse
import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path


MODEL_DIR = Path(__file__).resolve().parent / "models" / "Amelia1_ft_StyleTTS2"
STYLETTS2_DIR = Path(__file__).resolve().parent / "StyleTTS2"


MODEL_WEIGHTS = {
    "bert": "bert.pth",
    "bert_encoder": "bert_encoder.pth",
    "decoder": "decoder.pth",
    "diffusion": "diffusion.pth",
    "mpd": "mpd.pth",
    "msd": "msd.pth",
    "pitch_extractor": "pitch_extractor.pth",
    "predictor": "predictor.pth",
    "predictor_encoder": "predictor_encoder.pth",
    "style_encoder": "style_encoder.pth",
    "text_aligner": "text_aligner.pth",
    "text_encoder": "text_encoder.pth",
    "wd": "wd.pth",
}


def check_deps():
    missing = []
    try:
        import numpy
    except ImportError:
        missing.append("numpy")
    try:
        import soundfile
    except ImportError:
        missing.append("soundfile")
    try:
        import onnxruntime
    except ImportError:
        pass
    try:
        import torch
    except ImportError:
        missing.append("torch")
    return missing


def has_styletts2():
    return STYLETTS2_DIR.exists() and (STYLETTS2_DIR / "models.py").exists()


def has_utils():
    utils_asr = MODEL_DIR / "Utils" / "ASR" / "models.py"
    utils_jdc = MODEL_DIR / "Utils" / "JDC" / "model.py"
    return utils_asr.exists() or (STYLETTS2_DIR / "Utils" / "ASR" / "models.py").exists()


def _strip_module_prefix(state_dict):
    from collections import OrderedDict
    new_sd = OrderedDict()
    for k, v in state_dict.items():
        name = k[7:] if k.startswith("module.") else k
        new_sd[name] = v
    return new_sd


def _get_reference_style(model, device, ref_path=None):
    """Compute style vector from reference audio or generate a synthetic one."""
    import numpy as np
    import torch
    import librosa
    import torchaudio

    to_mel = torchaudio.transforms.MelSpectrogram(
        n_mels=80, n_fft=2048, win_length=1200, hop_length=300
    )
    mean, std = -4, 4

    def preprocess(wave):
        wave_tensor = torch.from_numpy(wave).float()
        mel_tensor = to_mel(wave_tensor)
        mel_tensor = (torch.log(1e-5 + mel_tensor.unsqueeze(0)) - mean) / std
        return mel_tensor

    if ref_path and os.path.exists(ref_path):
        wave, sr = librosa.load(ref_path, sr=24000)
        audio, _ = librosa.effects.trim(wave, top_db=30)
        if sr != 24000:
            audio = librosa.resample(audio, sr, 24000)
    else:
        duration = 2.0
        t = np.linspace(0, duration, int(24000 * duration), endpoint=False)
        audio = 0.5 * np.sin(2 * np.pi * 220 * t)

    mel_tensor = preprocess(audio).to(device)
    with torch.no_grad():
        ref_s = model.style_encoder(mel_tensor.unsqueeze(1))
        ref_p = model.predictor_encoder(mel_tensor.unsqueeze(1))
    return torch.cat([ref_s, ref_p], dim=1)


def synthesize_pytorch(text, output_path, voice_cfg=None):
    """Full StyleTTS2 PyTorch inference following official notebook pattern."""
    import sys
    sys.path.insert(0, str(STYLETTS2_DIR))
    sys.path.insert(0, str(STYLETTS2_DIR / "Utils"))

    import yaml
    import numpy as np
    import torch
    import torch.nn.functional as F
    import torchaudio
    import librosa
    from munch import Munch, munchify

    device = "cuda" if torch.cuda.is_available() else "cpu"

    # 1. Load config
    with open(MODEL_DIR / "config.yml") as f:
        config = yaml.safe_load(f)

    # 2. Load ASR (text aligner)
    from models import load_ASR_models
    asr_config = str(MODEL_DIR / config["ASR_config"])
    asr_path = str(MODEL_DIR / config["ASR_path"])
    text_aligner = load_ASR_models(asr_path, asr_config)
    text_aligner = text_aligner.to(device)

    # 3. Load F0 (pitch extractor)
    from models import load_F0_models
    f0_path = str(MODEL_DIR / config["F0_path"])
    pitch_extractor = load_F0_models(f0_path)
    pitch_extractor = pitch_extractor.to(device)

    # 4. Load BERT
    from Utils.PLBERT.util import load_plbert
    bert_path = str(MODEL_DIR / config["PLBERT_dir"])
    plbert = load_plbert(bert_path)
    plbert = plbert.to(device)

    # 5. Build model
    from utils import recursive_munch
    model_params = recursive_munch(config["model_params"])
    from models import build_model
    model = build_model(model_params, text_aligner, pitch_extractor, plbert)
    _ = [model[key].to(device) for key in model]

    # 6. Load weights from individual .pth files (strip module. prefix)
    for key, fname in MODEL_WEIGHTS.items():
        if key in model and (MODEL_DIR / fname).exists():
            sd = torch.load(MODEL_DIR / fname, map_location=device, weights_only=False)
            sd = _strip_module_prefix(sd)
            model[key].load_state_dict(sd, strict=False)
            print(f"  Loaded {key} from {fname}")

    _ = [model[key].eval() for key in model]

    # 7. Set up diffusion sampler
    from Modules.diffusion.sampler import DiffusionSampler, ADPM2Sampler, KarrasSchedule
    sampler = DiffusionSampler(
        model.diffusion.diffusion,
        sampler=ADPM2Sampler(),
        sigma_schedule=KarrasSchedule(sigma_min=0.0001, sigma_max=3.0, rho=9.0),
        clamp=False,
    )

    # 8. Compute reference style
    ref_s = _get_reference_style(model, device)

    # 9. Text preprocessing
    from text_utils import TextCleaner
    textclenaer = TextCleaner()

    text = text.strip()
    tokens = textclenaer(text)
    tokens.insert(0, 0)
    tokens = torch.LongTensor(tokens).to(device).unsqueeze(0)

    def length_to_mask(lengths):
        mask = torch.arange(lengths.max()).unsqueeze(0).expand(lengths.shape[0], -1).type_as(lengths)
        mask = torch.gt(mask + 1, lengths.unsqueeze(1))
        return mask

    # 10. Inference
    alpha = 0.3
    beta = 0.7
    diffusion_steps = 10
    embedding_scale = 1

    with torch.no_grad():
        input_lengths = torch.LongTensor([tokens.shape[-1]]).to(device)
        text_mask = length_to_mask(input_lengths).to(device)

        t_en = model.text_encoder(tokens, input_lengths, text_mask)
        bert_dur = model.bert(tokens, attention_mask=(~text_mask).int())
        d_en = model.bert_encoder(bert_dur).transpose(-1, -2)

        s_pred = sampler(
            noise=torch.randn((1, 256)).unsqueeze(1).to(device),
            embedding=bert_dur,
            embedding_scale=embedding_scale,
            features=ref_s,
            num_steps=diffusion_steps,
        ).squeeze(1)

        s = s_pred[:, 128:]
        ref = s_pred[:, :128]
        ref = alpha * ref + (1 - alpha) * ref_s[:, :128]
        s = beta * s + (1 - beta) * ref_s[:, 128:]

        d = model.predictor.text_encoder(d_en, s, input_lengths, text_mask)
        x, _ = model.predictor.lstm(d)
        duration = model.predictor.duration_proj(x)
        duration = torch.sigmoid(duration).sum(axis=-1)
        pred_dur = torch.round(duration.squeeze()).clamp(min=1)

        pred_aln_trg = torch.zeros(input_lengths, int(pred_dur.sum().data))
        c_frame = 0
        for i in range(pred_aln_trg.size(0)):
            pred_aln_trg[i, c_frame : c_frame + int(pred_dur[i].data)] = 1
            c_frame += int(pred_dur[i].data)

        en = d.transpose(-1, -2) @ pred_aln_trg.unsqueeze(0).to(device)
        if model_params.decoder.type == "hifigan":
            asr_new = torch.zeros_like(en)
            asr_new[:, :, 0] = en[:, :, 0]
            asr_new[:, :, 1:] = en[:, :, 0:-1]
            en = asr_new

        F0_pred, N_pred = model.predictor.F0Ntrain(en, s)
        asr = t_en @ pred_aln_trg.unsqueeze(0).to(device)
        if model_params.decoder.type == "hifigan":
            asr_new = torch.zeros_like(asr)
            asr_new[:, :, 0] = asr[:, :, 0]
            asr_new[:, :, 1:] = asr[:, :, 0:-1]
            asr = asr_new

        out = model.decoder(asr, F0_pred, N_pred, ref.squeeze().unsqueeze(0))

    audio = out.squeeze().cpu().numpy()[..., :-50]
    import soundfile as sf
    sf.write(output_path, audio, 24000)
    return output_path


def synthesize_onnx(text, output_path):
    """Lightweight ONNX inference."""
    sys.path.insert(0, str(MODEL_DIR))
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))

    from onnx_inference import StyleTTS2ONNX

    tts = StyleTTS2ONNX(str(MODEL_DIR / "lora"))
    audio = tts.synthesize(text, "default")
    import soundfile as sf
    sf.write(output_path, audio, 24000)
    return output_path


def synthesize_sapi(text, output_path):
    """Windows SAPI fallback - write a WAV using PowerShell."""
    ps_script = f'''
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.SetOutputToWaveFile("{output_path}")
$synth.Speak('{text.replace("'", "''")}')
$synth.Dispose()
'''
    subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], check=True, capture_output=True)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Local TTS inference")
    parser.add_argument("--text", required=True, help="Text to synthesize")
    parser.add_argument("--output", help="Output WAV file path")
    parser.add_argument("--play", action="store_true", help="Play audio after synthesis")
    parser.add_argument("--engine", choices=["auto", "pytorch", "onnx", "sapi"], default="auto",
                        help="TTS engine to use")
    args = parser.parse_args()

    if args.output:
        output_path = args.output
    else:
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        output_path = tmp.name
        tmp.close()

    engine = args.engine

    if engine == "auto":
        try:
            import torch
            if has_styletts2():
                engine = "pytorch"
            else:
                try:
                    import onnxruntime
                    if list((MODEL_DIR / "lora").glob("*.onnx")):
                        engine = "onnx"
                    else:
                        engine = "sapi"
                except ImportError:
                    engine = "sapi"
        except ImportError:
            try:
                import onnxruntime
                if list((MODEL_DIR / "lora").glob("*.onnx")):
                    engine = "onnx"
                else:
                    engine = "sapi"
            except ImportError:
                engine = "sapi"

    engines = {
        "pytorch": ("StyleTTS2 (PyTorch)", synthesize_pytorch),
        "onnx": ("ONNX Runtime", synthesize_onnx),
        "sapi": ("Windows SAPI", synthesize_sapi),
    }

    name, func = engines.get(engine, engines["sapi"])
    print(f"[TTS] Engine: {name}")

    try:
        func(args.text, output_path)
        print(f"[TTS] Output: {output_path}")

        if args.play:
            subprocess.run([
                "powershell", "-NoProfile", "-Command",
                f'(New-Object Media.SoundPlayer "{output_path}").PlaySync()'
            ], check=True)
    except Exception as e:
        print(f"[TTS] Error with {name}: {e}", file=sys.stderr)
        if engine != "sapi":
            print("[TTS] Falling back to SAPI...")
            synthesize_sapi(args.text, output_path)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
