# IMAGEtoCAD — Blueprint to DXF Conversion Pipeline

> **Convert technical blueprint images into production-ready 2D DXF files for CNC machining.**

IMAGEtoCAD is a self-contained Python application that takes uploaded technical blueprint images (containing multiple 2D orthographic views with dimensions), processes them through a computer vision pipeline, extracts geometry and dimensional annotations, and exports clean, layered DXF files suitable for CAM toolpath generation.

---

## Table of Contents

- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [Pipeline Flow](#pipeline-flow)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Module Reference](#module-reference)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [Layer Convention](#layer-convention)
- [Known Limitations](#known-limitations)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [License](#license)

---

## Features

### Core Capabilities
- **Multi-view segmentation** — Automatically separates Top, Front, and End views from a single blueprint image using whitespace gap analysis and contour bounding boxes
- **Line detection & merging** — Probabilistic Hough transform detects line segments; graph-based clustering with PCA principal axis projection merges broken fragments into continuous segments
- **Arc fitting** — Least-squares circle fitting (Taubin's algebraic method + Gauss-Newton refinement) converts pixelated corner contours into true CAD arc entities with proper winding order
- **OCR dimension extraction** — EasyOCR (with Tesseract fallback) extracts dimensional text and associates it with geometry using multi-factor scoring (perpendicular distance, angular alignment, endpoint proximity)
- **Scale calibration** — Auto-detects pixel-to-unit ratio from dimension text; manual override available when OCR fails
- **Clean DXF export** — ezdxf-based generation with CAM-standard numeric-prefixed layers (01_CUT_OUTLINE, 03_DRILL_BORES, etc.)
- **High-DPI print preview** — Matplotlib-based rasterization renders clean vector geometry at configurable DPI (300/450/600) for print-quality output
- **Web-based UI** — FastAPI + Jinja2 single-page application with drag-drop upload, side-by-side preview, and export controls

### Engineering Quality
- **No jagged polylines** — Radiused corners become true DXF ARC entities, not approximated line segments
- **CAM-ready layers** — Cutting layers (01–09) separated from non-cutting reference layers (90–99)
- **Coordinate transformation** — Pixel space (top-left origin, y-down) → engineering space (bottom-left origin, y-up) with scale division
- **Defensive validation** — Magic byte image verification, zero-division guards, bounds-clamped ROI extraction, RGBA channel handling

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        WEB UI (index.html)                       │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────┐ │
│  │  Upload   │→ │ SVG Preview  │→ │ Approve/Save │→ │ HD Prev │ │
│  │  Zone     │  │  (vector)    │  │   DXF File   │  │  (PNG)  │ │
│  └──────────┘  └──────────────┘  └──────────────┘  └─────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP / JSON
┌────────────────────────────▼────────────────────────────────────┐
│                     FastAPI Backend (app.py)                      │
│  /upload  →  /preview/{id}  →  /approve-save  →  /generate-preview│
└──┬──────────────┬──────────────┬──────────────┬──────────────────┘
   │              │              │              │
┌──▼──────────┐ ┌▼────────────┐│┌▼────────────┐│┌▼───────────────┐
│ vision_     │ │ cad_        │││ cad_        │││ preview_       │
│ engine.py   │ │ engine.py   │││ engine.py   │││ engine.py      │
│             │ │             │││             │││                │
│ OpenCV      │ │ ezdxf       │││ ezdxf       │││ matplotlib     │
│ EasyOCR     │ │ DXF writer  │││ DXF writer  │││ rasterizer     │
│ Geometry    │ │ Layers      │││ Layers      │││ High-DPI       │
│ Optimizer   │ │ Scale       │││ Scale       │││ Output         │
└─────────────┘ └─────────────┘│└─────────────┘│└────────────────┘
                               │               │
                    ┌──────────▼───────────────▼──────────┐
                    │       geometry_optimizer.py          │
                    │  merge_collinear_lines (PCA+union)   │
                    │  fit_circle_least_squares (Taubin)   │
                    └──────────────────────────────────────┘
```

---

## Pipeline Flow

1. **Upload** — User drops a blueprint image (PNG/JPG/BMP/TIFF) into the web UI
2. **Preprocess** — Grayscale conversion → Gaussian denoise → adaptive threshold → morphological close
3. **Detect** — HoughLinesP for line segments, HoughCircles for bores, contour extraction for arcs
4. **Segment** — View regions separated by whitespace gaps using projection profiles and contour bounding boxes
5. **OCR** — EasyOCR extracts dimension text; multi-factor scoring associates text with nearest geometry
6. **Calibrate** — Pixel-to-unit scale ratio computed from OCR dimension + associated line length
7. **Merge** — GeometryOptimizer merges collinear line fragments via union-find + PCA projection
8. **Fit Arcs** — Corner regions identified by turning angle analysis; least-squares circle fitting produces true arcs
9. **Generate DXF** — ezdxf writes geometry to CAM-standard layers with real-world coordinates
10. **Preview** — Matplotlib renders DXF entities to high-DPI PNG/JPEG with proper text sizing
11. **Export** — DXF saved to user-specified folder; HD preview available for download

---

## Installation

### Prerequisites
- Python 3.10 or higher
- 4GB+ RAM (EasyOCR model loading)
- No GPU required (runs on CPU)

### Setup

```bash
# Navigate to project directory
cd IMAGEtoCAD

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/macOS

# Install dependencies
pip install -r requirements.txt
```

### Dependencies

| Package | Purpose |
|---------|---------|
| `fastapi` + `uvicorn` | Web server and routing |
| `opencv-python` | Image preprocessing, line/circle/contour detection |
| `ezdxf` | DXF file generation and manipulation |
| `numpy` + `scipy` | Numerical computation, least-squares fitting |
| `easyocr` | Text extraction from blueprint images |
| `matplotlib` | High-DPI preview rendering |
| `Pillow` | Image format handling |
| `Jinja2` | HTML template rendering |
| `python-multipart` | Form data parsing |

---

## Quick Start

```bash
# Start the server
python app.py

# Open browser to
http://localhost:8000
```

### Usage Steps

1. **Upload** — Drag and drop a blueprint image or click to browse
2. **Review** — Side-by-side view shows original image and detected vector overlay
3. **Verify** — Check detected views, scale factor, and entity counts
4. **Export DXF** — Enter destination folder → click "Approve & Save DXF"
5. **Generate Preview** — Select format (PNG/JPEG) and DPI → click "Generate HD Preview"
6. **Download** — Click the download link for the rendered preview image

---

## Project Structure

```
IMAGEtoCAD/
├── app.py                          # FastAPI backend (routes, orchestration)
├── requirements.txt                # Python dependencies
├── pipeline/
│   ├── __init__.py
│   ├── vision_engine.py            # Image processing, OCR, segmentation, arc fitting
│   ├── cad_engine.py               # ezdxf DXF generation with CAM layers
│   ├── preview_engine.py           # Matplotlib high-DPI rasterization
│   └── geometry_optimizer.py       # Line merging (PCA) + circle fitting (Taubin)
├── templates/
│   └── index.html                  # Single-page web UI
├── uploads/                        # Temporary upload storage (auto-created)
└── docs/
    ├── README.md                   # This file
    └── README.html                 # Interactive HTML documentation
```

---

## Module Reference

### `pipeline/vision_engine.py` — Vision Processing Engine

**Class: `VisionEngine`**

| Method | Purpose |
|--------|---------|
| `process(image)` | Main entry point — runs full pipeline, returns `ProcessingResult` |
| `preprocess_image(image)` | Grayscale → denoise → adaptive threshold → morphological close |
| `detect_lines(binary)` | HoughLinesP line segment detection |
| `detect_circles(gray, binary)` | HoughCircles + crosshair detection for bores |
| `segment_views(binary, lines, circles)` | View region separation via whitespace analysis |
| `perform_ocr(image, segments)` | EasyOCR/Tesseract text extraction per view |
| `calibrate_scale(segments)` | Pixel-to-unit ratio from OCR dimension + line length |
| `merge_lines(lines)` | Delegates to GeometryOptimizer for collinear merging |
| `detect_arcs_from_contours(binary, segment)` | Contour-based arc detection with circle fitting |
| `fit_arcs_to_profile(contour)` | Turning-angle corner detection + least-squares arc fitting |
| `extract_outer_profile(binary, segment)` | Largest contour extraction (fallback polyline) |

**Data Classes:**
- `ProcessingResult` — Complete pipeline output (views, scale, profile, arcs, slots)
- `ViewSegment` — Single view with lines, circles, OCR results, scale factor
- `DetectedLine` — Line segment with pixel coordinates
- `DetectedCircle` — Circle/crosshair with center and radius
- `OCRResult` — Extracted text with bounding box and center

---

### `pipeline/cad_engine.py` — CAD Vector Generation

**Class: `CADGenerator`**

| Method | Purpose |
|--------|---------|
| `build_from_result(result)` | Main entry — builds DXF from ProcessingResult |
| `pixel_to_real(px, py)` | Coordinate transform: pixel → real-world (scale + Y-flip) |
| `add_line(x1, y1, x2, y2, layer)` | Add line entity to DXF |
| `add_circle(cx, cy, radius, layer)` | Add circle entity to DXF |
| `add_arc(cx, cy, radius, start, end, layer)` | Add arc entity to DXF |
| `add_polyline(points, layer, closed)` | Add polyline/LWPOLYLINE to DXF |
| `add_slot(cx, cy, length, width, angle, layer)` | Add obround/slot feature to DXF |
| `add_center_mark(cx, cy, size, layer)` | Add crosshair center mark to DXF |
| `add_text(text, x, y, height, layer)` | Add text annotation to DXF |
| `save(filepath)` | Write DXF to disk |
| `is_cutting_layer(name)` | Static — returns True for layers 01–09 |

---

### `pipeline/geometry_optimizer.py` — Geometric Post-Processing

**Class: `GeometryOptimizer`**

| Method | Purpose |
|--------|---------|
| `merge_collinear_lines(lines)` | Union-find clustering + PCA projection for line merging |
| `fit_circle_least_squares(points)` | Taubin algebraic fit + Gauss-Newton refinement → (cx, cy, r, rms) |

**Configurable Tolerances:**
- `line_angle_tolerance_deg` (default: 5.0°) — Max angle diff for merging
- `line_distance_tolerance` (default: 4.0 px) — Max endpoint gap for merging
- `arc_max_residual` (default: 1.5 px) — Max RMS error for valid arc fit
- `arc_min_points` (default: 6) — Min contour points for arc candidate

---

### `pipeline/preview_engine.py` — Print Preview Rasterization

**Class: `PreviewEngine`**

| Method | Purpose |
|--------|---------|
| `generate(doc, output_format)` | Render ezdxf document to high-DPI image buffer |
| `generate_from_file(dxf_path, output_path)` | Load DXF from disk, save rendered image |

**Convenience Function:**
- `generate_hd_print_preview(doc, format, dpi, min_width, min_height)` — One-call rendering

**Layer Styling:** Each CAM layer has defined color, linewidth (points), linestyle, and z-order for print optimization.

---

### `app.py` — FastAPI Backend

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Serve web UI |
| `/upload` | POST | Upload image, run pipeline, return session |
| `/preview/{session_id}` | GET | Get SVG preview for session |
| `/approve-save` | POST | Save DXF to user-specified folder |
| `/generate-preview` | POST | Render HD preview image from cached DXF |
| `/session/{session_id}` | DELETE | Clean up session |
| `/health` | GET | Health check |

All CPU-bound operations run via `run_in_threadpool` to avoid blocking the FastAPI event loop.

---

## Configuration

### Vision Engine Tuning

```python
vision_engine = VisionEngine(
    line_merge_distance=8.0,      # Max pixel gap to merge lines
    line_merge_angle_tol=10.0,    # Max angle diff (degrees) to merge
    use_easyocr=True,             # True = EasyOCR, False = Tesseract
)
```

### Preview Engine Tuning

```python
preview_engine = PreviewEngine(
    target_dpi=300,               # Output resolution
    min_width_px=3000,            # Minimum output width
    min_height_px=2000,           # Minimum output height
    padding_frac=0.08,            # Padding around drawing bounds
    background_color="#ffffff",   # Background color
)
```

### Geometry Optimizer Tuning

```python
optimizer = GeometryOptimizer(
    line_angle_tolerance_deg=5.0,  # Tighter = more selective merging
    line_distance_tolerance=4.0,   # Larger = more aggressive merging
    arc_max_residual=1.5,          # Lower = stricter arc fit quality
    arc_min_points=6,              # Higher = fewer false arc detections
)
```

---

## API Endpoints

### POST `/upload`

Upload a blueprint image for processing.

**Request:** `multipart/form-data` with `file` field (PNG/JPG/BMP/TIFF)

**Response:**
```json
{
  "session_id": "uuid-string",
  "preview_svg": "<svg>...</svg>",
  "view_count": 3,
  "views": [
    {"label": "TOP VIEW", "lines": 45, "circles": 6, "ocr_count": 12, "calibrated": true, "scale_factor": 12.5},
    {"label": "FRONT VIEW", "lines": 32, "circles": 2, "ocr_count": 8, "calibrated": true, "scale_factor": 12.5}
  ],
  "scale_factor": 12.5,
  "scale_unit": "mm",
  "primary_view": "TOP VIEW",
  "image_width": 2400,
  "image_height": 1800
}
```

### POST `/approve-save`

Save the processed DXF to a local folder.

**Request:** `multipart/form-data`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `session_id` | string | Yes | From upload response |
| `output_folder` | string | Yes | Destination folder path |
| `filename` | string | No | Custom filename (default: original name) |
| `manual_scale` | float | No | Override scale factor (px/unit) |
| `scale_unit` | string | No | "mm" or "in" |

**Response:**
```json
{
  "success": true,
  "saved_path": "C:\\output\\part.dxf",
  "filename": "part.dxf",
  "scale_factor": 12.5,
  "scale_unit": "mm",
  "entity_counts": {"01_CUT_OUTLINE": 45, "03_DRILL_BORES": 6},
  "total_entities": 51
}
```

### POST `/generate-preview`

Render the DXF to a high-resolution image.

**Request:** `multipart/form-data`
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `session_id` | string | — | From upload response |
| `image_format` | string | "png" | "png" or "jpeg" |
| `dpi` | int | 300 | 150–600 |

**Response:** Streaming image file with metadata headers:
- `X-Preview-Width`, `X-Preview-Height`, `X-Preview-DPI`, `X-Preview-Entities`

---

## Layer Convention

DXF output uses numeric-prefixed layer names for CAM software compatibility:

| Layer | Color | Purpose | CAM Usage |
|-------|-------|---------|-----------|
| `01_CUT_OUTLINE` | White (7) | Outer profile, primary cutting geometry | Toolpath: profile cut |
| `02_CUT_INNER` | White (7) | Internal cutouts and pockets | Toolpath: pocket cut |
| `03_DRILL_BORES` | Cyan (4) | Through holes, counterbores, circles | Toolpath: drill cycle |
| `04_MILL_SLOTS` | Green (3) | Elongated holes, milled features | Toolpath: slot mill |
| `90_CENTER_MARKS` | Red (1) | Crosshair center marks | Reference only |
| `95_DIMENSIONS` | Yellow (2) | Dimension text annotations | Reference only |
| `98_TEXT` | Yellow (2) | General text and notes | Reference only |
| `99_REFERENCE` | Gray (8) | View boundaries, construction lines | Reference only |

**Cutting vs Non-Cutting:** Layers prefixed 01–09 are cutting layers (CAM toolpaths). Layers 90–99 are non-cutting reference layers. Use `CADGenerator.is_cutting_layer(name)` to programmatically filter.

---

## Known Limitations

1. **OCR accuracy** — Small, skewed, or overlapping dimension text may not be extracted correctly. Use the manual scale override when auto-calibration fails.
2. **View segmentation** — Extremely dense blueprints with minimal whitespace between views may not segment cleanly.
3. **Arc detection range** — Contour-based arc detection filters by length (20–500 px by default). Very small fillets or very large arcs may be missed.
4. **Scale calibration** — Requires at least one readable dimension value near a detected line. If no dimension is found, defaults to 1:1 pixel-to-mm ratio.
5. **Memory usage** — EasyOCR model loading requires ~2GB RAM. HD preview generation at 600 DPI may require additional memory for large drawings.
6. **Single-session** — Sessions expire after 1 hour. No persistent storage between server restarts.

---

## Troubleshooting

### "No lines detected"
- Ensure the blueprint has clear, high-contrast lines on a light background
- Try increasing image resolution or adjusting contrast before upload
- Check that `min_line_length` in `detect_lines` isn't too high for your image

### "Scale not calibrated — using 1:1 ratio"
- The OCR engine couldn't find a dimension value near a detected line
- Use the **Manual Scale Override** field in the UI: measure a known dimension in pixels, divide by the real value
- Example: if a 7.50" dimension spans 150 pixels, enter `20.0` (150/7.5) with unit "in"

### "DXF saved but geometry looks wrong in CAD viewer"
- Check the layer visibility in your CAD software — reference layers (90–99) may be hidden
- Verify the scale factor in the export response matches your expected units
- Open the DXF in a viewer that supports R2018 format (AutoCAD 2018+, LibreCAD, QCAD)

### "Preview image is blank or tiny"
- The DXF may have no entities — check the entity counts in the save response
- Try a higher DPI setting (450 or 600) for better text visibility
- Ensure the blueprint image has detectable geometry (lines, circles, contours)

### "Server is slow or unresponsive"
- EasyOCR first-run downloads language models (~40MB) — this is normal
- Subsequent runs are faster as models are cached
- For production, consider running with a GPU-enabled EasyOCR build

---

## Development

### Running Tests

```bash
# Syntax check all modules
python -m py_compile pipeline/vision_engine.py
python -m py_compile pipeline/cad_engine.py
python -m py_compile pipeline/geometry_optimizer.py
python -m py_compile pipeline/preview_engine.py
python -m py_compile app.py
```

### Adding New Feature Detectors

1. Add detection method to `vision_engine.py` returning typed data
2. Add corresponding `add_*` method to `cad_engine.py`
3. Wire into `build_from_result` and `_process_segment`
4. Add layer styling to `preview_engine.py` `LAYER_STYLE` dict

### Code Conventions

- All coordinate systems use engineering floats (4 decimal places)
- Defensive try-catch blocks around image reading and geometry operations
- Docstrings on all public methods explaining vector transformation logic
- No mock functions or "TODO" placeholders in production code

---

## License

MIT License — use freely for personal and commercial projects.

---

*Built with FastAPI, OpenCV, ezdxf, EasyOCR, and matplotlib.*
