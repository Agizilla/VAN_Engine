"""
Geometry Optimizer — Collinear Line Merging & Arc Fitting

Provides robust geometric post-processing for blueprint-to-CAD conversion:
1. merge_collinear_lines: Merges fragmented line segments using angle/distance
   tolerancing with iterative graph-based clustering.
2. fit_circle_least_squares: Fits circles/arc to contour point sequences
   using Taubin's algebraic method with geometric refinement.

This module is the mathematical bridge between noisy OpenCV pixel data
and clean CAD vector geometry.
"""

import cv2
import numpy as np
import math
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class GeometryOptimizer:
    """
    Geometric post-processor for CAD vector cleanup.

    Handles two critical operations:
    - Collinear line merging: combines broken line fragments into
      continuous segments using angular and distance tolerancing.
    - Arc fitting: fits least-squares circles to contour point
      sequences, producing true arc geometry for CNC toolpaths.
    """

    def __init__(
        self,
        line_angle_tolerance_deg: float = 5.0,
        line_distance_tolerance: float = 4.0,
        arc_max_residual: float = 1.5,
        arc_min_points: int = 6,
    ):
        """
        Initialize optimizer with configurable tolerances.

        Args:
            line_angle_tolerance_deg: Max angle diff (degrees) to merge lines.
            line_distance_tolerance: Max endpoint gap (pixels) to merge lines.
            arc_max_residual: Max RMS residual (pixels) for a valid arc fit.
            arc_min_points: Minimum contour points required for arc fitting.
        """
        self.line_angle_tolerance_deg = line_angle_tolerance_deg
        self.line_distance_tolerance = line_distance_tolerance
        self.arc_max_residual = arc_max_residual
        self.arc_min_points = arc_min_points

    def merge_collinear_lines(
        self,
        lines: List[Tuple[float, float, float, float]],
    ) -> List[Tuple[float, float, float, float]]:
        """
        Merge collinear and nearly-touching line segments into
        continuous segments using iterative graph-based clustering.

        Algorithm:
        1. Build a connectivity graph where edges connect lines that
           are nearly collinear (angle < tolerance) and nearly touching
           (endpoint gap < distance tolerance).
        2. Find connected components in the graph.
        3. For each component, compute the principal axis via PCA.
        4. Project all endpoints onto the principal axis.
        5. The merged line spans from the min to max projected point.

        Args:
            lines: List of (x1, y1, x2, y2) tuples.

        Returns:
            List of merged (x1, y1, x2, y2) tuples.
        """
        if len(lines) < 2:
            return lines

        n = len(lines)
        parent = list(range(n))

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a: int, b: int) -> None:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb

        angle_tol = math.radians(self.line_angle_tolerance_deg)
        dist_tol = self.line_distance_tolerance

        for i in range(n):
            x1i, y1i, x2i, y2i = lines[i]
            dxi, dyi = x2i - x1i, y2i - y1i
            len_i = math.hypot(dxi, dyi)
            if len_i < 1e-6:
                continue
            angle_i = math.atan2(dyi, dxi)

            for j in range(i + 1, n):
                x1j, y1j, x2j, y2j = lines[j]
                dxj, dyj = x2j - x1j, y2j - y1j
                len_j = math.hypot(dxj, dyj)
                if len_j < 1e-6:
                    continue
                angle_j = math.atan2(dyj, dxj)

                angle_diff = abs(angle_i - angle_j)
                if angle_diff > math.pi:
                    angle_diff = 2 * math.pi - angle_diff
                angle_diff = min(angle_diff, math.pi - angle_diff)

                if angle_diff > angle_tol:
                    continue

                gaps = [
                    math.hypot(x1i - x1j, y1i - y1j),
                    math.hypot(x1i - x2j, y1i - y2j),
                    math.hypot(x2i - x1j, y2i - y1j),
                    math.hypot(x2i - x2j, y2i - y2j),
                ]

                if min(gaps) <= dist_tol:
                    union(i, j)

        components: dict = {}
        for i in range(n):
            root = find(i)
            components.setdefault(root, []).append(i)

        merged = []
        for indices in components.values():
            if len(indices) == 1:
                merged.append(lines[indices[0]])
                continue

            all_points = []
            for idx in indices:
                x1, y1, x2, y2 = lines[idx]
                all_points.append([x1, y1])
                all_points.append([x2, y2])

            pts = np.array(all_points)
            centroid = pts.mean(axis=0)
            centered = pts - centroid
            cov = centered.T @ centered / len(centered)

            try:
                eigvals, eigvecs = np.linalg.eigh(cov)
                principal_axis = eigvecs[:, 1]
            except np.linalg.LinAlgError:
                merged.append(lines[indices[0]])
                continue

            projections = centered @ principal_axis
            min_proj = projections.min()
            max_proj = projections.max()

            p_min = centroid + min_proj * principal_axis
            p_max = centroid + max_proj * principal_axis

            merged.append((
                float(p_min[0]), float(p_min[1]),
                float(p_max[0]), float(p_max[1]),
            ))

        reduction = len(lines) - len(merged)
        if reduction > 0:
            logger.info(
                f"Line merging: {len(lines)} -> {len(merged)} "
                f"({reduction} segments merged)."
            )

        return merged

    def fit_circle_least_squares(
        self, points: np.ndarray
    ) -> Optional[Tuple[float, float, float, float]]:
        """
        Fit a circle to a set of 2D points using Taubin's algebraic
        method with geometric least-squares refinement.

        The Taubin method minimizes the algebraic distance
        sum((xi - cx)^2 + (yi - cy)^2 - r^2)^2 subject to a
        normalization constraint, providing a robust non-iterative
        initial estimate. A single Gauss-Newton step refines it
        to minimize geometric residuals.

        Args:
            points: Array of shape (N, 2) contour points.

        Returns:
            Tuple of (cx, cy, radius, rms_residual) or None if fit fails.
            rms_residual is the root-mean-square geometric error in pixels.
        """
        if points.ndim != 2 or points.shape[0] < self.arc_min_points:
            return None

        x = points[:, 0].astype(np.float64)
        y = points[:, 1].astype(np.float64)
        n = len(x)

        x_mean = np.mean(x)
        y_mean = np.mean(y)
        u = x - x_mean
        v = y - y_mean

        suu = np.sum(u ** 2)
        svv = np.sum(v ** 2)
        suv = np.sum(u * v)
        suuu = np.sum(u ** 3)
        svvv = np.sum(v ** 3)
        suuv = np.sum(u ** 2 * v)
        suvv = np.sum(u * v ** 2)

        denom = suu * svv - suv ** 2
        if abs(denom) < 1e-12:
            return None

        uc = (svv * suuu + svv * suuv - suv * suvv - suv * suuu) / (2.0 * denom)
        vc = (suu * svvv + suu * suvv - suv * suuv - suv * svvv) / (2.0 * denom)

        cx = x_mean + uc
        cy = y_mean + vc

        radius = np.sqrt(np.mean((x - cx) ** 2 + (y - cy) ** 2))

        if radius < 2.0:
            return None

        residuals = np.sqrt((x - cx) ** 2 + (y - cy) ** 2) - radius
        rms = float(np.sqrt(np.mean(residuals ** 2)))

        if rms > self.arc_max_residual:
            return None

        for _ in range(3):
            dists = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
            valid = dists > 1e-10
            if not np.any(valid):
                break
            nx = (x[valid] - cx) / dists[valid]
            ny = (y[valid] - cy) / dists[valid]
            dr = dists[valid] - radius

            j0 = nx
            j1 = ny
            j2 = np.ones_like(dr)

            J = np.column_stack([j0, j1, j2])
            try:
                delta = np.linalg.lstsq(J, dr, rcond=None)[0]
            except np.linalg.LinAlgError:
                break

            cx += delta[0]
            cy += delta[1]
            radius += delta[2]

            if np.linalg.norm(delta) < 1e-6:
                break

        radius = max(radius, 1.0)
        residuals = np.sqrt((x - cx) ** 2 + (y - cy) ** 2) - radius
        rms = float(np.sqrt(np.mean(residuals ** 2)))

        if rms > self.arc_max_residual:
            return None

        return (float(cx), float(cy), float(radius), rms)
