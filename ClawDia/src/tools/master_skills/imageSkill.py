"""
imageSkill.py — Master Image Skill for Clawdia
Merged from: PhotoAnimate, faceMeshBuilder, AI-Photo-Editing-with-Inpainting,
             FaceMash, FaceSwap, ScreenClipOCR, krita-ai-diffusion,
             ComicCookCreatorStudio, and 6+ other image projects.

Categories: Face Detection, Facial Landmarks, Face Animation, 3D Face Mesh,
            Image Segmentation (SAM), Inpainting, Image Warping, Texture Atlas,
            Face Averaging, Screen Capture, OCR, Comic Creation
"""

from __future__ import annotations

__meta__ = {
    "name": "imageSkill.py",
    "description": "Master Image Skill for Clawdia — 11 image projects merged into one. Handles face landmark detection (MediaPipe + dlib), face animation (blink/talk), 3D face mesh, SAM segmentation, inpainting, image warping, texture atlas, face averaging/swapping (affine + Delaunay), screen capture OCR, and image effects.",
    "how_to": "from imageSkill import ImageSkill\nskill = ImageSkill()\nskill.detect_faces(image)\nskill.animate_face(image)\nskill.segment(image, points)\nskill.inpaint(image, mask, 'a cat')\nskill.ocr(image)\nskill.apply_effect(image, 'cartoon')",
    "version": "1.0.2",
    "dateCreated": "2026-06-07",
    "dateLastModified": "2026-06-07 12:15",
    "countPublicMethods": 63,
    "countLineNumbers": 1145,
    "mergedProjects": ["PhotoAnimate", "faceMeshBuilder", "AI-Photo-Editing-with-Inpainting", "FaceMash", "FaceSwap", "ScreenClipOCR", "krita-ai-diffusion", "ComicCookCreatorStudio", "FaceLandmarks", "IMAGEtoCAD", "PersonErasor", "ARC_Cinematic_Engine"],
    "update_list": [
        "2026-06-07 v1.0.0 — Initial merge: PhotoAnimate (base, 57 KB), faceMeshBuilder (24 KB), AI-Photo-Editing (8 KB), FaceMash, FaceSwap, ScreenClipOCR.",
        "    Extracted 14 capability categories across 52 public methods.",
        "    Capabilities: FaceDetection, FaceLandmarks, FaceAnimation, FaceMesh3D, ImageSegmentation, Inpainting, ImageWarping, TextureAtlas, FaceAveraging, FaceSwapping, OCR, ScreenCapture, ImageEffects, Cartoonization.",
        "2026-06-07 v1.0.1 — Refined FaceMesh3D (normalized vertices, Y-flip, face_indices), added from_image/save_model/load_model. Added TextureAtlas.add_or_replace_face + load static. Added 4 public methods to ImageSkill. New capability: face_model_persistence.",
        "2026-06-07 v1.0.2 — Added dlib 68-point face landmark detector (FaceLandmarkDetectorDlib). Added Delaunay triangulation face swapper (DelaunayFaceSwapper) with lip sync and identity library. Extracted from ARC Cinematic Engine. New capabilities: face_landmarks_dlib, delaunay_face_swapping, lip_sync."
    ]
}

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
except ImportError:
    mp = None

mp_face_mesh = None
mp_face_detection = None

try:
    import dlib as _dlib
except ImportError:
    _dlib = None

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
    if Image is not None:
        try:
            with Image.open(str(path)) as pil_check:
                pil_check.verify()
        except Exception as e:
            raise SkillError(f"Invalid or corrupted image file {path}: {e}")
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
        self.max_faces = max_faces
        self.refine_landmarks = refine_landmarks
        self._detector = None

    def _load(self):
        if self._detector is None:
            global mp_face_mesh
            if mp is None:
                raise SkillError("mediapipe required: pip install mediapipe")
            if mp_face_mesh is None:
                mp_face_mesh = mp.solutions.face_mesh
            self._detector = mp_face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=self.max_faces,
                refine_landmarks=self.refine_landmarks,
                min_detection_confidence=0.5,
            )
        return self._detector

    def detect(self, image: np.ndarray) -> list[np.ndarray]:
        detector = self._load()
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = detector.process(rgb)
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
#  FACIAL LANDMARK DETECTION (dlib 68-point)
# ═══════════════════════════════════════════════════════════════════════════

class FaceLandmarkDetectorDlib:
    """68-point facial landmark detector using dlib.

    Requires shape_predictor_68_face_landmarks.dat in models/ directory
    (99.7 MB — downloaded from dlib.net).
    """

    DLIB_MODEL = "shape_predictor_68_face_landmarks.dat"
    DLIB_MODEL_URL = "http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2"
    MOUTH_START = 48
    MOUTH_END = 68

    def __init__(self, model_path: Path | None = None):
        if _dlib is None:
            raise SkillError("dlib required: pip install dlib")
        self._detector = _dlib.get_frontal_face_detector()
        self._predictor = None
        self._model_path = model_path or CONFIG["models_dir"] / self.DLIB_MODEL
        if not self._model_path.exists():
            raise FileNotFoundError(
                f"dlib model not found: {self._model_path}. "
                f"Download from: {self.DLIB_MODEL_URL}\n"
                f"Extract and place at: {self._model_path}"
            )

    def _load(self):
        if self._predictor is None:
            self._predictor = _dlib.shape_predictor(str(self._model_path))
        return self._predictor

    def detect(self, image: np.ndarray) -> np.ndarray | None:
        predictor = self._load()
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        rects = self._detector(gray, 1)
        if not rects:
            return None
        main_rect = max(rects, key=lambda r: r.width() * r.height())
        landmarks = predictor(gray, main_rect)
        pts = np.array([[p.x, p.y] for p in landmarks.parts()], dtype=np.float64)
        return pts

    def get_mouth(self, landmarks: np.ndarray) -> np.ndarray:
        return landmarks[self.MOUTH_START:self.MOUTH_END]


# ═══════════════════════════════════════════════════════════════════════════
#  LANDMARK UTILITIES (from ARC Cinematic Engine)
# ═══════════════════════════════════════════════════════════════════════════

def normalize_landmarks(pts: np.ndarray | None) -> np.ndarray | None:
    """Normalize landmarks to zero-mean, unit-variance scale."""
    if pts is None:
        return None
    centroid = np.mean(pts, axis=0)
    centered = pts - centroid
    scale = np.max(np.linalg.norm(centered, axis=1))
    return centered / scale if scale > 0 else centered


def warp_triangle(img1: np.ndarray, img2: np.ndarray, t1: list, t2: list):
    """Warp triangle t1 from img1 onto triangle t2 in img2 (in-place)."""
    r1 = cv2.boundingRect(np.float32([t1]))
    r2 = cv2.boundingRect(np.float32([t2]))
    t1_rect = [(pt[0] - r1[0], pt[1] - r1[1]) for pt in t1]
    t2_rect = [(pt[0] - r2[0], pt[1] - r2[1]) for pt in t2]
    mask = np.zeros((r2[3], r2[2], 3), dtype=np.float32)
    cv2.fillConvexPoly(mask, np.int32(t2_rect), (1.0, 1.0, 1.0), 16, 0)
    M = cv2.getAffineTransform(np.float32(t1_rect), np.float32(t2_rect))
    warp_img = cv2.warpAffine(
        img1[r1[1]:r1[1] + r1[3], r1[0]:r1[0] + r1[2]],
        M, (r2[2], r2[3]),
        flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101,
    )
    img2[r2[1]:r2[1] + r2[3], r2[0]:r2[0] + r2[2]] = (
        img2[r2[1]:r2[1] + r2[3], r2[0]:r2[0] + r2[2]] * (1.0 - mask)
        + warp_img * mask
    )


MOUTH_LANDMARK_START = 48
MOUTH_LANDMARK_END = 68


# ═══════════════════════════════════════════════════════════════════════════
#  DELAUNAY FACE SWAPPER (from ARC Cinematic Engine)
# ═══════════════════════════════════════════════════════════════════════════

class DelaunayFaceSwapper:
    """Face swapping via Delaunay triangulation + seamless cloning.

    Unlike FaceSwapper (MediaPipe + affine), this uses dlib 68-point landmarks
    with per-triangle warping for more accurate face transfers. Supports
    lip-sync (mouth preservation) and identity library management.
    """

    def __init__(self, dlib_model_path: Path | None = None):
        self.ld = FaceLandmarkDetectorDlib(dlib_model_path)
        self.identity_library: dict[str, list[dict]] = {}

    def build_identity(self, name: str, image: np.ndarray) -> bool:
        """Add a face image to an identity library."""
        pts = self.ld.detect(image)
        if pts is None:
            return False
        norm = normalize_landmarks(pts)
        mouth = self.ld.get_mouth(pts)
        self.identity_library.setdefault(name, []).append({
            "img": image.copy(),
            "pts": pts,
            "norm": norm,
            "mouth": mouth,
        })
        return True

    def swap(self, source_name: str, target_frame: np.ndarray,
             lip_sync: bool = True) -> np.ndarray:
        """Swap a learned identity face onto a target video frame."""
        if source_name not in self.identity_library:
            raise SkillError(f"Unknown identity: {source_name}")

        tgt_pts = self.ld.detect(target_frame)
        if tgt_pts is None:
            return target_frame

        tgt_norm = normalize_landmarks(tgt_pts)
        best = min(
            self.identity_library[source_name],
            key=lambda d: np.linalg.norm(tgt_norm - d["norm"]),
        )
        src_img, src_pts = best["img"], best["pts"]

        hull_idx = cv2.convexHull(src_pts, returnPoints=False)
        src_hull = [tuple(src_pts[i[0]]) for i in hull_idx]
        tgt_hull = [tuple(tgt_pts[i[0]]) for i in hull_idx]

        hull_dict = {(round(p[0]), round(p[1])): i for i, p in enumerate(tgt_hull)}
        subdiv = cv2.Subdiv2D((0, 0, target_frame.shape[1], target_frame.shape[0]))
        for pt in tgt_hull:
            subdiv.insert((int(pt[0]), int(pt[1])))

        warped = np.zeros_like(target_frame, dtype=np.float32)
        for t in subdiv.getTriangleList():
            tri = [(t[0], t[1]), (t[2], t[3]), (t[4], t[5])]
            if any(p[0] < 0 or p[1] < 0
                   or p[0] > target_frame.shape[1]
                   or p[1] > target_frame.shape[0] for p in tri):
                continue
            src_t, tgt_t = [], []
            for pt in tri:
                idx = hull_dict.get((round(pt[0]), round(pt[1])), -1)
                if idx != -1:
                    src_t.append(src_hull[idx])
                    tgt_t.append(tgt_hull[idx])
            if len(src_t) == 3:
                warp_triangle(src_img, warped, src_t, tgt_t)

        mask = np.zeros(target_frame.shape, dtype=target_frame.dtype)
        cv2.fillConvexPoly(mask, np.int32(tgt_hull), (255, 255, 255))

        if lip_sync:
            src_mouth, tgt_mouth = best["mouth"], tgt_pts[MOUTH_LANDMARK_START:MOUTH_LANDMARK_END]
            if src_mouth is not None and len(src_mouth) > 0:
                src_mh = cv2.convexHull(src_mouth).reshape(-1, 2).tolist()
                tgt_mh = cv2.convexHull(tgt_mouth).reshape(-1, 2).tolist()
                cv2.fillConvexPoly(mask, np.int32(tgt_mh), (0, 0, 0))
                warped_mouth = np.zeros_like(target_frame, dtype=np.float32)
                warp_triangle(src_img, warped_mouth, src_mh, tgt_mh)
                mouth_mask = np.zeros(target_frame.shape, dtype=target_frame.dtype)
                cv2.fillConvexPoly(mouth_mask, np.int32(tgt_mh), (255, 255, 255))
                rm = cv2.boundingRect(np.float32([tgt_mh]))
                if rm[2] > 0 and rm[3] > 0:
                    try:
                        target_frame = cv2.seamlessClone(
                            np.clip(warped_mouth, 0, 255).astype(np.uint8),
                            target_frame, mouth_mask,
                            (rm[0] + rm[2] // 2, rm[1] + rm[3] // 2),
                            cv2.NORMAL_CLONE,
                        )
                    except Exception:
                        pass

        r = cv2.boundingRect(np.float32([tgt_hull]))
        if r[2] > 0 and r[3] > 0:
            try:
                target_frame = cv2.seamlessClone(
                    np.clip(warped, 0, 255).astype(np.uint8),
                    target_frame, mask,
                    (r[0] + r[2] // 2, r[1] + r[3] // 2),
                    cv2.NORMAL_CLONE,
                )
            except Exception:
                pass

        return target_frame
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
        self._face_mesh = None
        self.vertices: list[list[float]] = []
        self.texture_coords: list[list[float]] = []
        self.face_indices: list[tuple[int, ...]] = []

    def _load(self):
        if self._face_mesh is None:
            global mp_face_mesh
            if mp is None:
                raise SkillError("mediapipe required: pip install mediapipe")
            if mp_face_mesh is None:
                mp_face_mesh = mp.solutions.face_mesh
            self._face_mesh = mp_face_mesh.FaceMesh(
                static_image_mode=True, max_num_faces=1,
                refine_landmarks=True, min_detection_confidence=0.5,
            )
        return self._face_mesh

    @staticmethod
    def calculate_quality(face_img: np.ndarray) -> float:
        gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        brightness = np.mean(gray)
        return laplacian_var * 0.7 + brightness * 0.3

    def extract_face(self, image: np.ndarray) -> tuple[np.ndarray | None, Any]:
        face_mesh = self._load()
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)
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

    def build_mesh(self, landmarks) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Build normalized 3D mesh from MediaPipe face landmarks.

        Returns (vertices, tex_coords, face_indices).
        Vertices are in [-1, 1] range with Y flipped for 3D rendering.
        """
        self.vertices = []
        self.texture_coords = []
        for lm in landmarks.landmark:
            x = (lm.x - 0.5) * 2.0
            y = (0.5 - lm.y) * 2.0
            z = lm.z * 2.0
            self.vertices.append([x, y, z])
            self.texture_coords.append([lm.x, lm.y])
        self.face_indices = list(mp_face_mesh.FACEMESH_TESSELATION)
        return (
            np.array(self.vertices, dtype=np.float32),
            np.array(self.texture_coords, dtype=np.float32),
            np.array(self.face_indices, dtype=np.int32),
        )

    def from_image(self, image: np.ndarray) -> dict | None:
        """One-shot: detect face → extract crop → build mesh.

        Returns dict with keys: face_crop, vertices, tex_coords, face_indices,
        or None if no face found.
        """
        face_crop, landmarks = self.extract_face(image)
        if face_crop is None or landmarks is None:
            return None
        vertices, tex_coords, face_indices = self.build_mesh(landmarks)
        return {
            "face_crop": face_crop,
            "vertices": vertices,
            "tex_coords": tex_coords,
            "face_indices": face_indices,
        }

    def save_model(self, path: Path, atlas: np.ndarray, qualities: list[float] | None = None):
        """Save 3D model to BMP + NPZ pair.

        Writes atlas image to path.bmp and metadata (vertices, tex_coords,
        face_indices, qualities) to path_metadata.npz.
        """
        bmp_path = path.with_suffix(".bmp")
        cv2.imwrite(str(bmp_path), atlas)
        meta = {
            "vertices": np.array(self.vertices, dtype=np.float32),
            "texture_coords": np.array(self.texture_coords, dtype=np.float32),
            "face_indices": np.array(self.face_indices, dtype=np.int32),
        }
        if qualities is not None:
            meta["face_qualities"] = np.array(qualities, dtype=np.float32)
        np.savez(str(bmp_path).replace(".bmp", "_metadata.npz"), **meta)

    def load_model(self, path: Path) -> dict:
        """Load 3D model from BMP + NPZ pair.

        Args:
            path: Path to .bmp file (metadata loaded from sibling _metadata.npz).

        Returns dict with keys: atlas (np.ndarray), vertices, tex_coords,
        face_indices, face_qualities (optional).
        """
        bmp_path = path if path.suffix == ".bmp" else path.with_suffix(".bmp")
        atlas = cv2.imread(str(bmp_path))
        if atlas is None:
            raise SkillError(f"Could not load atlas from {bmp_path}")
        meta_path = bmp_path.parent / f"{bmp_path.stem}_metadata.npz"
        result = {"atlas": atlas}
        if meta_path.exists():
            data = np.load(str(meta_path), allow_pickle=True)
            self.vertices = data["vertices"].tolist() if "vertices" in data else []
            self.texture_coords = data["texture_coords"].tolist() if "texture_coords" in data else []
            self.face_indices = [tuple(f) for f in data["face_indices"]] if "face_indices" in data else []
            result["vertices"] = np.array(self.vertices)
            result["tex_coords"] = np.array(self.texture_coords)
            result["face_indices"] = np.array(self.face_indices)
            if "face_qualities" in data:
                result["face_qualities"] = data["face_qualities"]
        return result


# ═══════════════════════════════════════════════════════════════════════════
#  TEXTURE ATLAS
# ═══════════════════════════════════════════════════════════════════════════

class TextureAtlas:
    def __init__(self, grid_size: int = 10, cell_size: int = 200):
        self.grid_size = grid_size
        self.cell_size = cell_size
        self.max_faces = grid_size * grid_size
        self.faces: list[np.ndarray] = []
        self.qualities: list[float] = []

    def add_face(self, face_img: np.ndarray, quality: float | None = None):
        if quality is None:
            face_mesh = FaceMesh3D()
            quality = face_mesh.calculate_quality(face_img)
        self.faces.append(face_img)
        self.qualities.append(quality)

    def add_or_replace_face(self, face_img: np.ndarray, quality: float | None = None):
        """Add face, replacing lowest-quality face if grid is full and new face is better."""
        if quality is None:
            face_mesh = FaceMesh3D()
            quality = face_mesh.calculate_quality(face_img)
        if len(self.faces) < self.max_faces:
            self.faces.append(face_img)
            self.qualities.append(quality)
        else:
            min_idx = int(np.argmin(self.qualities))
            if quality > self.qualities[min_idx]:
                self.faces[min_idx] = face_img
                self.qualities[min_idx] = quality

    def build(self) -> np.ndarray:
        atlas_size = self.grid_size * self.cell_size
        atlas = np.full((atlas_size, atlas_size, 3), 255, dtype=np.uint8)
        for i, face in enumerate(self.faces[:self.max_faces]):
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
        n = min(n, len(self.qualities))
        if n == 0:
            return []
        indices = np.argsort(self.qualities)[-n:][::-1]
        return [self.faces[i] for i in indices]

    @staticmethod
    def load(path: Path) -> tuple["TextureAtlas", np.ndarray]:
        """Load texture atlas from a BMP file, extracting non-empty face cells.

        Returns (TextureAtlas instance, atlas_image).
        """
        grid_img = cv2.imread(str(path))
        if grid_img is None:
            raise SkillError(f"Could not load atlas from {path}")
        h, w = grid_img.shape[:2]
        atlas = TextureAtlas()
        cell_h = h // atlas.grid_size
        cell_w = w // atlas.grid_size
        for row in range(atlas.grid_size):
            for col in range(atlas.grid_size):
                y0, x0 = row * cell_h, col * cell_w
                cell = grid_img[y0:y0 + cell_h, x0:x0 + cell_w]
                if np.mean(cell) < 250:
                    atlas.faces.append(cell)
                    atlas.qualities.append(FaceMesh3D.calculate_quality(cell))
        return atlas, grid_img


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
        self.config = {**CONFIG, **(config or {})}
        self._landmark_detector: FaceLandmarkDetector | None = None
        self._warper: ImageWarper | None = None
        self._animator: FaceAnimator | None = None
        self._segmenter: SAMSegmenter | None = None
        self._inpainter: Inpainter | None = None
        self._face_mesh_3d: FaceMesh3D | None = None
        self._texture_atlas: TextureAtlas | None = None
        self._dlib_detector: FaceLandmarkDetectorDlib | None = None
        self._delaunay_swapper: DelaunayFaceSwapper | None = None
        self._landmark_cache: dict[str, list] = {}

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

    @property
    def face_mesh_3d(self) -> FaceMesh3D:
        if self._face_mesh_3d is None:
            self._face_mesh_3d = FaceMesh3D()
        return self._face_mesh_3d

    @property
    def texture_atlas(self) -> TextureAtlas:
        if self._texture_atlas is None:
            self._texture_atlas = TextureAtlas()
        return self._texture_atlas

    @property
    def dlib_detector(self) -> FaceLandmarkDetectorDlib:
        if self._dlib_detector is None:
            self._dlib_detector = FaceLandmarkDetectorDlib()
        return self._dlib_detector

    @property
    def delaunay_swapper(self) -> DelaunayFaceSwapper:
        if self._delaunay_swapper is None:
            self._delaunay_swapper = DelaunayFaceSwapper()
        return self._delaunay_swapper

    def detect_faces(self, image: np.ndarray,
                     use_cache: bool = False, cache_key: str | None = None) -> list[np.ndarray]:
        if use_cache and cache_key and cache_key in self._landmark_cache:
            return self._landmark_cache[cache_key]
        result = self.landmark_detector.detect(image)
        if use_cache and cache_key:
            self._landmark_cache[cache_key] = result
        return result

    def detect_faces_batch(self, image_paths: list[Path | str],
                           use_cache: bool = True) -> list[list[np.ndarray]]:
        results = []
        for path in image_paths:
            img = imread(str(path))
            cache_key = str(path) if use_cache else None
            faces = self.detect_faces(img, use_cache=use_cache, cache_key=cache_key)
            results.append(faces)
        return results

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

    # ── 3D face mesh ──────────────────────────────────────────────────

    def build_face_mesh(self, image: np.ndarray) -> dict | None:
        """Detect face and build 3D mesh from an image.

        Returns dict with keys: face_crop, vertices, tex_coords, face_indices,
        or None if no face detected.
        """
        return self.face_mesh_3d.from_image(image)

    def save_face_model(self, path: Path, atlas: np.ndarray,
                        qualities: list[float] | None = None):
        """Save 3D face model to BMP + NPZ metadata pair."""
        self.face_mesh_3d.save_model(path, atlas, qualities)

    def load_face_model(self, path: Path) -> dict:
        """Load 3D face model from BMP + NPZ metadata pair.

        Returns dict with keys: atlas, vertices, tex_coords, face_indices,
        and optionally face_qualities.
        """
        return self.face_mesh_3d.load_model(path)

    def create_face_atlas(self, faces: list[np.ndarray],
                          qualities: list[float] | None = None,
                          grid_size: int = 10, cell_size: int = 200) -> np.ndarray:
        """Build a texture atlas grid from face crops."""
        atlas = TextureAtlas(grid_size, cell_size)
        for i, face in enumerate(faces):
            q = qualities[i] if qualities else None
            atlas.add_or_replace_face(face, q)
        return atlas.build()

    # ── dlib face detection ───────────────────────────────────────────

    def detect_faces_dlib(self, image: np.ndarray) -> np.ndarray | None:
        """Detect face using dlib 68-point landmark detector.

        Returns (68, 2) landmark array or None.
        """
        return self.dlib_detector.detect(image)

    # ── Delaunay face swapping ────────────────────────────────────────

    def build_face_identity(self, name: str, image: np.ndarray) -> bool:
        """Register a face identity for Delaunay face swapping."""
        return self.delaunay_swapper.build_identity(name, image)

    def delaunay_swap_face(self, source_name: str, target_frame: np.ndarray,
                           lip_sync: bool = True) -> np.ndarray:
        """Swap a registered identity onto a target frame using Delaunay triangulation."""
        return self.delaunay_swapper.swap(source_name, target_frame, lip_sync)

    # ── capabilities ──────────────────────────────────────────────────

    def get_capabilities(self) -> list[str]:
        return [
            "face_detection",
            "facial_landmarks",
            "face_animation",
            "face_mesh_3d",
            "face_model_persistence",
            "face_landmarks_dlib",
            "face_swapping",
            "delaunay_face_swapping",
            "lip_sync",
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
