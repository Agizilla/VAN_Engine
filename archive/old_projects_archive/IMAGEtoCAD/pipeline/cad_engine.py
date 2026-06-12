"""
CAD Vector Generation Engine (ezdxf)

Takes structural primitives (points, circles, lines, polylines) extracted
from the vision pipeline and writes them to a clean 2D DXF file with
proper layering, scale calibration, and geometry cleanup.

Coordinate Transformation:
- Input: pixel coordinates (origin top-left, y-down)
- Output: real-world coordinates (origin bottom-left, y-up) in mm or inches
- Scale factor (pixels per unit) is applied to all coordinates.
- Y-axis is flipped: y_real = (image_height - y_pixel) / scale_factor

CAM Layer Convention (numeric prefix for sort order):
- 01_CUT_OUTLINE: Outer profile and primary cutting geometry
- 02_CUT_INNER: Internal cutouts and pockets
- 03_DRILL_BORES: Through holes, counterbores, and circles
- 04_MILL_SLOTS: Elongated holes and milled features
- 90_CENTER_MARKS: Crosshair center marks (non-cutting)
- 95_DIMENSIONS: Dimension text annotations (non-cutting)
- 98_TEXT: General text and notes (non-cutting)
- 99_REFERENCE: View boundaries and construction lines (non-cutting)
"""

import ezdxf
from ezdxf.enums import TextEntityAlignment
from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass
import logging
import os
import math
import re

from pipeline.vision_engine import (
    ProcessingResult, ViewSegment, DetectedLine, DetectedCircle
)

logger = logging.getLogger(__name__)


@dataclass
class CADPrimitive:
    """Represents a geometric primitive ready for DXF output."""
    kind: str
    points: List[Tuple[float, float]]
    radius: float = 0.0
    layer: str = "01_CUT_OUTLINE"
    attributes: Dict[str, Any] = None

    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}


class CADGenerator:
    """
    Generates clean 2D DXF files from processed blueprint geometry.

    The generator applies scale calibration, coordinate transformation,
    and geometry cleanup to produce production-ready vector files
    suitable for CAM toolpath generation.
    """

    def __init__(
        self,
        scale_factor: float = 1.0,
        unit: str = "mm",
        image_height: int = 0,
    ):
        """
        Initialize the CAD generator with scale and unit parameters.

        Args:
            scale_factor: Pixels per real-world unit (from vision calibration).
            unit: Real-world unit string ('mm' or 'in').
            image_height: Image height in pixels (for Y-axis flip).
        """
        self.scale_factor = max(scale_factor, 0.001)
        self.unit = unit
        self.image_height = image_height
        self._doc = None
        self._msp = None

    def pixel_to_real(
        self, px: float, py: float
    ) -> Tuple[float, float]:
        """
        Convert pixel coordinates to real-world coordinates.

        Applies scale division and Y-axis flip to transform from
        image space (top-left origin, y-down) to engineering space
        (bottom-left origin, y-up).

        Args:
            px: X coordinate in pixels.
            py: Y coordinate in pixels.

        Returns:
            Tuple of (x_real, y_real) in calibrated units.
        """
        x_real = px / self.scale_factor
        y_real = (self.image_height - py) / self.scale_factor
        return (round(x_real, 4), round(y_real, 4))

    def _create_document(self) -> None:
        """Create a new ezdxf document with standard configuration."""
        self._doc = ezdxf.new(dxfversion="R2018")
        self._msp = self._doc.modelspace()

        self._doc.header["$INSUNITS"] = 4 if self.unit == "mm" else 1

        self._setup_layers()

    def _setup_layers(self) -> None:
        """
        Create CAM-standard CAD layers with numeric prefix sort order.

        Layer naming convention:
        - 01-09: Cutting layers (CAM toolpaths)
        - 90-99: Non-cutting layers (reference, text, dimensions)
        """
        self._ensure_linetypes()

        layer_defs = [
            ("01_CUT_OUTLINE", 7, "CONTINUOUS", 35),
            ("02_CUT_INNER", 7, "CONTINUOUS", 35),
            ("03_DRILL_BORES", 4, "CONTINUOUS", 25),
            ("04_MILL_SLOTS", 3, "CONTINUOUS", 25),
            ("90_CENTER_MARKS", 1, "CONTINUOUS", 13),
            ("95_DIMENSIONS", 2, "CONTINUOUS", 18),
            ("98_TEXT", 2, "CONTINUOUS", 18),
            ("99_REFERENCE", 8, "DASHED", 13),
        ]

        for name, color, linetype, weight in layer_defs:
            if name in self._doc.layers:
                continue
            try:
                self._doc.layers.new(
                    name,
                    dxfattribs={
                        "color": color,
                        "linetype": linetype,
                        "lineweight": weight,
                    },
                )
            except Exception:
                pass

    @staticmethod
    def is_cutting_layer(layer_name: str) -> bool:
        """
        Check if a layer is a cutting layer (CAM toolpath target).

        Layers prefixed with 01-09 are cutting layers.
        Layers prefixed with 90-99 are non-cutting reference layers.

        Args:
            layer_name: DXF layer name string.

        Returns:
            True if the layer should be used for CAM toolpaths.
        """
        if not layer_name:
            return False
        prefix = layer_name[:2]
        try:
            num = int(prefix)
            return 1 <= num <= 9
        except ValueError:
            return False

    def _ensure_linetypes(self) -> None:
        """Ensure required linetypes exist in the document."""
        if "DASHED" not in self._doc.linetypes:
            try:
                lt = self._doc.linetypes.new("DASHED")
                lt.pattern = [0.5, -0.25]
                lt.description = "Dashed line __ __ __"
            except (ValueError, AttributeError):
                pass

    def add_line(
        self,
        x1: float, y1: float, x2: float, y2: float,
        layer: str = "01_CUT_OUTLINE",
    ) -> None:
        """
        Add a line segment to the DXF document.

        Converts pixel coordinates to real-world units and writes
        to the specified layer.

        Args:
            x1, y1: Start point in pixel coordinates.
            x2, y2: End point in pixel coordinates.
            layer: Target DXF layer name.
        """
        p1 = self.pixel_to_real(x1, y1)
        p2 = self.pixel_to_real(x2, y2)

        if self._points_coincide(p1, p2):
            return

        self._msp.add_line(p1, p2, dxfattribs={"layer": layer})

    def add_circle(
        self,
        cx: float, cy: float, radius: float,
        layer: str = "03_DRILL_BORES",
    ) -> None:
        """
        Add a circle to the DXF document.

        Converts center point and radius from pixel to real-world units.

        Args:
            cx, cy: Center point in pixel coordinates.
            radius: Radius in pixels.
            layer: Target DXF layer name.
        """
        center = self.pixel_to_real(cx, cy)
        real_radius = radius / self.scale_factor

        if real_radius < 0.001:
            logger.warning(f"Circle radius too small: {real_radius}. Skipping.")
            return

        self._msp.add_circle(
            center, real_radius, dxfattribs={"layer": layer}
        )

    def add_arc(
        self,
        cx: float, cy: float, radius: float,
        start_angle: float, end_angle: float,
        layer: str = "01_CUT_OUTLINE",
    ) -> None:
        """
        Add an arc entity to the DXF document.

        Used for radiused corners fitted by the vision engine's
        least-squares circle fitting algorithm. Produces true
        arc geometry (not approximated line segments) for
        CNC-quality toolpaths.

        Args:
            cx, cy: Arc center in pixel coordinates.
            radius: Arc radius in pixels.
            start_angle: Start angle in degrees (math convention).
            end_angle: End angle in degrees (math convention).
            layer: Target DXF layer name.
        """
        center = self.pixel_to_real(cx, cy)
        real_radius = radius / self.scale_factor

        if real_radius < 0.001:
            return

        self._msp.add_arc(
            center,
            real_radius,
            start_angle=start_angle,
            end_angle=end_angle,
            dxfattribs={"layer": layer},
        )

    def add_center_mark(
        self,
        cx: float, cy: float,
        size: float = 5.0,
        layer: str = "90_CENTER_MARKS",
    ) -> None:
        """
        Add a crosshair center mark to the DXF document.

        Used for bore center points detected from crosshairs
        in the blueprint. Written to a non-cutting reference layer.

        Args:
            cx, cy: Center point in pixel coordinates.
            size: Crosshair arm length in pixels.
            layer: Target DXF layer name.
        """
        center = self.pixel_to_real(cx, cy)
        real_size = size / self.scale_factor

        if real_size < 0.01:
            return

        self._msp.add_line(
            (center[0] - real_size, center[1]),
            (center[0] + real_size, center[1]),
            dxfattribs={"layer": layer},
        )
        self._msp.add_line(
            (center[0], center[1] - real_size),
            (center[0], center[1] + real_size),
            dxfattribs={"layer": layer},
        )

    def add_polyline(
        self,
        points: List[Tuple[float, float]],
        layer: str = "01_CUT_OUTLINE",
        closed: bool = True,
    ) -> None:
        """
        Add a polyline (continuous path) to the DXF document.

        Converts all vertices from pixel to real-world coordinates.
        Optionally closes the polyline to form a loop.

        Args:
            points: List of (x, y) pixel coordinates.
            layer: Target DXF layer name.
            closed: If True, closes the polyline into a loop.
        """
        if len(points) < 2:
            return

        real_points = [self.pixel_to_real(x, y) for x, y in points]

        real_points = self._deduplicate_points(real_points)

        if len(real_points) < 2:
            return

        attribs = {"layer": layer}
        if closed:
            attribs["closed"] = True

        self._msp.add_lwpolyline(real_points, dxfattribs=attribs)

    def add_text(
        self,
        text: str,
        x: float, y: float,
        height: float = 2.5,
        layer: str = "95_DIMENSIONS",
    ) -> None:
        """
        Add dimension text annotation to the DXF document.

        Args:
            text: Text string to render.
            x, y: Insertion point in pixel coordinates.
            height: Text height in real-world units.
            layer: Target DXF layer name.
        """
        pos = self.pixel_to_real(x, y)
        real_height = max(height / self.scale_factor, 0.5)

        text_entity = self._msp.add_text(
            text,
            dxfattribs={
                "layer": layer,
                "height": real_height,
            },
        )
        try:
            text_entity.set_pos(pos, align=TextEntityAlignment.MIDDLE_CENTER)
        except (AttributeError, TypeError):
            text_entity.set_pos(pos, align="MIDDLE_CENTER")

    def add_linear_dimension(
        self,
        x1: float, y1: float,
        x2: float, y2: float,
        offset: float = 5.0,
        layer: str = "95_DIMENSIONS",
        measurement: Optional[float] = None,
    ) -> None:
        """
        Add a true DXF DIMENSION entity between two points.

        Creates an associative linear dimension that CAM software
        can read for tolerance checking.

        Args:
            x1, y1: First definition point in pixel coordinates.
            x2, y2: Second definition point in pixel coordinates.
            offset: Perpendicular offset for dimension line placement.
            layer: Target DXF layer name.
            measurement: Override measurement value (in real units).
                         If None, computed from geometry.
        """
        p1 = self.pixel_to_real(x1, y1)
        p2 = self.pixel_to_real(x2, y2)

        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        length = (dx ** 2 + dy ** 2) ** 0.5

        if length < 1e-6:
            return

        nx = -dy / length
        ny = dx / length
        mid_x = (p1[0] + p2[0]) / 2
        mid_y = (p1[1] + p2[1]) / 2
        dim_line_x = mid_x + nx * offset
        dim_line_y = mid_y + ny * offset

        dim_attribs = {"layer": layer}

        try:
            self._msp.add_linear_dim(
                location=(dim_line_x, dim_line_y),
                defpoint1=p1,
                defpoint2=p2,
                angle=math.degrees(math.atan2(dy, dx)),
                dxfattribs=dim_attribs,
            )
        except (TypeError, AttributeError):
            self._msp.add_text(
                f"{measurement or length:.2f}",
                dxfattribs={
                    "layer": layer,
                    "height": max(2.5 / self.scale_factor, 0.5),
                },
            ).set_pos((mid_x, mid_y), align=TextEntityAlignment.MIDDLE_CENTER)

    def add_slot(
        self,
        cx: float, cy: float,
        length: float, width: float,
        angle: float = 0.0,
        layer: str = "04_MILL_SLOTS",
    ) -> None:
        """
        Add an elongated slot feature to the DXF document.

        A slot is constructed as two semicircles connected by
        parallel line segments, forming a stadium/obround shape.

        Args:
            cx, cy: Center point in pixel coordinates.
            length: Total slot length in pixels.
            width: Slot width in pixels.
            angle: Rotation angle in degrees.
            layer: Target DXF layer name.
        """
        center = self.pixel_to_real(cx, cy)
        real_length = length / self.scale_factor
        real_width = width / self.scale_factor

        if real_length < 0.01 or real_width < 0.01:
            return

        radius = real_width / 2.0
        straight_len = real_length - real_width

        if straight_len < 0:
            logger.warning(
                f"Slot length ({real_length:.2f}) less than width ({real_width:.2f}). "
                "Rendering as circle instead."
            )
            self._msp.add_circle(center, radius, dxfattribs={"layer": layer})
            return

        half_len = straight_len / 2.0
        cos_a = math.cos(math.radians(angle))
        sin_a = math.sin(math.radians(angle))

        def rotate_translate(dx: float, dy: float) -> Tuple[float, float]:
            rx = dx * cos_a - dy * sin_a + center[0]
            ry = dx * sin_a + dy * cos_a + center[1]
            return (rx, ry)

        p1 = rotate_translate(-half_len, radius)
        p2 = rotate_translate(half_len, radius)
        p3 = rotate_translate(half_len, -radius)
        p4 = rotate_translate(-half_len, -radius)

        slot_points = [p1, p2, p3, p4]
        self._msp.add_lwpolyline(
            slot_points,
            dxfattribs={"layer": layer, "closed": True},
        )

        self._msp.add_arc(
            rotate_translate(-half_len, 0),
            radius,
            start_angle=90 + angle,
            end_angle=270 + angle,
            dxfattribs={"layer": layer},
        )
        self._msp.add_arc(
            rotate_translate(half_len, 0),
            radius,
            start_angle=-90 + angle,
            end_angle=90 + angle,
            dxfattribs={"layer": layer},
        )

    def _points_coincide(
        self, p1: Tuple[float, float], p2: Tuple[float, float], tol: float = 0.001
    ) -> bool:
        """Check if two points are within tolerance of each other."""
        return math.hypot(p1[0] - p2[0], p1[1] - p2[1]) < tol

    def _deduplicate_points(
        self, points: List[Tuple[float, float]], tol: float = 0.001
    ) -> List[Tuple[float, float]]:
        """
        Remove consecutive duplicate points from a vertex list.

        Args:
            points: List of (x, y) coordinates.
            tol: Distance tolerance for considering points equal.

        Returns:
            Deduplicated point list.
        """
        if not points:
            return []

        result = [points[0]]
        for p in points[1:]:
            if not self._points_coincide(result[-1], p, tol):
                result.append(p)

        if len(result) > 1 and self._points_coincide(result[0], result[-1], tol):
            result = result[:-1]

        return result

    def build_from_result(self, result: ProcessingResult) -> None:
        """
        Build a complete DXF document from a ProcessingResult.

        Processes all view segments, extracting lines, circles,
        arcs, outer profiles, slots, and dimension text into the
        appropriate DXF layers.

        Args:
            result: Complete output from the vision processing pipeline.
        """
        self._create_document()
        self.image_height = result.image_shape[0]
        self.scale_factor = max(result.scale_factor, 0.001)

        for segment in result.views:
            self._process_segment(segment)

        for view_label, arcs in result.view_arcs.items():
            self._process_view_arcs(arcs)

        if result.primary_view:
            self._process_primary_view(result)

        logger.info(
            f"DXF document built: {result.scale_factor:.2f} px/{result.scale_unit}, "
            f"{len(result.views)} views, "
            f"{sum(len(a) for a in result.view_arcs.values())} arcs processed."
        )

    def _process_view_arcs(
        self, arcs: List[Dict[str, float]]
    ) -> None:
        """
        Write detected arcs from all views to the DXF document.

        Arcs are written to the cutting outline layer as true
        ARC entities (not approximated polylines).

        Args:
            arcs: List of arc dicts from detect_arcs_from_contours.
        """
        for arc in arcs:
            self.add_arc(
                cx=arc["cx"],
                cy=arc["cy"],
                radius=arc["radius"],
                start_angle=arc["start_angle"],
                end_angle=arc["end_angle"],
                layer="01_CUT_OUTLINE",
            )

    def _process_segment(self, segment: ViewSegment) -> None:
        """
        Process a single view segment into DXF entities.

        Adds lines, circles, and OCR text annotations to the
        appropriate CAM-standard layers.

        Args:
            segment: View segment with detected features.
        """
        for line in segment.lines:
            self.add_line(
                line.x1, line.y1, line.x2, line.y2,
                layer="01_CUT_OUTLINE",
            )

        for circle in segment.circles:
            if circle.is_crosshair:
                self.add_center_mark(
                    circle.cx, circle.cy,
                    size=max(circle.radius * 0.5, 5.0),
                    layer="90_CENTER_MARKS",
                )
            else:
                self.add_circle(
                    circle.cx, circle.cy, circle.radius,
                    layer="03_DRILL_BORES",
                )

        for ocr in segment.ocr_results:
            if self._is_dimension_text(ocr.text):
                self.add_text(
                    ocr.text,
                    ocr.center_x, ocr.center_y,
                    layer="95_DIMENSIONS",
                )

        x, y, w, h = segment.bbox
        bounds = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
        self.add_polyline(bounds, layer="99_REFERENCE", closed=True)

    def _process_primary_view(self, result: ProcessingResult) -> None:
        """
        Process the primary view's outer profile and slots.

        The primary view (typically Top View) provides the main
        2D profile for CAM toolpath generation. Uses arc-fitted
        segments when available for true arc geometry output.

        Args:
            result: Processing result with primary view reference.
        """
        segment = result.primary_view

        arc_segments = result.primary_profile_arcs
        if arc_segments:
            self._write_arc_fitted_profile(arc_segments)
            logger.info(
                f"Arc-fitted profile written: "
                f"{sum(1 for s in arc_segments if s['type'] == 'arc')} arcs, "
                f"{sum(1 for s in arc_segments if s['type'] == 'line')} lines."
            )
        elif result.primary_profile and len(result.primary_profile) >= 3:
            self.add_polyline(
                result.primary_profile, layer="01_CUT_OUTLINE", closed=True
            )
            logger.info(
                f"Primary profile written (polyline): "
                f"{len(result.primary_profile)} vertices."
            )

        for slot in result.primary_slots:
            self.add_slot(
                cx=slot["center_x"],
                cy=slot["center_y"],
                length=slot["length"],
                width=slot["width"],
                angle=slot.get("angle", 0.0),
                layer="04_MILL_SLOTS",
            )

    def _write_arc_fitted_profile(
        self, arc_segments: List[Dict[str, Any]]
    ) -> None:
        """
        Write arc-fitted profile segments to the DXF document.

        Takes the output of vision_engine.fit_arcs_to_profile and
        writes each segment as either a LINE or ARC entity on the
        cutting outline layer. This produces true arc geometry
        for radiused corners instead of jagged polyline approximations.

        Args:
            arc_segments: List of segment dicts from fit_arcs_to_profile.
        """
        layer = "01_CUT_OUTLINE"

        for seg in arc_segments:
            if seg["type"] == "arc":
                self.add_arc(
                    cx=seg["cx"],
                    cy=seg["cy"],
                    radius=seg["radius"],
                    start_angle=seg["start_angle"],
                    end_angle=seg["end_angle"],
                    layer=layer,
                )
            elif seg["type"] == "line":
                self.add_line(
                    seg["x1"], seg["y1"],
                    seg["x2"], seg["y2"],
                    layer=layer,
                )

    def _is_dimension_text(self, text: str) -> bool:
        """
        Check if a text string appears to be a dimension value.

        Matches patterns like '7.00"', '180mm', '3.50', etc.

        Args:
            text: Text string to evaluate.

        Returns:
            True if the text looks like a dimension annotation.
        """
        patterns = [
            r'^[\d.]+\s*["\']$',
            r'^[\d.]+\s*(mm|in|cm)$',
            r'^[\d.]+$',
            r'^[\d.]+\s*x\s*[\d.]+',
        ]
        cleaned = text.strip().replace(",", "")
        return any(re.match(p, cleaned, re.IGNORECASE) for p in patterns)

    def save(self, filepath: str) -> str:
        """
        Save the DXF document to the specified file path.

        Creates parent directories if they do not exist.
        Validates the output path before saving.

        Args:
            filepath: Full path to the output .dxf file.

        Returns:
            Absolute path to the saved file.

        Raises:
            ValueError: If no document has been built.
            OSError: If the file cannot be written.
        """
        if self._doc is None:
            raise ValueError(
                "No DXF document built. Call build_from_result() first."
            )

        if not filepath.lower().endswith(".dxf"):
            filepath += ".dxf"

        output_dir = os.path.dirname(filepath)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        try:
            audit_errors = self._doc.audit()
            if audit_errors:
                logger.warning(
                    f"DXF audit found {len(audit_errors)} issues before save. "
                    f"First: {audit_errors[0] if audit_errors else 'N/A'}"
                )

            self._doc.saveas(filepath)
            abs_path = os.path.abspath(filepath)
            logger.info(f"DXF saved to: {abs_path}")
            return abs_path
        except Exception as e:
            logger.error(f"Failed to save DXF: {e}")
            raise OSError(f"Cannot save DXF to {filepath}: {e}")

    def add_title_block(
        self,
        part_name: str = "",
        drawing_no: str = "",
        material: str = "",
        scale_text: str = "",
        drawn_by: str = "",
        date: str = "",
        revision: str = "A",
        width: float = 180.0,
        height: float = 27.0,
        x_offset: float = 0.0,
        y_offset: float = 0.0,
    ) -> None:
        """
        Add an AS1100/ISO-compliant title block to the DXF.

        Draws a bordered table with part name, drawing number, material,
        scale, date, and revision fields at the bottom-right of the sheet.

        Args:
            part_name: Name/description of the part.
            drawing_no: Drawing number identifier.
            material: Material specification.
            scale_text: Scale ratio text (e.g. "1:1", "NTS").
            drawn_by: Drafter/author name.
            date: Drawing date string.
            revision: Revision letter.
            width: Title block width in real units.
            height: Title block height in real units.
            x_offset: X position offset.
            y_offset: Y position offset.
        """
        if self._doc is None:
            return

        layer = "99_REFERENCE"
        text_h = max(height / 5.0, 1.5)
        small_h = max(text_h * 0.7, 1.0)

        cells = [
            (0, 0, width * 0.6, height * 0.5, "PART", part_name),
            (width * 0.6, 0, width * 0.2, height * 0.5, "DWG NO", drawing_no),
            (width * 0.8, 0, width * 0.2, height * 0.5, "REV", revision),
            (0, height * 0.5, width * 0.3, height * 0.5, "MATERIAL", material),
            (width * 0.3, height * 0.5, width * 0.15, height * 0.5, "SCALE", scale_text),
            (width * 0.45, height * 0.5, width * 0.25, height * 0.5, "DRAWN", drawn_by),
            (width * 0.7, height * 0.5, width * 0.3, height * 0.5, "DATE", date),
        ]

        for cx, cy, cw, ch, label, value in cells:
            px = x_offset + cx
            py = y_offset + cy
            self._msp.add_line(
                (px, py), (px + cw, py), dxfattribs={"layer": layer}
            )
            self._msp.add_line(
                (px, py + ch), (px + cw, py + ch), dxfattribs={"layer": layer}
            )
            self._msp.add_line(
                (px, py), (px, py + ch), dxfattribs={"layer": layer}
            )
            self._msp.add_line(
                (px + cw, py), (px + cw, py + ch), dxfattribs={"layer": layer}
            )

            self._msp.add_text(
                label,
                dxfattribs={
                    "layer": layer,
                    "height": small_h,
                    "color": 8,
                },
            ).set_pos((px + 1, py + ch - small_h * 0.3), align="LEFT")

            if value:
                self._msp.add_text(
                    str(value),
                    dxfattribs={
                        "layer": layer,
                        "height": text_h,
                    },
                ).set_pos((px + 1, py + ch * 0.5), align="LEFT")

    def get_preview_data(self) -> Dict[str, Any]:
        """
        Extract preview data from the current DXF document.

        Returns geometry counts and layer information for
        display in the web UI preview panel.

        Returns:
            Dictionary with entity counts and layer names.
        """
        if self._doc is None:
            return {"error": "No document built."}

        counts = {}
        for entity in self._msp:
            layer = entity.dxf.layer
            counts[layer] = counts.get(layer, 0) + 1

        return {
            "layers": list(counts.keys()),
            "entity_counts": counts,
            "total_entities": sum(counts.values()),
            "scale_factor": self.scale_factor,
            "unit": self.unit,
        }


def generate_dxf(
    result: ProcessingResult,
    output_path: str,
) -> str:
    """
    Convenience function to generate and save a DXF file in one call.

    Args:
        result: ProcessingResult from the vision engine.
        output_path: Destination file path for the DXF.

    Returns:
        Absolute path to the saved DXF file.
    """
    generator = CADGenerator(
        scale_factor=result.scale_factor,
        unit=result.scale_unit,
        image_height=result.image_shape[0],
    )

    generator.build_from_result(result)

    saved_path = generator.save(output_path)

    preview = generator.get_preview_data()
    logger.info(f"DXF preview data: {preview}")

    return saved_path
