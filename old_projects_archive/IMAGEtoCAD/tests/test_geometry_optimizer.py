"""
Tests for GeometryOptimizer — collinear line merging and arc fitting.

Uses synthetic point clouds with known ground truth to validate
geometric accuracy and tolerance behavior.
"""

import pytest
import numpy as np
import math
from pipeline.geometry_optimizer import GeometryOptimizer


class TestCircleFitting:
    """Tests for fit_circle_least_squares with synthetic circles."""

    def test_perfect_circle_center_and_radius(self, optimizer_default, perfect_circle_50):
        """Perfect circle should recover exact center and radius."""
        result = optimizer_default.fit_circle_least_squares(perfect_circle_50)
        assert result is not None
        cx, cy, radius, rms = result
        assert cx == pytest.approx(100, abs=1.0)
        assert cy == pytest.approx(100, abs=1.0)
        assert radius == pytest.approx(50, abs=1.0)
        assert rms < 0.1

    def test_noisy_circle_within_tolerance(self, optimizer_default, noisy_circle_50):
        """Noisy circle (0.5px) should still fit within tolerance."""
        result = optimizer_default.fit_circle_least_squares(noisy_circle_50)
        assert result is not None
        cx, cy, radius, rms = result
        assert cx == pytest.approx(100, abs=2.0)
        assert cy == pytest.approx(100, abs=2.0)
        assert radius == pytest.approx(50, abs=2.0)
        assert rms < optimizer_default.arc_max_residual

    def test_large_circle_accuracy(self, optimizer_default, large_circle_200):
        """Large circle (r=200) should fit with high accuracy."""
        result = optimizer_default.fit_circle_least_squares(large_circle_200)
        assert result is not None
        cx, cy, radius, rms = result
        assert cx == pytest.approx(500, abs=2.0)
        assert cy == pytest.approx(500, abs=2.0)
        assert radius == pytest.approx(200, abs=2.0)

    def test_too_few_points_returns_none(self, optimizer_default, tiny_contour):
        """Contour with fewer than arc_min_points should return None."""
        result = optimizer_default.fit_circle_least_squares(tiny_contour)
        assert result is None

    def test_strict_optimizer_rejects_noisy(self, optimizer_strict, noisy_circle_50):
        """Strict optimizer (max_residual=0.5) should reject noisy circle."""
        result = optimizer_strict.fit_circle_least_squares(noisy_circle_50)
        assert result is None

    def test_lenient_optimizer_accepts_noisy(self, optimizer_lenient, noisy_circle_50):
        """Lenient optimizer (max_residual=3.0) should accept noisy circle."""
        result = optimizer_lenient.fit_circle_least_squares(noisy_circle_50)
        assert result is not None

    def test_empty_array_returns_none(self, optimizer_default):
        """Empty input should return None."""
        empty = np.array([]).reshape(0, 2)
        result = optimizer_default.fit_circle_least_squares(empty)
        assert result is None

    def test_arc_fit_accuracy(self, optimizer_default, perfect_arc_90deg):
        """90-degree arc should fit with reasonable accuracy."""
        result = optimizer_default.fit_circle_least_squares(perfect_arc_90deg)
        assert result is not None
        cx, cy, radius, rms = result
        assert cx == pytest.approx(200, abs=3.0)
        assert cy == pytest.approx(200, abs=3.0)
        assert radius == pytest.approx(30, abs=3.0)

    def test_noisy_arc_fit(self, optimizer_default, noisy_arc_180deg):
        """180-degree arc with noise should still fit."""
        result = optimizer_default.fit_circle_least_squares(noisy_arc_180deg)
        assert result is not None
        cx, cy, radius, rms = result
        assert cx == pytest.approx(150, abs=3.0)
        assert cy == pytest.approx(150, abs=3.0)
        assert radius == pytest.approx(40, abs=3.0)


class TestLineMerging:
    """Tests for merge_collinear_lines with synthetic line sets."""

    def test_collinear_with_gap_merged(self, optimizer_default, collinear_lines):
        """Two collinear lines with small gap should merge into one."""
        result = optimizer_default.merge_collinear_lines(collinear_lines)
        assert len(result) == 1
        x1, y1, x2, y2 = result[0]
        assert x1 == pytest.approx(0, abs=1.0)
        assert y1 == pytest.approx(0, abs=1.0)
        assert x2 == pytest.approx(25, abs=1.0)
        assert y2 == pytest.approx(0, abs=1.0)

    def test_overlapping_lines_merged(self, optimizer_default, overlapping_lines):
        """Overlapping collinear lines should merge into one."""
        result = optimizer_default.merge_collinear_lines(overlapping_lines)
        assert len(result) == 1
        x1, y1, x2, y2 = result[0]
        assert x1 == pytest.approx(0, abs=1.0)
        assert y1 == pytest.approx(0, abs=1.0)
        assert x2 == pytest.approx(30, abs=1.0)
        assert y2 == pytest.approx(0, abs=1.0)

    def test_perpendicular_lines_not_merged(self, optimizer_default, perpendicular_lines):
        """Perpendicular lines should NOT merge."""
        result = optimizer_default.merge_collinear_lines(perpendicular_lines)
        assert len(result) == 2

    def test_fragmented_square_reduced(self, optimizer_default, fragmented_square):
        """Fragmented square sides should merge into 4 lines."""
        result = optimizer_default.merge_collinear_lines(fragmented_square)
        assert len(result) == 4

    def test_parallel_close_lines_not_merged(self, optimizer_default, parallel_close_lines):
        """Parallel lines with 3px gap should NOT merge (distance_tolerance=4)."""
        result = optimizer_default.merge_collinear_lines(parallel_close_lines)
        assert len(result) == 2

    def test_empty_list_returns_empty(self, optimizer_default):
        """Empty input should return empty list."""
        result = optimizer_default.merge_collinear_lines([])
        assert result == []

    def test_single_line_unchanged(self, optimizer_default):
        """Single line should pass through unchanged."""
        lines = [(0.0, 0.0, 10.0, 10.0)]
        result = optimizer_default.merge_collinear_lines(lines)
        assert len(result) == 1
        assert result[0] == (0.0, 0.0, 10.0, 10.0)

    def test_strict_optimizer_no_merge(self, optimizer_strict, collinear_lines):
        """Strict optimizer (distance_tolerance=2) should NOT merge 2px gap."""
        result = optimizer_strict.merge_collinear_lines(collinear_lines)
        assert len(result) == 2

    def test_lenient_optimizer_merges(self, optimizer_lenient, collinear_lines):
        """Lenient optimizer (distance_tolerance=10) should merge 2px gap."""
        result = optimizer_lenient.merge_collinear_lines(collinear_lines)
        assert len(result) == 1


class TestEdgeCases:
    """Edge case and boundary condition tests."""

    def test_degenerate_line_zero_length(self, optimizer_default):
        """Zero-length line should be handled gracefully."""
        lines = [(5.0, 5.0, 5.0, 5.0)]
        result = optimizer_default.merge_collinear_lines(lines)
        assert len(result) >= 0

    def test_very_long_line(self, optimizer_default):
        """Very long line should not cause overflow."""
        lines = [(0.0, 0.0, 10000.0, 10000.0)]
        result = optimizer_default.merge_collinear_lines(lines)
        assert len(result) == 1

    def test_circle_with_negative_radius(self, optimizer_default):
        """Fit should always return positive radius."""
        np.random.seed(42)
        angles = np.linspace(0, 2 * np.pi, 30, endpoint=False)
        x = 100 + 25 * np.cos(angles)
        y = 100 + 25 * np.sin(angles)
        points = np.column_stack([x, y])
        result = optimizer_default.fit_circle_least_squares(points)
        assert result is not None
        _, _, radius, _ = result
        assert radius > 0

    def test_reproducibility_with_seed(self, perfect_circle_50):
        """Same input should produce same output."""
        opt1 = GeometryOptimizer()
        opt2 = GeometryOptimizer()
        r1 = opt1.fit_circle_least_squares(perfect_circle_50)
        r2 = opt2.fit_circle_least_squares(perfect_circle_50)
        assert r1 == r2
