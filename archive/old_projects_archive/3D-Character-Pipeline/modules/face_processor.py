import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, List
import logging

logger = logging.getLogger(__name__)

try:
    import mediapipe as mp
    mp_face_detection = mp.solutions.face_detection
    mp_face_mesh = mp.solutions.face_mesh
    _HAS_MP = True
except ImportError:
    _HAS_MP = False

try:
    import skimage
    _HAS_SKIMAGE = True
except ImportError:
    _HAS_SKIMAGE = False

HAAR_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"


class FaceProcessor:
    def __init__(self, config: dict):
        self.config = config
        self.target_size = config.get("target_size", 512)
        self.margin_ratio = config.get("margin_ratio", 0.2)
        self.min_confidence = config.get("min_detection_confidence", 0.5)
        self._init_detectors()

    def _init_detectors(self):
        self._mp_detection = None
        self._mp_mesh = None
        self._haar = None
        self._init_errors = []

        if _HAS_MP:
            try:
                self._mp_detection = mp_face_detection.FaceDetection(
                    model_selection=1, min_detection_confidence=self.min_confidence
                )
                self._mp_mesh = mp_face_mesh.FaceMesh(
                    static_image_mode=True, max_num_faces=1,
                    min_detection_confidence=self.min_confidence
                )
            except Exception as e:
                msg = f"MediaPipe init failed: {e}"
                logger.warning(msg)
                self._init_errors.append(msg)

        try:
            self._haar = cv2.CascadeClassifier(HAAR_PATH)
            if self._haar.empty():
                raise RuntimeError("Haar cascade XML not found or corrupt")
        except Exception as e:
            msg = f"Haar cascade init failed: {e}"
            logger.warning(msg)
            self._init_errors.append(msg)

    def detect_face(self, image: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        bbox = self._detect_mediapipe(image)
        if bbox is not None:
            return bbox

        logger.warning("MediaPipe detection failed, falling back to Haar cascade")
        bbox = self._detect_haar(image)
        if bbox is not None:
            return bbox

        logger.error("All face detectors failed")
        return None

    def _detect_mediapipe(self, image: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        if self._mp_detection is None:
            return None

        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self._mp_detection.process(rgb_image)

        if not results or not results.detections:
            return None

        detection = results.detections[0]
        bbox = detection.location_data.relative_bounding_box
        h, w = image.shape[:2]

        x = int(bbox.xmin * w)
        y = int(bbox.ymin * h)
        width = int(bbox.width * w)
        height = int(bbox.height * h)

        margin_x = int(width * self.margin_ratio)
        margin_y = int(height * self.margin_ratio)

        x = max(0, x - margin_x)
        y = max(0, y - margin_y)
        width = min(w - x, width + 2 * margin_x)
        height = min(h - y, height + 2 * margin_y)

        size = max(width, height)
        x = max(0, min(x, w - size))
        y = max(0, min(y, h - size))

        return (x, y, size, size)

    def _detect_haar(self, image: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self._haar.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100)
        )
        if len(faces) == 0:
            return None

        x, y, w, h = faces[0]
        margin_x = int(w * self.margin_ratio)
        margin_y = int(h * self.margin_ratio)

        img_h, img_w = image.shape[:2]
        x = max(0, x - margin_x)
        y = max(0, y - margin_y)
        w = min(img_w - x, w + 2 * margin_x)
        h = min(img_h - y, h + 2 * margin_y)

        size = max(w, h)
        x = max(0, min(x, img_w - size))
        y = max(0, min(y, img_h - size))

        return (x, y, size, size)

    def estimate_pose(self, image: np.ndarray) -> str:
        if self._mp_mesh is None:
            return "unknown"

        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self._mp_mesh.process(rgb)
        if not results or not results.multi_face_landmarks:
            return "unknown"

        lm = results.multi_face_landmarks[0].landmark
        left_eye = np.array([lm[33].x, lm[33].y, lm[33].z])
        right_eye = np.array([lm[263].x, lm[263].y, lm[263].z])
        nose_tip = np.array([lm[1].x, lm[1].y, lm[1].z])
        left_ear = np.array([lm[234].x, lm[234].y, lm[234].z])
        right_ear = np.array([lm[454].x, lm[454].y, lm[454].z])

        eye_center = (left_eye + right_eye) / 2
        nose_offset = nose_tip[0] - eye_center[0]
        ear_width = abs(left_ear[0] - right_ear[0])

        if ear_width < 0.15:
            return "side"
        elif abs(nose_offset) < 0.02:
            return "front"
        else:
            return "three_quarter"

    def align_face(self, image: np.ndarray, bbox: Tuple[int, int, int, int]) -> np.ndarray:
        x, y, w, h = bbox
        face_roi = image[y:y+h, x:x+w]

        if self._mp_mesh is None:
            face_roi = cv2.resize(face_roi, (self.target_size, self.target_size))
            return face_roi

        rgb_roi = cv2.cvtColor(face_roi, cv2.COLOR_BGR2RGB)
        mesh_results = self._mp_mesh.process(rgb_roi)

        if mesh_results and mesh_results.multi_face_landmarks:
            landmarks = mesh_results.multi_face_landmarks[0]
            h_roi, w_roi = face_roi.shape[:2]

            left_eye = landmarks.landmark[33]
            right_eye = landmarks.landmark[263]

            left_x, left_y = int(left_eye.x * w_roi), int(left_eye.y * h_roi)
            right_x, right_y = int(right_eye.x * w_roi), int(right_eye.y * h_roi)

            delta_y = right_y - left_y
            delta_x = right_x - left_x
            angle = np.degrees(np.arctan2(delta_y, delta_x))

            if abs(angle) > 1.0:
                center = (w_roi // 2, h_roi // 2)
                rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
                face_roi = cv2.warpAffine(face_roi, rotation_matrix, (w_roi, h_roi))

        face_roi = cv2.resize(face_roi, (self.target_size, self.target_size))
        return face_roi

    def generate_uv_map(self, face: np.ndarray) -> np.ndarray:
        h, w = face.shape[:2]
        uv_map = np.zeros((h, w * 2, 3), dtype=np.uint8)

        uv_map[:, :w] = face

        flipped = cv2.flip(face, 1)
        uv_map[:, w:] = flipped

        seam = np.ones((h, 4, 3), dtype=np.uint8) * 128
        uv_map = np.hstack([face, seam, flipped])

        uv_map = cv2.resize(uv_map, (1024, 512), interpolation=cv2.INTER_LANCZOS4)
        return uv_map

    def draw_preview(self, image: np.ndarray) -> np.ndarray:
        preview = image.copy()
        bbox = self.detect_face(image)
        if bbox:
            x, y, w, h = bbox
            cv2.rectangle(preview, (x, y), (x + w, y + h), (0, 255, 0), 3)
            cv2.putText(preview, "FACE", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        if self._mp_mesh:
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = self._mp_mesh.process(rgb)
            if results and results.multi_face_landmarks:
                h, w = image.shape[:2]
                for lm in results.multi_face_landmarks[0].landmark:
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    cv2.circle(preview, (cx, cy), 1, (0, 255, 255), -1)

        return preview

    def process(self, image_path: Path, output_path: Path) -> bool:
        logger.info(f"Processing face from: {image_path}")

        image = cv2.imread(str(image_path))
        if image is None:
            logger.error(f"Cannot load image: {image_path}")
            return False

        bbox = self.detect_face(image)
        if bbox is None:
            logger.error("Face detection failed")
            return False

        logger.info(f"Face detected at: {bbox}")

        face = self.align_face(image, bbox)
        face = self.enhance_illumination(face)

        cv2.imwrite(str(output_path), face)
        logger.info(f"Face saved to: {output_path}")
        return True

    def process_with_pose(self, image_path: Path, output_path: Path, uv_path: Optional[Path] = None) -> dict:
        logger.info(f"Processing face from: {image_path}")

        image = cv2.imread(str(image_path))
        if image is None:
            return {"success": False, "error": "Cannot load image"}

        bbox = self.detect_face(image)
        if bbox is None:
            return {"success": False, "error": "Face detection failed"}

        pose = self.estimate_pose(image)

        face = self.align_face(image, bbox)
        face = self.enhance_illumination(face)

        cv2.imwrite(str(output_path), face)
        logger.info(f"Face saved to: {output_path}")

        result = {
            "success": True,
            "bbox": bbox,
            "pose": pose,
            "face_array": face,
        }

        if uv_path:
            uv_map = self.generate_uv_map(face)
            cv2.imwrite(str(uv_path), uv_map)
            logger.info(f"UV map saved to: {uv_path}")
            result["uv_path"] = str(uv_path)

        return result

    def enhance_illumination(self, face: np.ndarray) -> np.ndarray:
        lab = cv2.cvtColor(face, cv2.COLOR_BGR2LAB)
        l, a, b_ch = cv2.split(lab)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_enhanced = clahe.apply(l)

        lab_enhanced = cv2.merge([l_enhanced, a, b_ch])
        face_enhanced = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)

        b_ch, g, r = cv2.split(face_enhanced)
        avg_b, avg_g, avg_r = np.mean(b_ch), np.mean(g), np.mean(r)
        avg_gray = (avg_b + avg_g + avg_r) / 3

        eps = 1e-6
        b_ch = np.clip(b_ch * (avg_gray / max(avg_b, eps)), 0, 255).astype(np.uint8)
        g = np.clip(g * (avg_gray / max(avg_g, eps)), 0, 255).astype(np.uint8)
        r = np.clip(r * (avg_gray / max(avg_r, eps)), 0, 255).astype(np.uint8)

        return cv2.merge([b_ch, g, r])

    def __del__(self):
        if self._mp_detection:
            self._mp_detection.close()
        if self._mp_mesh:
            self._mp_mesh.close()
