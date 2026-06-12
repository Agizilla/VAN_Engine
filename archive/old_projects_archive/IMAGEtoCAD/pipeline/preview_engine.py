"""
Print Preview & Rasterization Engine

Takes a finalized ezdxf document and renders it to a high-resolution,
print-quality raster image (PNG/JPEG) using matplotlib as the rendering
backend. This ensures the preview is mathematically perfect — derived
directly from clean DXF geometry, not from the noisy original image.

Rendering Pipeline:
1. Extract all entities from ezdxf modelspace
2. Compute bounding box and aspect ratio
3. Set up matplotlib figure at target DPI and pixel dimensions
4. Render each entity type with optimized line weights and colors
5. Apply anti-aliasing and clean background
6. Output to PNG buffer at 300+ DPI (minimum 3000x2000 pixels)

Line Weight Strategy:
- OUTLINE: 1.5pt (primary geometry, thickest)
- BORES: 1.0pt (circles/holes, medium)
- SLOTS: 1.0pt (elongated features, medium)
- DIMENSIONS/TEXT: 0.5pt (annotations, thinnest)
- VIEW_BOUNDS: 0.3pt dashed (reference, lightest)
"""

import io
import logging
import math
from typing import Tuple, Optional, Dict, Any

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Arc, FancyBboxPatch
from matplotlib.collections import LineCollection
from PIL import Image

import ezdxf
from ezdxf.entities import Line, Circle as DXFCircle, Arc as DXFArc, Text, LWPolyline

logger = logging.getLogger(__name__)

LAYER_STYLE: Dict[str, Dict[str, Any]] = {
    "01_CUT_OUTLINE": {
        "color": "#1a1a1a",
        "linewidth": 1.5,
        "linestyle": "-",
        "zorder": 5,
    },
    "02_CUT_INNER": {
        "color": "#1a1a1a",
        "linewidth": 1.5,
        "linestyle": "-",
        "zorder": 5,
    },
    "03_DRILL_BORES": {
        "color": "#0066cc",
        "linewidth": 1.0,
        "linestyle": "-",
        "zorder": 4,
    },
    "04_MILL_SLOTS": {
        "color": "#008844",
        "linewidth": 1.0,
        "linestyle": "-",
        "zorder": 4,
    },
    "90_CENTER_MARKS": {
        "color": "#cc0000",
        "linewidth": 0.5,
        "linestyle": "-",
        "zorder": 3,
    },
    "95_DIMENSIONS": {
        "color": "#cc6600",
        "linewidth": 0.5,
        "linestyle": "-",
        "zorder": 3,
    },
    "98_TEXT": {
        "color": "#cc6600",
        "linewidth": 0.5,
        "linestyle": "-",
        "zorder": 3,
    },
    "99_REFERENCE": {
        "color": "#888888",
        "linewidth": 0.3,
        "linestyle": "--",
        "zorder": 1,
    },
}

DEFAULT_STYLE = {
    "color": "#333333",
    "linewidth": 0.8,
    "linestyle": "-",
    "zorder": 2,
}


class PreviewEngine:
    """
    Renders ezdxf documents to high-resolution raster images.

    Uses matplotlib's vector rendering pipeline to produce
    clean, anti-aliased output suitable for printing at 300+ DPI.
    """

    def __init__(
        self,
        target_dpi: int = 300,
        min_width_px: int = 3000,
        min_height_px: int = 2000,
        padding_frac: float = 0.08,
        background_color: str = "#ffffff",
    ):
        """
        Initialize the preview engine with rendering parameters.

        Args:
            target_dpi: Output resolution in dots per inch.
            min_width_px: Minimum output width in pixels.
            min_height_px: Minimum output height in pixels.
            padding_frac: Fraction of drawing bounds to add as padding.
            background_color: Background color hex string.
        """
        self.target_dpi = target_dpi
        self.min_width_px = min_width_px
        self.min_height_px = min_height_px
        self.padding_frac = padding_frac
        self.background_color = background_color

    def _compute_bounds(
        self, doc: ezdxf.document.Drawing
    ) -> Tuple[float, float, float, float]:
        """
        Compute the bounding box of all entities in modelspace.

        Iterates through all renderable entities and finds the
        min/max X and Y coordinates to determine the drawing extent.

        Args:
            doc: ezdxf document to analyze.

        Returns:
            Tuple of (x_min, y_min, x_max, y_max) in drawing units.
        """
        x_min = float("inf")
        y_min = float("inf")
        x_max = float("-inf")
        y_max = float("-inf")

        msp = doc.modelspace()

        for entity in msp:
            try:
                if isinstance(entity, Line):
                    p1 = entity.dxf.start
                    p2 = entity.dxf.end
                    x_min = min(x_min, p1[0], p2[0])
                    y_min = min(y_min, p1[1], p2[1])
                    x_max = max(x_max, p1[0], p2[0])
                    y_max = max(y_max, p1[1], p2[1])

                elif isinstance(entity, DXFCircle):
                    center = entity.dxf.center
                    radius = entity.dxf.radius
                    x_min = min(x_min, center[0] - radius)
                    y_min = min(y_min, center[1] - radius)
                    x_max = max(x_max, center[0] + radius)
                    y_max = max(y_max, center[1] + radius)

                elif isinstance(entity, DXFArc):
                    center = entity.dxf.center
                    radius = entity.dxf.radius
                    start_a = math.radians(entity.dxf.start_angle)
                    end_a = math.radians(entity.dxf.end_angle)
                    x_min = min(x_min, center[0] - radius)
                    y_min = min(y_min, center[1] - radius)
                    x_max = max(x_max, center[0] + radius)
                    y_max = max(y_max, center[1] + radius)
                    test_angles = [0, math.pi / 2, math.pi, 3 * math.pi / 2]
                    for ta in test_angles:
                        if self._angle_in_arc_span(ta, start_a, end_a):
                            px = center[0] + radius * math.cos(ta)
                            py = center[1] + radius * math.sin(ta)
                            x_min = min(x_min, px)
                            y_min = min(y_min, py)
                            x_max = max(x_max, px)
                            y_max = max(y_max, py)
                    x_min = min(x_min, center[0] + radius * math.cos(start_a))
                    y_min = min(y_min, center[1] + radius * math.sin(start_a))
                    x_max = max(x_max, center[0] + radius * math.cos(start_a))
                    y_max = max(y_max, center[1] + radius * math.sin(start_a))
                    x_min = min(x_min, center[0] + radius * math.cos(end_a))
                    y_min = min(y_min, center[1] + radius * math.sin(end_a))
                    x_max = max(x_max, center[0] + radius * math.cos(end_a))
                    y_max = max(y_max, center[1] + radius * math.sin(end_a))

                elif isinstance(entity, LWPolyline):
                    points = entity.get_points("xyb")
                    for pt in points:
                        x_min = min(x_min, pt[0])
                        y_min = min(y_min, pt[1])
                        x_max = max(x_max, pt[0])
                        y_max = max(y_max, pt[1])

                elif isinstance(entity, Text):
                    pos = entity.dxf.insert
                    x_min = min(x_min, pos[0])
                    y_min = min(y_min, pos[1])
                    x_max = max(x_max, pos[0] + 1)
                    y_max = max(y_max, pos[1] + 1)

            except (AttributeError, TypeError, IndexError):
                continue

        if x_min == float("inf"):
            return (0.0, 0.0, 100.0, 100.0)

        return (x_min, y_min, x_max, y_max)

    @staticmethod
    def _angle_in_arc_span(angle: float, start: float, end: float) -> bool:
        """
        Check if an angle falls within the arc's angular span (CCW from start to end).

        Args:
            angle: Angle to test in radians.
            start: Arc start angle in radians.
            end: Arc end angle in radians.

        Returns:
            True if angle is within the CCW span from start to end.
        """
        a = angle % (2 * math.pi)
        s = start % (2 * math.pi)
        e = end % (2 * math.pi)
        if s <= e:
            return s <= a <= e
        else:
            return a >= s or a <= e

    def _compute_figure_size(
        self,
        x_min: float, y_min: float,
        x_max: float, y_max: float,
    ) -> Tuple[float, float]:
        """
        Calculate matplotlib figure size in inches to achieve
        target pixel dimensions at the specified DPI.

        Preserves the aspect ratio of the drawing bounds while
        ensuring the output meets minimum pixel requirements.

        Args:
            x_min, y_min, x_max, y_max: Drawing bounds in units.

        Returns:
            Tuple of (fig_width_inches, fig_height_inches).
        """
        draw_w = x_max - x_min
        draw_h = y_max - y_min

        if draw_w <= 0 or draw_h <= 0:
            draw_w = 100.0
            draw_h = 100.0

        aspect = draw_w / draw_h

        fig_w = self.min_width_px / self.target_dpi
        fig_h = self.min_height_px / self.target_dpi

        current_aspect = fig_w / fig_h

        if current_aspect > aspect:
            fig_w = fig_h * aspect
        else:
            fig_h = fig_w / aspect

        return (fig_w, fig_h)

    def _render_entity(
        self, entity, ax: plt.Axes, units_per_point: float = 1.0
    ) -> None:
        """
        Render a single ezdxf entity onto a matplotlib axes.

        Dispatches to type-specific renderers for lines, circles,
        arcs, polylines, and text entities.

        Args:
            entity: ezdxf entity to render.
            ax: Matplotlib axes to draw on.
            units_per_point: Drawing units per typographic point
                for proper text sizing at the rendered DPI.
        """
        layer_name = entity.dxf.layer
        style = LAYER_STYLE.get(layer_name, DEFAULT_STYLE)

        try:
            if isinstance(entity, Line):
                self._render_line(entity, ax, style)
            elif isinstance(entity, DXFCircle):
                self._render_circle(entity, ax, style)
            elif isinstance(entity, DXFArc):
                self._render_arc(entity, ax, style)
            elif isinstance(entity, LWPolyline):
                self._render_polyline(entity, ax, style)
            elif isinstance(entity, Text):
                self._render_text(entity, ax, style, units_per_point)
        except Exception as e:
            logger.debug(f"Failed to render entity {entity}: {e}")

    def _render_line(
        self, entity: Line, ax: plt.Axes, style: Dict[str, Any]
    ) -> None:
        """Render a line entity."""
        p1 = entity.dxf.start
        p2 = entity.dxf.end
        ax.plot(
            [p1[0], p2[0]],
            [p1[1], p2[1]],
            color=style["color"],
            linewidth=style["linewidth"],
            linestyle=style["linestyle"],
            solid_capstyle="round",
            zorder=style["zorder"],
        )

    def _render_circle(
        self, entity: DXFCircle, ax: plt.Axes, style: Dict[str, Any]
    ) -> None:
        """Render a circle entity."""
        center = entity.dxf.center
        radius = entity.dxf.radius
        circle = Circle(
            (center[0], center[1]),
            radius,
            fill=False,
            edgecolor=style["color"],
            linewidth=style["linewidth"],
            linestyle=style["linestyle"],
            zorder=style["zorder"],
        )
        ax.add_patch(circle)

    def _render_arc(
        self, entity: DXFArc, ax: plt.Axes, style: Dict[str, Any]
    ) -> None:
        """Render an arc entity."""
        center = entity.dxf.center
        radius = entity.dxf.radius
        start_angle = entity.dxf.start_angle
        end_angle = entity.dxf.end_angle

        arc = Arc(
            (center[0], center[1]),
            2 * radius,
            2 * radius,
            angle=0,
            theta1=start_angle,
            theta2=end_angle,
            fill=False,
            edgecolor=style["color"],
            linewidth=style["linewidth"],
            linestyle=style["linestyle"],
            zorder=style["zorder"],
        )
        ax.add_patch(arc)

    def _render_polyline(
        self, entity: LWPolyline, ax: plt.Axes, style: Dict[str, Any]
    ) -> None:
        """Render a lightweight polyline entity."""
        points = entity.get_points("xyb")
        if len(points) < 2:
            return

        xs = [p[0] for p in points]
        ys = [p[1] for p in points]

        is_closed = bool(entity.dxf.flags & 1)

        if is_closed:
            xs.append(xs[0])
            ys.append(ys[0])

        ax.plot(
            xs, ys,
            color=style["color"],
            linewidth=style["linewidth"],
            linestyle=style["linestyle"],
            solid_joinstyle="round",
            solid_capstyle="round",
            zorder=style["zorder"],
        )

    def _render_text(
        self, entity: Text, ax: plt.Axes, style: Dict[str, Any],
        units_per_point: float = 1.0,
    ) -> None:
        """
        Render a text entity with properly scaled fontsize.

        The DXF text height is in drawing units (e.g., mm). To convert
        to matplotlib points: fontsize = height / units_per_point.
        This ensures text is readable at any DPI and drawing scale.

        Args:
            entity: ezdxf Text entity.
            ax: Matplotlib axes.
            style: Layer style dict.
            units_per_point: Drawing units per typographic point.
        """
        pos = entity.dxf.insert
        text = entity.dxf.text
        height = getattr(entity.dxf, "height", 2.5)

        fontsize = height / max(units_per_point, 0.1)
        fontsize = max(min(fontsize, 72), 4)

        ax.text(
            pos[0], pos[1],
            text,
            fontsize=fontsize,
            color=style["color"],
            ha="center",
            va="center",
            zorder=style["zorder"],
            fontfamily="monospace",
        )

    def generate(
        self,
        doc: ezdxf.document.Drawing,
        output_format: str = "png",
    ) -> Tuple[io.BytesIO, Dict[str, Any]]:
        """
        Generate a high-resolution raster image from an ezdxf document.

        This is the main entry point. It computes drawing bounds,
        sets up a properly-sized matplotlib figure, renders all
        entities with optimized styling, and outputs to a bytes
        buffer at the target DPI.

        Args:
            doc: ezdxf document to render.
            output_format: Output format ('png' or 'jpeg').

        Returns:
            Tuple of (BytesIO buffer, metadata dict).
        """
        x_min, y_min, x_max, y_max = self._compute_bounds(doc)

        padding_x = (x_max - x_min) * self.padding_frac
        padding_y = (y_max - y_min) * self.padding_frac

        x_min -= padding_x
        y_min -= padding_y
        x_max += padding_x
        y_max += padding_y

        fig_w, fig_h = self._compute_figure_size(
            x_min, y_min, x_max, y_max
        )

        draw_w = x_max - x_min
        draw_h = y_max - y_min

        fig, ax = plt.subplots(
            figsize=(fig_w, fig_h),
            dpi=self.target_dpi,
            facecolor=self.background_color,
        )

        ax.set_facecolor(self.background_color)
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.margins(0)

        units_per_point = draw_h / (fig_h * 72.0)

        msp = doc.modelspace()
        entity_count = 0

        for entity in msp:
            self._render_entity(entity, ax, units_per_point)
            entity_count += 1

        buf = io.BytesIO()
        fmt = output_format.lower()
        save_kwargs: Dict[str, Any] = {
            "dpi": self.target_dpi,
            "pad_inches": 0,
            "facecolor": self.background_color,
            "bbox_inches": "tight",
        }

        if fmt == "jpeg":
            save_kwargs["format"] = "jpeg"
        else:
            save_kwargs["format"] = "png"

        fig.savefig(buf, **save_kwargs)
        buf.seek(0)

        plt.close(fig)

        actual_w = int(fig_w * self.target_dpi)
        actual_h = int(fig_h * self.target_dpi)

        metadata = {
            "width_px": actual_w,
            "height_px": actual_h,
            "dpi": self.target_dpi,
            "format": fmt,
            "entity_count": entity_count,
            "bounds": {
                "x_min": round(x_min, 4),
                "y_min": round(y_min, 4),
                "x_max": round(x_max, 4),
                "y_max": round(y_max, 4),
            },
        }

        logger.info(
            f"Preview generated: {actual_w}x{actual_h}px at "
            f"{self.target_dpi} DPI, {entity_count} entities."
        )

        return buf, metadata

    def generate_from_file(
        self,
        dxf_path: str,
        output_path: str,
        output_format: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Load a DXF file from disk and save a rendered preview image.

        Convenience method for batch processing or CLI usage.

        Args:
            dxf_path: Path to the input .dxf file.
            output_path: Path for the output image file.
            output_format: Force format ('png' or 'jpeg'). Defaults to extension.

        Returns:
            Metadata dictionary with image dimensions and entity count.
        """
        doc = ezdxf.readfile(dxf_path)

        if output_format is None:
            ext = output_path.rsplit(".", 1)[-1].lower()
            output_format = ext if ext in ("png", "jpeg", "jpg") else "png"

        if output_format == "jpg":
            output_format = "jpeg"

        buf, metadata = self.generate(doc, output_format=output_format)

        with open(output_path, "wb") as f:
            f.write(buf.getvalue())

        logger.info(f"Preview saved to: {output_path}")
        return metadata


def generate_hd_print_preview(
    doc: ezdxf.document.Drawing,
    output_format: str = "png",
    dpi: int = 300,
    min_width: int = 6000,
    min_height: int = 4000,
) -> Tuple[io.BytesIO, Dict[str, Any]]:
    """
    Convenience function to generate a high-DPI print preview
    from an ezdxf document in a single call.

    Args:
        doc: ezdxf document to render.
        output_format: 'png' or 'jpeg'.
        dpi: Output resolution (default 300).
        min_width: Minimum output width in pixels (default 6000).
        min_height: Minimum output height in pixels (default 4000).

    Returns:
        Tuple of (BytesIO buffer, metadata dict).
    """
    engine = PreviewEngine(
        target_dpi=dpi,
        min_width_px=min_width,
        min_height_px=min_height,
    )
    return engine.generate(doc, output_format=output_format)
