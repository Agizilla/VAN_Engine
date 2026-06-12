from __future__ import annotations
"""
videoSkill.py — Master Video Skill for Clawdia
Merged from: Video Frame, TalkingAvatar, MovieDirector, Video Blink Counter,
             YoutubeDL GUI, PhotoAnimate (video mode), and MusicVideoGenerator.

Categories: Face Detection (Haar), Eye Detection, Blink Detection, Webcam Capture,
            Video Processing, Frame Extraction, Talking Avatar, Video Download,
            Movie Director Tools, Music Video Generation
"""

__meta__ = {
    "name": "videoSkill.py",
    "description": "Master Video Skill for Clawdia — 5 video projects merged into one. Handles Haar cascade face/eye detection, blink detection (EAR), talking avatar mouth tracking, frame extraction, video trimming/concat, download (yt-dlp), GIF creation, music video generation, webcam capture, video effects, and text overlay.",
    "how_to": "from videoSkill import VideoSkill\nskill = VideoSkill()\nskill.detect_faces_in_video(Path('video.mp4'))\nskill.make_gif(Path('video.mp4'))\nskill.trim_video(Path('video.mp4'), 10, 30)\nskill.download_video('https://youtu.be/...')\nskill.apply_effect(Path('video.mp4'), 'sepia')",
    "version": "2.0.0",
    "dateCreated": "2026-06-07",
    "dateLastModified": "2026-06-10",
    "countPublicMethods": 60,
    "countLineNumbers": 896,
    "mergedProjects": ["Video Frame", "TalkingAvatar", "MovieDirector", "Video Blink Counter", "YoutubeDL GUI", "MusicVideoGenerator"],
    "update_list": [
        "2026-06-07 v1.0.0 — Initial merge",
        "2026-06-10 v2.0.0 — subprocess timeout, progress callback, lazy mediapipe, yt-dlp validation, scene detect frame sampling, add_subtitles"
    ]
}
import os, sys, json, time, subprocess, tempfile, shutil
from pathlib import Path
from typing import Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading
import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None

try:
    from PIL import Image, ImageDraw, ImageFilter
except ImportError:
    Image = None

try:
    import torch
except ImportError:
    torch = None


ROOT = Path(__file__).parent.resolve()

CONFIG = {
    "output_dir": ROOT / "outputs",
    "models_dir": ROOT / "models",
    "haar_cascade_dir": cv2.data.haarcascades if cv2 else "",
    "default_fps": 24,
    "ffmpeg_path": "ffmpeg",
    "ffmpeg_timeout": 300,
}

CONFIG["output_dir"].mkdir(parents=True, exist_ok=True)
CONFIG["models_dir"].mkdir(parents=True, exist_ok=True)


class SkillError(Exception):
    pass


def _require(pkg: str, install_hint: str | None = None):
    import importlib
    try:
        return importlib.import_module(pkg)
    except ImportError:
        hint = install_hint or f"pip install {pkg}"
        raise SkillError(f"Missing package '{pkg}'. Install with: {hint}")


def ffmpeg(*args, check=False, timeout=None) -> subprocess.CompletedProcess:
    cmd = [CONFIG["ffmpeg_path"], *args]
    timeout = timeout or CONFIG.get("ffmpeg_timeout", 300)
    try:
        return subprocess.run(cmd, capture_output=True, check=check, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise SkillError(f"ffmpeg command timed out after {timeout}s: {' '.join(cmd[:4])}...")


class VideoFormat(Enum):
    MP4 = "mp4"
    AVI = "avi"
    MOV = "mov"
    MKV = "mkv"
    GIF = "gif"
    WEBM = "webm"


# ═══════════════════════════════════════════════════════════════════════════
#  VIDEO I/O UTILITIES
# ═══════════════════════════════════════════════════════════════════════════

class VideoReader:
    def __init__(self, path: Path | int = 0):
        if cv2 is None:
            raise SkillError("OpenCV required: pip install opencv-python")
        self.cap = cv2.VideoCapture(int(path) if isinstance(path, int) else str(path))
        if not self.cap.isOpened():
            raise SkillError(f"Could not open video source: {path}")
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

    def read(self) -> tuple[bool, np.ndarray]:
        return self.cap.read()

    def release(self):
        self.cap.release()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.release()

    def get_fps(self) -> float:
        return self.fps

    def get_frame_count(self) -> int:
        return self.total_frames

    def get_duration(self) -> float:
        if self.fps > 0:
            return self.total_frames / self.fps
        return 0.0

    def seek(self, frame_idx: int) -> bool:
        return self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)


class VideoWriter:
    def __init__(self, path: Path, fps: int | float = 24,
                 size: tuple[int, int] | None = None,
                 fourcc: str = "mp4v"):
        if cv2 is None:
            raise SkillError("OpenCV required")
        self.path = path
        self.fps = fps
        self.writer = None
        self.size = size
        self.fourcc = cv2.VideoWriter_fourcc(*fourcc)

    def write(self, frame: np.ndarray):
        if self.writer is None:
            h, w = frame.shape[:2]
            self.size = self.size or (w, h)
            self.writer = cv2.VideoWriter(str(self.path), self.fourcc,
                                          self.fps, self.size)
        self.writer.write(frame)

    def release(self):
        if self.writer:
            self.writer.release()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.release()


# ═══════════════════════════════════════════════════════════════════════════
#  FRAME EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════

class FrameExtractor:
    def __init__(self, quality: int = 95):
        self.quality = quality

    def extract_all(self, video_path: Path, output_dir: Path,
                    format: str = "jpg",
                    progress_callback: Callable[[int, int], None] | None = None) -> list[Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        frames = []
        with VideoReader(video_path) as reader:
            idx = 0
            total = reader.total_frames
            while True:
                ret, frame = reader.read()
                if not ret:
                    break
                out_path = output_dir / f"frame_{idx:06d}.{format}"
                cv2.imwrite(str(out_path), frame,
                            [int(cv2.IMWRITE_JPEG_QUALITY), self.quality])
                frames.append(out_path)
                idx += 1
                if progress_callback:
                    progress_callback(idx, total)
        return frames

    def extract_every_n(self, video_path: Path, output_dir: Path,
                        n: int = 30, format: str = "jpg",
                        progress_callback: Callable[[int, int], None] | None = None) -> list[Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        frames = []
        with VideoReader(video_path) as reader:
            idx = 0
            total = reader.total_frames
            while True:
                ret, frame = reader.read()
                if not ret:
                    break
                if idx % n == 0:
                    out_path = output_dir / f"frame_{idx:06d}.{format}"
                    cv2.imwrite(str(out_path), frame)
                    frames.append(out_path)
                idx += 1
                if progress_callback:
                    progress_callback(idx, total)
        return frames

    def extract_scene_keyframes(self, video_path: Path, output_dir: Path,
                                scene_threshold: float = 0.3,
                                format: str = "jpg",
                                progress_callback: Callable[[int, int], None] | None = None) -> list[Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        frames = []
        scene_file = output_dir / "scene_timestamps.txt"
        cmd = [
            CONFIG["ffmpeg_path"], "-i", str(video_path),
            "-filter:v", f"select='gt(scene,{scene_threshold})',showinfo",
            "-vsync", "vfr",
            "-f", "null", "-",
        ]
        timeout = CONFIG.get("ffmpeg_timeout", 300)
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise SkillError(f"Scene detection timed out after {timeout}s")

        timestamps = []
        for line in result.stderr.split('\n'):
            if 'pts_time:' in line:
                m = __import__('re').search(r'pts_time:([\d.]+)', line)
                if m:
                    timestamps.append(float(m.group(1)))

        with VideoReader(video_path) as reader:
            for i, ts in enumerate(timestamps):
                frame_idx = int(ts * reader.fps)
                reader.seek(frame_idx)
                ret, frame = reader.read()
                if ret:
                    out_path = output_dir / f"scene_{i:04d}_{ts:.2f}s.{format}"
                    cv2.imwrite(str(out_path), frame)
                    frames.append(out_path)
                if progress_callback:
                    progress_callback(i + 1, len(timestamps))

        return frames

    def extract_at_timestamps(self, video_path: Path, timestamps: list[float],
                              output_dir: Path) -> dict[float, Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        result = {}
        timeout = CONFIG.get("ffmpeg_timeout", 300)
        for ts in timestamps:
            out_path = output_dir / f"frame_{ts:.2f}s.jpg"
            cmd = [
                CONFIG["ffmpeg_path"], "-ss", str(ts), "-i", str(video_path),
                "-vframes", "1", "-q:v", "2", str(out_path), "-y",
            ]
            try:
                subprocess.run(cmd, capture_output=True, timeout=timeout)
            except subprocess.TimeoutExpired:
                continue
            if out_path.exists():
                result[ts] = out_path
        return result

    def probe(self, video_path: Path) -> dict:
        cmd = [
            CONFIG["ffmpeg_path"], "-i", str(video_path),
            "-f", "null", "-",
        ]
        timeout = CONFIG.get("ffmpeg_timeout", 300)
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return {"path": str(video_path), "error": "timeout"}
        info = {"path": str(video_path)}
        for line in result.stderr.split("\n"):
            if "Duration" in line:
                parts = line.strip().split(",")
                dur = parts[0].split("Duration:")[-1].strip()
                h, m, s = dur.split(":")
                info["duration"] = int(h) * 3600 + int(m) * 60 + float(s)
            if "Stream" in line and "Video" in line:
                if "fps" in line:
                    fps_part = line.split("fps")[0].split()[-1]
                    info["fps"] = float(fps_part)
                if "x" in line:
                    import re
                    dims = re.findall(r"(\d+)x(\d+)", line)
                    if dims:
                        info["width"] = int(dims[0][0])
                        info["height"] = int(dims[0][1])
        return info


# ═══════════════════════════════════════════════════════════════════════════
#  FACE / EYE DETECTION (Haar Cascade)
# ═══════════════════════════════════════════════════════════════════════════

class HaarCascadeDetector:
    def __init__(self):
        if cv2 is None:
            raise SkillError("OpenCV required")
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_eye.xml"
        )
        self.smile_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_smile.xml"
        )

    def detect_faces(self, frame: np.ndarray) -> list[tuple[int, int, int, int]]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        return [(x, y, w, h) for x, y, w, h in faces]

    def detect_eyes(self, frame: np.ndarray, face_region: tuple[int, int, int, int] | None = None
                    ) -> list[tuple[int, int, int, int]]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if face_region:
            x, y, w, h = face_region
            roi = gray[y:y + h, x:x + w]
            eyes = self.eye_cascade.detectMultiScale(roi)
            return [(x + ex, y + ey, ew, eh) for ex, ey, ew, eh in eyes]
        eyes = self.eye_cascade.detectMultiScale(gray)
        return [(ex, ey, ew, eh) for ex, ey, ew, eh in eyes]

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        display = frame.copy()
        faces = self.detect_faces(frame)
        for x, y, w, h in faces:
            cv2.rectangle(display, (x, y), (x + w, y + h), (255, 0, 0), 2)
            eyes = self.detect_eyes(frame, (x, y, w, h))
            for ex, ey, ew, eh in eyes:
                cv2.rectangle(display, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2)
        return display

    def detect_in_video(self, video_path: Path, output_path: Path | None = None) -> Path | None:
        if output_path is None:
            output_path = CONFIG["output_dir"] / f"detected_{video_path.stem}.mp4"

        with VideoReader(video_path) as reader:
            writer = VideoWriter(output_path, fps=reader.fps,
                                 size=(reader.width, reader.height))
            while True:
                ret, frame = reader.read()
                if not ret:
                    break
                processed = self.process_frame(frame)
                writer.write(processed)

        return output_path if output_path.exists() else None


# ═══════════════════════════════════════════════════════════════════════════
#  BLINK DETECTION
# ═══════════════════════════════════════════════════════════════════════════

class BlinkDetector:
    def __init__(self, ear_threshold: float = 0.2, consecutive_frames: int = 3):
        self.ear_threshold = ear_threshold
        self.consecutive_frames = consecutive_frames
        self._counter = 0
        self._total_blinks = 0

    def eye_aspect_ratio(self, eye_points: np.ndarray) -> float:
        A = np.linalg.norm(eye_points[1] - eye_points[5])
        B = np.linalg.norm(eye_points[2] - eye_points[4])
        C = np.linalg.norm(eye_points[0] - eye_points[3])
        return (A + B) / (2.0 * C + 1e-10)

    def detect(self, frame: np.ndarray, landmarks: np.ndarray | None = None) -> int:
        if landmarks is not None and len(landmarks) >= 468:
            left_eye = np.array([landmarks[i] for i in [33, 160, 158, 133, 153, 144]])
            right_eye = np.array([landmarks[i] for i in [362, 385, 387, 263, 373, 380]])
            left_ear = self.eye_aspect_ratio(left_eye)
            right_ear = self.eye_aspect_ratio(right_eye)
            ear = (left_ear + right_ear) / 2.0

            if ear < self.ear_threshold:
                self._counter += 1
            else:
                if self._counter >= self.consecutive_frames:
                    self._total_blinks += 1
                self._counter = 0

        return self._total_blinks

    def reset(self):
        self._counter = 0
        self._total_blinks = 0

    @property
    def total_blinks(self) -> int:
        return self._total_blinks


# ═══════════════════════════════════════════════════════════════════════════
#  TALKING AVATAR (Mouth tracking from video)
# ═══════════════════════════════════════════════════════════════════════════

class TalkingAvatar:
    def __init__(self):
        try:
            import mediapipe as mp
            self._mp = mp
        except ImportError:
            self._mp = None
        if self._mp is None:
            raise SkillError("mediapipe required: pip install mediapipe")
        self.face_mesh = self._mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False, max_num_faces=1,
            refine_landmarks=True, min_detection_confidence=0.5,
        )
        self.mouth_indices = list(range(0, 20))

    def get_mouth_coords(self, frame: np.ndarray) -> list[tuple[int, int]] | None:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb)
        if results.multi_face_landmarks:
            h, w = frame.shape[:2]
            landmarks = results.multi_face_landmarks[0]
            mouth = []
            for idx in self.mouth_indices:
                lm = landmarks.landmark[idx]
                mouth.append((int(lm.x * w), int(lm.y * h)))
            return mouth
        return None

    def detect_mouth_open(self, frame: np.ndarray) -> float:
        mouth = self.get_mouth_coords(frame)
        if mouth is None:
            return 0.0
        mouth_pts = np.array(mouth)
        if len(mouth_pts) < 2:
            return 0.0
        top = np.mean([p[1] for p in mouth_pts[:len(mouth_pts)//2]])
        bottom = np.mean([p[1] for p in mouth_pts[len(mouth_pts)//2:]])
        return max(0, bottom - top)

    def process_video(self, video_path: Path, output_path: Path | None = None) -> Path:
        if output_path is None:
            output_path = CONFIG["output_dir"] / f"avatar_{video_path.stem}.mp4"

        with VideoReader(video_path) as reader:
            writer = VideoWriter(output_path, fps=reader.fps,
                                 size=(reader.width, reader.height))
            while True:
                ret, frame = reader.read()
                if not ret:
                    break
                mouth = self.get_mouth_coords(frame)
                if mouth:
                    for pt in mouth:
                        cv2.circle(frame, pt, 2, (0, 255, 0), -1)
                    openness = self.detect_mouth_open(frame)
                    cv2.putText(frame, f"Mouth: {openness:.1f}px",
                                (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                                0.7, (0, 255, 0), 2)
                writer.write(frame)

        return output_path

    def extract_mouth_frames(self, video_path: Path, output_dir: Path) -> list[Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        frames = []
        with VideoReader(video_path) as reader:
            idx = 0
            while True:
                ret, frame = reader.read()
                if not ret:
                    break
                mouth = self.get_mouth_coords(frame)
                if mouth:
                    pts = np.array(mouth)
                    x, y, w, h = cv2.boundingRect(pts)
                    padding = 20
                    x = max(0, x - padding)
                    y = max(0, y - padding)
                    w = min(frame.shape[1] - x, w + 2 * padding)
                    h = min(frame.shape[0] - y, h + 2 * padding)
                    mouth_roi = frame[y:y + h, x:x + w]
                    out_path = output_dir / f"mouth_{idx:06d}.jpg"
                    cv2.imwrite(str(out_path), mouth_roi)
                    frames.append(out_path)
                idx += 1
        return frames


# ═══════════════════════════════════════════════════════════════════════════
#  VIDEO TO GIF
# ═══════════════════════════════════════════════════════════════════════════

class VideoToGIF:
    def __init__(self, fps: int = 10, scale: float = 1.0):
        self.fps = fps
        self.scale = scale

    def convert(self, video_path: Path, output_path: Path | None = None,
                start_time: float = 0, duration: float | None = None,
                progress_callback: Callable[[int, int], None] | None = None) -> Path:
        if output_path is None:
            output_path = CONFIG["output_dir"] / f"{video_path.stem}.gif"

        if Image is None:
            raise SkillError("PIL required: pip install Pillow")

        with VideoReader(video_path) as reader:
            start_frame = int(start_time * reader.fps)
            end_frame = reader.total_frames
            if duration:
                end_frame = min(end_frame, start_frame + int(duration * reader.fps))

            reader.seek(start_frame)
            frame_interval = max(1, int(reader.fps / self.fps))
            pil_frames = []
            idx = 0
            total_frames = end_frame - start_frame
            while True:
                ret, frame = reader.read()
                if not ret or idx >= end_frame:
                    break
                if idx >= start_frame and (idx - start_frame) % frame_interval == 0:
                    if self.scale != 1.0:
                        h, w = frame.shape[:2]
                        new_size = (int(w * self.scale), int(h * self.scale))
                        frame = cv2.resize(frame, new_size)
                    pil_frames.append(Image.fromarray(
                        cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    ))
                idx += 1
                if progress_callback:
                    progress_callback(idx - start_frame, total_frames)

        if pil_frames:
            pil_frames[0].save(output_path, save_all=True,
                               append_images=pil_frames[1:],
                               duration=int(1000 / self.fps), loop=0)
        return output_path


# ═══════════════════════════════════════════════════════════════════════════
#  VIDEO DOWNLOADER (from YoutubeDL GUI)
# ═══════════════════════════════════════════════════════════════════════════

class VideoDownloader:
    def __init__(self, output_dir: Path | None = None):
        self.output_dir = output_dir or CONFIG["output_dir"] / "downloads"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def download(self, url: str, format: str = "mp4",
                 quality: str = "best") -> Path | None:
        try:
            import yt_dlp
        except ImportError:
            raise SkillError("yt-dlp required: pip install yt-dlp")

        ydl_opts = {
            "format": f"{format}/best" if quality == "best" else quality,
            "outtmpl": str(self.output_dir / "%(title)s.%(ext)s"),
            "quiet": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = self.output_dir / f"{info['title']}.{format}"
            return path if path.exists() else None

    def extract_audio(self, video_path: Path, output_path: Path | None = None,
                      format: str = "mp3") -> Path:
        if output_path is None:
            output_path = video_path.with_suffix(f".{format}")
        ffmpeg("-i", str(video_path), "-vn",
               "-acodec", "libmp3lame" if format == "mp3" else "aac",
               "-y", str(output_path), check=True)
        return output_path

    def get_info(self, url: str) -> dict:
        try:
            import yt_dlp
        except ImportError:
            raise SkillError("yt-dlp required: pip install yt-dlp")
        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            return ydl.extract_info(url, download=False)


# ═══════════════════════════════════════════════════════════════════════════
#  VIDEO EDITING TOOLS (from MovieDirector)
# ═══════════════════════════════════════════════════════════════════════════

class VideoEditor:
    @staticmethod
    def trim(video_path: Path, output_path: Path, start: float,
             end: float | None = None, duration: float | None = None) -> Path:
        cmd = [CONFIG["ffmpeg_path"], "-i", str(video_path), "-ss", str(start)]
        if duration:
            cmd += ["-t", str(duration)]
        elif end:
            cmd += ["-t", str(end - start)]
        cmd += ["-c", "copy", "-y", str(output_path)]
        subprocess.run(cmd, check=True, timeout=CONFIG.get("ffmpeg_timeout", 300))
        return output_path

    @staticmethod
    def concat(video_paths: list[Path], output_path: Path) -> Path:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt",
                                         delete=False) as f:
            for vp in video_paths:
                f.write(f"file '{vp}'\n")
            list_file = f.name
        cmd = [
            CONFIG["ffmpeg_path"], "-f", "concat", "-safe", "0",
            "-i", list_file, "-c", "copy", "-y", str(output_path),
        ]
        subprocess.run(cmd, check=True, timeout=CONFIG.get("ffmpeg_timeout", 300))
        os.unlink(list_file)
        return output_path

    @staticmethod
    def add_audio(video_path: Path, audio_path: Path, output_path: Path,
                  volume: float = 1.0) -> Path:
        cmd = [
            CONFIG["ffmpeg_path"], "-i", str(video_path),
            "-i", str(audio_path),
            "-c:v", "copy", "-c:a", "aac",
            "-filter:a", f"volume={volume}",
            "-map", "0:v:0", "-map", "1:a:0",
            "-shortest", "-y", str(output_path),
        ]
        subprocess.run(cmd, check=True, timeout=CONFIG.get("ffmpeg_timeout", 300))
        return output_path

    @staticmethod
    def speed_change(video_path: Path, output_path: Path,
                     speed: float = 2.0) -> Path:
        pts = 1.0 / speed
        cmd = [
            CONFIG["ffmpeg_path"], "-i", str(video_path),
            "-filter:v", f"setpts={pts}*PTS",
            "-filter:a", f"atempo={speed}",
            "-y", str(output_path),
        ]
        subprocess.run(cmd, check=True, timeout=CONFIG.get("ffmpeg_timeout", 300))
        return output_path

    @staticmethod
    def resize(video_path: Path, output_path: Path,
               width: int, height: int) -> Path:
        cmd = [
            CONFIG["ffmpeg_path"], "-i", str(video_path),
            "-vf", f"scale={width}:{height}",
            "-c:a", "copy", "-y", str(output_path),
        ]
        subprocess.run(cmd, check=True, timeout=CONFIG.get("ffmpeg_timeout", 300))
        return output_path

    @staticmethod
    def add_text_overlay(video_path: Path, output_path: Path,
                         text: str, position: str = "bottom") -> Path:
        pos_map = {
            "top": "(w-text_w)/2:10",
            "bottom": "(w-text_w)/2:h-th-10",
            "center": "(w-text_w)/2:(h-text_h)/2",
        }
        pos = pos_map.get(position, pos_map["bottom"])
        cmd = [
            CONFIG["ffmpeg_path"], "-i", str(video_path),
            "-vf", f"drawtext=text='{text}':fontsize=24:fontcolor=white:x={pos}:box=1:boxcolor=black@0.5",
            "-c:a", "copy", "-y", str(output_path),
        ]
        subprocess.run(cmd, check=True, timeout=CONFIG.get("ffmpeg_timeout", 300))
        return output_path

    @staticmethod
    def add_subtitles(video_path: Path, subtitle_path: Path, output_path: Path | None = None) -> Path:
        if output_path is None:
            output_path = CONFIG["output_dir"] / f"subtitled_{video_path.stem}.mp4"
        sub_escaped = str(subtitle_path).replace(':', '\\:').replace('\'', '\\\\\'')
        ext = subtitle_path.suffix.lower()
        if ext == '.ass':
            filter_str = f"ass={sub_escaped}"
        else:
            filter_str = f"subtitles={sub_escaped}"
        cmd = [
            CONFIG["ffmpeg_path"], "-i", str(video_path),
            "-vf", filter_str,
            "-c:a", "copy", "-y", str(output_path),
        ]
        subprocess.run(cmd, check=True, timeout=CONFIG.get("ffmpeg_timeout", 300))
        return output_path

    @staticmethod
    def extract_audio(video_path: Path, output_path: Path | None = None,
                      format: str = "mp3") -> Path:
        if output_path is None:
            output_path = video_path.with_suffix(f".{format}")
        codec = "libmp3lame" if format == "mp3" else "aac"
        ffmpeg("-i", str(video_path), "-vn",
               "-acodec", codec, "-y", str(output_path), check=True)
        return output_path


# ═══════════════════════════════════════════════════════════════════════════
#  MUSIC VIDEO GENERATOR (with images + audio)
# ═══════════════════════════════════════════════════════════════════════════

class MusicVideoGenerator:
    def __init__(self, fps: int = 24):
        self.fps = fps

    def from_images(self, audio_path: Path, image_paths: list[Path],
                    output_path: Path, transitions: bool = True) -> Path:
        try:
            from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips
        except ImportError:
            raise SkillError("moviepy required: pip install moviepy")

        audio = AudioFileClip(str(audio_path))
        duration = audio.duration

        if not image_paths:
            raise SkillError("At least one image required")

        clip_duration = duration / len(image_paths)
        clips = []
        for img_path in image_paths:
            clip = ImageClip(str(img_path), duration=clip_duration)
            clip = clip.resize(height=720)
            if transitions:
                clip = clip.crossfadein(0.3).crossfadeout(0.3)
            clips.append(clip)

        video = concatenate_videoclips(clips, method="compose")
        video = video.set_audio(audio)
        video.write_videofile(str(output_path), fps=self.fps,
                              codec="libx264", audio_codec="aac")
        return output_path

    def with_lyrics(self, audio_path: Path, image_paths: list[Path],
                    lyrics: list[tuple[str, float]], output_path: Path) -> Path:
        try:
            from moviepy.editor import ImageClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
        except ImportError:
            raise SkillError("moviepy required")

        audio = AudioFileClip(str(audio_path))
        duration = audio.duration
        clip_duration = duration / max(len(image_paths), 1)
        clips = []
        for img_path in image_paths:
            clip = ImageClip(str(img_path), duration=clip_duration).resize(height=720)
            clips.append(clip)
        video = concatenate_videoclips(clips, method="compose").set_audio(audio)

        text_clips = []
        for text, timestamp in lyrics:
            txt = TextClip(text, fontsize=24, color="white",
                           stroke_color="black", stroke_width=1)
            txt = txt.set_position(("center", "bottom")).set_start(timestamp).set_duration(2)
            text_clips.append(txt)

        final = CompositeVideoClip([video] + text_clips)
        final.write_videofile(str(output_path), fps=self.fps,
                              codec="libx264", audio_codec="aac")
        return output_path


# ═══════════════════════════════════════════════════════════════════════════
#  WEBCAM CAPTURE
# ═══════════════════════════════════════════════════════════════════════════

class WebcamCapture:
    def __init__(self, camera_id: int = 0):
        self.camera_id = camera_id

    def capture_frame(self) -> np.ndarray:
        if cv2 is None:
            raise SkillError("OpenCV required")
        cap = cv2.VideoCapture(self.camera_id)
        ret, frame = cap.read()
        cap.release()
        if not ret:
            raise SkillError("Could not capture frame from webcam")
        return frame

    def record(self, output_path: Path, duration: float = 5.0,
               fps: int = 24) -> Path:
        if cv2 is None:
            raise SkillError("OpenCV required")
        cap = cv2.VideoCapture(self.camera_id)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        writer = cv2.VideoWriter(str(output_path), fourcc, fps, (w, h))

        start = time.time()
        while time.time() - start < duration:
            ret, frame = cap.read()
            if not ret:
                break
            writer.write(frame)

        cap.release()
        writer.release()
        return output_path


# ═══════════════════════════════════════════════════════════════════════════
#  VIDEO EFFECTS
# ═══════════════════════════════════════════════════════════════════════════

class VideoEffects:
    @staticmethod
    def apply_to_frame(frame: np.ndarray, effect: str) -> np.ndarray:
        effects = {
            "grayscale": lambda f: cv2.cvtColor(
                cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR
            ),
            "sepia": lambda f: cv2.transform(f, np.array(
                [[0.272, 0.534, 0.131],
                 [0.349, 0.686, 0.168],
                 [0.393, 0.769, 0.189]]
            )).clip(0, 255).astype(np.uint8),
            "invert": lambda f: cv2.bitwise_not(f),
            "blur": lambda f: cv2.GaussianBlur(f, (15, 15), 0),
            "edge": lambda f: cv2.Canny(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY),
                                        100, 200),
            "pixelate": VideoEffects._pixelate,
        }
        fn = effects.get(effect)
        if fn is None:
            raise SkillError(f"Unknown effect: {effect}")
        return fn(frame)

    @staticmethod
    def _pixelate(frame: np.ndarray, block_size: int = 16) -> np.ndarray:
        h, w = frame.shape[:2]
        temp = cv2.resize(frame, (w // block_size, h // block_size),
                          interpolation=cv2.INTER_LINEAR)
        return cv2.resize(temp, (w, h), interpolation=cv2.INTER_NEAREST)

    @staticmethod
    def apply_to_video(video_path: Path, output_path: Path, effect: str) -> Path:
        with VideoReader(video_path) as reader:
            writer = VideoWriter(output_path, fps=reader.fps,
                                 size=(reader.width, reader.height))
            while True:
                ret, frame = reader.read()
                if not ret:
                    break
                processed = VideoEffects.apply_to_frame(frame, effect)
                if len(processed.shape) == 2:
                    processed = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)
                writer.write(processed)
        return output_path


# ═══════════════════════════════════════════════════════════════════════════
#  MASTER VIDEO SKILL — Clawdia integration
# ═══════════════════════════════════════════════════════════════════════════

class VideoSkill:
    def __init__(self, config: dict | None = None):
        if config:
            CONFIG.update(config)
        self._detector: HaarCascadeDetector | None = None
        self._avatar: TalkingAvatar | None = None
        self._blink: BlinkDetector | None = None

    @property
    def detector(self) -> HaarCascadeDetector:
        if self._detector is None:
            self._detector = HaarCascadeDetector()
        return self._detector

    @property
    def avatar(self) -> TalkingAvatar:
        if self._avatar is None:
            self._avatar = TalkingAvatar()
        return self._avatar

    @property
    def blink(self) -> BlinkDetector:
        if self._blink is None:
            self._blink = BlinkDetector()
        return self._blink

    def detect_faces_in_frame(self, frame: np.ndarray) -> list[tuple[int, int, int, int]]:
        return self.detector.detect_faces(frame)

    def detect_faces_in_video(self, video_path: Path,
                                output_path: Path | None = None) -> Path | None:
        return self.detector.detect_in_video(video_path, output_path)

    def extract_frames(self, video_path: Path, output_dir: Path | None = None,
                       every_n: int = 1,
                       use_scene_detect: bool = False,
                       scene_threshold: float = 0.3,
                       progress_callback: Callable[[int, int], None] | None = None) -> list[Path]:
        extractor = FrameExtractor()
        out = output_dir or CONFIG["output_dir"] / "frames" / video_path.stem
        if use_scene_detect:
            return extractor.extract_scene_keyframes(video_path, out, scene_threshold, progress_callback=progress_callback)
        if every_n > 1:
            return extractor.extract_every_n(video_path, out, every_n, progress_callback=progress_callback)
        return extractor.extract_all(video_path, out, progress_callback=progress_callback)

    def trim_video(self, video_path: Path, start: float,
                   end: float | None = None, duration: float | None = None,
                   output_path: Path | None = None) -> Path:
        if output_path is None:
            output_path = CONFIG["output_dir"] / f"trimmed_{video_path.stem}.mp4"
        return VideoEditor.trim(video_path, output_path, start, end, duration)

    def concat_videos(self, video_paths: list[Path],
                      output_path: Path | None = None) -> Path:
        if output_path is None:
            output_path = CONFIG["output_dir"] / f"concat_{int(time.time())}.mp4"
        return VideoEditor.concat(video_paths, output_path)

    def download_video(self, url: str, format: str = "mp4") -> Path | None:
        downloader = VideoDownloader()
        return downloader.download(url, format)

    def make_gif(self, video_path: Path, output_path: Path | None = None,
                 fps: int = 10, start: float = 0,
                 duration: float | None = None,
                 progress_callback: Callable[[int, int], None] | None = None) -> Path:
        gif = VideoToGIF(fps=fps)
        return gif.convert(video_path, output_path, start, duration, progress_callback=progress_callback)

    def make_music_video(self, audio_path: Path, image_paths: list[Path],
                         output_path: Path | None = None) -> Path:
        gen = MusicVideoGenerator()
        if output_path is None:
            output_path = CONFIG["output_dir"] / f"mv_{audio_path.stem}.mp4"
        return gen.from_images(audio_path, image_paths, output_path)

    def detect_blinks(self, frame: np.ndarray,
                      landmarks: np.ndarray | None = None) -> int:
        return self.blink.detect(frame, landmarks)

    def process_avatar(self, video_path: Path,
                       output_path: Path | None = None) -> Path:
        return self.avatar.process_video(video_path, output_path)

    def add_audio_to_video(self, video_path: Path, audio_path: Path,
                            output_path: Path | None = None,
                            volume: float = 1.0) -> Path:
        if output_path is None:
            output_path = CONFIG["output_dir"] / f"with_audio_{video_path.stem}.mp4"
        return VideoEditor.add_audio(video_path, audio_path, output_path, volume)

    def change_speed(self, video_path: Path, speed: float,
                      output_path: Path | None = None) -> Path:
        if output_path is None:
            output_path = CONFIG["output_dir"] / f"speed_{video_path.stem}.mp4"
        return VideoEditor.speed_change(video_path, output_path, speed)

    def apply_effect(self, video_path: Path, effect: str,
                      output_path: Path | None = None) -> Path:
        if output_path is None:
            output_path = CONFIG["output_dir"] / f"{effect}_{video_path.stem}.mp4"
        return VideoEffects.apply_to_video(video_path, output_path, effect)

    def add_subtitles(self, video_path: Path, subtitle_path: Path,
                      output_path: Path | None = None) -> Path:
        return VideoEditor.add_subtitles(video_path, subtitle_path, output_path)

    def get_capabilities(self) -> list[str]:
        return [
            "face_detection",
            "eye_detection",
            "blink_detection",
            "frame_extraction",
            "talking_avatar",
            "mouth_tracking",
            "video_trimming",
            "video_concatenation",
            "video_download",
            "gif_creation",
            "music_video_generation",
            "webcam_capture",
            "video_effects",
            "video_speed_change",
            "audio_extraction",
        ]

    def get_feature_matrix(self) -> dict[str, bool]:
        return {c: True for c in self.get_capabilities()}
