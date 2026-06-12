"""
Batch CLI Mode — Process multiple blueprint images to DXF files.

Usage:
    python -m imagetocad --input ./blueprints/ --output ./dxf/
    python -m imagetocad --input ./blueprints/ --output ./dxf/ --unit mm --workers 4

Supports glob patterns and recursive directory scanning.
"""

import argparse
import sys
import os
import time
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np

from pipeline.vision_engine import VisionEngine
from pipeline.cad_engine import CADGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"}


def find_images(input_dir: str, recursive: bool = True) -> list:
    """
    Find all supported image files in a directory.

    Args:
        input_dir: Path to search directory.
        recursive: Whether to search subdirectories.

    Returns:
        Sorted list of image file paths.
    """
    input_path = Path(input_dir)
    if not input_path.is_dir():
        raise ValueError(f"Input directory does not exist: {input_dir}")

    pattern = "**/*" if recursive else "*"
    images = []
    for p in input_path.glob(pattern):
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS:
            images.append(p)
    return sorted(images)


def process_single_image(
    image_path: Path,
    output_dir: Path,
    vision_engine: VisionEngine,
    unit: str,
) -> dict:
    """
    Process a single blueprint image to DXF.

    Args:
        image_path: Path to the input image.
        output_dir: Output directory for DXF files.
        vision_engine: Initialized VisionEngine instance.
        unit: Scale unit (mm or in).

    Returns:
        Dict with status, path, and entity count.
    """
    try:
        image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if image is None:
            return {
                "file": str(image_path),
                "status": "error",
                "message": "Failed to decode image",
            }

        result = vision_engine.process(image)

        generator = CADGenerator(
            scale_factor=result.scale_factor,
            unit=unit,
            image_height=result.image_shape[0],
        )
        generator.build_from_result(result)

        output_path = output_dir / f"{image_path.stem}.dxf"
        generator.save(str(output_path))

        preview = generator.get_preview_data()

        return {
            "file": str(image_path),
            "status": "success",
            "output": str(output_path),
            "entities": preview.get("total_entities", 0),
        }

    except Exception as e:
        return {
            "file": str(image_path),
            "status": "error",
            "message": str(e),
        }


def main():
    parser = argparse.ArgumentParser(
        description="Batch process blueprint images to DXF files.",
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input directory containing blueprint images.",
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Output directory for DXF files.",
    )
    parser.add_argument(
        "--unit", "-u",
        default="mm",
        choices=["mm", "in"],
        help="Scale unit for output DXF (default: mm).",
    )
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=1,
        help="Number of parallel workers (default: 1).",
    )
    parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        default=True,
        help="Search subdirectories recursively (default: True).",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Disable recursive directory search.",
    )

    args = parser.parse_args()

    input_dir = args.input
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    recursive = not args.no_recursive
    images = find_images(input_dir, recursive)

    if not images:
        logger.warning(f"No supported images found in {input_dir}")
        sys.exit(0)

    logger.info(f"Found {len(images)} images to process.")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Workers: {args.workers}, Unit: {args.unit}")

    vision_engine = VisionEngine(
        line_merge_distance=8.0,
        line_merge_angle_tol=10.0,
        use_easyocr=True,
    )

    success_count = 0
    error_count = 0
    total_entities = 0
    start_time = time.time()

    if args.workers > 1:
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {
                executor.submit(
                    process_single_image, img, output_dir, vision_engine, args.unit
                ): img
                for img in images
            }
            for future in as_completed(futures):
                result = future.result()
                if result["status"] == "success":
                    success_count += 1
                    total_entities += result.get("entities", 0)
                    logger.info(
                        f"[{success_count}/{len(images)}] {result['file']} -> "
                        f"{result['output']} ({result['entities']} entities)"
                    )
                else:
                    error_count += 1
                    logger.error(
                        f"Failed: {result['file']} — {result['message']}"
                    )
    else:
        for i, img in enumerate(images, 1):
            result = process_single_image(img, output_dir, vision_engine, args.unit)
            if result["status"] == "success":
                success_count += 1
                total_entities += result.get("entities", 0)
                logger.info(
                    f"[{i}/{len(images)}] {result['file']} -> "
                    f"{result['output']} ({result['entities']} entities)"
                )
            else:
                error_count += 1
                logger.error(
                    f"Failed: {result['file']} — {result['message']}"
                )

    elapsed = time.time() - start_time
    logger.info(
        f"Batch complete: {success_count} succeeded, {error_count} failed, "
        f"{total_entities} total entities, {elapsed:.1f}s elapsed."
    )

    if error_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
