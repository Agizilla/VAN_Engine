#!/usr/bin/env python3
import sys
import json
import logging
import argparse
import importlib
import hashlib
import traceback
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, List, Callable, Tuple

sys.path.insert(0, str(Path(__file__).parent))

from modules.daz_orchestrator import MAX_RETRIES

HERE = Path(__file__).parent

CACHE_DIR = HERE / ".cache"


def file_hash(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def check_dependencies():
    required = {
        "numpy": "numpy",
        "cv2": "opencv-python",
        "mediapipe": "mediapipe",
        "sklearn.cluster": "scikit-learn",
    }
    missing = []
    for mod_name, pip_name in required.items():
        try:
            importlib.import_module(mod_name)
        except ImportError:
            missing.append(pip_name)

    if missing:
        print("Missing dependencies. Install them with:")
        print(f"  pip install {' '.join(missing)}")
        sys.exit(1)


def setup_logging(log_dir: Path) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Logging to: {log_file}")
    return logger


def load_config(config_path: Path) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    base_dir = config_path.parent
    config["workspace_dir"] = str(base_dir / config.get("workspace_dir", "./workspace"))
    config["output_dir"] = str(base_dir / config.get("output_dir", "./workspace/output"))
    config["logs_dir"] = str(base_dir / config.get("logs_dir", "./logs"))

    return config


def safe_json_write(path: Path, data, logger: logging.Logger) -> bool:
    try:
        tmp = path.with_suffix(path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        tmp.replace(path)
        return True
    except (OSError, TypeError, ValueError) as e:
        logger.error(f"Failed to write {path}: {e}")
        return False


def safe_imwrite(path: Path, img, logger: logging.Logger) -> bool:
    try:
        import cv2
        return cv2.imwrite(str(path), img)
    except Exception as e:
        logger.error(f"Failed to write image {path}: {e}")
        return False


def get_cache_path(image_path: Path) -> Optional[Path]:
    try:
        h = file_hash(image_path)
        cache_dir = CACHE_DIR / h[:2] / h[2:4]
        manifest = cache_dir / "manifest.json"
        if manifest.exists():
            return manifest
    except OSError:
        pass
    return None


def write_cache(image_path: Path, result: dict):
    try:
        h = file_hash(image_path)
        cache_dir = CACHE_DIR / h[:2] / h[2:4]
        cache_dir.mkdir(parents=True, exist_ok=True)
        manifest = cache_dir / "manifest.json"
        result["image_hash"] = h
        result["source_image"] = str(image_path)
        safe_json_write(manifest, result, logging.getLogger(__name__))
    except Exception as e:
        logging.getLogger(__name__).warning(f"Cache write failed (non-fatal): {e}")


def print_dry_run_plan(args, config):
    workspace = Path(config["workspace_dir"])
    face_output = workspace / "face_source.png"
    skin_output = workspace / "skin_data.json"

    print()
    print("=" * 60)
    print(" DRY RUN - No actions will be executed")
    print("=" * 60)
    print()
    print(f"  Input:        {args.image or args.batch or '(none)'}")
    print(f"  Config file:  {args.config}")
    print(f"  Workspace:    {workspace}")
    print(f"  Face output:  {face_output}")
    print(f"  Skin output:  {skin_output}")
    print(f"  UV output:    {workspace / 'uv_map.png'}")
    print(f"  DAZ Studio:   {'SKIPPED' if args.skip_daz else 'Will be launched'}")
    print(f"  Batch mode:   {'YES' if args.batch else 'NO'}")
    print(f"  Preview:      {'YES' if args.preview else 'NO'}")
    if not args.skip_daz:
        print(f"  Output dir:   {config['output_dir']}")
    print()
    print("  Steps:")
    print(f"    1. Validate config ({args.config})")
    print(f"    2. Load image(s)")
    print("    3. Detect face (MediaPipe -> Haar fallback)")
    print(f"    4. Estimate pose and align face -> {face_output}")
    print(f"    5. Generate UV texture map -> {workspace / 'uv_map.png'}")
    print(f"    6. Skin tone analysis (adaptive HSV + KMeans) -> {skin_output}")
    if not args.skip_daz:
        print(f"    7. Launch DAZ Studio (up to {MAX_RETRIES} retries)")
        print(f"    8. Run daz_bridge.dsa, monitor heartbeat")
    print()
    print("=" * 60)
    return 0


def show_preview(args):
    import cv2
    from modules.face_processor import FaceProcessor
    from modules.skin_analyzer import SkinAnalyzer

    image = cv2.imread(args.image)
    if image is None:
        print(f"Cannot load image: {args.image}")
        return False

    face_proc = FaceProcessor({})
    preview = face_proc.draw_preview(image)

    skin_proc = SkinAnalyzer({})
    skin_overlay = skin_proc.get_skin_mask_preview(image)

    combined = cv2.hconcat([preview, skin_overlay])
    combined = cv2.resize(combined, (1200, 600))

    cv2.imshow("Preview: Face Detection (L) | Skin Mask (R)", combined)
    print("Preview window open. Press any key to close.")
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    return True


def run_single_pipeline(
    image_path: Path,
    config: dict,
    skip_daz: bool,
    progress_callback: Optional[Callable] = None,
    use_cache: bool = True,
    run_dir: Optional[Path] = None,
) -> Tuple[bool, Optional[str]]:
    logger = logging.getLogger(__name__)

    if run_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = image_path.stem[:40]
        run_dir = Path(config["workspace_dir"]) / f"{stem}_{timestamp}"

    try:
        run_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error(f"Cannot create run directory {run_dir}: {e}")
        return False, None

    face_output = run_dir / "face_source.png"
    skin_output = run_dir / "skin_data.json"
    uv_output = run_dir / "uv_map.png"

    if progress_callback:
        progress_callback(0, f"Processing: {image_path.name}")

    if use_cache:
        try:
            cached = get_cache_path(image_path)
            if cached:
                logger.info(f"Cache hit for {image_path.name}, reusing results")
                data = json.loads(cached.read_text())
                if Path(data.get("face_path", "")).exists() and Path(data.get("skin_path", "")).exists():
                    logger.info("Using cached face and skin data")
                    if progress_callback:
                        progress_callback(65, "Using cached results")
                    if not skip_daz:
                        daz_result = _run_daz(config, logger, progress_callback)
                        return daz_result.get("success", False), str(run_dir)
                    return True, str(run_dir)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Cache read failed (proceeding fresh): {e}")

    if progress_callback:
        progress_callback(5, "Module 1: Face Isolation & Alignment")

    try:
        from modules.face_processor import FaceProcessor
        face_config = config.get("face", {})
        face_processor = FaceProcessor(face_config)

        face_result = face_processor.process_with_pose(image_path, face_output, uv_output)
        if not face_result.get("success"):
            logger.error(f"Face processing failed: {face_result.get('error')}")
            return False, None
    except Exception as e:
        logger.error(f"Face processor crashed: {e}\n{traceback.format_exc()}")
        return False, None

    pose = face_result.get("pose", "unknown")
    logger.info(f"Face pose estimated: {pose}")
    if progress_callback:
        progress_callback(40, f"Module 1 done - face isolated (pose: {pose})")

    if progress_callback:
        progress_callback(40, "Module 2: Skin Tone Extraction")

    try:
        from modules.skin_analyzer import SkinAnalyzer
        skin_config = config.get("skin", {})
        skin_analyzer = SkinAnalyzer(skin_config)

        success = skin_analyzer.process(face_output, skin_output)
        if not success:
            logger.warning("Skin analysis failed, using fallback values")
            fallback = {
                "rgb": {"r": 200, "g": 160, "b": 120, "hex": "#c8a078"},
                "color_temperature": "neutral",
                "sample_count": 0,
                "sources": 0,
            }
            safe_json_write(skin_output, fallback, logger)
    except Exception as e:
        logger.error(f"Skin analyzer crashed: {e}\n{traceback.format_exc()}")
        fallback = {
            "rgb": {"r": 200, "g": 160, "b": 120, "hex": "#c8a078"},
            "color_temperature": "neutral",
            "sample_count": 0,
            "sources": 0,
        }
        safe_json_write(skin_output, fallback, logger)

    if progress_callback:
        progress_callback(65, "Module 2 done - skin tone extracted")

    if use_cache:
        write_cache(image_path, {
            "face_path": str(face_output),
            "skin_path": str(skin_output),
            "uv_path": str(uv_output),
            "pose": pose,
            "timestamp": datetime.now().isoformat(),
        })

    if not skip_daz:
        try:
            daz_result = _run_daz(config, logger, progress_callback)
            if not daz_result.get("success"):
                return False, None
        except Exception as e:
            logger.error(f"DAZ module crashed: {e}\n{traceback.format_exc()}")
            return False, None

    return True, str(run_dir)


def _run_daz(config: dict, logger, progress_callback=None):
    if progress_callback:
        progress_callback(65, "Module 3: DAZ Studio Automation")

    from modules.daz_orchestrator import DAZOrchestrator
    daz_config = config.get("daz", {})
    daz_config["workspace_dir"] = config["workspace_dir"]
    daz_config["output_dir"] = config["output_dir"]

    daz_orchestrator = DAZOrchestrator(daz_config)
    result = daz_orchestrator.run_automation()

    if result.get("success"):
        logger.info("DAZ Studio automation completed successfully")
        logger.info(f"Output saved to: {config['output_dir']}")
        if progress_callback:
            progress_callback(100, "Module 3 complete - DAZ automation done")
    else:
        logger.error(f"DAZ Studio failed: {result.get('error', 'Unknown error')}")

    return result


def run_pipeline(args, config, progress_callback=None):
    logger = logging.getLogger(__name__)

    workspace = Path(config["workspace_dir"])
    workspace.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = workspace / f"run_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    images = []
    if args.batch:
        batch_dir = Path(args.batch)
        if not batch_dir.is_dir():
            logger.error(f"Batch directory not found: {args.batch}")
            return False, None
        exts = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
        images = sorted([p for p in batch_dir.iterdir() if p.suffix.lower() in exts])
        if not images:
            logger.error(f"No image files found in {args.batch}")
            return False, None
        logger.info(f"Batch mode: found {len(images)} images in {batch_dir}")
    else:
        img_path = Path(args.image)
        if not img_path.exists():
            logger.error(f"Input image not found: {img_path}")
            return False, None
        images = [img_path]

    if args.multi_images:
        extra_paths = [Path(p.strip()) for p in args.multi_images.split(",") if p.strip()]
        for ep in extra_paths:
            if ep.exists() and ep not in images:
                images.append(ep)
        logger.info(f"Multi-image mode: {len(images)} total sources")

    parallel = args.parallel if hasattr(args, "parallel") else False
    use_cache = not args.no_cache

    if parallel and len(images) > 1 and args.batch:
        logger.info(f"Running parallel pipeline on {len(images)} images")
        with ThreadPoolExecutor(max_workers=min(len(images), 4)) as executor:
            futures = {}
            for img in images:
                img_run = run_dir / img.stem[:40]
                img_run.mkdir(parents=True, exist_ok=True)
                fut = executor.submit(
                    run_single_pipeline, img, config, args.skip_daz, None, use_cache, img_run
                )
                futures[fut] = img
            all_ok = True
            for future in as_completed(futures):
                img = futures[future]
                try:
                    ok, _ = future.result()
                    if not ok:
                        logger.error(f"Pipeline failed for {img.name}")
                        all_ok = False
                except Exception as e:
                    logger.error(f"Pipeline error for {img.name}: {e}")
                    all_ok = False
            return all_ok, str(run_dir) if all_ok else None
    else:
        all_ok = True
        for i, img in enumerate(images):
            logger.info("")
            logger.info(f"[{i+1}/{len(images)}] Processing: {img.name}")
            if progress_callback:
                progress_callback(0, f"[{i+1}/{len(images)}] {img.name}")

            args.image = str(img)

            if len(images) > 1 and use_cache:
                cached = get_cache_path(img)
                if cached and args.skip_daz:
                    logger.info(f"  Skipping {img.name} (cached, --skip-daz)")
                    continue

            img_run = run_dir if len(images) == 1 else (run_dir / img.stem[:40])
            ok, _ = run_single_pipeline(
                img, config, args.skip_daz, progress_callback, use_cache, run_dir=img_run
            )
            if not ok:
                if args.batch:
                    logger.error(f"  FAILED: {img.name}")
                    if not args.keep_going:
                        logger.error("  Aborting batch (use --keep-going to continue on error)")
                        return False, str(run_dir)
                else:
                    return False, str(run_dir)

    return all_ok, str(run_dir)


def main():
    parser = argparse.ArgumentParser(description="3D Character Generation Pipeline")
    parser.add_argument("--image", "-i", type=str, help="Input image path")
    parser.add_argument("--batch", "-b", type=str, help="Directory of images to batch process")
    parser.add_argument("--multi-images", "-m", type=str,
                        help="Comma-separated extra image paths for skin blending")
    parser.add_argument("--config", "-c", type=str, default="config.json", help="Config file path")
    parser.add_argument("--skip-daz", action="store_true", help="Skip DAZ Studio launch")
    parser.add_argument("--dry-run", action="store_true", help="Print plan without executing")
    parser.add_argument("--preview", action="store_true", help="Show face/skin preview window")
    parser.add_argument("--gui", action="store_true", help="Launch GUI progress window")
    parser.add_argument("--parallel", action="store_true", help="Parallel batch processing")
    parser.add_argument("--no-cache", action="store_true", help="Disable result caching")
    parser.add_argument("--keep-going", action="store_true",
                        help="Continue batch on individual failures")
    args = parser.parse_args()

    if not args.image and not args.batch and not args.preview:
        parser.error("One of --image, --batch, or --preview is required")

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Config file not found: {config_path}")
        return 1

    config = load_config(config_path)

    from modules.config_validator import ensure_validated
    ensure_validated(config, config_path)

    if args.dry_run:
        return print_dry_run_plan(args, config)

    if args.preview:
        if not args.image:
            print("--preview requires --image")
            return 1
        check_dependencies()
        show_preview(args)
        return 0

    check_dependencies()

    if args.gui:
        try:
            from gui import PipelineGUI
            gui = PipelineGUI()
            return gui.run()
        except ImportError:
            print("Tkinter not available. Install with: pip install tk")
            return 1

    logger = setup_logging(Path(config["logs_dir"]))

    logger.info("=" * 60)
    logger.info("3D Character Generation Pipeline Started")
    mode = "batch" if args.batch else ("multi-image" if args.multi_images else "single")
    logger.info(f"Mode: {mode}")
    logger.info("=" * 60)

    success, run_dir = run_pipeline(args, config)
    if success:
        logger.info("")
        logger.info("=" * 60)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY")
        logger.info(f"Output saved to: {run_dir}")
        logger.info("=" * 60)
    else:
        logger.error("PIPELINE FAILED")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
