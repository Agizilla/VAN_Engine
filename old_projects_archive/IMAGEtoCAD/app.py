"""
FastAPI Backend - Blueprint to DXF Conversion Service

Orchestrates the vision processing pipeline, CAD generation,
and high-resolution print preview rendering.

Endpoints:
- GET  /                  : Serve the web UI
- POST /upload            : Upload a blueprint image and process it
- GET  /preview/{id}      : Get the SVG preview of processed geometry
- POST /approve-save      : Approve the preview and save DXF to folder
- POST /generate-preview  : Render DXF geometry to HD PNG/JPEG image
"""

import os
import uuid
import logging
import time
import io
import asyncio
import json
import html
import math
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import cv2
import ezdxf
import numpy as np
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.concurrency import run_in_threadpool
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from pipeline.vision_engine import VisionEngine, ProcessingResult
from pipeline.cad_engine import CADGenerator
from pipeline.preview_engine import PreviewEngine
from pipeline.session_backend import SessionBackend

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

IMAGE_MAGIC_BYTES = {
    b"\x89PNG\r\n\x1a\n": ".png",
    b"\xff\xd8\xff": ".jpg",
    b"BM": ".bmp",
    b"II\x2a\x00": ".tiff",
    b"MM\x00\x2a": ".tiff",
}

import threading

_trace_context = threading.local()


class StructuredFormatter(logging.Formatter):
    """
    JSON-structured log formatter with trace ID support.

    Produces log lines like:
    {"ts": "...", "level": "INFO", "msg": "...", "trace_id": "abc-123", "module": "app"}
    """

    def format(self, record):
        trace_id = getattr(_trace_context, "trace_id", None)
        entry = {
            "ts": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "msg": record.getMessage(),
            "trace_id": trace_id,
            "module": record.module,
        }
        if record.exc_info and record.exc_info[0] is not None:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, default=str)


def set_trace_id(trace_id: Optional[str]) -> None:
    """Set the trace ID for the current thread."""
    _trace_context.trace_id = trace_id


def get_trace_id() -> Optional[str]:
    """Get the trace ID for the current thread."""
    return getattr(_trace_context, "trace_id", None)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

root_logger = logging.getLogger()
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

json_handler = logging.StreamHandler()
json_handler.setFormatter(StructuredFormatter())
root_logger.addHandler(json_handler)

logger = logging.getLogger(__name__)


async def _session_cleanup_loop() -> None:
    """Background task that periodically evicts expired sessions."""
    while True:
        await asyncio.sleep(300)
        _cleanup_expired_sessions()


@asynccontextmanager
async def lifespan(app_instance):
    """Manage startup/shutdown lifecycle with background cleanup task."""
    task = asyncio.create_task(_session_cleanup_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="Blueprint to DXF Converter",
    description="Process technical blueprint images and export production-ready DXF files.",
    version="2.0.0",
    lifespan=lifespan,
)


def _is_path_within(path: Path, base: Path) -> bool:
    """
    Check if path is strictly within base directory.

    Prevents path traversal bypasses like outputs_evil matching outputs.
    """
    try:
        common = os.path.commonpath([str(path), str(base)])
        return os.path.normpath(common) == os.path.normpath(str(base))
    except ValueError:
        return False


BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

session_db = SessionBackend(str(BASE_DIR / "sessions.db"))
session_store: dict = {}
progress_queues: dict = {}
SESSION_TTL_SECONDS = 3600

vision_engine = VisionEngine(
    line_merge_distance=8.0,
    line_merge_angle_tol=10.0,
    use_easyocr=True,
)

preview_engine = PreviewEngine(
    target_dpi=300,
    min_width_px=3000,
    min_height_px=2000,
)


def _cleanup_expired_sessions() -> None:
    """Remove sessions older than SESSION_TTL_SECONDS."""
    removed = session_db.cleanup_expired(SESSION_TTL_SECONDS)
    if removed:
        logger.info(f"Cleaned up {removed} expired sessions.")
        logger.info(f"Cleaned up expired session: {sid}")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main web UI."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload")
async def upload_blueprint(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
):
    """
    Upload a blueprint image and start the vision processing pipeline.

    Returns immediately with a session_id. Processing continues in
    the background. Connect to /progress/{session_id} for real-time
    stage updates, then poll /upload-status/{session_id} for results.

    Returns:
        JSON with session_id immediately.
    """
    allowed_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"}
    file_ext = os.path.splitext(file.filename)[1].lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Allowed: {allowed_extensions}",
        )

    effective_sid = session_id or str(uuid.uuid4())

    _cleanup_expired_sessions()

    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    detected_ext = None
    for magic, ext in IMAGE_MAGIC_BYTES.items():
        if contents[:len(magic)] == magic:
            detected_ext = ext
            break
    if detected_ext is None:
        if file_ext in allowed_extensions:
            detected_ext = file_ext
        else:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file does not appear to be a valid image.",
            )

    image_array = np.frombuffer(contents, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if image is None:
        raise HTTPException(
            status_code=400,
            detail="Failed to decode image. File may be corrupted or in an unsupported format.",
        )

    upload_path = UPLOAD_DIR / f"{effective_sid}{file_ext}"
    with open(upload_path, "wb") as f:
        f.write(contents)

    progress_queue = asyncio.Queue()
    progress_queues[effective_sid] = progress_queue

    set_trace_id(effective_sid)
    logger.info(f"Processing image: {file.filename} ({image.shape[1]}x{image.shape[0]})")

    loop = asyncio.get_running_loop()

    def progress_cb(stage: str, status: str, elapsed_ms: int):
        loop.call_soon_threadsafe(
            progress_queue.put_nowait,
            {"stage": stage, "status": status, "elapsed_ms": elapsed_ms},
        )

    async def run_pipeline():
        return await run_in_threadpool(
            lambda: vision_engine.process(image, progress_callback=progress_cb)
        )

    async def process_background():
        try:
            result = await run_pipeline()

            await progress_queue.put({"stage": "done", "status": "complete", "elapsed_ms": 0})

            session_store[effective_sid] = {
                "result": result,
                "upload_path": str(upload_path),
                "filename": file.filename,
                "image_shape": result.image_shape,
                "created_at": time.time(),
                "dxf_doc": None,
                "dxf_path": None,
            }

            session_db.set(effective_sid, {
                "upload_path": str(upload_path),
                "filename": file.filename,
                "image_shape": result.image_shape,
                "created_at": time.time(),
                "dxf_path": None,
            })
        except Exception as e:
            logger.error(f"Background processing failed: {e}", exc_info=True)
            await progress_queue.put({"stage": "error", "status": "failed", "error": str(e)})
        finally:
            pending_sessions.pop(effective_sid, None)

    asyncio.create_task(process_background())

    return JSONResponse({
        "session_id": effective_sid,
        "status": "processing",
    })


@app.get("/upload-status/{session_id}")
async def get_upload_status(session_id: str):
    """
    Poll for upload processing results.

    Returns the full processing result when ready, or a status
    indicating the pipeline is still running.
    """
    session = session_store.get(session_id)
    if session and session.get("result"):
        result: ProcessingResult = session["result"]

        view_info = []
        for view in result.views:
            view_info.append({
                "label": view.label,
                "lines": len(view.lines),
                "circles": len(view.circles),
                "ocr_count": len(view.ocr_results),
                "calibrated": view.calibrated,
                "scale_factor": round(view.scale_factor, 2),
            })

        return JSONResponse({
            "session_id": session_id,
            "status": "complete",
            "preview_svg": result.preview_svg,
            "view_count": len(result.views),
            "views": view_info,
            "scale_factor": round(result.scale_factor, 4),
            "scale_unit": result.scale_unit,
            "primary_view": result.primary_view.label if result.primary_view else None,
            "image_width": result.image_shape[1],
            "image_height": result.image_shape[0],
        })

    if session_id in progress_queues or session_id in pending_sessions:
        return JSONResponse({
            "session_id": session_id,
            "status": "processing",
        })

    raise HTTPException(status_code=404, detail="Session not found.")


@app.get("/progress/{session_id}")
async def stream_progress(session_id: str):
    """
    Server-Sent Events endpoint for pipeline stage progress.

    Clients subscribe with a session_id and receive JSON events
    as the processing pipeline advances through stages.

    Events:
    - {"stage": "preprocess", "status": "start"}
    - {"stage": "preprocess", "status": "complete", "elapsed_ms": 123}
    - {"stage": "detect", "status": "start"}
    - {"stage": "detect", "status": "complete", "elapsed_ms": 456}
    - {"stage": "segment", "status": "start"}
    - {"stage": "segment", "status": "complete", "elapsed_ms": 78}
    - {"stage": "ocr", "status": "start"}
    - {"stage": "ocr", "status": "complete", "elapsed_ms": 2345}
    - {"stage": "calibrate", "status": "start"}
    - {"stage": "calibrate", "status": "complete", "elapsed_ms": 12}
    - {"stage": "merge", "status": "start"}
    - {"stage": "merge", "status": "complete", "elapsed_ms": 34}
    - {"stage": "done", "status": "complete"}
    """
    if session_id not in progress_queues:
        raise HTTPException(status_code=404, detail="No progress stream for this session.")

    queue = progress_queues[session_id]

    async def event_generator():
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                if event is None:
                    break
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("stage") == "done" or event.get("stage") == "error":
                    break
        except asyncio.CancelledError:
            pass
        except Exception:
            pass
        finally:
            progress_queues.pop(session_id, None)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/preview/{session_id}")
async def get_preview(session_id: str):
    """
    Retrieve the SVG preview for a processed session.

    Args:
        session_id: Session identifier from the upload response.

    Returns:
        JSON with preview SVG and processing metadata.
    """
    session = session_store.get(session_id)
    if not session:
        meta = session_db.get(session_id)
        if meta:
            raise HTTPException(
                status_code=410,
                detail="Session expired. Result is not cached. Re-upload the image.",
            )
        raise HTTPException(status_code=404, detail="Session not found.")

    result: ProcessingResult = session["result"]

    return JSONResponse({
        "preview_svg": result.preview_svg,
        "scale_factor": round(result.scale_factor, 4),
        "scale_unit": result.scale_unit,
        "view_count": len(result.views),
        "primary_view": result.primary_view.label if result.primary_view else None,
    })


@app.post("/approve-save")
async def approve_and_save(
    session_id: str = Form(...),
    output_folder: str = Form(...),
    filename: Optional[str] = Form(None),
    manual_scale: Optional[float] = Form(None),
    scale_unit: Optional[str] = Form(None),
):
    """
    Approve the processed preview and save the DXF file.

    Takes the session ID from a previous upload, builds the DXF
    document using the calibrated scale and processed geometry,
    and saves it to the user-specified output folder.

    If manual_scale is provided (>0), it overrides the auto-detected
    scale factor, allowing users to correct scale calibration drift.

    The generated DXF document is cached in the session for
    subsequent HD preview generation.

    Args:
        session_id: Session identifier from the upload response.
        output_folder: Destination folder path for the DXF file.
        filename: Optional custom filename (defaults to original name).
        manual_scale: Optional manual scale override (pixels per unit).
        scale_unit: Optional unit string ('mm' or 'in').

    Returns:
        JSON with saved file path and entity counts.
    """
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    result: ProcessingResult = session["result"]

    if manual_scale is not None and manual_scale > 0:
        logger.info(
            f"Manual scale override: {manual_scale} px/{scale_unit or result.scale_unit}"
        )
        result.scale_factor = manual_scale
        if scale_unit:
            result.scale_unit = scale_unit
        for view in result.views:
            view.scale_factor = manual_scale
            view.calibrated = True

    if not output_folder or not output_folder.strip():
        raise HTTPException(
            status_code=400,
            detail="Output folder path is required.",
        )

    output_path = Path(output_folder).expanduser().resolve()

    allowed_bases = [
        BASE_DIR.resolve() / "outputs",
        Path.home(),
    ]
    is_allowed = any(
        _is_path_within(output_path, base) for base in allowed_bases
    )
    if not is_allowed:
        raise HTTPException(
            status_code=403,
            detail=f"Output path not permitted: {output_path}. "
                   f"Allowed locations: outputs/ folder or user home directory.",
        )

    try:
        os.makedirs(output_path, exist_ok=True)
    except PermissionError:
        raise HTTPException(
            status_code=403,
            detail=f"Permission denied: cannot create folder {output_path}",
        )
    except OSError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Cannot create output folder: {str(e)}",
        )

    base_name = filename or Path(session["filename"]).stem
    dxf_filename = f"{base_name}.dxf"
    full_path = output_path / dxf_filename

    try:
        generator = CADGenerator(
            scale_factor=result.scale_factor,
            unit=result.scale_unit,
            image_height=result.image_shape[0],
        )
        await run_in_threadpool(generator.build_from_result, result)
        saved_path = await run_in_threadpool(generator.save, str(full_path))

        preview_data = generator.get_preview_data()

        session["dxf_doc"] = generator._doc
        session["dxf_path"] = saved_path

        return JSONResponse({
            "success": True,
            "saved_path": saved_path,
            "filename": dxf_filename,
            "scale_factor": round(result.scale_factor, 4),
            "scale_unit": result.scale_unit,
            "entity_counts": preview_data.get("entity_counts", {}),
            "total_entities": preview_data.get("total_entities", 0),
        })

    except Exception as e:
        logger.error(f"DXF generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"DXF generation failed: {str(e)}",
        )


@app.post("/generate-preview")
async def generate_hd_preview(
    session_id: str = Form(...),
    image_format: str = Form("png"),
    dpi: int = Form(300),
):
    """
    Generate a high-resolution print preview from the cached DXF document.

    Renders the clean DXF geometry (not the original image) to a
    high-DPI raster image suitable for printing. The output uses
    optimized line weights, colors, and anti-aliasing.

    Args:
        session_id: Session identifier from a saved DXF session.
        image_format: Output format ('png' or 'jpeg').
        dpi: Output resolution (default 300, max 600).

    Returns:
        StreamingResponse with the rendered image file.
    """
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    dxf_doc = session.get("dxf_doc")
    if dxf_doc is None:
        raise HTTPException(
            status_code=400,
            detail="No DXF document available. Save the DXF first via /approve-save.",
        )

    image_format = image_format.lower()
    if image_format not in ("png", "jpeg", "jpg"):
        image_format = "png"
    if image_format == "jpg":
        image_format = "jpeg"

    dpi = max(150, min(dpi, 600))

    try:
        engine = PreviewEngine(
            target_dpi=dpi,
            min_width_px=3000,
            min_height_px=2000,
        )

        buf, metadata = await run_in_threadpool(
            engine.generate, dxf_doc, image_format
        )

        media_type = "image/png" if image_format == "png" else "image/jpeg"
        ext = "png" if image_format == "png" else "jpg"

        base_name = Path(session.get("filename", "blueprint")).stem
        content_disposition = f"attachment; filename=\"{base_name}_preview.{ext}\""

        return StreamingResponse(
            buf,
            media_type=media_type,
            headers={
                "Content-Disposition": content_disposition,
                "X-Preview-Width": str(metadata["width_px"]),
                "X-Preview-Height": str(metadata["height_px"]),
                "X-Preview-DPI": str(metadata["dpi"]),
                "X-Preview-Entities": str(metadata["entity_count"]),
            },
        )

    except Exception as e:
        logger.error(f"HD preview generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Preview generation failed: {str(e)}",
        )


@app.post("/export")
async def export_multi_format(
    session_id: str = Form(...),
    export_format: str = Form("dxf"),
):
    """
    Export processed geometry in multiple formats.

    Supported formats:
    - dxf: AutoCAD DXF (default)
    - svg: Scalable Vector Graphics
    - pdf: Portable Document Format

    Args:
        session_id: Session identifier.
        export_format: Target format (dxf, svg, pdf).

    Returns:
        File download in the requested format.
    """
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    result: ProcessingResult = session["result"]
    export_format = export_format.lower()

    if export_format == "dxf":
        dxf_doc = session.get("dxf_doc")
        if dxf_doc is None:
            generator = CADGenerator(
                scale_factor=result.scale_factor,
                unit=result.scale_unit,
                image_height=result.image_shape[0],
            )
            generator.build_from_result(result)
            dxf_doc = generator._doc

        buf = io.BytesIO()
        dxf_doc.saveas(buf, fmt="asc")
        buf.seek(0)

        return StreamingResponse(
            buf,
            media_type="application/dxf",
            headers={
                "Content-Disposition": f'attachment; filename="{session.get("filename", "blueprint")}.dxf"',
            },
        )

    elif export_format == "svg":
        svg_content = result.preview_svg
        return StreamingResponse(
            io.BytesIO(svg_content.encode("utf-8")),
            media_type="image/svg+xml",
            headers={
                "Content-Disposition": f'attachment; filename="{session.get("filename", "blueprint")}.svg"',
            },
        )

    elif export_format == "pdf":
        from matplotlib.backends.backend_pdf import PdfPages

        buf = io.BytesIO()
        with PdfPages(buf) as pdf:
            fig, ax = plt.subplots(figsize=(11, 8.5))
            ax.set_facecolor("#1a1a2e")
            fig.patch.set_facecolor("#1a1a2e")

            for view in result.views:
                x, y, w, h = view.bbox
                ax.add_patch(plt.Rectangle(
                    (x, y), w, h, fill=False,
                    edgecolor="white", linewidth=0.5, alpha=0.3,
                    linestyle="--",
                ))
                ax.text(x + 5, y + 15, view.label, color="white", fontsize=8)

                for line in view.lines:
                    ax.plot(
                        [line.x1, line.x2], [line.y1, line.y2],
                        color="#00ff88", linewidth=1, alpha=0.8,
                    )
                for circle in view.circles:
                    ax.add_patch(plt.Circle(
                        (circle.cx, circle.cy), circle.radius,
                        fill=False, edgecolor="#ff6b6b", linewidth=1, alpha=0.8,
                    ))

            ax.set_xlim(0, result.image_shape[1])
            ax.set_ylim(result.image_shape[0], 0)
            ax.set_aspect("equal")
            ax.axis("off")
            pdf.savefig(fig, dpi=300, bbox_inches="tight")
            plt.close(fig)

        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{session.get("filename", "blueprint")}.pdf"',
            },
        )

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {export_format}. Use dxf, svg, or pdf.",
        )


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Clean up a processing session."""
    session = session_store.pop(session_id, None)
    if session:
        upload_path = session.get("upload_path")
        if upload_path and os.path.exists(upload_path):
            try:
                os.remove(upload_path)
            except OSError:
                pass
    session_db.delete(session_id)
    return JSONResponse({"success": True})


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse({
        "status": "healthy",
        "sessions_active": len(session_store),
        "sessions_persisted": session_db.count(),
    })


@app.get("/viewer", response_class=HTMLResponse)
async def dxf_viewer(request: Request):
    """Serve the standalone DXF viewer page."""
    return templates.TemplateResponse("viewer.html", {"request": request})


@app.post("/dxf-preview")
async def dxf_preview(file: UploadFile = File(...)):
    """
    Parse a DXF file and return an SVG preview with layer/entity metadata.
    """
    try:
        if not file.filename or not file.filename.lower().endswith(".dxf"):
            raise HTTPException(status_code=400, detail="Only .dxf files are supported.")

        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Empty file.")

        import tempfile
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as tmp:
                tmp.write(contents if isinstance(contents, bytes) else contents.encode("utf-8"))
                tmp_path = tmp.name
            doc = ezdxf.readfile(tmp_path)
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

        msp = doc.modelspace()

        svg_parts = []
        layer_counts = {}
        entity_counts = {}
        all_x, all_y = [], []

        layer_colors = {
            "01_CUT_OUTLINE": "#00ff88",
            "02_CUT_INNER": "#4ecdc4",
            "03_DRILL_BORES": "#ff6b6b",
            "04_MILL_SLOTS": "#ffd93d",
            "90_CENTER_MARKS": "#a29bfe",
            "95_DIMENSIONS": "#fd79a8",
            "98_TEXT": "#fdcb6e",
            "99_REFERENCE": "#74b9ff",
        }

        for entity in msp:
            layer_name = entity.dxf.layer
            color = layer_colors.get(layer_name, "#888")
            layer_counts[layer_name] = layer_counts.get(layer_name, 0) + 1
            entity_type = entity.dxftype()
            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1

            try:
                if entity_type == "LINE":
                    x1, y1 = entity.dxf.start[0], entity.dxf.start[1]
                    x2, y2 = entity.dxf.end[0], entity.dxf.end[1]
                    all_x.extend([x1, x2])
                    all_y.extend([y1, y2])
                    svg_parts.append(
                        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                        f'stroke="{color}" stroke-width="0.5" data-layer="{layer_name}"/>'
                    )

                elif entity_type == "CIRCLE":
                    cx, cy = entity.dxf.center[0], entity.dxf.center[1]
                    r = entity.dxf.radius
                    all_x.extend([cx - r, cx + r])
                    all_y.extend([cy - r, cy + r])
                    svg_parts.append(
                        f'<circle cx="{cx}" cy="{cy}" r="{r}" '
                        f'fill="none" stroke="{color}" stroke-width="0.5" data-layer="{layer_name}"/>'
                    )

                elif entity_type == "ARC":
                    cx, cy = entity.dxf.center[0], entity.dxf.center[1]
                    r = entity.dxf.radius
                    start_a = math.radians(entity.dxf.start_angle)
                    end_a = math.radians(entity.dxf.end_angle)
                    x1 = cx + r * math.cos(start_a)
                    y1 = cy + r * math.sin(start_a)
                    x2 = cx + r * math.cos(end_a)
                    y2 = cy + r * math.sin(end_a)
                    all_x.extend([cx - r, cx + r])
                    all_y.extend([cy - r, cy + r])
                    sweep = 1 if entity.dxf.end_angle > entity.dxf.start_angle else 0
                    large = abs(entity.dxf.end_angle - entity.dxf.start_angle) > 180
                    svg_parts.append(
                        f'<path d="M {x1} {y1} A {r} {r} 0 {1 if large else 0} {sweep} {x2} {y2}" '
                        f'fill="none" stroke="{color}" stroke-width="0.5" data-layer="{layer_name}"/>'
                    )

                elif entity_type in ("LWPOLYLINE", "POLYLINE"):
                    if entity_type == "LWPOLYLINE":
                        raw_pts = entity.get_points("xy")
                        pts = [(p[0], p[1]) for p in raw_pts]
                    else:
                        pts = [(v.dxf.location[0], v.dxf.location[1]) for v in entity.vertices]
                    if pts:
                        pts_str = " ".join(f"{x},{y}" for x, y in pts)
                        for x, y in pts:
                            all_x.append(x)
                            all_y.append(y)
                        svg_parts.append(
                            f'<polyline points="{pts_str}" '
                            f'fill="none" stroke="{color}" stroke-width="0.5" '
                            f'data-layer="{layer_name}"/>'
                        )

                elif entity_type in ("TEXT", "MTEXT"):
                    pos = entity.dxf.insert
                    px, py = pos[0], pos[1]
                    text = entity.plain_text() if hasattr(entity, 'plain_text') else entity.dxf.text
                    all_x.append(px)
                    all_y.append(py)
                    svg_parts.append(
                        f'<text x="{px}" y="{py}" '
                        f'fill="{color}" font-size="2" font-family="monospace" '
                        f'data-layer="{layer_name}">{html.escape(str(text))}</text>'
                    )

            except (AttributeError, TypeError, IndexError):
                continue

        if all_x and all_y:
            margin = max(max(all_x) - min(all_x), max(all_y) - min(all_y)) * 0.05
            vb = [
                min(all_x) - margin,
                min(all_y) - margin,
                max(all_x) - min(all_x) + margin * 2,
                max(all_y) - min(all_y) + margin * 2,
            ]
        else:
            vb = [0, 0, 100, 100]

        svg_content = (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="{vb[0]} {vb[1]} {vb[2]} {vb[3]}">'
            f'<rect x="{vb[0]}" y="{vb[1]}" width="{vb[2]}" height="{vb[3]}" fill="#12121f"/>'
            + "".join(svg_parts) + "</svg>"
        )

        layers = []
        for name, count in sorted(layer_counts.items()):
            layers.append({
                "name": name,
                "count": count,
                "color": layer_colors.get(name, "#888"),
            })

        return JSONResponse({
            "svg": svg_content,
            "viewBox": vb,
            "layers": layers,
            "entityCounts": entity_counts,
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DXF preview failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"DXF preview failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
