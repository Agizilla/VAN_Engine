import struct
import time
from typing import Optional, Callable

import numpy as np
import webrtcvad


SAMPLE_RATE = 16000
FRAME_DURATION_MS = 30
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)
VAD_MODE = 1


class AudioCapture:
    def __init__(self, sample_rate: int = SAMPLE_RATE):
        self.sample_rate = sample_rate
        self.vad = webrtcvad.Vad(VAD_MODE)
        self._stream = None

    @property
    def available(self) -> bool:
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            input_devices = [d for d in devices if d["max_input_channels"] > 0]
            return len(input_devices) > 0
        except Exception:
            return False

    def record_until_silence(self, max_duration: float = 30.0, silence_duration: float = 1.5,
                             on_energy: Optional[Callable] = None) -> Optional[np.ndarray]:
        import sounddevice as sd

        frames = []
        silent_chunks = 0
        silence_chunks_needed = int(silence_duration / (FRAME_DURATION_MS / 1000))
        max_chunks = int(max_duration / (FRAME_DURATION_MS / 1000))
        speaking = False

        def callback(indata, frames_count, time_info, status):
            nonlocal silent_chunks, speaking
            chunk = indata[:, 0]
            if len(chunk) != FRAME_SIZE:
                return
            pcm = (chunk * 32767).astype(np.int16)
            is_speech = self.vad.is_speech(pcm.tobytes(), self.sample_rate)

            if is_speech:
                speaking = True
                silent_chunks = 0
                frames.append(chunk.copy())
            elif speaking:
                silent_chunks += 1
                frames.append(chunk.copy())

            if on_energy:
                on_energy(np.sqrt(np.mean(chunk ** 2)))

        with sd.InputStream(samplerate=self.sample_rate, channels=1,
                            blocksize=FRAME_SIZE, callback=callback):
            chunk_count = 0
            while chunk_count < max_chunks:
                if speaking and silent_chunks >= silence_chunks_needed:
                    break
                time.sleep(0.05)
                chunk_count += 1

        if not frames:
            return None
        return np.concatenate(frames)

    def list_devices(self):
        import sounddevice as sd
        return sd.query_devices()
