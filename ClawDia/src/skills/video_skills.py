import concurrent.futures
import shutil
import tempfile
from pathlib import Path
from typing import Any

from .base import BaseSkill, register_skill
from ..tools.master_skills.videoSkill import VideoSkill

_video = VideoSkill()

_FFMPEG_AVAILABLE: bool | None = None

def _check_ffmpeg() -> bool:
    global _FFMPEG_AVAILABLE
    if _FFMPEG_AVAILABLE is None:
        _FFMPEG_AVAILABLE = shutil.which("ffmpeg") is not None
    return _FFMPEG_AVAILABLE


def _run_with_timeout(func, args, timeout: int):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(func, *args)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            return None


@register_skill("video_trim", "video")
class VideoTrimSkill(BaseSkill):
    name = "video_trim"
    description = "Trim video to specified start time and end time or duration"
    category = "video"
    def execute(self, **kwargs) -> dict:
        path = Path(kwargs.get("path", ""))
        if not path.exists():
            return {"error": f"File not found: {path}"}
        if not _check_ffmpeg():
            return {"error": "ffmpeg not found on system PATH"}
        start = kwargs.get("start", 0)
        end = kwargs.get("end")
        duration = kwargs.get("duration")
        timeout = kwargs.get("timeout", 300)
        self.publish("progress", {"type": "progress", "current": 0, "total": 1})
        result = _run_with_timeout(_video.trim_video, (path, start, end, duration), timeout)
        if result is None:
            return {"error": "Timed out", "result": None}
        self.publish("progress", {"type": "progress", "current": 1, "total": 1})
        return {"result": {"path": str(result)}}


@register_skill("video_scenes", "video")
class VideoSceneDetectSkill(BaseSkill):
    name = "video_scenes"
    description = "Extract keyframes/frames from video at intervals"
    category = "video"
    def execute(self, **kwargs) -> dict:
        path = Path(kwargs.get("path", ""))
        if not path.exists():
            return {"error": f"File not found: {path}"}
        if not _check_ffmpeg():
            return {"error": "ffmpeg not found on system PATH"}
        every_n = kwargs.get("every_n", 30)
        timeout = kwargs.get("timeout", 300)
        tmp_dir = tempfile.mkdtemp(prefix="vidframes_")
        try:
            self.publish("progress", {"type": "progress", "current": 0, "total": 1})
            frames = _video.extract_frames(path, Path(tmp_dir), every_n=every_n)
            self.publish("progress", {"type": "progress", "current": 1, "total": 1})
            return {"result": {"frames": [str(f) for f in frames], "count": len(frames)}}
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)


@register_skill("video_analyze", "video")
class VideoAnalyzeSkill(BaseSkill):
    name = "video_analyze"
    description = "Detect faces in video using Haar cascade, return annotated video"
    category = "video"
    def execute(self, **kwargs) -> dict:
        path = Path(kwargs.get("path", ""))
        if not path.exists():
            return {"error": f"File not found: {path}"}
        if not _check_ffmpeg():
            return {"error": "ffmpeg not found on system PATH"}
        timeout = kwargs.get("timeout", 300)
        self.publish("progress", {"type": "progress", "current": 0, "total": 1})
        out = _run_with_timeout(_video.detect_faces_in_video, (path,), timeout)
        if out is None:
            return {"error": "Timed out", "result": None}
        self.publish("progress", {"type": "progress", "current": 1, "total": 1})
        return {"result": {"output_path": str(out)} if out else {"error": "Detection failed"}}


@register_skill("video_concat", "video")
class VideoConcatSkill(BaseSkill):
    name = "video_concat"
    description = "Concatenate multiple video files into one"
    category = "video"
    def execute(self, **kwargs) -> dict:
        paths = [Path(p) for p in kwargs.get("paths", [])]
        if len(paths) < 2:
            return {"error": "At least 2 video paths required"}
        if not _check_ffmpeg():
            return {"error": "ffmpeg not found on system PATH"}
        timeout = kwargs.get("timeout", 300)
        self.publish("progress", {"type": "progress", "current": 0, "total": len(paths)})
        out = _run_with_timeout(_video.concat_videos, (paths,), timeout)
        if out is None:
            return {"error": "Timed out", "result": None}
        self.publish("progress", {"type": "progress", "current": len(paths), "total": len(paths)})
        return {"result": {"path": str(out)}}


@register_skill("video_download", "video")
class VideoDownloadSkill(BaseSkill):
    name = "video_download"
    description = "Download video from URL using yt-dlp"
    category = "video"
    def execute(self, **kwargs) -> dict:
        url = kwargs.get("url", "")
        fmt = kwargs.get("format", "mp4")
        timeout = kwargs.get("timeout", 300)
        if not url:
            return {"error": "No URL provided"}
        self.publish("progress", {"type": "progress", "current": 0, "total": 1})
        result = _run_with_timeout(_video.download_video, (url, fmt), timeout)
        if result is None:
            return {"error": "Download timed out", "result": None}
        self.publish("progress", {"type": "progress", "current": 1, "total": 1})
        return {"result": {"path": str(result)} if result else {"error": "Download failed"}}


@register_skill("video_gif", "video")
class VideoGifSkill(BaseSkill):
    name = "video_gif"
    description = "Convert video to animated GIF"
    category = "video"
    def execute(self, **kwargs) -> dict:
        path = Path(kwargs.get("path", ""))
        if not path.exists():
            return {"error": f"File not found: {path}"}
        if not _check_ffmpeg():
            return {"error": "ffmpeg not found on system PATH"}
        fps = kwargs.get("fps", 10)
        start = kwargs.get("start", 0)
        duration = kwargs.get("duration")
        timeout = kwargs.get("timeout", 300)
        self.publish("progress", {"type": "progress", "current": 0, "total": 1})
        out = _run_with_timeout(_video.make_gif, (path, None, fps, start, duration), timeout)
        if out is None:
            return {"error": "Timed out", "result": None}
        self.publish("progress", {"type": "progress", "current": 1, "total": 1})
        return {"result": {"path": str(out)}}


@register_skill("video_music_video", "video")
class VideoMusicVideoSkill(BaseSkill):
    name = "video_music_video"
    description = "Generate music video from audio file and images"
    category = "video"
    def execute(self, **kwargs) -> dict:
        audio_path = Path(kwargs.get("audio", ""))
        images = [Path(p) for p in kwargs.get("images", [])]
        if not audio_path.exists() or not images:
            return {"error": "Audio or images missing"}
        if not _check_ffmpeg():
            return {"error": "ffmpeg not found on system PATH"}
        timeout = kwargs.get("timeout", 300)
        self.publish("progress", {"type": "progress", "current": 0, "total": 1})
        out = _run_with_timeout(_video.make_music_video, (audio_path, images), timeout)
        if out is None:
            return {"error": "Timed out", "result": None}
        self.publish("progress", {"type": "progress", "current": 1, "total": 1})
        return {"result": {"path": str(out)}}


@register_skill("video_effects", "video")
class VideoEffectsSkill(BaseSkill):
    name = "video_effects"
    description = "Apply video effects: grayscale, sepia, invert, blur, edge, pixelate"
    category = "video"
    def execute(self, **kwargs) -> dict:
        path = Path(kwargs.get("path", ""))
        effect = kwargs.get("effect", "grayscale")
        if not path.exists():
            return {"error": f"File not found: {path}"}
        if not _check_ffmpeg():
            return {"error": "ffmpeg not found on system PATH"}
        timeout = kwargs.get("timeout", 300)
        self.publish("progress", {"type": "progress", "current": 0, "total": 1})
        out = _run_with_timeout(_video.apply_effect, (path, effect), timeout)
        if out is None:
            return {"error": "Timed out", "result": None}
        self.publish("progress", {"type": "progress", "current": 1, "total": 1})
        return {"result": {"path": str(out)}}


@register_skill("video_speed", "video")
class VideoSpeedSkill(BaseSkill):
    name = "video_speed"
    description = "Change video playback speed"
    category = "video"
    def execute(self, **kwargs) -> dict:
        path = Path(kwargs.get("path", ""))
        speed = kwargs.get("speed", 2.0)
        if not path.exists():
            return {"error": f"File not found: {path}"}
        if not _check_ffmpeg():
            return {"error": "ffmpeg not found on system PATH"}
        timeout = kwargs.get("timeout", 300)
        self.publish("progress", {"type": "progress", "current": 0, "total": 1})
        out = _run_with_timeout(_video.change_speed, (path, speed), timeout)
        if out is None:
            return {"error": "Timed out", "result": None}
        self.publish("progress", {"type": "progress", "current": 1, "total": 1})
        return {"result": {"path": str(out)}}


@register_skill("video_avatar", "video")
class VideoAvatarSkill(BaseSkill):
    name = "video_avatar"
    description = "Process video through talking avatar: detect and overlay mouth landmarks"
    category = "video"
    def execute(self, **kwargs) -> dict:
        path = Path(kwargs.get("path", ""))
        if not path.exists():
            return {"error": f"File not found: {path}"}
        if not _check_ffmpeg():
            return {"error": "ffmpeg not found on system PATH"}
        timeout = kwargs.get("timeout", 300)
        self.publish("progress", {"type": "progress", "current": 0, "total": 1})
        out = _run_with_timeout(_video.process_avatar, (path,), timeout)
        if out is None:
            return {"error": "Timed out", "result": None}
        self.publish("progress", {"type": "progress", "current": 1, "total": 1})
        return {"result": {"path": str(out)}}


@register_skill("video_audio_add", "video")
class VideoAudioAddSkill(BaseSkill):
    name = "video_audio_add"
    description = "Add/replace audio track on a video file"
    category = "video"
    def execute(self, **kwargs) -> dict:
        video_path = Path(kwargs.get("video", ""))
        audio_path = Path(kwargs.get("audio", ""))
        if not video_path.exists() or not audio_path.exists():
            return {"error": "Video or audio file not found"}
        if not _check_ffmpeg():
            return {"error": "ffmpeg not found on system PATH"}
        volume = kwargs.get("volume", 1.0)
        timeout = kwargs.get("timeout", 300)
        self.publish("progress", {"type": "progress", "current": 0, "total": 1})
        out = _run_with_timeout(_video.add_audio_to_video, (video_path, audio_path, None, volume), timeout)
        if out is None:
            return {"error": "Timed out", "result": None}
        self.publish("progress", {"type": "progress", "current": 1, "total": 1})
        return {"result": {"path": str(out)}}


@register_skill("video_webcam", "video")
class VideoWebcamSkill(BaseSkill):
    name = "video_webcam"
    description = "Capture a single frame from webcam"
    category = "video"
    def execute(self, **kwargs) -> dict:
        from ..tools.master_skills.videoSkill import WebcamCapture
        cam = WebcamCapture(kwargs.get("camera_id", 0))
        frame = cam.capture_frame()
        output = Path(kwargs.get("output", "")) if kwargs.get("output") else Path("webcam_capture.jpg")
        import cv2
        cv2.imwrite(str(output), frame)
        return {"result": {"path": str(output)}}


@register_skill("video_info", "video")
class VideoInfoSkill(BaseSkill):
    name = "video_info"
    description = "Get video skill metadata and capabilities"
    category = "video"
    def execute(self, **kwargs) -> dict:
        from ..tools.master_skills.videoSkill import __meta__
        return {"result": __meta__}
