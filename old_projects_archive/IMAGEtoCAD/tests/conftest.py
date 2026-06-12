"""
Pytest fixtures for IMAGEtoCAD pipeline testing.

Provides synthetic point clouds, known-geometry fixtures,
and optimizer instances for reproducible test cases.
"""

import pytest
import numpy as np
import math
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pipeline.geometry_optimizer import GeometryOptimizer


@pytest.fixture
def optimizer_default():
    """GeometryOptimizer with default tolerances."""
    return GeometryOptimizer()


@pytest.fixture
def optimizer_strict():
    """GeometryOptimizer with tight tolerances for precision tests."""
    return GeometryOptimizer(
        line_angle_tolerance_deg=2.0,
        line_distance_tolerance=2.0,
        arc_max_residual=0.5,
        arc_min_points=8,
    )


@pytest.fixture
def optimizer_lenient():
    """GeometryOptimizer with loose tolerances for noisy data tests."""
    return GeometryOptimizer(
        line_angle_tolerance_deg=15.0,
        line_distance_tolerance=10.0,
        arc_max_residual=3.0,
        arc_min_points=4,
    )


def _circle_points(cx, cy, radius, n_points, noise_std=0.0):
    """Generate points on a circle with optional Gaussian noise."""
    angles = np.linspace(0, 2 * np.pi, n_points, endpoint=False)
    x = cx + radius * np.cos(angles) + np.random.normal(0, noise_std, n_points)
    y = cy + radius * np.sin(angles) + np.random.normal(0, noise_std, n_points)
    return np.column_stack([x, y])


def _arc_points(cx, cy, radius, start_angle, end_angle, n_points, noise_std=0.0):
    """Generate points on an arc with optional Gaussian noise."""
    angles = np.linspace(start_angle, end_angle, n_points)
    x = cx + radius * np.cos(angles) + np.random.normal(0, noise_std, n_points)
    y = cy + radius * np.sin(angles) + np.random.normal(0, noise_std, n_points)
    return np.column_stack([x, y])


def _line_points(x1, y1, x2, y2, n_points, noise_std=0.0):
    """Generate points along a line segment with optional Gaussian noise."""
    t = np.linspace(0, 1, n_points)
    x = x1 + t * (x2 - x1) + np.random.normal(0, noise_std, n_points)
    y = y1 + t * (y2 - y1) + np.random.normal(0, noise_std, n_points)
    return np.column_stack([x, y])


@pytest.fixture
def perfect_circle_50():
    """50 points on a perfect circle centered at (100, 100) with radius 50."""
    np.random.seed(42)
    return _circle_points(100, 100, 50, 50)


@pytest.fixture
def noisy_circle_50():
    """50 points on a circle at (100, 100) radius 50 with noise=0.5px."""
    np.random.seed(42)
    return _circle_points(100, 100, 50, 50, noise_std=0.5)


@pytest.fixture
def perfect_arc_90deg():
    """30 points on a 90-degree arc at (200, 200) radius 30, 0 to pi/2."""
    np.random.seed(42)
    return _arc_points(200, 200, 30, 0, math.pi / 2, 30)


@pytest.fixture
def noisy_arc_180deg():
    """40 points on a 180-degree arc at (150, 150) radius 40 with noise=0.3px."""
    np.random.seed(42)
    return _arc_points(150, 150, 40, 0, math.pi, 40, noise_std=0.3)


@pytest.fixture
def collinear_lines():
    """Two collinear line segments with a small gap."""
    return [
        (0.0, 0.0, 10.0, 0.0),
        (12.0, 0.0, 25.0, 0.0),
    ]


@pytest.fixture
def overlapping_lines():
    """Two overlapping line segments on the same line."""
    return [
        (0.0, 0.0, 20.0, 0.0),
        (10.0, 0.0, 30.0, 0.0),
    ]


@pytest.fixture
def perpendicular_lines():
    """Two perpendicular line segments that should NOT merge."""
    return [
        (0.0, 0.0, 20.0, 0.0),
        (10.0, -10.0, 10.0, 10.0),
    ]


@pytest.fixture
def fragmented_square():
    """Four sides of a square as fragmented line segments."""
    return [
        (0.0, 0.0, 10.0, 0.0),
        (12.0, 0.0, 20.0, 0.0),
        (20.0, 0.0, 20.0, 10.0),
        (20.0, 12.0, 20.0, 20.0),
        (20.0, 20.0, 10.0, 20.0),
        (8.0, 20.0, 0.0, 20.0),
        (0.0, 20.0, 0.0, 10.0),
        (0.0, 8.0, 0.0, 0.0),
    ]


@pytest.fixture
def parallel_close_lines():
    """Two parallel lines close together that should NOT merge."""
    return [
        (0.0, 0.0, 20.0, 0.0),
        (0.0, 3.0, 20.0, 3.0),
    ]


@pytest.fixture
def tiny_contour():
    """A contour with too few points for arc fitting."""
    np.random.seed(42)
    return _circle_points(50, 50, 10, 3)


@pytest.fixture
def large_circle_200():
    """200 points on a large circle at (500, 500) radius 200."""
    np.random.seed(42)
    return _circle_points(500, 500, 200, 200)


@pytest.fixture
def noisy_line_segment():
    """50 points along a line from (0,0) to (100,50) with noise=0.3px."""
    np.random.seed(42)
    return _line_points(0, 0, 100, 50, 50, noise_std=0.3)
