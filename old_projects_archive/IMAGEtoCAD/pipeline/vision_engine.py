"""
Vision Processing & Segmentation Engine

Handles image preprocessing, contour segmentation, feature clustering,
OCR extraction with spatial mapping, scale calibration, and line merging
for blueprint-to-CAD conversion.

Coordinate System:
- Input: pixel coordinates (origin top-left, y-down)
- Output: real-world units (mm or inches, origin bottom-left, y-up)
- Scale calibration maps pixels to real-world units via detected dimensions.
"""

import cv2
import html
import numpy as np
from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass, field
import logging
import re
import math
import time
from scipy.spatial import distance as spatial_distance

from pipeline.geometry_optimizer import GeometryOptimizer

logger = logging.getLogger(__name__)


@dataclass
class DetectedLine:
    """Represents a detected line segment in pixel coordinates."""
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float = 1.0
    view_label: str = ""
    merged: bool = False


@dataclass
class DetectedCircle:
    """Represents a detected circle/bore in pixel coordinates."""
    cx: float
    cy: float
    radius: float
    confidence: float = 1.0
    view_label: str = ""
    is_crosshair: bool = False


@dataclass
class DetectedArc:
    """Represents a detected arc segment in pixel coordinates."""
    cx: float
    cy: float
    radius: float
    start_angle: float
    end_angle: float
    confidence: float = 1.0
    view_label: str = ""
    rms_residual: float = 0.0


@dataclass
class OCRResult:
    """Represents an OCR-extracted text element with bounding box."""
    text: str
    bbox: Tuple[int, int, int, int]
    confidence: float
    center_x: float = 0.0
    center_y: float = 0.0

    def __post_init__(self):
        x1, y1, x2, y2 = self.bbox
        self.center_x = (x1 + x2) / 2.0
        self.center_y = (y1 + y2) / 2.0


@dataclass
class ViewSegment:
    """Represents a segmented view region with its detected features."""
    label: str
    bbox: Tuple[int, int, int, int]
    lines: List[DetectedLine] = field(default_factory=list)
    circles: List[DetectedCircle] = field(default_factory=list)
    arcs: List[DetectedArc] = field(default_factory=list)
    ocr_results: List[OCRResult] = field(default_factory=list)
    scale_factor: float = 1.0
    calibrated: bool = False


@dataclass
class ProcessingResult:
    """Complete output of the vision processing pipeline."""
    views: List[ViewSegment]
    scale_factor: float = 1.0
    scale_unit: str = "mm"
    primary_view: Optional[ViewSegment] = None
    primary_profile: List[Tuple[float, float]] = field(default_factory=list)
    primary_profile_arcs: List[Dict[str, Any]] = field(default_factory=list)
    primary_slots: List[Dict[str, Any]] = field(default_factory=list)
    view_arcs: Dict[str, List[Dict[str, float]]] = field(default_factory=dict)
    image_shape: Tuple[int, int] = (0, 0)
    preview_svg: str = ""


class VisionEngine:
    """
    Core vision processing engine for blueprint image analysis.

    Pipeline stages:
    1. Preprocess: grayscale, denoise, adaptive threshold
    2. Detect: lines, circles, contours
    3. Segment: separate views by whitespace gaps
    4. OCR: extract dimension text and map to geometry
    5. Calibrate: compute pixel-to-unit scale ratio
    6. Merge: combine broken line fragments into continuous polylines
    """

    def __init__(
        self,
        line_merge_distance: float = 8.0,
        line_merge_angle_tol: float = 10.0,
        ocr_lang: str = "en",
        use_easyocr: bool = True,
        arc_min_points: int = 6,
        arc_max_residual: float = 1.5,
    ):
        """
        Initialize the vision engine with configurable parameters.

        Args:
            line_merge_distance: Max pixel distance to merge line endpoints.
            line_merge_angle_tol: Max angle difference (degrees) to merge lines.
            ocr_lang: Language code for OCR engine.
            use_easyocr: True to use EasyOCR, False for Tesseract fallback.
            arc_min_points: Minimum contour points to attempt arc fitting.
            arc_max_residual: Max RMS residual (pixels) for a valid arc fit.
        """
        self.line_merge_distance = line_merge_distance
        self.line_merge_angle_tol = line_merge_angle_tol
        self.ocr_lang = ocr_lang
        self.use_easyocr = use_easyocr
        self.arc_min_points = arc_min_points
        self.arc_max_residual = arc_max_residual
        self._ocr_engine = None
        self.optimizer = GeometryOptimizer(
            line_angle_tolerance_deg=line_merge_angle_tol,
            line_distance_tolerance=line_merge_distance,
            arc_max_residual=arc_max_residual,
            arc_min_points=arc_min_points,
        )

    def _init_ocr(self):
        """Lazy-initialize the OCR engine."""
        if self._ocr_engine is not None:
            return
        if self.use_easyocr:
            try:
                import easyocr
                self._ocr_engine = easyocr.Reader(
                    [self.ocr_lang], gpu=False, verbose=False
                )
                logger.info("EasyOCR engine initialized.")
            except Exception as e:
                logger.warning(f"EasyOCR failed: {e}. Falling back to Tesseract.")
                self._init_tesseract()
        else:
            self._init_tesseract()

    def _init_tesseract(self):
        """Initialize Tesseract via pytesseract as fallback."""
        try:
            import pytesseract
            self._ocr_engine = "tesseract"
            logger.info("Tesseract OCR engine initialized.")
        except Exception as e:
            logger.error(f"Tesseract initialization failed: {e}")
            self._ocr_engine = None

    def preprocess_image(
        self, image: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Preprocess a blueprint image for feature detection.

        Applies grayscale conversion, Gaussian denoising, and adaptive
        thresholding to produce a clean binary image suitable for
        contour and line detection.

        Args:
            image: Input image as numpy array (BGR or grayscale).

        Returns:
            Tuple of (preprocessed binary image, denoised grayscale image).
        """
        if image is None or image.size == 0:
            raise ValueError("Input image is empty or None.")

        if len(image.shape) == 2:
            gray = image
        elif image.shape[2] == 4:
            gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
        else:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        denoised = cv2.GaussianBlur(gray, (5, 5), 0)

        binary = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            blockSize=15,
            C=8,
        )

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)

        return binary, denoised

    def detect_lines(
        self, binary: np.ndarray, min_line_length: int = 20
    ) -> List[DetectedLine]:
        """
        Detect line segments from a binary image using probabilistic Hough transform.

        Args:
            binary: Preprocessed binary image (white lines on black background).
            min_line_length: Minimum pixel length for a valid line segment.

        Returns:
            List of DetectedLine objects with pixel coordinates.
        """
        lines = cv2.HoughLinesP(
            binary,
            rho=1,
            theta=np.pi / 180,
            threshold=30,
            minLineLength=min_line_length,
            maxLineGap=10,
        )

        if lines is None:
            logger.warning("No lines detected via HoughLinesP.")
            return []

        h, w = binary.shape[:2]
        max_diag = np.sqrt(h ** 2 + w ** 2)

        detected = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            confidence = float(np.clip(length / (max_diag * 0.5), 0.1, 1.0))
            detected.append(DetectedLine(
                x1=float(x1), y1=float(y1),
                x2=float(x2), y2=float(y2),
                confidence=confidence,
            ))

        logger.info(f"Detected {len(detected)} line segments.")
        return detected

    def detect_circles(
        self,
        gray: np.ndarray,
        binary: np.ndarray,
        min_radius: int = 5,
        max_radius: int = 200,
    ) -> List[DetectedCircle]:
        """
        Detect circles using Hough Circle transform and contour-based analysis.

        Also detects crosshairs (intersecting perpendicular lines) which
        indicate bore centers.

        Args:
            gray: Denoised grayscale image.
            binary: Preprocessed binary image.
            min_radius: Minimum circle radius in pixels.
            max_radius: Maximum circle radius in pixels.

        Returns:
            List of DetectedCircle objects.
        """
        circles = []

        try:
            hough_circles = cv2.HoughCircles(
                gray,
                cv2.HOUGH_GRADIENT,
                dp=1.2,
                minDist=30,
                param1=50,
                param2=30,
                minRadius=min_radius,
                maxRadius=max_radius,
            )
            if hough_circles is not None:
                h, w = gray.shape[:2]
                max_dim = max(h, w)
                for c in hough_circles[0]:
                    cx, cy, r = c
                    ideal_ratio = 0.05
                    actual_ratio = r / max_dim
                    size_conf = 1.0 - min(abs(actual_ratio - ideal_ratio) / ideal_ratio, 1.0)
                    circles.append(DetectedCircle(
                        cx=float(cx), cy=float(cy), radius=float(r),
                        confidence=float(np.clip(size_conf, 0.3, 1.0)),
                    ))
        except Exception as e:
            logger.warning(f"HoughCircles failed: {e}")

        crosshairs = self._detect_crosshairs(binary, circles)
        circles.extend(crosshairs)

        logger.info(f"Detected {len(circles)} circles/crosshairs.")
        return circles

    def _detect_crosshairs(
        self, binary: np.ndarray, existing_circles: List[DetectedCircle]
    ) -> List[DetectedCircle]:
        """
        Detect crosshair patterns indicating bore centers.

        Looks for pairs of perpendicular line segments whose intersection
        point is not already covered by a detected circle.

        Args:
            binary: Binary image for line analysis.
            existing_circles: Already detected circles to avoid duplicates.

        Returns:
            List of DetectedCircle objects inferred from crosshairs.
        """
        contours, _ = cv2.findContours(
            binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        crosshairs = []
        for contour in contours:
            perimeter = cv2.arcLength(contour, True)
            if perimeter < 30:
                continue
            approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(approx)
                aspect = max(w, h) / max(min(w, h), 1)
                if aspect > 3.0:
                    cx = x + w / 2.0
                    cy = y + h / 2.0
                    radius = max(w, h) / 4.0
                    already_found = any(
                        spatial_distance.euclidean(
                            (c.cx, c.cy), (cx, cy)
                        ) < 10
                        for c in existing_circles
                    )
                    if not already_found:
                        crosshair_conf = float(np.clip(perimeter / 200.0, 0.4, 0.9))
                        crosshairs.append(DetectedCircle(
                            cx=cx, cy=cy, radius=radius,
                            confidence=crosshair_conf,
                            is_crosshair=True,
                        ))

        return crosshairs

    def segment_views(
        self,
        binary: np.ndarray,
        lines: List[DetectedLine],
        circles: List[DetectedCircle],
        min_view_area: int = 10000,
    ) -> List[ViewSegment]:
        """
        Segment the blueprint into separate view regions based on
        whitespace gaps and bounding contour analysis.

        Uses horizontal and vertical projection profiles to find
        whitespace separators, then groups features into view segments.

        Args:
            binary: Preprocessed binary image.
            lines: Detected line segments.
            circles: Detected circles/crosshairs.
            min_view_area: Minimum pixel area for a valid view region.

        Returns:
            List of ViewSegment objects with grouped features.
        """
        height, width = binary.shape[:2]

        view_regions = self._find_view_regions(binary, min_view_area)

        if not view_regions:
            logger.warning("No view regions found. Treating entire image as one view.")
            view_regions = [(0, 0, width, height)]

        segments = []
        view_labels = ["TOP VIEW", "FRONT VIEW", "END VIEW", "SIDE VIEW", "DETAIL VIEW"]

        for idx, (x, y, w, h) in enumerate(view_regions):
            label = view_labels[idx] if idx < len(view_labels) else f"VIEW_{idx + 1}"

            view_lines = [
                ln for ln in lines
                if self._line_in_region(ln, x, y, w, h)
            ]
            view_circles = [
                c for c in circles
                if x <= c.cx <= x + w and y <= c.cy <= y + h
            ]

            segments.append(ViewSegment(
                label=label,
                bbox=(x, y, w, h),
                lines=view_lines,
                circles=view_circles,
            ))

        logger.info(f"Segmented {len(segments)} view regions.")
        return segments

    def _find_view_regions(
        self, binary: np.ndarray, min_area: int
    ) -> List[Tuple[int, int, int, int]]:
        """
        Find view regions using contour-based bounding box analysis.

        Identifies large rectangular regions separated by whitespace
        (low-density pixel areas) that correspond to individual views.

        Args:
            binary: Binary image.
            min_area: Minimum area threshold for a valid region.

        Returns:
            List of (x, y, width, height) tuples for each view region.
        """
        height, width = binary.shape[:2]

        contours, _ = cv2.findContours(
            binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        regions = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue
            x, y, w, h = cv2.boundingRect(contour)
            aspect = max(w, h) / max(min(w, h), 1)
            if aspect < 10:
                regions.append((x, y, w, h))

        if not regions:
            regions = self._projection_split(binary, min_area)

        regions = self._merge_overlapping_regions(regions)
        return regions

    def _projection_split(
        self, binary: np.ndarray, min_area: int
    ) -> List[Tuple[int, int, int, int]]:
        """
        Fallback view segmentation using horizontal/vertical projection profiles.

        Finds whitespace gaps in the projection histogram to split
        the image into separate view regions.

        Args:
            binary: Binary image.
            min_area: Minimum area for a valid region.

        Returns:
            List of (x, y, width, height) tuples.
        """
        height, width = binary.shape[:2]
        h_proj = np.sum(binary > 0, axis=1)
        v_proj = np.sum(binary > 0, axis=0)

        h_max = np.max(h_proj) if h_proj.size > 0 else 0
        v_max = np.max(v_proj) if v_proj.size > 0 else 0

        if h_max == 0 and v_max == 0:
            return [(0, 0, width, height)]

        h_threshold = h_max * 0.1
        v_threshold = v_max * 0.1

        h_gaps = self._find_gaps(h_proj, h_threshold, min_gap=50)
        v_gaps = self._find_gaps(v_proj, v_threshold, min_gap=50)

        regions = []
        if h_gaps:
            y_starts = [0] + [g[1] for g in h_gaps]
            y_ends = [g[0] for g in h_gaps] + [height]
            for ys, ye in zip(y_starts, y_ends):
                if ye - ys > 50:
                    regions.append((0, ys, width, ye - ys))

        if not regions and v_gaps:
            x_starts = [0] + [g[1] for g in v_gaps]
            x_ends = [g[0] for g in v_gaps] + [width]
            for xs, xe in zip(x_starts, x_ends):
                if xe - xs > 50:
                    regions.append((xs, 0, xe - xs, height))

        return regions if regions else [(0, 0, width, height)]

    def _find_gaps(
        self, projection: np.ndarray, threshold: float, min_gap: int = 50
    ) -> List[Tuple[int, int]]:
        """
        Find gaps (low-density regions) in a 1D projection profile.

        Args:
            projection: 1D array of pixel counts.
            threshold: Value below which a position is considered empty.
            min_gap: Minimum gap length in pixels.

        Returns:
            List of (start, end) index tuples for each gap.
        """
        gaps = []
        in_gap = False
        gap_start = 0

        for i, val in enumerate(projection):
            if val < threshold and not in_gap:
                in_gap = True
                gap_start = i
            elif val >= threshold and in_gap:
                in_gap = False
                if i - gap_start >= min_gap:
                    gaps.append((gap_start, i))

        if in_gap and len(projection) - gap_start >= min_gap:
            gaps.append((gap_start, len(projection)))

        return gaps

    def _merge_overlapping_regions(
        self, regions: List[Tuple[int, int, int, int]]
    ) -> List[Tuple[int, int, int, int]]:
        """
        Merge overlapping or nearly-adjacent view regions.

        Args:
            regions: List of (x, y, w, h) tuples.

        Returns:
            Merged list of non-overlapping regions.
        """
        if not regions:
            return []

        regions = sorted(regions, key=lambda r: r[1])
        merged = [regions[0]]

        for current in regions[1:]:
            last = merged[-1]
            overlap_y = min(last[1] + last[3], current[1] + current[3]) - max(
                last[1], current[1]
            )
            if overlap_y > 0:
                new_y = min(last[1], current[1])
                new_h = max(last[1] + last[3], current[1] + current[3]) - new_y
                new_x = min(last[0], current[0])
                new_w = max(last[0] + last[2], current[0] + current[2]) - new_x
                merged[-1] = (new_x, new_y, new_w, new_h)
            else:
                merged.append(current)

        return merged

    def _line_in_region(
        self, line: DetectedLine, x: int, y: int, w: int, h: int
    ) -> bool:
        """Check if a line segment falls within a rectangular region."""
        cx = (line.x1 + line.x2) / 2.0
        cy = (line.y1 + line.y2) / 2.0
        return x <= cx <= x + w and y <= cy <= y + h

    def perform_ocr(
        self, image: np.ndarray, segments: List[ViewSegment]
    ) -> List[ViewSegment]:
        """
        Perform OCR on each view segment to extract dimension text.

        Maps extracted text to spatial coordinates and associates
        with the corresponding view segment.

        Args:
            image: Original input image (for OCR context).
            segments: List of view segments to process.

        Returns:
            Updated segments with OCR results attached.
        """
        self._init_ocr()

        if self._ocr_engine is None:
            logger.error("No OCR engine available. Skipping OCR.")
            return segments

        for segment in segments:
            x, y, w, h = segment.bbox
            roi, adj_x, adj_y = self._safe_roi(image, x, y, w, h)

            if roi.size == 0:
                continue

            ocr_results = self._ocr_region(roi, adj_x, adj_y)
            segment.ocr_results = ocr_results

            logger.info(
                f"OCR for {segment.label}: found {len(ocr_results)} text elements."
            )

        return segments

    def _ocr_region(
        self, roi: np.ndarray, offset_x: int, offset_y: int
    ) -> List[OCRResult]:
        """
        Run OCR on a region of interest and return text elements
        with global pixel coordinates.

        Args:
            roi: Image region to process.
            offset_x: X offset to convert local to global coordinates.
            offset_y: Y offset to convert local to global coordinates.

        Returns:
            List of OCRResult objects with text and bounding boxes.
        """
        results = []

        if isinstance(self._ocr_engine, str) and self._ocr_engine == "tesseract":
            results = self._ocr_tesseract(roi, offset_x, offset_y)
        else:
            results = self._ocr_easyocr(roi, offset_x, offset_y)

        return results

    def _ocr_easyocr(
        self, roi: np.ndarray, offset_x: int, offset_y: int
    ) -> List[OCRResult]:
        """Run EasyOCR on a region."""
        results = []
        try:
            ocr_output = self._ocr_engine.readtext(roi, detail=1)
            for bbox, text, conf in ocr_output:
                if not text.strip():
                    continue
                pts = np.array(bbox, dtype=np.float32)
                x1 = int(np.min(pts[:, 0])) + offset_x
                y1 = int(np.min(pts[:, 1])) + offset_y
                x2 = int(np.max(pts[:, 0])) + offset_x
                y2 = int(np.max(pts[:, 1])) + offset_y
                results.append(OCRResult(
                    text=text.strip(),
                    bbox=(x1, y1, x2, y2),
                    confidence=conf,
                ))
        except Exception as e:
            logger.warning(f"EasyOCR region processing failed: {e}")

        return results

    def _ocr_tesseract(
        self, roi: np.ndarray, offset_x: int, offset_y: int
    ) -> List[OCRResult]:
        """Run Tesseract OCR on a region with HOCR output for bounding boxes."""
        results = []
        try:
            import pytesseract
            if len(roi.shape) == 2:
                gray = roi
            elif roi.shape[2] == 4:
                gray = cv2.cvtColor(roi, cv2.COLOR_BGRA2GRAY)
            else:
                gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            data = pytesseract.image_to_data(
                thresh, output_type=pytesseract.Output.DICT
            )

            for i in range(len(data["text"])):
                text = data["text"][i].strip()
                conf = int(data["conf"][i])
                if text and conf > 30:
                    x = data["left"][i] + offset_x
                    y = data["top"][i] + offset_y
                    w = data["width"][i]
                    h = data["height"][i]
                    results.append(OCRResult(
                        text=text,
                        bbox=(x, y, x + w, y + h),
                        confidence=conf / 100.0,
                    ))
        except Exception as e:
            logger.warning(f"Tesseract region processing failed: {e}")

        return results

    def calibrate_scale(
        self, segments: List[ViewSegment]
    ) -> Tuple[float, str]:
        """
        Calculate the pixel-to-real-world-unit scale ratio.

        Searches OCR results for dimension values (e.g., '7.00"', '180mm')
        and computes the scale factor by comparing the pixel distance
        between associated line endpoints to the stated dimension.

        Args:
            segments: View segments with OCR results.

        Returns:
            Tuple of (scale_factor, unit_string).
            scale_factor = pixels per unit (e.g., pixels per mm).
        """
        best_scale = 1.0
        unit = "mm"

        for segment in segments:
            for ocr in segment.ocr_results:
                dimension_value, detected_unit = self._parse_dimension(ocr.text)
                if dimension_value is None:
                    continue

                unit = detected_unit

                nearest_line = self._find_nearest_line(
                    ocr, segment.lines, max_distance=80
                )
                if nearest_line is None:
                    continue

                pixel_length = np.sqrt(
                    (nearest_line.x2 - nearest_line.x1) ** 2
                    + (nearest_line.y2 - nearest_line.y1) ** 2
                )

                if pixel_length > 0:
                    scale = pixel_length / dimension_value
                    if 0.1 < scale < 1000:
                        best_scale = scale
                        logger.info(
                            f"Scale calibrated: {scale:.2f} px/{unit} "
                            f"from dimension '{ocr.text}' ({dimension_value} {unit})"
                        )
                        segment.scale_factor = scale
                        segment.calibrated = True
                        return best_scale, unit

        if best_scale == 1.0:
            logger.warning(
                "Could not calibrate scale from dimensions. "
                "Using default 1:1 pixel-to-mm ratio."
            )

        return best_scale, unit

    def _parse_dimension(self, text: str) -> Tuple[Optional[float], str]:
        """
        Parse a dimension string to extract numeric value and unit.

        Handles formats like: '7.00"', '7.00 in', '180mm', '180.0',
        '7"', '3.50'.

        Args:
            text: Raw OCR text string.

        Returns:
            Tuple of (numeric_value, unit_string) or (None, "") if invalid.
        """
        text = text.strip().replace(",", "")

        if '"' in text:
            match = re.search(r"([\d.]+)\s*\"", text)
            if match:
                try:
                    return float(match.group(1)), "in"
                except ValueError:
                    pass

        if "in" in text.lower():
            match = re.search(r"([\d.]+)\s*in", text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1)), "in"
                except ValueError:
                    pass

        if "mm" in text.lower():
            match = re.search(r"([\d.]+)\s*mm", text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1)), "mm"
                except ValueError:
                    pass

        match = re.search(r"^[\d.]+$", text)
        if match:
            try:
                value = float(match.group(0))
                if 0.01 < value < 10000:
                    digit_count = sum(1 for c in text if c.isdigit())
                    if digit_count / max(len(text), 1) >= 0.7:
                        return value, "mm"
            except ValueError:
                pass

        return None, ""

    def _find_nearest_line(
        self, ocr: OCRResult, lines: List[DetectedLine], max_distance: float = 80
    ) -> Optional[DetectedLine]:
        """
        Find the line segment best associated with an OCR text element.

        Uses a multi-factor scoring system:
        1. Perpendicular distance from text center to the line
        2. Angular alignment (dimension text is typically parallel to
           the dimensioned feature)
        3. Proximity to line endpoints (dimension text is often near
           extension line terminations)

        Args:
            ocr: OCR result with bounding box.
            lines: List of detected lines.
            max_distance: Maximum acceptable distance in pixels.

        Returns:
            Best-matching DetectedLine or None.
        """
        if not lines:
            return None

        best_line = None
        best_score = float("inf")

        tx, ty = ocr.center_x, ocr.center_y

        for line in lines:
            dx = line.x2 - line.x1
            dy = line.y2 - line.y1
            line_len = math.hypot(dx, dy)

            if line_len < 1.0:
                continue

            perp_dist = self._point_to_line_distance(tx, ty, line)

            proj_t = ((tx - line.x1) * dx + (ty - line.y1) * dy) / (line_len ** 2)
            proj_t = max(0, min(1, proj_t))
            proj_x = line.x1 + proj_t * dx
            proj_y = line.y1 + proj_t * dy
            endpoint_dist = min(
                math.hypot(tx - line.x1, ty - line.y1),
                math.hypot(tx - line.x2, ty - line.y2),
            )

            text_angle = math.degrees(math.atan2(
                ocr.bbox[3] - ocr.bbox[1],
                ocr.bbox[2] - ocr.bbox[0],
            )) if (ocr.bbox[2] - ocr.bbox[0]) > 0 else 0
            line_angle = math.degrees(math.atan2(dy, dx))
            angle_diff = abs(text_angle - line_angle)
            angle_diff = min(angle_diff, 180 - angle_diff)
            angle_score = 1.0 if angle_diff < 15 else 0.3

            score = (
                perp_dist * 1.0
                + endpoint_dist * 0.5 * angle_score
                + (0 if perp_dist < max_distance else 9999)
            )

            if score < best_score:
                best_score = score
                best_line = line

        return best_line

    @staticmethod
    def _point_to_line_distance(
        px: float, py: float, line: "DetectedLine"
    ) -> float:
        """
        Compute perpendicular distance from a point to a line segment.

        Args:
            px, py: Point coordinates.
            line: DetectedLine segment.

        Returns:
            Perpendicular distance in pixels.
        """
        dx = line.x2 - line.x1
        dy = line.y2 - line.y1
        length_sq = dx * dx + dy * dy

        if length_sq < 1e-10:
            return math.hypot(px - line.x1, py - line.y1)

        t = max(0, min(1, ((px - line.x1) * dx + (py - line.y1) * dy) / length_sq))
        proj_x = line.x1 + t * dx
        proj_y = line.y1 + t * dy

        return math.hypot(px - proj_x, py - proj_y)

    @staticmethod
    def _contour_winding_order(points: np.ndarray) -> bool:
        """
        Determine if a closed contour is clockwise (CW) or counter-clockwise (CCW).

        Uses the signed area (shoelace formula). Positive area = CCW,
        negative area = CW. OpenCV contours are typically CCW for outer
        boundaries, but this can vary based on how they were extracted.

        DXF ARC entities are always drawn CCW. If the contour is CW,
        the start/end angles must be swapped to produce the correct arc.

        Args:
            points: Array of shape (N, 2) contour vertices.

        Returns:
            True if the contour is clockwise, False if counter-clockwise.
        """
        n = len(points)
        if n < 3:
            return False

        signed_area = 0.0
        for i in range(n):
            j = (i + 1) % n
            signed_area += points[i][0] * points[j][1]
            signed_area -= points[j][0] * points[i][1]

        return signed_area < 0

    def merge_lines(
        self,
        lines: List[DetectedLine],
        distance_tol: Optional[float] = None,
        angle_tol: Optional[float] = None,
    ) -> List[DetectedLine]:
        """
        Merge collinear and nearly-touching line segments into
        continuous polylines using the GeometryOptimizer.

        Delegates to GeometryOptimizer.merge_collinear_lines which
        uses graph-based clustering with PCA principal axis projection
        for robust merging of broken line fragments.

        Args:
            lines: List of detected line segments.
            distance_tol: Max pixel distance between endpoints to merge.
            angle_tol: Max angle difference in degrees to merge.

        Returns:
            List of merged DetectedLine objects.
        """
        if not lines:
            return []

        if distance_tol is not None:
            self.optimizer.line_distance_tolerance = distance_tol
        if angle_tol is not None:
            self.optimizer.line_angle_tolerance_deg = angle_tol

        line_tuples = [
            (ln.x1, ln.y1, ln.x2, ln.y2) for ln in lines
        ]

        merged_tuples = self.optimizer.merge_collinear_lines(line_tuples)

        result = []
        for x1, y1, x2, y2 in merged_tuples:
            result.append(DetectedLine(
                x1=x1, y1=y1, x2=x2, y2=y2,
                confidence=1.0,
                view_label=lines[0].view_label if lines else "",
                merged=True,
            ))

        logger.info(
            f"Line merging: {len(lines)} -> {len(result)} segments "
            f"({len(lines) - len(result)} merged)."
        )
        return result

    def detect_arcs_from_contours(
        self,
        binary: np.ndarray,
        segment: ViewSegment,
        min_arc_length: int = 20,
        max_arc_length: int = 500,
    ) -> List[Dict[str, float]]:
        """
        Detect arc features from contours within a view segment.

        Extracts contours, filters by length, and uses the
        GeometryOptimizer's fit_circle_least_squares to fit arcs.
        This complements HoughCircles by detecting partial circles
        or arcs broken by image noise.

        Args:
            binary: Binary image.
            segment: View segment to search.
            min_arc_length: Minimum contour length for arc candidate.
            max_arc_length: Maximum contour length (avoids fitting outer profile).

        Returns:
            List of arc dicts with cx, cy, radius, start_angle, end_angle.
        """
        x, y, w, h = segment.bbox
        roi, adj_x, adj_y = self._safe_roi(binary, x, y, w, h)

        if roi.size == 0:
            return []

        contours, _ = cv2.findContours(
            roi, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE
        )

        arcs = []
        for cnt in contours:
            if len(cnt) < self.optimizer.arc_min_points:
                continue

            arc_length = cv2.arcLength(cnt, False)
            if arc_length < min_arc_length or arc_length > max_arc_length:
                continue

            pts = cnt.reshape(-1, 2).astype(np.float64)

            fit = self.optimizer.fit_circle_least_squares(pts)
            if fit is None:
                continue

            cx, cy, radius, rms = fit
            cx += adj_x
            cy += adj_y

            angles = np.arctan2(pts[:, 1] - (cy - adj_y), pts[:, 0] - (cx - adj_x))
            angles_deg = np.degrees(angles) % 360

            start_angle = float(angles_deg[0])
            end_angle = float(angles_deg[-1])

            sweep = end_angle - start_angle
            if sweep < 0:
                sweep += 360.0

            if sweep < 15.0:
                continue

            is_cw = self._contour_winding_order(pts)
            if is_cw:
                start_angle, end_angle = end_angle, start_angle
                sweep = 360.0 - sweep if sweep < 360.0 else sweep

            arcs.append({
                "cx": cx,
                "cy": cy,
                "radius": radius,
                "start_angle": start_angle,
                "end_angle": end_angle,
                "sweep": sweep,
                "rms": rms,
            })

        logger.info(
            f"Arc detection for {segment.label}: {len(arcs)} arcs found."
        )
        return arcs

    def extract_outer_profile(
        self, binary: np.ndarray, segment: ViewSegment
    ) -> List[Tuple[float, float]]:
        """
        Extract the outer profile (closed-loop boundary) from a view segment.

        Finds the largest contour within the segment's bounding box and
        returns its vertices as a list of (x, y) pixel coordinates.

        Args:
            binary: Binary image.
            segment: View segment to extract profile from.

        Returns:
            List of (x, y) tuples forming the outer profile polygon.
        """
        x, y, w, h = segment.bbox
        roi, adj_x, adj_y = self._safe_roi(binary, x, y, w, h)

        if roi.size == 0:
            return []

        contours, _ = cv2.findContours(
            roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            return []

        largest = max(contours, key=cv2.contourArea)
        perimeter = cv2.arcLength(largest, True)

        if perimeter < 50:
            return []

        approx = cv2.approxPolyDP(largest, 0.01 * perimeter, True)

        profile = []
        for point in approx:
            px = float(point[0][0]) + adj_x
            py = float(point[0][1]) + adj_y
            profile.append((px, py))

        logger.info(
            f"Extracted outer profile for {segment.label}: "
            f"{len(profile)} vertices."
        )
        return profile

    def fit_arcs_to_profile(
        self,
        contour: np.ndarray,
        offset_x: float = 0,
        offset_y: float = 0,
        angle_threshold: float = 30.0,
        min_arc_points: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Fit arcs to radiused corners in a contour using least-squares
        circle fitting. Replaces jagged approxPolyDP vertices with
        true arc entities (center, radius, start/end angles) for
        CNC-quality output.

        Algorithm:
        1. Compute turning angle at each vertex along the contour
        2. Identify corner regions where angle deviates > angle_threshold
        3. For each corner region, collect nearby contour points
        4. Fit a circle via algebraic least-squares (Taubin method)
        5. Compute arc start/end angles from the fitted circle
        6. Return mixed list of LINE and ARC segments

        Args:
            contour: OpenCV contour array of shape (N, 1, 2).
            offset_x: X offset to apply to all coordinates.
            offset_y: Y offset to apply to all coordinates.
            angle_threshold: Minimum turning angle (degrees) to fit an arc.
            min_arc_points: Minimum points in a corner region for arc fitting.

        Returns:
            List of segment dicts. Each has 'type' ('line' or 'arc')
            and type-specific parameters.
        """
        points = contour.reshape(-1, 2).astype(np.float64)
        n = len(points)
        if n < 3:
            return []

        angles = self._compute_turning_angles(points)

        segments = []
        i = 0
        while i < n:
            if abs(angles[i]) > angle_threshold:
                corner_points = self._extract_corner_region(points, i, angles, angle_threshold)

                if len(corner_points) >= min_arc_points:
                    fit = self.optimizer.fit_circle_least_squares(corner_points)
                    if fit is not None:
                        cx, cy, radius, rms = fit
                        angles_rad = np.arctan2(
                            corner_points[:, 1] - (cy - offset_y),
                            corner_points[:, 0] - (cx - offset_x),
                        )
                        start_angle = float(np.degrees(angles_rad[0]))
                        end_angle = float(np.degrees(angles_rad[-1]))
                        if end_angle < start_angle:
                            end_angle += 360.0
                        sweep = end_angle - start_angle
                        if sweep > 270:
                            start_angle, end_angle = end_angle - 360, start_angle

                        is_cw = self._contour_winding_order(corner_points)
                        if is_cw:
                            start_angle, end_angle = end_angle, start_angle

                        arc = {
                            "cx": cx + offset_x,
                            "cy": cy + offset_y,
                            "radius": radius,
                            "start_angle": start_angle,
                            "end_angle": end_angle,
                            "sweep": sweep,
                        }
                        arc["type"] = "arc"
                        segments.append(arc)
                        i += len(corner_points)
                        continue

            next_i = (i + 1) % n
            p1 = points[i]
            p2 = points[next_i]
            segments.append({
                "type": "line",
                "x1": float(p1[0]) + offset_x,
                "y1": float(p1[1]) + offset_y,
                "x2": float(p2[0]) + offset_x,
                "y2": float(p2[1]) + offset_y,
            })
            i += 1

        arc_count = sum(1 for s in segments if s["type"] == "arc")
        logger.info(f"Arc fitting: {arc_count} arcs fitted from {n} contour points.")
        return segments

    def _compute_turning_angles(self, points: np.ndarray) -> np.ndarray:
        """
        Compute the signed turning angle at each vertex of a closed contour.

        The turning angle is the angle between the incoming and outgoing
        edge vectors at each vertex. Positive = left turn, negative = right.

        Args:
            points: Array of shape (N, 2) contour vertices.

        Returns:
            Array of N turning angles in degrees.
        """
        n = len(points)
        angles = np.zeros(n)

        for i in range(n):
            prev_pt = points[(i - 1) % n]
            curr_pt = points[i]
            next_pt = points[(i + 1) % n]

            v1 = prev_pt - curr_pt
            v2 = next_pt - curr_pt

            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)

            if norm1 < 1e-6 or norm2 < 1e-6:
                angles[i] = 0.0
                continue

            cos_angle = np.clip(np.dot(v1, v2) / (norm1 * norm2), -1.0, 1.0)
            angle = np.degrees(np.arccos(cos_angle))

            cross = v1[0] * v2[1] - v1[1] * v2[0]
            if cross < 0:
                angle = -angle

            angles[i] = angle

        return angles

    def _extract_corner_region(
        self,
        points: np.ndarray,
        center_idx: int,
        angles: np.ndarray,
        angle_threshold: float,
        max_radius: int = 15,
    ) -> np.ndarray:
        """
        Extract the subset of contour points belonging to a corner region.

        Expands outward from the peak-angle vertex until the turning
        angle drops below the threshold or max_radius is reached.

        Args:
            points: Full contour point array.
            center_idx: Index of the peak turning angle vertex.
            angles: Precomputed turning angles.
            angle_threshold: Minimum angle to include in region.
            max_radius: Maximum number of points to include on each side.

        Returns:
            Array of corner region points.
        """
        n = len(points)
        left = center_idx
        right = center_idx

        for _ in range(max_radius):
            prev_left = (left - 1) % n
            if abs(angles[prev_left]) > angle_threshold * 0.5:
                left = prev_left
            else:
                break

        for _ in range(max_radius):
            next_right = (right + 1) % n
            if abs(angles[next_right]) > angle_threshold * 0.5:
                right = next_right
            else:
                break

        if left <= right:
            return points[left:right + 1].copy()
        else:
            return np.vstack([points[left:], points[:right + 1]])

    def detect_slots(
        self, binary: np.ndarray, segment: ViewSegment
    ) -> List[Dict[str, Any]]:
        """
        Detect slot features (elongated holes) within a view segment.

        Slots are identified as contours with high aspect ratios
        (length >> width) that are not part of the outer profile.

        Args:
            binary: Binary image.
            segment: View segment to search.

        Returns:
            List of slot dictionaries with center, length, width, angle.
        """
        x, y, w, h = segment.bbox
        roi, adj_x, adj_y = self._safe_roi(binary, x, y, w, h)

        if roi.size == 0:
            return []

        contours, _ = cv2.findContours(
            roi, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
        )

        slots = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 100:
                continue

            rect = cv2.minAreaRect(contour)
            (cx, cy), (width_r, height_r), angle = rect

            if min(width_r, height_r) < 3:
                continue

            aspect = max(width_r, height_r) / max(min(width_r, height_r), 1)
            if aspect > 2.5:
                slots.append({
                    "center_x": cx + adj_x,
                    "center_y": cy + adj_y,
                    "length": max(width_r, height_r),
                    "width": min(width_r, height_r),
                    "angle": angle,
                })

        logger.info(f"Detected {len(slots)} slots in {segment.label}.")
        return slots

    def process(
        self,
        image: np.ndarray,
        progress_callback=None,
    ) -> ProcessingResult:
        """
        Run the complete vision processing pipeline on an input image.

        Pipeline stages:
        1. Preprocess (threshold, denoise)
        2. Detect lines and circles
        3. Segment into views
        4. OCR extraction
        5. Scale calibration
        6. Line merging
        7. Feature extraction (profiles, bores, slots)

        Args:
            image: Input blueprint image as numpy array.
            progress_callback: Optional callable(stage: str, status: str, elapsed_ms: int).

        Returns:
            ProcessingResult with all extracted geometry and metadata.
        """
        if image is None or image.size == 0:
            raise ValueError("Input image is empty or None.")

        height, width = image.shape[:2]
        logger.info(f"Processing image: {width}x{height} pixels.")

        t0 = time.time()
        if progress_callback:
            progress_callback("preprocess", "start", 0)
        binary, gray = self.preprocess_image(image)
        if progress_callback:
            progress_callback("preprocess", "complete", int((time.time() - t0) * 1000))

        if progress_callback:
            progress_callback("detect", "start", int((time.time() - t0) * 1000))
        lines = self.detect_lines(binary)
        circles = self.detect_circles(gray, binary)
        if progress_callback:
            progress_callback("detect", "complete", int((time.time() - t0) * 1000))

        if progress_callback:
            progress_callback("segment", "start", int((time.time() - t0) * 1000))
        segments = self.segment_views(binary, lines, circles)
        if progress_callback:
            progress_callback("segment", "complete", int((time.time() - t0) * 1000))

        if progress_callback:
            progress_callback("ocr", "start", int((time.time() - t0) * 1000))
        segments = self.perform_ocr(image, segments)
        if progress_callback:
            progress_callback("ocr", "complete", int((time.time() - t0) * 1000))

        if progress_callback:
            progress_callback("calibrate", "start", int((time.time() - t0) * 1000))
        scale_factor, unit = self.calibrate_scale(segments)
        if progress_callback:
            progress_callback("calibrate", "complete", int((time.time() - t0) * 1000))

        for segment in segments:
            if not segment.calibrated:
                segment.scale_factor = scale_factor

            segment.lines = self.merge_lines(segment.lines)

        if progress_callback:
            progress_callback("merge", "start", int((time.time() - t0) * 1000))
        view_arcs: Dict[str, List[Dict[str, float]]] = {}
        for segment in segments:
            arcs = self.detect_arcs_from_contours(binary, segment)
            if arcs:
                view_arcs[segment.label] = arcs
        if progress_callback:
            progress_callback("merge", "complete", int((time.time() - t0) * 1000))

        primary_view = self._select_primary_view(segments)

        if primary_view:
            primary_profile = self.extract_outer_profile(binary, primary_view)
            primary_profile_arcs = self._extract_and_fit_arcs(binary, primary_view)
            primary_slots = self.detect_slots(binary, primary_view)
        else:
            primary_profile = []
            primary_profile_arcs = []
            primary_slots = []

        preview_svg = self._generate_preview_svg(
            segments, width, height, binary
        )

        return ProcessingResult(
            views=segments,
            scale_factor=scale_factor,
            scale_unit=unit,
            primary_view=primary_view,
            primary_profile=primary_profile,
            primary_profile_arcs=primary_profile_arcs,
            primary_slots=primary_slots,
            view_arcs=view_arcs,
            image_shape=(height, width),
            preview_svg=preview_svg,
        )

    def _select_primary_view(
        self, segments: List[ViewSegment]
    ) -> Optional[ViewSegment]:
        """
        Select the primary view for DXF generation.

        Defaults to the view labeled 'TOP VIEW'. If not found,
        selects the view with the largest bounding box area.

        Args:
            segments: List of view segments.

        Returns:
            Selected primary ViewSegment or None.
        """
        for segment in segments:
            if "TOP" in segment.label.upper():
                return segment

        if segments:
            return max(segments, key=lambda s: s.bbox[2] * s.bbox[3])

        return None

    def _extract_and_fit_arcs(
        self, binary: np.ndarray, segment: ViewSegment
    ) -> List[Dict[str, Any]]:
        """
        Extract the raw outer contour and fit arcs to radiused corners.

        This is the production-quality path for CNC output. Unlike
        extract_outer_profile which uses approxPolyDP (producing jagged
        straight-line segments), this method preserves the original
        contour and fits least-squares circles to corner regions.

        Args:
            binary: Binary image.
            segment: View segment to process.

        Returns:
            List of line/arc segment dicts from fit_arcs_to_profile.
        """
        x, y, w, h = segment.bbox
        roi, adj_x, adj_y = self._safe_roi(binary, x, y, w, h)

        if roi.size == 0:
            return []

        contours, _ = cv2.findContours(
            roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
        )

        if not contours:
            return []

        largest = max(contours, key=cv2.contourArea)
        perimeter = cv2.arcLength(largest, True)

        if perimeter < 50:
            return []

        return self.fit_arcs_to_profile(largest, adj_x, adj_y)

    def _generate_preview_svg(
        self,
        segments: List[ViewSegment],
        width: int,
        height: int,
        binary: np.ndarray,
    ) -> str:
        """
        Generate an SVG string for vector path preview in the web UI.

        Renders merged lines, circles, and outer profiles as SVG
        elements with distinct styling per feature type.

        Args:
            segments: Processed view segments.
            width: Image width in pixels.
            height: Image height in pixels.
            binary: Binary image for contour extraction.

        Returns:
            SVG string suitable for embedding in HTML.
        """
        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">'
        ]

        svg_parts.append(
            f'<rect width="{width}" height="{height}" fill="#1a1a2e"/>'
        )

        colors = {
            "lines": "#00ff88",
            "circles": "#ff6b6b",
            "arcs": "#ff9f43",
            "profiles": "#4ecdc4",
            "text": "#ffd93d",
            "view_bounds": "#ffffff40",
        }

        svg_parts.append('<g id="layer-view-bounds">')
        for segment in segments:
            x, y, w, h = segment.bbox
            svg_parts.append(
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
                f'fill="none" stroke="{colors["view_bounds"]}" '
                f'stroke-width="1" stroke-dasharray="5,5"/>'
            )
            svg_parts.append(
                f'<text x="{x + 5}" y="{y + 15}" '
                f'fill="white" font-size="12" font-family="monospace">'
                f'{segment.label}</text>'
            )
        svg_parts.append('</g>')

        svg_parts.append('<g id="layer-lines">')
        for segment in segments:
            for line in segment.lines:
                opacity = max(line.confidence, 0.2)
                stroke_width = 1.0 + line.confidence * 1.5
                svg_parts.append(
                    f'<line x1="{line.x1:.1f}" y1="{line.y1:.1f}" '
                    f'x2="{line.x2:.1f}" y2="{line.y2:.1f}" '
                    f'stroke="{colors["lines"]}" stroke-width="{stroke_width:.1f}" '
                    f'stroke-linecap="round" opacity="{opacity:.2f}"/>'
                )
                if line.confidence < 0.6:
                    mx = (line.x1 + line.x2) / 2
                    my = (line.y1 + line.y2) / 2
                    svg_parts.append(
                        f'<text x="{mx:.1f}" y="{my - 5:.1f}" '
                        f'fill="#ff6b6b" font-size="8" '
                        f'font-family="monospace" text-anchor="middle" '
                        f'opacity="0.7">{line.confidence:.2f}</text>'
                    )
        svg_parts.append('</g>')

        svg_parts.append('<g id="layer-circles">')
        for segment in segments:
            for circle in segment.circles:
                opacity = max(circle.confidence, 0.2)
                stroke_width = 1.0 + circle.confidence * 1.5
                svg_parts.append(
                    f'<circle cx="{circle.cx:.1f}" cy="{circle.cy:.1f}" '
                    f'r="{circle.radius:.1f}" fill="none" '
                    f'stroke="{colors["circles"]}" stroke-width="{stroke_width:.1f}" '
                    f'opacity="{opacity:.2f}"/>'
                )
                if circle.confidence < 0.6:
                    svg_parts.append(
                        f'<text x="{circle.cx:.1f}" y="{circle.cy - circle.radius - 5:.1f}" '
                        f'fill="#ff6b6b" font-size="8" '
                        f'font-family="monospace" text-anchor="middle" '
                        f'opacity="0.7">{circle.confidence:.2f}</text>'
                    )
        svg_parts.append('</g>')

        svg_parts.append('<g id="layer-arcs">')
        for segment in segments:
            for arc in segment.arcs:
                opacity = max(arc.confidence, 0.2)
                start_deg = math.degrees(arc.start_angle)
                end_deg = math.degrees(arc.end_angle)
                large_arc = abs(end_deg - start_deg) > 180
                sweep = end_deg > start_deg
                x1 = arc.cx + arc.radius * math.cos(arc.start_angle)
                y1 = arc.cy + arc.radius * math.sin(arc.start_angle)
                x2 = arc.cx + arc.radius * math.cos(arc.end_angle)
                y2 = arc.cy + arc.radius * math.sin(arc.end_angle)
                svg_parts.append(
                    f'<path d="M {x1:.1f} {y1:.1f} '
                    f'A {arc.radius:.1f} {arc.radius:.1f} 0 '
                    f'{1 if large_arc else 0} {1 if sweep else 0} '
                    f'{x2:.1f} {y2:.1f}" '
                    f'fill="none" stroke="{colors["arcs"]}" '
                    f'stroke-width="1.5" opacity="{opacity:.2f}"/>'
                )
        svg_parts.append('</g>')

        svg_parts.append('<g id="layer-text">')
        for segment in segments:
            for ocr in segment.ocr_results:
                safe_text = html.escape(ocr.text)
                svg_parts.append(
                    f'<text x="{ocr.center_x:.1f}" y="{ocr.center_y:.1f}" '
                    f'fill="{colors["text"]}" font-size="10" '
                    f'font-family="monospace" text-anchor="middle">'
                    f'{safe_text}</text>'
                )
        svg_parts.append('</g>')

        svg_parts.append("</svg>")
        return "\n".join(svg_parts)

    @staticmethod
    def _safe_roi(
        image: np.ndarray, x: int, y: int, w: int, h: int
    ) -> Tuple[np.ndarray, int, int]:
        """
        Extract a region of interest with bounds clamping.

        Prevents out-of-bounds slicing by clamping coordinates
        to the image dimensions.

        Args:
            image: Source image array.
            x, y: Top-left corner of region.
            w, h: Width and height of region.

        Returns:
            Tuple of (clipped_roi, adjusted_x, adjusted_y).
        """
        img_h, img_w = image.shape[:2]
        x1 = max(0, min(x, img_w - 1))
        y1 = max(0, min(y, img_h - 1))
        x2 = max(0, min(x + w, img_w))
        y2 = max(0, min(y + h, img_h))
        return image[y1:y2, x1:x2], x1, y1
