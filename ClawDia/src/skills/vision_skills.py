from pathlib import Path
from typing import Any
import numpy as np
from .base import BaseSkill, register_skill
from ..tools.master_skills.imageSkill import ImageSkill, resize_to_square, detect_face_in_image

_img: ImageSkill | None = None


def _get_img() -> ImageSkill:
    global _img
    if _img is None:
        _img = ImageSkill()
    return _img


def _load_image(path: str) -> np.ndarray | None:
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        return None
    try:
        from PIL import Image as PILImage
        with PILImage.open(str(p)) as im:
            im.verify()
    except Exception:
        return None
    import cv2
    img = cv2.imread(str(p))
    return img


def _is_video(path: str) -> bool:
    return Path(path).suffix.lower() in {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv'}


@register_skill("vision_detect", "vision")
class VisionDetectSkill(BaseSkill):
    name = "vision_detect"
    description = "Detect faces and return 468-point facial landmarks using MediaPipe"
    category = "vision"
    def execute(self, **kwargs) -> dict:
        path = kwargs.get("path", "")
        p = Path(path)
        if not p.exists():
            return {"error": "File not found"}
        if _is_video(path):
            return self._detect_video(path)
        img = _load_image(path)
        if img is None:
            return {"error": "Could not load image"}
        faces = _get_img().detect_faces(img)
        landmarks, scores = self._extract_scores(faces)
        return {"result": {
            "faces_detected": len(faces),
            "landmarks": landmarks,
            "confidence_scores": scores,
        }}

    def _detect_video(self, path: str) -> dict:
        import cv2
        cap = cv2.VideoCapture(path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        sample_interval = max(1, int(fps))
        all_faces = []
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % sample_interval == 0:
                faces = _get_img().detect_faces(frame)
                landmarks, scores = self._extract_scores(faces)
                all_faces.append({
                    "frame": frame_idx,
                    "faces_detected": len(faces),
                    "landmarks": landmarks,
                    "confidence_scores": scores,
                })
            frame_idx += 1
        cap.release()
        return {"result": {
            "mode": "video",
            "total_frames": total_frames,
            "fps": fps,
            "frames_sampled": len(all_faces),
            "per_frame": all_faces,
        }}

    def _extract_scores(self, faces: list) -> tuple[list, list | None]:
        landmarks = []
        scores = []
        has_scores = False
        for f in faces:
            if isinstance(f, (tuple, list)) and len(f) == 2:
                landmarks.append(f[0].tolist())
                scores.append(float(f[1]))
                has_scores = True
            else:
                landmarks.append(f.tolist() if hasattr(f, 'tolist') else f)
        return landmarks, scores if has_scores else None


@register_skill("vision_classify", "vision")
class VisionClassifySkill(BaseSkill):
    name = "vision_classify"
    description = "Detect if image contains a face using Haar cascade"
    category = "vision"
    def execute(self, **kwargs) -> dict:
        path = kwargs.get("path", "")
        if not path:
            return {"error": "No path provided"}
        has_face = detect_face_in_image(Path(path))
        return {"result": {"has_face": has_face}}


@register_skill("vision_ocr", "vision")
class VisionOcrSkill(BaseSkill):
    name = "vision_ocr"
    description = "Extract text from image using Tesseract OCR"
    category = "vision"
    def execute(self, **kwargs) -> dict:
        path = kwargs.get("path", "")
        img = _load_image(path)
        if img is None:
            return {"error": "Could not load image"}
        text = _get_img().ocr(img)
        return {"result": {"text": text}}


@register_skill("vision_segment", "vision")
class VisionSegmentSkill(BaseSkill):
    name = "vision_segment"
    description = "Segment objects in image using SAM click-point segmentation"
    category = "vision"
    def execute(self, **kwargs) -> dict:
        path = kwargs.get("path", "")
        points = kwargs.get("points", [])
        img = _load_image(path)
        if img is None:
            return {"error": "Could not load image"}
        if not points:
            return {"error": "No click points provided"}
        mask, scores = _get_img().segment(img, points, return_scores=True) if hasattr(_get_img().segment, '__wrapped__') or True else (_get_img().segment(img, points), None)
        mask_val = mask
        score_val = scores
        if isinstance(mask_val, tuple) and len(mask_val) == 2:
            mask_val, score_val = mask_val
        import cv2
        mask_path = Path(kwargs.get("output", "")) if kwargs.get("output") else Path(path).parent / f"mask_{Path(path).name}"
        cv2.imwrite(str(mask_path), (mask_val * 255).astype(np.uint8))
        result = {"mask_path": str(mask_path), "shape": list(mask_val.shape)}
        if score_val is not None:
            result["confidence_scores"] = score_val
        return {"result": result}


@register_skill("vision_inpaint", "vision")
class VisionInpaintSkill(BaseSkill):
    name = "vision_inpaint"
    description = "Inpaint image using Stable Diffusion — replace background or subject"
    category = "vision"
    def execute(self, **kwargs) -> dict:
        path = kwargs.get("path", "")
        prompt = kwargs.get("prompt", "")
        points = kwargs.get("points", [])
        invert = kwargs.get("invert", False)
        img = _load_image(path)
        if img is None or not prompt:
            return {"error": "Image or prompt missing"}
        if not points:
            return {"error": "No click points provided"}
        import cv2
        mask = _get_img().segment(img, points)
        if invert:
            result = _get_img().inpaint(img, mask, prompt)
        else:
            from ..tools.master_skills.imageSkill import Inpainter
            inpainter = Inpainter()
            result = inpainter.fill_background(img, mask, prompt)
        output = Path(kwargs.get("output", "")) if kwargs.get("output") else Path(path).parent / f"inpainted_{Path(path).name}"
        result.save(str(output))
        return {"result": {"path": str(output)}}


@register_skill("vision_animate", "vision")
class VisionAnimateSkill(BaseSkill):
    name = "vision_animate"
    description = "Animate face in image: blinking and talking GIF"
    category = "vision"
    def execute(self, **kwargs) -> dict:
        path = kwargs.get("path", "")
        img = _load_image(path)
        if img is None:
            return {"error": "Could not load image"}
        blink_freq = kwargs.get("blink_freq", 0.8)
        talk_amp = kwargs.get("talk_amp", 0.6)
        speed = kwargs.get("speed", 1.0)
        duration = kwargs.get("duration", 2.5)
        out = _get_img().animate_face(img, blink_freq, talk_amp, speed, duration)
        return {"result": {"gif_path": str(out)}}


@register_skill("vision_effects", "vision")
class VisionEffectsSkill(BaseSkill):
    name = "vision_effects"
    description = "Apply image effects: cartoon, sketch, oil_paint, sepia"
    category = "vision"
    def execute(self, **kwargs) -> dict:
        path = kwargs.get("path", "")
        effect = kwargs.get("effect", "cartoon")
        img = _load_image(path)
        if img is None:
            return {"error": "Could not load image"}
        result = _get_img().apply_effect(img, effect)
        output = Path(kwargs.get("output", "")) if kwargs.get("output") else Path(path).parent / f"{effect}_{Path(path).name}"
        import cv2
        cv2.imwrite(str(output), result)
        return {"result": {"path": str(output)}}


@register_skill("vision_swap", "vision")
class VisionSwapSkill(BaseSkill):
    name = "vision_swap"
    description = "Swap face from source image onto target image"
    category = "vision"
    def execute(self, **kwargs) -> dict:
        source = kwargs.get("source", "")
        target = kwargs.get("target", "")
        src_img = _load_image(source)
        tgt_img = _load_image(target)
        if src_img is None or tgt_img is None:
            return {"error": "Could not load source or target image"}
        from ..tools.master_skills.imageSkill import FaceSwapper
        swapper = FaceSwapper()
        result = swapper.swap(src_img, tgt_img)
        output = Path(kwargs.get("output", "")) if kwargs.get("output") else Path(target).parent / f"swapped_{Path(target).name}"
        import cv2
        cv2.imwrite(str(output), result)
        return {"result": {"path": str(output)}}


@register_skill("vision_info", "vision")
class VisionInfoSkill(BaseSkill):
    name = "vision_info"
    description = "Get image skill metadata and capabilities"
    category = "vision"
    def execute(self, **kwargs) -> dict:
        from ..tools.master_skills.imageSkill import __meta__
        return {"result": __meta__}
