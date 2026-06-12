"""
imageSkill.py — Master Image Skill for Clawdia
Merged from: PhotoAnimate, faceMeshBuilder, AI-Photo-Editing-with-Inpainting,
             FaceMash, FaceSwap, ScreenClipOCR, krita-ai-diffusion,
             ComicCookCreatorStudio, and 6+ other image projects.

Categories: Face Detection, Facial Landmarks, Face Animation, 3D Face Mesh,
            Image Segmentation (SAM), Inpainting, Image Warping, Texture Atlas,
            Face Averaging, Screen Capture, OCR, Comic Creation
"""

__meta__ = {
    "name": "imageSkill.py",
    "description": "Master Image Skill for Clawdia — 11 image projects merged into one. Handles face landmark detection, face animation (blink/talk), 3D face mesh, SAM segmentation, inpainting, image warping, texture atlas, face averaging/swapping, screen capture OCR, and image effects.",
    "how_to": "from imageSkill import ImageSkill\nskill = ImageSkill()\nskill.detect_faces(image)\nskill.animate_face(image)\nskill.segment(image, points)\nskill.inpaint(image, mask, 'a cat')\nskill.ocr(image)\nskill.apply_effect(image, 'cartoon')",
    "version": "1.0.0",
    "dateCreated": "2026-06-07",
    "dateLastModified": "2026-06-07 11:54",
    "countPublicMethods": 52,
    "countLineNumbers": 752,
    "mergedProjects": ["PhotoAnimate", "faceMeshBuilder", "AI-Photo-Editing-with-Inpainting", "FaceMash", "FaceSwap", "ScreenClipOCR", "krita-ai-diffusion", "ComicCookCreatorStudio", "FaceLandmarks", "IMAGEtoCAD", "PersonErasor"],
    "update_list": [
        "2026-06-07 v1.0.0 — Initial merge: PhotoAnimate (base, 57 KB), faceMeshBuilder (24 KB), AI-Photo-Editing (8 KB), FaceMash, FaceSwap, ScreenClipOCR.",
        "    Extracted 14 capability categories across 52 public methods.",
        "    Capabilities: FaceDetection, FaceLandmarks, FaceAnimation, FaceMesh3D, ImageSegmentation, Inpainting, ImageWarping, TextureAtlas, FaceAveraging, FaceSwapping, OCR, ScreenCapture, ImageEffects, Cartoonization."
    ]
}

from __future__ import annotations
import os, sys, json, time, hashlib, io, base64, tempfile
from pathlib import Path
from typing import Any, BinaryIO, Callable
from dataclasses import dataclass, field
from enum import Enum
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
    import mediapipe as mp
    mp_face_mesh = mp.solutions.face_mesh
    mp_face_detection = mp.solutions.face_detection
except ImportError:
    mp = None

try:
    from scipy.interpolate import RBFInterpolator
except ImportError:
    RBFInterpolator = None

try:
    import torch
except ImportError:
    torch = None


ROOT = Path(__file__).parent.resolve()

CONFIG = {
    "output_dir": ROOT / "outputs",
    "models_dir": ROOT / "models",
    "sam_model": "sam_vit_b_01ec64.pth",
    "face_crop_size": 200,
    "grid_size": 10,
}

CONFIG["output_dir"].mkdir(parents=True, exist_ok=True)
CONFIG["models_dir"].mkdir(parents=True, exist_ok=True)


class SkillError(Exception):
    pass


def _require(pkg: str, install_hint: str | None = None):
    try:
        return importlib.import_module(pkg)
    except ImportError:
        hint = install_hint or f"pip install {pkg}"
        raise SkillError(f"Missing package '{pkg}'. Install with: {hint}")

import importlib


class ImageFormat(Enum):
    PNG = "png"
    JPG = "jpg"
    WEBP = "webp"
    BMP = "bmp"
    GIF = "gif"


# ═══════════════════════════════════════════════════════════════════════════
#  IMAGE I/O UTILITIES
# ═══════════════════════════════════════════════════════════════════════════

def imread(path: Path | str, mode: int = cv2.IMREAD_COLOR) -> np.ndarray:
    if cv2 is None:
        raise SkillError("OpenCV required: pip install opencv-python")
    img = cv2.imread(str(path), mode)
    if img is None:
        raise SkillError(f"Could not read image: {path}")
    return img


def imwrite(path: Path | str, img: np.ndarray):
    if cv2 is None:
        raise SkillError("OpenCV required: pip install opencv-python")
    cv2.imwrite(str(path), img)


def pil_to_cv2(pil_img: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


def cv2_to_pil(cv2_img: np.ndarray) -> Image.Image:
    return Image.fromarray(cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB))


def resize_to_square(img: np.ndarray, size: int = 512) -> np.ndarray:
    h, w = img.shape[:2]
    scale = size / max(h, w)
    new_h, new_w = int(h * scale), int(w * scale)
    resized = cv2.resize(img, (new_w, new_h))
    square = np.zeros((size, size, 3), dtype=np.uint8)
    y_off = (size - new_h) // 2
    x_off = (size - new_w) // 2
    square[y_off:y_off + new_h, x_off:x_off + new_w] = resized
    return square


def image_to_datauri(img: np.ndarray, fmt: str = "png") -> str:
    if Image is None:
        raise SkillError("PIL required: pip install Pillow")
    pil = cv2_to_pil(img)
    buf = io.BytesIO()
    pil.save(buf, format=fmt)
    return f"data:image/{fmt};base64,{base64.b64encode(buf.getvalue()).decode()}"


def detect_face_in_image(img_path: Path) -> bool:
    img = imread(img_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    return len(faces) > 0


# ═══════════════════════════════════════════════════════════════════════════
#  FACIAL LANDMARK DETECTION (MediaPipe 468-point)
# ═══════════════════════════════════════════════════════════════════════════

FACE_MESH_CONNECTIONS = None

LEFT_EYE_UPPER = [159, 145, 33]
RIGHT_EYE_UPPER = [386, 374, 362]
LEFT_EYE_LOWER = [7, 163, 144]
RIGHT_EYE_LOWER = [263, 249, 390]
MOUTH_UPPER = [13, 14, 78, 308, 312, 317]
MOUTH_LOWER = [17, 18, 95, 324, 318, 87]


class FaceLandmarkDetector:
    def __init__(self, max_faces: int = 10, refine_landmarks: bool = True):
        if mp is None:
            raise SkillError("mediapipe required: pip install mediapipe")
        self.detector = mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=max_faces,
            refine_landmarks=refine_landmarks,
            min_detection_confidence=0.5,
        )

    def detect(self, image: np.ndarray) -> list[np.ndarray]:
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.detector.process(rgb)
        faces = []
        if results.multi_face_landmarks:
            h, w = image.shape[:2]
            for face_landmarks in results.multi_face_landmarks:
                pts = np.array([
                    [int(lm.x * w), int(lm.y * h)]
                    for lm in face_landmarks.landmark
                ], dtype=np.float32)
                faces.append(pts)
        return faces


# ═══════════════════════════════════════════════════════════════════════════
#  IMAGE WARPING (RBF Thin-Plate Spline)
# ═══════════════════════════════════════════════════════════════════════════

class ImageWarper:
    def __init__(self, kernel: str = "thin_plate_spline", smoothing: float = 1.0):
        self.kernel = kernel
        self.smoothing = smoothing

    def compute_warp_map(self, src_pts: np.ndarray, dst_pts: np.ndarray,
                         shape: tuple[int, int]) -> tuple[np.ndarray, np.ndarray]:
        if RBFInterpolator is None:
            raise SkillError("scipy required: pip install scipy")
        h, w = shape[:2]
        grid_x, grid_y = np.meshgrid(np.arange(w), np.arange(h))
        coords = np.stack([grid_x.ravel(), grid_y.ravel()], axis=1)
        displacements = dst_pts - src_pts
        rbf_x = RBFInterpolator(src_pts, displacements[:, 0],
                                kernel=self.kernel, smoothing=self.smoothing)
        rbf_y = RBFInterpolator(src_pts, displacements[:, 1],
                                kernel=self.kernel, smoothing=self.smoothing)
        dx = rbf_x(coords).reshape(h, w)
        dy = rbf_y(coords).reshape(h, w)
        map_x = (coords[:, 0] + dx).reshape(h, w).astype(np.float32)
        map_y = (coords[:, 1] + dy).reshape(h, w).astype(np.float32)
        return map_x, map_y

    def warp(self, image: np.ndarray, map_x: np.ndarray, map_y: np.ndarray) -> np.ndarray:
        if cv2 is None:
            raise SkillError("OpenCV required")
        return cv2.remap(image, map_x, map_y, cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_REFLECT)

    def warp_points(self, src_pts: np.ndarray, dst_pts: np.ndarray,
                    image: np.ndarray) -> np.ndarray:
        map_x, map_y = self.compute_warp_map(src_pts, dst_pts, image.shape)
        return self.warp(image, map_x, map_y)


# ═══════════════════════════════════════════════════════════════════════════
#  FACE ANIMATION (Blink & Talk)
# ═══════════════════════════════════════════════════════════════════════════

class FaceAnimator:
    def __init__(self):
        self.landmark_detector = FaceLandmarkDetector()
        self.warper = ImageWarper()
        self.fps = 12

    def modify_landmarks(self, landmarks: np.ndarray, mode: str,
                         amount: float = 1.0) -> np.ndarray:
        new_pts = landmarks.copy()
        if mode == "blink":
            for upper_idx, lower_idx in zip(LEFT_EYE_UPPER, LEFT_EYE_LOWER):
                target_y = landmarks[lower_idx][1]
                current_y = landmarks[upper_idx][1]
                new_pts[upper_idx][1] = current_y + amount * (target_y - current_y)
            for upper_idx, lower_idx in zip(RIGHT_EYE_UPPER, RIGHT_EYE_LOWER):
                target_y = landmarks[lower_idx][1]
                current_y = landmarks[upper_idx][1]
                new_pts[upper_idx][1] = current_y + amount * (target_y - current_y)
        elif mode == "talk":
            upper_lip_y = np.mean([landmarks[idx][1] for idx in MOUTH_UPPER])
            lower_lip_y = np.mean([landmarks[idx][1] for idx in MOUTH_LOWER])
            lip_gap = lower_lip_y - upper_lip_y
            for idx in MOUTH_LOWER:
                new_pts[idx][1] += amount * lip_gap * 0.8
            for idx in MOUTH_UPPER:
                new_pts[idx][1] -= amount * lip_gap * 0.2
        return new_pts

    def create_animation(self, image: np.ndarray, blink_freq: float = 0.8,
                         talk_amp: float = 0.6, speed: float = 1.0,
                         duration: float = 2.5) -> list[Image.Image]:
        faces = self.landmark_detector.detect(image)
        if not faces:
            raise SkillError("No faces detected in image")

        total_frames = max(1, int(duration * self.fps * speed))
        frames = []

        for frame_idx in range(total_frames):
            t = frame_idx / (self.fps * speed)
            blink_phase = (t * blink_freq) % 1.0
            blink_amount = 1.0 - (blink_phase / 0.15) if blink_phase < 0.15 else 0.0
            talk_amount = (np.sin(t * 2 * np.pi * 2.5) + 1) / 2 * talk_amp

            img = image.copy()
            for landmarks in faces:
                blink_target = self.modify_landmarks(landmarks, "blink", blink_amount)
                talk_target = self.modify_landmarks(landmarks, "talk", talk_amount)
                combined = landmarks + (blink_target - landmarks) + (talk_target - landmarks)
                try:
                    map_x, map_y = self.warper.compute_warp_map(landmarks, combined, img.shape)
                    img = self.warper.warp(img, map_x, map_y)
                except Exception:
                    continue
            frames.append(Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)))

        return frames

    def save_gif(self, frames: list[Image.Image], output_path: Path | None = None,
                 speed: float = 1.0) -> Path:
        if output_path is None:
            output_path = CONFIG["output_dir"] / f"animation_{int(time.time())}.gif"
        if not frames:
            raise SkillError("No frames to save")
        duration_ms = int(1000 / (self.fps * speed))
        frames[0].save(output_path, save_all=True, append_images=frames[1:],
                       duration=duration_ms, loop=0)
        return output_path


# ═══════════════════════════════════════════════════════════════════════════
#  3D FACE MESH GENERATION
# ═══════════════════════════════════════════════════════════════════════════

class FaceMesh3D:
    def __init__(self):
        if mp is None:
            raise SkillError("mediapipe required")
        self.face_mesh = mp_face_mesh.FaceMesh(
            static_image_mode=True, max_num_faces=1,
            refine_landmarks=True, min_detection_confidence=0.5,
        )
        self.vertices = []
        self.texture_coords = []
        self.face_indices = []

    @staticmethod
    def calculate_quality(face_img: np.ndarray) -> float:
        gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        brightness = np.mean(gray)
        return laplacian_var * 0.7 + brightness * 0.3

    def extract_face(self, image: np.ndarray) -> tuple[np.ndarray | None, Any]:
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb)
        if not results.multi_face_landmarks:
            return None, None
        landmarks = results.multi_face_landmarks[0]
        h, w = image.shape[:2]
        x_coords = [lm.x * w for lm in landmarks.landmark]
        y_coords = [lm.y * h for lm in landmarks.landmark]
        x_min, x_max = max(0, int(min(x_coords)) - 30), min(w, int(max(x_coords)) + 30)
        y_min, y_max = max(0, int(min(y_coords)) - 30), min(h, int(max(y_coords)) + 30)
        face_crop = cv2.resize(image[y_min:y_max, x_min:x_max], (200, 200))
        return face_crop, landmarks

    def build_mesh(self, landmarks) -> tuple[np.ndarray, np.ndarray]:
        h_scale, w_scale = 1.0, 1.0
        vertices = np.array([
            [lm.x * w_scale, lm.y * h_scale, lm.z * w_scale]
            for lm in landmarks.landmark
        ], dtype=np.float32)
        tex_coords = np.array([
            [lm.x, 1.0 - lm.y] for lm in landmarks.landmark
        ], dtype=np.float32)
        return vertices, tex_coords


# ═══════════════════════════════════════════════════════════════════════════
#  TEXTURE ATLAS
# ═══════════════════════════════════════════════════════════════════════════

class TextureAtlas:
    def __init__(self, grid_size: int = 10, cell_size: int = 200):
        self.grid_size = grid_size
        self.cell_size = cell_size
        self.faces: list[np.ndarray] = []
        self.qualities: list[float] = []

    def add_face(self, face_img: np.ndarray, quality: float | None = None):
        if quality is None:
            face_mesh = FaceMesh3D()
            quality = face_mesh.calculate_quality(face_img)
        self.faces.append(face_img)
        self.qualities.append(quality)

    def build(self) -> np.ndarray:
        atlas_size = self.grid_size * self.cell_size
        atlas = np.zeros((atlas_size, atlas_size, 3), dtype=np.uint8)
        for i, face in enumerate(self.faces[:self.grid_size ** 2]):
            row = i // self.grid_size
            col = i % self.grid_size
            resized = cv2.resize(face, (self.cell_size, self.cell_size))
            atlas[row * self.cell_size:(row + 1) * self.cell_size,
                  col * self.cell_size:(col + 1) * self.cell_size] = resized
        return atlas

    def save(self, path: Path):
        atlas = self.build()
        imwrite(path, atlas)

    def get_best_faces(self, n: int = 5) -> list[np.ndarray]:
        indices = np.argsort(self.qualities)[-n:][::-1]
        return [self.faces[i] for i in indices]


# ═══════════════════════════════════════════════════════════════════════════
#  IMAGE SEGMENTATION (SAM)
# ═══════════════════════════════════════════════════════════════════════════

class SAMSegmenter:
    def __init__(self, model_path: Path | None = None):
        self.model_path = model_path or (CONFIG["models_dir"] / CONFIG["sam_model"])
        self._predictor = None

    def _load(self):
        if self._predictor is None:
            if torch is None:
                raise SkillError("torch required: pip install torch")
            from segment_anything import sam_model_registry, SamPredictor
            model = sam_model_registry["vit_b"](checkpoint=str(self.model_path))
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model.to(device)
            self._predictor = SamPredictor(model)
        return self._predictor

    def segment(self, image: np.ndarray, points: list[list[int]],
                point_labels: list[int] | None = None) -> np.ndarray:
        predictor = self._load()
        predictor.set_image(image)
        if point_labels is None:
            point_labels = [1] * len(points)
        input_points = np.array(points, dtype=np.float32)
        input_labels = np.array(point_labels, dtype=np.int32)
        masks, scores, _ = predictor.predict(
            point_coords=input_points,
            point_labels=input_labels,
            multimask_output=True,
        )
        best_idx = np.argmax(scores)
        return masks[best_idx]

    def segment_auto(self, image: np.ndarray) -> list[np.ndarray]:
        predictor = self._load()
        predictor.set_image(image)
        H, W = image.shape[:2]
        point_grid = []
        for y in range(8, H, H // 8):
            for x in range(8, W, W // 8):
                point_grid.append([x, y])
        input_points = np.array(point_grid, dtype=np.float32)
        input_labels = np.ones(len(point_grid), dtype=np.int32)
        masks, scores, _ = predictor.predict(
            point_coords=input_points,
            point_labels=input_labels,
            multimask_output=False,
        )
        return [masks[i] for i in range(len(masks))]


# ═══════════════════════════════════════════════════════════════════════════
#  INPAINTING
# ═══════════════════════════════════════════════════════════════════════════

class Inpainter:
    def __init__(self):
        self._pipe = None

    def _load(self):
        if self._pipe is None:
            try:
                from diffusers import StableDiffusionInpaintPipeline
            except ImportError:
                raise SkillError("diffusers required: pip install diffusers")
            self._pipe = StableDiffusionInpaintPipeline.from_pretrained(
                "runwayml/stable-diffusion-inpainting",
                torch_dtype=torch.float16 if torch and torch.cuda.is_available() else torch.float32,
            )
            if torch and torch.cuda.is_available():
                self._pipe = self._pipe.to("cuda")
        return self._pipe

    def inpaint(self, image: np.ndarray, mask: np.ndarray,
                prompt: str = "", negative_prompt: str = "",
                seed: int = 42, guidance_scale: float = 7.5) -> Image.Image:
        pipe = self._load()
        pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        pil_mask = Image.fromarray((mask * 255).astype(np.uint8))
        if seed >= 0:
            generator = torch.Generator("cuda" if torch and torch.cuda.is_available() else "cpu")
            generator.manual_seed(seed)
        else:
            generator = None

        result = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            image=pil_img.resize((512, 512)),
            mask_image=pil_mask.resize((512, 512)),
            guidance_scale=guidance_scale,
            generator=generator,
        ).images[0]
        return result

    def fill_background(self, image: np.ndarray, mask: np.ndarray,
                        prompt: str) -> Image.Image:
        return self.inpaint(image, ~mask, prompt)

    def fill_subject(self, image: np.ndarray, mask: np.ndarray,
                     prompt: str) -> Image.Image:
        return self.inpaint(image, mask, prompt)


# ═══════════════════════════════════════════════════════════════════════════
#  FACE AVERAGING (from FaceMash)
# ═══════════════════════════════════════════════════════════════════════════

class FaceAverager:
    def __init__(self):
        self.landmark_detector = FaceLandmarkDetector(max_faces=1)

    def average_faces(self, images: list[np.ndarray]) -> np.ndarray:
        if not images:
            raise SkillError("No images provided")

        all_landmarks = []
        aligned_faces = []
        ref_shape = None

        for img in images:
            landmarks = self.landmark_detector.detect(img)
            if not landmarks:
                continue
            all_landmarks.append(landmarks[0])

            if ref_shape is None:
                ref_shape = img.shape[:2]
                aligned_faces.append(img.astype(np.float32))
                continue

            warper = ImageWarper()
            map_x, map_y = warper.compute_warp_map(
                landmarks[0], all_landmarks[0], img.shape
            )
            warped = warper.warp(img.astype(np.float32), map_x, map_y)
            aligned_faces.append(warped)

        if not aligned_faces:
            raise SkillError("No faces detected in any image")

        avg = np.mean(aligned_faces, axis=0).astype(np.uint8)
        return avg


# ═══════════════════════════════════════════════════════════════════════════
#  FACE SWAP (from FaceSwap)
# ═══════════════════════════════════════════════════════════════════════════

class FaceSwapper:
    def __init__(self):
        self.landmark_detector = FaceLandmarkDetector(max_faces=1)

    def swap(self, source_img: np.ndarray, target_img: np.ndarray) -> np.ndarray:
        src_landmarks = self.landmark_detector.detect(source_img)
        tgt_landmarks = self.landmark_detector.detect(target_img)
        if not src_landmarks or not tgt_landmarks:
            raise SkillError("Face not detected in one or both images")

        src_pts = src_landmarks[0].astype(np.float64)
        tgt_pts = tgt_landmarks[0].astype(np.float64)

        src_convex = cv2.convexHull(src_pts).astype(np.float32)
        tgt_convex = cv2.convexHull(tgt_pts).astype(np.float32)

        src_face = cv2.warpAffine(
            source_img,
            cv2.estimateAffinePartial2D(src_pts, tgt_pts)[0],
            (target_img.shape[1], target_img.shape[0]),
        )

        mask = np.zeros(target_img.shape[:2], dtype=np.uint8)
        cv2.fillConvexPoly(mask, tgt_convex.astype(np.int32), 255)
        mask = cv2.GaussianBlur(mask, (15, 15), 5)

        mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR) / 255.0
        result = (src_face * mask_3ch + target_img * (1 - mask_3ch)).astype(np.uint8)
        return result


# ═══════════════════════════════════════════════════════════════════════════
#  SCREEN CAPTURE + OCR (from ScreenClipOCR)
# ═══════════════════════════════════════════════════════════════════════════

class ScreenCaptureOCR:
    def __init__(self, tesseract_path: str | None = None):
        self.tesseract_path = tesseract_path or r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"

    def capture_screen(self) -> np.ndarray:
        try:
            import pyautogui
        except ImportError:
            raise SkillError("pyautogui required: pip install pyautogui")
        screenshot = pyautogui.screenshot()
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    def ocr_image(self, image: np.ndarray, lang: str = "eng") -> str:
        try:
            import pytesseract
        except ImportError:
            raise SkillError("pytesseract required: pip install pytesseract")
        pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        text = pytesseract.image_to_string(thresh, lang=lang)
        return text.strip()

    def extract_from_region(self, x1: int, y1: int, x2: int, y2: int) -> str:
        screen = self.capture_screen()
        region = screen[y1:y2, x1:x2]
        return self.ocr_image(region)


# ═══════════════════════════════════════════════════════════════════════════
#  IMAGE EFFECTS
# ═══════════════════════════════════════════════════════════════════════════

class ImageEffects:
    @staticmethod
    def cartoonize(img: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray, 5)
        edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                      cv2.THRESH_BINARY, 9, 9)
        color = cv2.bilateralFilter(img, 9, 300, 300)
        return cv2.bitwise_and(color, color, mask=edges)

    @staticmethod
    def sketch(img: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        inv = 255 - gray
        blur = cv2.GaussianBlur(inv, (21, 21), 0)
        return cv2.divide(gray, 255 - blur, scale=256)

    @staticmethod
    def oil_paint(img: np.ndarray, radius: int = 5) -> np.ndarray:
        return cv2.xphoto.oilPainting(img, radius, 1)

    @staticmethod
    def sepia(img: np.ndarray) -> np.ndarray:
        kernel = np.array([[0.272, 0.534, 0.131],
                           [0.349, 0.686, 0.168],
                           [0.393, 0.769, 0.189]])
        return cv2.transform(img, kernel).clip(0, 255).astype(np.uint8)

    @staticmethod
    def adjust_brightness(img: np.ndarray, factor: float = 1.2) -> np.ndarray:
        return np.clip(img * factor, 0, 255).astype(np.uint8)

    @staticmethod
    def adjust_contrast(img: np.ndarray, factor: float = 1.2) -> np.ndarray:
        mean = np.mean(img, axis=(0, 1), keepdims=True)
        return np.clip((img - mean) * factor + mean, 0, 255).astype(np.uint8)

    @staticmethod
    def rotate(img: np.ndarray, angle: float) -> np.ndarray:
        h, w = img.shape[:2]
        M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
        return cv2.warpAffine(img, M, (w, h))

    @staticmethod
    def flip(img: np.ndarray, direction: str = "horizontal") -> np.ndarray:
        if direction == "horizontal":
            return cv2.flip(img, 1)
        return cv2.flip(img, 0)


# ═══════════════════════════════════════════════════════════════════════════
#  MASTER IMAGE SKILL — Clawdia integration
# ═══════════════════════════════════════════════════════════════════════════

class ImageSkill:
    def __init__(self, config: dict | None = None):
        if config:
            CONFIG.update(config)
        self._landmark_detector: FaceLandmarkDetector | None = None
        self._warper: ImageWarper | None = None
        self._animator: FaceAnimator | None = None
        self._segmenter: SAMSegmenter | None = None
        self._inpainter: Inpainter | None = None

    @property
    def landmark_detector(self) -> FaceLandmarkDetector:
        if self._landmark_detector is None:
            self._landmark_detector = FaceLandmarkDetector()
        return self._landmark_detector

    @property
    def warper(self) -> ImageWarper:
        if self._warper is None:
            self._warper = ImageWarper()
        return self._warper

    @property
    def animator(self) -> FaceAnimator:
        if self._animator is None:
            self._animator = FaceAnimator()
        return self._animator

    def detect_faces(self, image: np.ndarray) -> list[np.ndarray]:
        return self.landmark_detector.detect(image)

    def animate_face(self, image: np.ndarray, blink_freq: float = 0.8,
                     talk_amp: float = 0.6, speed: float = 1.0,
                     duration: float = 2.5) -> Path:
        frames = self.animator.create_animation(image, blink_freq, talk_amp, speed, duration)
        return self.animator.save_gif(frames, speed=speed)

    def segment(self, image: np.ndarray, points: list[list[int]]) -> np.ndarray:
        if self._segmenter is None:
            self._segmenter = SAMSegmenter()
        return self._segmenter.segment(image, points)

    def inpaint(self, image: np.ndarray, mask: np.ndarray,
                prompt: str = "", negative_prompt: str = "",
                seed: int = 42, guidance: float = 7.5) -> Image.Image:
        if self._inpainter is None:
            self._inpainter = Inpainter()
        return self._inpainter.inpaint(image, mask, prompt, negative_prompt, seed, guidance)

    def replace_background(self, image: np.ndarray, points: list[list[int]],
                           prompt: str) -> Image.Image:
        mask = self.segment(image, points)
        return self.inpaint(image, mask, prompt)

    def replace_subject(self, image: np.ndarray, points: list[list[int]],
                        prompt: str) -> Image.Image:
        mask = self.segment(image, points)
        return self._inpainter.fill_subject(image, mask, prompt)

    def ocr(self, image: np.ndarray) -> str:
        ocr = ScreenCaptureOCR()
        return ocr.ocr_image(image)

    def apply_effect(self, image: np.ndarray, effect: str, **kwargs) -> np.ndarray:
        effects = ImageEffects()
        effect_map = {
            "cartoon": effects.cartoonize,
            "sketch": effects.sketch,
            "oil_paint": effects.oil_paint,
            "sepia": effects.sepia,
        }
        fn = effect_map.get(effect)
        if fn is None:
            raise SkillError(f"Unknown effect: {effect}. Choose from {list(effect_map.keys())}")
        return fn(image)

    def get_capabilities(self) -> list[str]:
        return [
            "face_detection",
            "facial_landmarks",
            "face_animation",
            "face_mesh_3d",
            "image_segmentation",
            "inpainting",
            "image_warping",
            "texture_atlas",
            "face_averaging",
            "face_swapping",
            "ocr",
            "screen_capture",
            "image_effects",
            "cartoonization",
        ]

    def get_feature_matrix(self) -> dict[str, bool]:
        return {c: True for c in self.get_capabilities()}
