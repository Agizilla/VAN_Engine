# path: Services/ClawdiaBridge/transposer.py
import sys, json, os, tempfile, struct, math, argparse, io
import numpy as np

EMOTIONAL_DICT_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'emotional_dictionary.json')
EMOTIONAL_DICT = {}
if os.path.exists(EMOTIONAL_DICT_PATH):
    with open(EMOTIONAL_DICT_PATH, 'r') as f:
        EMOTIONAL_DICT = json.load(f)

HAS_SCIPY = False
HAS_SOUNDFILE = False
HAS_LIBROSA = False
try:
    import scipy.io.wavfile as wavfile
    import scipy.signal as signal
    HAS_SCIPY = True
except: pass
try:
    import soundfile as sf
    HAS_SOUNDFILE = True
except: pass
try:
    import librosa
    HAS_LIBROSA = True
except: pass

NOP = lambda *a, **k: None
log = NOP

def stft(x, n_fft=2048, hop_length=512, win_length=None, window='hann'):
    if HAS_LIBROSA:
        return librosa.stft(x.astype(np.float32), n_fft=n_fft, hop_length=hop_length, win_length=win_length or n_fft, window=window)
    win = signal.get_window(window, win_length or n_fft)
    n_frames = 1 + (len(x) - len(win)) // hop_length
    X = np.zeros((1 + n_fft // 2, n_frames), dtype=np.complex128)
    for i in range(n_frames):
        frame = x[i * hop_length:i * hop_length + len(win)]
        if len(frame) < len(win):
            frame = np.pad(frame, (0, len(win) - len(frame)))
        X[:, i] = np.fft.rfft(frame * win, n=n_fft)
    return X

def istft(X, hop_length=512, win_length=None, window='hann', n_fft=None):
    if HAS_LIBROSA:
        return librosa.istft(X.astype(np.complex64), hop_length=hop_length, win_length=win_length, window=window)
    n_fft = n_fft or 2 * (X.shape[0] - 1)
    win = signal.get_window(window, win_length or n_fft)
    n_frames = X.shape[1]
    expected_len = hop_length * (n_frames - 1) + len(win)
    y = np.zeros(expected_len)
    for i in range(n_frames):
        frame = np.fft.irfft(X[:, i], n=n_fft).real[:len(win)] * win
        start = i * hop_length
        end = start + len(frame)
        y[start:end] += frame
    return y

def formant_shift(X, sr, shift_ratio=1.0):
    if abs(shift_ratio - 1.0) < 0.001:
        return X
    n_bins, n_frames = X.shape
    freqs = np.fft.rfftfreq(2 * (n_bins - 1), 1.0 / sr)
    shifted = np.zeros_like(X, dtype=np.complex128)
    target_freqs = freqs * shift_ratio
    for i in range(n_bins):
        target = target_freqs[i]
        if target > freqs[-1]:
            continue
        src_idx = np.argmin(np.abs(freqs - target))
        shifted[i, :] = X[src_idx, :]
    return shifted

def pitch_shift_phase_vocoder(X, shift_semitones=0):
    if abs(shift_semitones) < 0.01:
        return X
    ratio = 2.0 ** (shift_semitones / 12.0)
    n_bins, n_frames = X.shape
    new_n_frames = max(1, int(n_frames / ratio))
    phase = np.angle(X)
    magnitude = np.abs(X)
    phase_advance = 2 * np.pi * np.arange(n_bins)[:, None] * (ratio - 1)
    phase_accum = phase[:, 0:1]
    resynth = np.zeros((n_bins, new_n_frames), dtype=np.complex128)
    for i in range(new_n_frames):
        src_idx = min(int(i * ratio), n_frames - 1)
        src_idx2 = min(src_idx + 1, n_frames - 1)
        frac = (i * ratio) - src_idx
        mag = magnitude[:, src_idx] * (1 - frac) + magnitude[:, src_idx2] * frac
        phase_accum = phase_accum + phase_advance
        resynth[:, i] = mag * np.exp(1j * phase_accum[:, 0])
    return resynth

def apply_spectral_envelope(X, sr, emotion_params=None):
    if emotion_params is None:
        emotion_params = {}
    brightness = emotion_params.get('brightness', 0.0)
    warmth = emotion_params.get('warmth', 0.0)
    breathiness = emotion_params.get('breathiness', 0.0)
    n_bins = X.shape[0]
    freqs = np.fft.rfftfreq(2 * (n_bins - 1), 1.0 / sr)
    eq = np.ones(n_bins)
    if brightness > 0:
        eq *= 1.0 + brightness * (freqs / (sr / 2))
    elif brightness < 0:
        shelf = 1.0 + brightness * (1.0 - freqs / (sr / 2))
        eq *= np.maximum(shelf, 0.1)
    if warmth > 0:
        warmth_filter = 1.0 + warmth * np.exp(-((freqs - 500) ** 2) / (2 * (300 ** 2)))
        eq *= warmth_filter
    if breathiness > 0:
        noise_floor = breathiness * 0.05
        noise = np.random.randn(*X.shape) * noise_floor * np.abs(X)
        X = X + noise * 1j
    return X * eq[:, None]

def apply_emotion_transform(X, sr, emotion, intensity=1.0):
    emotion_presets = {
        'anger': {'brightness': 0.4 * intensity, 'warmth': -0.3 * intensity, 'breathiness': 0.0},
        'surprise': {'brightness': 0.6 * intensity, 'warmth': 0.2 * intensity, 'breathiness': 0.0},
        'tension': {'brightness': 0.2 * intensity, 'warmth': -0.4 * intensity, 'breathiness': 0.0},
        'contempt': {'brightness': -0.2 * intensity, 'warmth': -0.3 * intensity, 'breathiness': 0.0},
        'joy': {'brightness': 0.5 * intensity, 'warmth': 0.4 * intensity, 'breathiness': 0.0},
        'sadness': {'brightness': -0.3 * intensity, 'warmth': 0.1 * intensity, 'breathiness': 0.1 * intensity},
        'neutral': {'brightness': 0.0, 'warmth': 0.0, 'breathiness': 0.0},
        'fear': {'brightness': 0.5 * intensity, 'warmth': -0.5 * intensity, 'breathiness': 0.2 * intensity},
        'disgust': {'brightness': -0.3 * intensity, 'warmth': -0.5 * intensity, 'breathiness': 0.0},
        'anticipation': {'brightness': 0.3 * intensity, 'warmth': 0.2 * intensity, 'breathiness': 0.0},
        'trust': {'brightness': 0.0, 'warmth': 0.4 * intensity, 'breathiness': 0.05 * intensity},
        'love': {'brightness': 0.2 * intensity, 'warmth': 0.6 * intensity, 'breathiness': 0.15 * intensity},
    }
    new_presets = {
        'Calculation': {'brightness': -0.1 * intensity, 'warmth': -0.2 * intensity, 'breathiness': 0.0},
        'RighteousIndignation': {'brightness': 0.3 * intensity, 'warmth': -0.3 * intensity, 'breathiness': 0.0},
        'SmugSatisfaction': {'brightness': -0.1 * intensity, 'warmth': 0.3 * intensity, 'breathiness': 0.0},
        'Panic': {'brightness': 0.7 * intensity, 'warmth': -0.6 * intensity, 'breathiness': 0.3 * intensity},
        'Triumph': {'brightness': 0.5 * intensity, 'warmth': 0.3 * intensity, 'breathiness': 0.0},
        'Stonewall': {'brightness': -0.3 * intensity, 'warmth': -0.2 * intensity, 'breathiness': 0.0},
        'Curiosity': {'brightness': 0.2 * intensity, 'warmth': 0.1 * intensity, 'breathiness': 0.05 * intensity},
        'Doubt': {'brightness': -0.2 * intensity, 'warmth': 0.0 * intensity, 'breathiness': 0.1 * intensity},
        'Exhaustion': {'brightness': -0.4 * intensity, 'warmth': 0.0 * intensity, 'breathiness': 0.2 * intensity},
        'Mischief': {'brightness': 0.3 * intensity, 'warmth': 0.2 * intensity, 'breathiness': 0.0},
    }
    emotion_presets.update(new_presets)
    params = emotion_presets.get(emotion, emotion_presets['neutral'])
    X = apply_spectral_envelope(X, sr, params)
    return X

def process_wav(input_path, output_path, sr=None, formant_ratio=1.0, pitch_semitones=0.0, emotion='neutral', intensity=1.0,
                n_fft=2048, hop_length=512, window='hann',
                brightness=None, warmth=None, breathiness=None,
                formant_enabled=True, pitch_enabled=True, emotion_enabled=True, spectral_enabled=True):
    if HAS_SOUNDFILE:
        data, orig_sr = sf.read(input_path)
    elif HAS_SCIPY:
        orig_sr, data = wavfile.read(input_path)
        if data.dtype == np.int16:
            data = data.astype(np.float32) / 32768.0
    else:
        raise RuntimeError('No audio backend available (install soundfile or scipy)')

    if data.ndim > 1:
        data = data.mean(axis=1)
    sr = sr or orig_sr
    if orig_sr != sr:
        if HAS_LIBROSA:
            data = librosa.resample(data.astype(np.float32), orig_sr=orig_sr, target_sr=sr)
        else:
            ratio = sr / orig_sr
            new_len = int(len(data) * ratio)
            data = np.interp(np.linspace(0, len(data) - 1, new_len), np.arange(len(data)), data)
    
    X = stft(data, n_fft=n_fft, hop_length=hop_length, window=window)
    if formant_enabled:
        X = formant_shift(X, sr, formant_ratio)
    if pitch_enabled:
        X = pitch_shift_phase_vocoder(X, pitch_semitones)
    if emotion_enabled and spectral_enabled:
        if brightness is not None or warmth is not None or breathiness is not None:
            manual_params = {}
            if brightness is not None: manual_params['brightness'] = brightness
            if warmth is not None: manual_params['warmth'] = warmth
            if breathiness is not None: manual_params['breathiness'] = breathiness
            X = apply_spectral_envelope(X, sr, manual_params)
        else:
            X = apply_emotion_transform(X, sr, emotion, intensity)
    elif emotion_enabled:
        X = apply_emotion_transform(X, sr, emotion, intensity)
    elif spectral_enabled:
        if brightness is not None or warmth is not None or breathiness is not None:
            manual_params = {}
            if brightness is not None: manual_params['brightness'] = brightness
            if warmth is not None: manual_params['warmth'] = warmth
            if breathiness is not None: manual_params['breathiness'] = breathiness
            X = apply_spectral_envelope(X, sr, manual_params)
    y = istft(X)
    peak = np.max(np.abs(y))
    if peak > 0:
        y = y / peak * 0.95
    
    if HAS_SOUNDFILE:
        sf.write(output_path, y.astype(np.float32), sr)
    elif HAS_SCIPY:
        y_int = (y * 32767).clip(-32768, 32767).astype(np.int16)
        wavfile.write(output_path, sr, y_int)
    
    return {'status': 'ok', 'output': output_path, 'sr': sr, 'samples': len(y),
            'emotion': emotion, 'intensity': intensity,
            'n_fft': n_fft, 'hop_length': hop_length, 'window': window}

def parse_affective_tags(text):
    import re
    tags = re.findall(r'\[Emotion:\s*"([^"]+)"(?:\s*,\s*"intensity"\s*:\s*([\d.]+))?\]', text)
    if not tags:
        return None, 1.0
    last = tags[-1]
    return last[0], float(last[1]) if last[1] else 1.0

PARAM_REGISTRY = {
    'stft': {
        'n_fft': {'type': 'int', 'min': 256, 'max': 4096, 'step': 128, 'default': 2048, 'label': 'Window Size', 'group': 'STFT Engine'},
        'hop_length': {'type': 'int', 'min': 64, 'max': 2048, 'step': 64, 'default': 512, 'label': 'Hop Length', 'group': 'STFT Engine'},
        'window': {'type': 'select', 'options': ['hann','hamming','blackman','blackmanharris','nuttall'], 'default': 'hann', 'label': 'Window Type', 'group': 'STFT Engine'},
        'sr': {'type': 'select', 'options': [8000,16000,22050,24000,44100,48000], 'default': 24000, 'label': 'Sample Rate', 'group': 'STFT Engine', 'labels': {'8000':'8 kHz','16000':'16 kHz','22050':'22 kHz','24000':'24 kHz','44100':'44 kHz','48000':'48 kHz'}},
    },
    'voice': {
        'formant_ratio': {'type': 'float', 'min': 0.5, 'max': 2.0, 'step': 0.01, 'default': 1.0, 'label': 'Formant Ratio', 'group': 'Voice Morph'},
        'pitch_semitones': {'type': 'float', 'min': -12, 'max': 12, 'step': 0.5, 'default': 0, 'label': 'Pitch Shift', 'group': 'Voice Morph'},
        'intensity': {'type': 'float', 'min': 0.0, 'max': 2.0, 'step': 0.05, 'default': 1.0, 'label': 'Emotion Intensity', 'group': 'Voice Morph'},
    },
    'engine': {
        'engine': {'type': 'select', 'options': ['auto','local','sapi'], 'default': 'auto', 'label': 'TTS Engine', 'group': 'Synthesis Engine', 'labels': {'auto':'Auto-fallback','local':'Local TTS','sapi':'Windows SAPI'}},
        'voice_id': {'type': 'text', 'default': '', 'label': 'Voice ID', 'group': 'Synthesis Engine', 'placeholder': 'custom voice ID'},
    },
    'spectral': {
        'brightness': {'type': 'float', 'min': -1.0, 'max': 1.0, 'step': 0.05, 'default': 0, 'label': 'Brightness', 'group': 'Spectral Envelope'},
        'warmth': {'type': 'float', 'min': -1.0, 'max': 1.0, 'step': 0.05, 'default': 0, 'label': 'Warmth', 'group': 'Spectral Envelope'},
        'breathiness': {'type': 'float', 'min': 0, 'max': 1.0, 'step': 0.05, 'default': 0, 'label': 'Breathiness', 'group': 'Spectral Envelope'},
    },
    'pipeline': {
        'formant_enabled': {'type': 'bool', 'default': True, 'label': 'Formant', 'group': 'Processing Pipeline'},
        'pitch_enabled': {'type': 'bool', 'default': True, 'label': 'Pitch', 'group': 'Processing Pipeline'},
        'emotion_enabled': {'type': 'bool', 'default': True, 'label': 'Emotion', 'group': 'Processing Pipeline'},
        'spectral_enabled': {'type': 'bool', 'default': True, 'label': 'Spectral', 'group': 'Processing Pipeline'},
    }
}

def render_param_control(name, spec):
    cid = f'p-{name}'
    label = spec.get('label', name)
    t = spec['type']
    if t == 'int' or t == 'float':
        return f'''          <div class="param-row"><label>{label}</label><input type="range" id="{cid}" min="{spec["min"]}" max="{spec["max"]}" step="{spec["step"]}" value="{spec["default"]}"><span class="val" id="{cid}-val">{spec["default"]}</span></div>'''
    elif t == 'select':
        labels = spec.get('labels', {})
        opts = ''.join(f'<option value="{o}"{" selected" if str(o)==str(spec["default"]) else ""}>{labels.get(str(o),o)}</option>' for o in spec['options'])
        return f'''          <div class="param-row"><label>{label}</label><select id="{cid}">{opts}</select></div>'''
    elif t == 'bool':
        checked = 'checked' if spec.get('default') else ''
        return f'''          <label class="skill-chip active"><input type="checkbox" {checked} data-skill="{name}"> {label}</label>'''
    elif t == 'text':
        ph = spec.get('placeholder', '')
        return f'''          <div class="param-row"><label>{label}</label><input type="text" id="{cid}" placeholder="{ph}" style="flex:1;background:#05080c;border:1px solid var(--border);border-radius:4px;padding:4px 8px;color:var(--text);font-size:0.9em"></div>'''
    return ''

def render_param_group(group_name):
    group = PARAM_REGISTRY.get(group_name, {})
    seen = set()
    html = ''
    for name, spec in group.items():
        g = spec.get('group', group_name.title())
        if g not in seen:
            if html: html += '        </div>\n'
            html += f'        <div class="param-group">\n          <h3>{g}</h3>\n'
            seen.add(g)
        html += render_param_control(name, spec)
    if html:
        html += '        </div>\n'
    return html

def handle_http():
    import http.server
    import urllib.parse, json, os
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root = os.path.join(script_dir, '..', '..')
    with open(os.path.join(root, 'config', 'ports.json')) as f:
        ports = json.load(f)
    port = ports.get('saas_transposer', 9999)
    
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            try:
                params = json.loads(body)
            except: params = {}
            parsed = urllib.parse.urlparse(self.path)
            
            if parsed.path == '/transpose':
                input_path = params.get('input')
                if not input_path or not os.path.exists(input_path):
                    self.send_error(400, 'input file required')
                    return
                tmp = tempfile.mktemp(suffix='.wav')
                try:
                    result = process_wav(
                        input_path, tmp,
                        sr=params.get('sr', 24000),
                        formant_ratio=params.get('formant_ratio', 1.0),
                        pitch_semitones=params.get('pitch_semitones', 0.0),
                        emotion=params.get('emotion', 'neutral'),
                        intensity=params.get('intensity', 1.0),
                        n_fft=params.get('n_fft', 2048),
                        hop_length=params.get('hop_length', 512),
                        window=params.get('window', 'hann'),
                        brightness=params.get('brightness'),
                        warmth=params.get('warmth'),
                        breathiness=params.get('breathiness'),
                        formant_enabled=params.get('formant_enabled', True),
                        pitch_enabled=params.get('pitch_enabled', True),
                        emotion_enabled=params.get('emotion_enabled', True),
                        spectral_enabled=params.get('spectral_enabled', True),
                    )
                    with open(tmp, 'rb') as f:
                        audio_data = f.read()
                    self.send_response(200)
                    self.send_header('Content-Type', 'audio/wav')
                    self.send_header('X-Emotion', result['emotion'])
                    self.send_header('X-Intensity', str(result['intensity']))
                    self.send_header('X-Samples', str(result['samples']))
                    self.send_header('X-SampleRate', str(result['sr']))
                    self.send_header('X-Nfft', str(result['n_fft']))
                    self.send_header('X-HopLength', str(result['hop_length']))
                    self.send_header('X-Window', result['window'])
                    self.send_header('Content-Length', str(len(audio_data)))
                    self.end_headers()
                    self.wfile.write(audio_data)
                except Exception as e:
                    self.send_error(500, str(e))
                finally:
                    try: os.unlink(tmp)
                    except: pass
            elif parsed.path == '/transform':
                qs = urllib.parse.parse_qs(parsed.query)
                def q(name, default=None):
                    v = qs.get(name)
                    if v is None: return default
                    return v[0] if isinstance(v, list) else v
                tmp = tempfile.mktemp(suffix='.wav')
                try:
                    with open(tmp, 'wb') as f:
                        f.write(body)
                    result = process_wav(
                        tmp, tmp,
                        sr=int(q('sr', 24000)),
                        formant_ratio=float(q('formant', 1.0)),
                        pitch_semitones=float(q('pitch', 0.0)),
                        emotion=q('emotion', 'neutral'),
                        intensity=float(q('intensity', 1.0)),
                        n_fft=int(q('n_fft', 2048)),
                        hop_length=int(q('hop_length', 512)),
                        window=q('window', 'hann'),
                        brightness=float(q('brightness')) if q('brightness') else None,
                        warmth=float(q('warmth')) if q('warmth') else None,
                        breathiness=float(q('breathiness')) if q('breathiness') else None,
                        formant_enabled=q('formant_enabled', 'true').lower() == 'true',
                        pitch_enabled=q('pitch_enabled', 'true').lower() == 'true',
                        emotion_enabled=q('emotion_enabled', 'true').lower() == 'true',
                        spectral_enabled=q('spectral_enabled', 'true').lower() == 'true',
                    )
                    with open(tmp, 'rb') as f:
                        audio_data = f.read()
                    self.send_response(200)
                    self.send_header('Content-Type', 'audio/wav')
                    self.send_header('X-Emotion', result['emotion'])
                    self.send_header('X-Samples', str(result['samples']))
                    self.send_header('X-SampleRate', str(result['sr']))
                    self.send_header('Content-Length', str(len(audio_data)))
                    self.end_headers()
                    self.wfile.write(audio_data)
                except Exception as e:
                    self.send_error(500, str(e))
                finally:
                    try: os.unlink(tmp)
                    except: pass
            elif parsed.path == '/emotional-dictionary':
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(EMOTIONAL_DICT).encode())
            elif parsed.path == '/health':
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'status': 'ok',
                    'backends': {'librosa': HAS_LIBROSA, 'scipy': HAS_SCIPY, 'soundfile': HAS_SOUNDFILE},
                    'emotional_dictionary_version': EMOTIONAL_DICT.get('version', 'none')
                }).encode())
            else:
                self.send_error(404)
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == '/params/html':
                qs = urllib.parse.parse_qs(parsed.query)
                groups = qs.get('group', list(PARAM_REGISTRY.keys()))
                if isinstance(groups, str): groups = [groups]
                html = ''
                for g in groups:
                    html += render_param_group(g)
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(html.encode())
            elif parsed.path == '/params/schema':
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(PARAM_REGISTRY).encode())
            else:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'status': 'ok',
                    'version': '1.0.0',
                    'name': 'SAAS - Soul As A Service',
                    'transforms': ['formant_shift', 'pitch_shift', 'spectral_envelope', 'emotion_morph'],
                    'emotional_dictionary_version': EMOTIONAL_DICT.get('version', 'none'),
                    'available_emotions': list(EMOTIONAL_DICT.get('emotions', {}).keys()),
                }).encode())
    server = http.server.HTTPServer(('127.0.0.1', port), Handler)
    log = print
    log(f'SAAS transposer running on http://127.0.0.1:{port}')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()

if __name__ == '__main__':
    if '--serve' in sys.argv:
        handle_http()
    else:
        parser = argparse.ArgumentParser(description='SAAS - Soul As A Service frequency transposer')
        parser.add_argument('input', help='Input WAV file')
        parser.add_argument('output', nargs='?', help='Output WAV file (default: input_morphed.wav)')
        parser.add_argument('--sr', type=int, default=24000, help='Sample rate')
        parser.add_argument('--formant', type=float, default=1.0, help='Formant shift ratio (0.5-2.0)')
        parser.add_argument('--pitch', type=float, default=0.0, help='Pitch shift in semitones')
        parser.add_argument('--emotion', default='neutral', help='Emotion preset')
        parser.add_argument('--intensity', type=float, default=1.0, help='Emotion intensity 0.0-2.0')
        parser.add_argument('--n-fft', type=int, default=2048, help='STFT window size')
        parser.add_argument('--hop-length', type=int, default=512, help='STFT hop length')
        parser.add_argument('--window', default='hann', help='STFT window type (hann/hamming/blackman)')
        parser.add_argument('--brightness', type=float, help='Spectral brightness override (-1..1)')
        parser.add_argument('--warmth', type=float, help='Spectral warmth override (-1..1)')
        parser.add_argument('--breathiness', type=float, help='Spectral breathiness override (0..1)')
        parser.add_argument('--no-formant', action='store_true', help='Disable formant shift')
        parser.add_argument('--no-pitch', action='store_true', help='Disable pitch shift')
        parser.add_argument('--no-emotion', action='store_true', help='Disable emotion transform')
        parser.add_argument('--no-spectral', action='store_true', help='Disable spectral envelope')
        args = parser.parse_args()
        output = args.output or args.input.replace('.wav', '_morphed.wav')
        result = process_wav(args.input, output, sr=args.sr, formant_ratio=args.formant, pitch_semitones=args.pitch,
                             emotion=args.emotion, intensity=args.intensity,
                             n_fft=args.n_fft, hop_length=args.hop_length, window=args.window,
                             brightness=args.brightness, warmth=args.warmth, breathiness=args.breathiness,
                             formant_enabled=not args.no_formant, pitch_enabled=not args.no_pitch,
                             emotion_enabled=not args.no_emotion, spectral_enabled=not args.no_spectral)
        print(json.dumps(result))
