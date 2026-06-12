import cv2
import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from sklearn.cluster import KMeans
import logging

from pipeline_types import SkinData, RGBColor

logger = logging.getLogger(__name__)


class SkinAnalyzer:
    def __init__(self, config: dict):
        self.config = config
        self.sample_regions = config.get("sample_regions", ["forehead", "cheeks"])

    def detect_skin_mask_adaptive(self, image: np.ndarray) -> np.ndarray:
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        lower_broad = np.array([0, 10, 40], dtype=np.uint8)
        upper_broad = np.array([30, 200, 255], dtype=np.uint8)
        broad_mask = cv2.inRange(hsv, lower_broad, upper_broad)

        candidate_pixels = hsv[broad_mask > 0]
        if len(candidate_pixels) < 500:
            logger.warning("Too few skin candidates for adaptive threshold, using defaults")
            lower = np.array([0, 20, 70], dtype=np.uint8)
            upper = np.array([20, 180, 255], dtype=np.uint8)
        else:
            try:
                h_mean, s_mean, v_mean = candidate_pixels.mean(axis=0)
                h_std, s_std, v_std = candidate_pixels.std(axis=0)

                h_std = float(max(h_std, 5))
                s_std = float(max(s_std, 15))
                v_std = float(max(v_std, 15))

                lower = np.array([
                    max(0, int(h_mean - 2 * h_std)),
                    max(0, int(s_mean - 1.5 * s_std)),
                    max(0, int(v_mean - 1.5 * v_std)),
                ], dtype=np.uint8)
                upper = np.array([
                    min(179, int(h_mean + 2 * h_std)),
                    min(255, int(s_mean + 1.5 * s_std)),
                    min(255, int(v_mean + 1.5 * v_std)),
                ], dtype=np.uint8)
            except Exception as e:
                logger.warning(f"Adaptive HSV computation failed ({e}), using defaults")
                lower = np.array([0, 20, 70], dtype=np.uint8)
                upper = np.array([20, 180, 255], dtype=np.uint8)

        logger.info(f"Adaptive HSV range: H[{lower[0]}-{upper[0]}] "
                     f"S[{lower[1]}-{upper[1]}] V[{lower[2]}-{upper[2]}]")

        mask = cv2.inRange(hsv, lower, upper)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        return mask

    def segment_skin_regions(self, image: np.ndarray, mask: np.ndarray) -> List[np.ndarray]:
        h, w = image.shape[:2]
        regions = []

        upper_mask = mask.copy()
        upper_mask[h*2//3:, :] = 0
        upper_pixels = image[upper_mask > 0]
        if len(upper_pixels) > 100:
            regions.append(upper_pixels)

        mid_mask = mask.copy()
        mid_mask[:h//3, :] = 0
        mid_mask[h*2//3:, :] = 0
        mid_pixels = image[mid_mask > 0]
        if len(mid_pixels) > 100:
            regions.append(mid_pixels)

        lower_mask = mask.copy()
        lower_mask[:h*2//3, :] = 0
        lower_pixels = image[lower_mask > 0]
        if len(lower_pixels) > 100:
            regions.append(lower_pixels)

        return regions

    def extract_dominant_color(self, pixels: np.ndarray, n_colors: int = 3) -> Tuple[int, int, int]:
        if len(pixels) == 0:
            return (128, 128, 128)

        pixels_float = pixels.reshape(-1, 3).astype(np.float32)

        if len(pixels_float) < n_colors:
            avg = pixels_float.mean(axis=0)
            return tuple(int(c) for c in avg)

        try:
            kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
            kmeans.fit(pixels_float)

            labels = kmeans.labels_
            unique, counts = np.unique(labels, return_counts=True)
            dominant_idx = unique[np.argmax(counts)]
            dominant_color = kmeans.cluster_centers_[dominant_idx]

            return tuple(int(c) for c in dominant_color)
        except Exception as e:
            logger.warning(f"KMeans failed ({e}), using mean color instead")
            avg = pixels_float.mean(axis=0)
            return tuple(int(c) for c in avg)

    def compute_skin_tone(self, image: np.ndarray) -> SkinData:
        logger.info("Analyzing skin tone...")

        mask = self.detect_skin_mask_adaptive(image)
        skin_pixels = image[mask > 0]

        if len(skin_pixels) < 1000:
            logger.warning("Limited skin pixels detected, using fallback values")
            return self._get_fallback_values()

        regions = self.segment_skin_regions(image, mask)

        region_colors = {}
        for i, region_pixels in enumerate(regions):
            region_name = ["upper_body", "mid_body", "lower_body"][i]
            color = self.extract_dominant_color(region_pixels)
            region_colors[region_name] = {
                "r": int(color[2]), "g": int(color[1]), "b": int(color[0])
            }

        overall_color = self.extract_dominant_color(skin_pixels)
        b, g, r = overall_color

        color_temp = "warm" if r > b else "cool" if b > r else "neutral"

        result: SkinData = {
            "rgb": {
                "r": int(r),
                "g": int(g),
                "b": int(b),
                "hex": f"#{r:02x}{g:02x}{b:02x}"
            },
            "region_colors": region_colors,
            "color_temperature": color_temp,
            "sample_count": len(skin_pixels),
            "sources": 1,
        }

        logger.info(f"Skin tone extracted: RGB({r}, {g}, {b})")
        return result

    def blend_multi_image(self, image_paths: List[Path]) -> SkinData:
        logger.info(f"Blending skin tone from {len(image_paths)} images")

        all_results = []
        for path in image_paths:
            image = cv2.imread(str(path))
            if image is None:
                logger.warning(f"Skipping unreadable image: {path}")
                continue
            result = self.compute_skin_tone(image)
            all_results.append(result)

        if not all_results:
            logger.warning("No valid images for blending, using fallback")
            return self._get_fallback_values()

        if len(all_results) == 1:
            result = all_results[0]
            result["sources"] = 1
            return result

        weights = [min(r["sample_count"], 50000) for r in all_results]
        total_weight = sum(weights)

        avg_r = int(sum(r["rgb"]["r"] * w for r, w in zip(all_results, weights)) / total_weight)
        avg_g = int(sum(r["rgb"]["g"] * w for r, w in zip(all_results, weights)) / total_weight)
        avg_b = int(sum(r["rgb"]["b"] * w for r, w in zip(all_results, weights)) / total_weight)

        ctemps = [r["color_temperature"] for r in all_results]
        if ctemps.count("warm") > len(ctemps) / 2:
            color_temp = "warm"
        elif ctemps.count("cool") > len(ctemps) / 2:
            color_temp = "cool"
        else:
            color_temp = "neutral"

        merged: SkinData = {
            "rgb": {
                "r": avg_r, "g": avg_g, "b": avg_b,
                "hex": f"#{avg_r:02x}{avg_g:02x}{avg_b:02x}"
            },
            "region_colors": all_results[0].get("region_colors", {}),
            "color_temperature": color_temp,
            "sample_count": sum(r["sample_count"] for r in all_results),
            "sources": len(all_results),
        }

        logger.info(f"Blended skin tone: RGB({avg_r}, {avg_g}, {avg_b}) from {len(all_results)} sources")
        return merged

    def process(self, image_path: Path, output_path: Path) -> bool:
        logger.info(f"Analyzing skin from: {image_path}")

        image = cv2.imread(str(image_path))
        if image is None:
            logger.error(f"Cannot load image: {image_path}")
            return False

        skin_data = self.compute_skin_tone(image)

        with open(output_path, 'w') as f:
            json.dump(skin_data, f, indent=2)

        logger.info(f"Skin data saved to: {output_path}")
        return True

    def process_multi(self, image_paths: List[Path], output_path: Path) -> bool:
        logger.info(f"Multi-image skin analysis from {len(image_paths)} images")

        valid = [p for p in image_paths if p.exists()]
        if not valid:
            logger.error("No valid image paths provided")
            return False

        skin_data = self.blend_multi_image(valid)

        with open(output_path, 'w') as f:
            json.dump(skin_data, f, indent=2)

        logger.info(f"Blended skin data saved to: {output_path}")
        return True

    def _get_fallback_values(self) -> SkinData:
        return {
            "rgb": {"r": 200, "g": 160, "b": 120, "hex": "#c8a078"},
            "region_colors": {},
            "color_temperature": "neutral",
            "sample_count": 0,
            "sources": 0,
        }

    def get_skin_mask_preview(self, image: np.ndarray) -> np.ndarray:
        mask = self.detect_skin_mask_adaptive(image)
        overlay = image.copy()
        overlay[mask > 0] = (0, 255, 0)
        blended = cv2.addWeighted(image, 0.6, overlay, 0.4, 0)
        return blended
