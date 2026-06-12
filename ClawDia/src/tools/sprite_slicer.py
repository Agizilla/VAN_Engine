import base64
from pathlib import Path

import cv2
import numpy as np


def slice_sprite_sheet(
    image_path: str,
    output_dir: str = "assets",
    threshold: int = 200,
    alpha_threshold: int = 240,
    padding: int = 10,
    sort_by: str = "position",
    base64_output: bool = False,
) -> list[dict]:
    """Slice a sprite sheet into individual transparent PNGs.

    Each contour in the source image is extracted, given an alpha channel
    (white → transparent), and saved as a separate PNG.

    Args:
        image_path: Path to the source sprite sheet (PNG/JPG).
        output_dir: Directory for sliced output PNGs (auto-created).
        threshold: Binary threshold for contour detection (0-255).
            Lower = more sensitive. Default 200.
        alpha_threshold: Pixels above this become transparent. Default 240.
        padding: Extra pixels around each sprite bounding box. Default 10.
        sort_by: "position" (left-to-right, top-to-bottom) or "area" (largest first).
        base64_output: If True, return base64 strings instead of saving files.

    Returns:
        List of dicts: {"index": int, "path": str | None, "base64": str | None,
                        "bounds": (x, y, w, h), "area": int}

    Raises:
        FileNotFoundError: if image_path doesn't exist.
        ValueError: if no contours found in the image.
    """
    src = Path(image_path)
    if not src.exists():
        raise FileNotFoundError(f"Sprite sheet not found: {image_path}")

    img = cv2.imread(str(src))
    if img is None:
        raise ValueError(f"Failed to load image: {image_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY_INV)

    contours, hierarchy = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        raise ValueError(f"No contours found in {image_path} (threshold={threshold})")

    # Filter out noise — min 20px area
    contours = [c for c in contours if cv2.contourArea(c) >= 20]
    if not contours:
        raise ValueError("All contours filtered as noise (< 20px area)")

    # Sort
    if sort_by == "position":
        contours.sort(key=lambda c: (cv2.boundingRect(c)[1], cv2.boundingRect(c)[0]))
    elif sort_by == "area":
        contours.sort(key=cv2.contourArea, reverse=True)

    out_path = Path(output_dir)
    results: list[dict] = []

    for i, contour in enumerate(contours):
        x, y, w, h = cv2.boundingRect(contour)

        x1 = max(0, x - padding)
        y1 = max(0, y - padding)
        x2 = min(img.shape[1], x + w + padding)
        y2 = min(img.shape[0], y + h + padding)

        crop = img[y1:y2, x1:x2]
        gray_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        _, alpha = cv2.threshold(gray_crop, alpha_threshold, 255, cv2.THRESH_BINARY_INV)

        b, g, r = cv2.split(crop)
        rgba = cv2.merge([b, g, r, alpha])

        entry = {
            "index": i,
            "path": None,
            "base64": None,
            "bounds": (x, y, w, h),
            "area": int(cv2.contourArea(contour)),
        }

        if base64_output:
            _, buffer = cv2.imencode(".png", rgba)
            entry["base64"] = base64.b64encode(buffer).decode("utf-8")
        else:
            out_path.mkdir(parents=True, exist_ok=True)
            filename = f"sprite_{i:04d}.png"
            filepath = out_path / filename
            cv2.imwrite(str(filepath), rgba)
            entry["path"] = str(filepath)

        results.append(entry)

    return results


# ─── CLI entry point ─────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(
        prog="sprite-slicer",
        description="Slice a sprite sheet into individual transparent PNGs.",
    )
    parser.add_argument("image", help="Path to the sprite sheet image")
    parser.add_argument("--output", "-o", default="assets", help="Output directory")
    parser.add_argument("--threshold", "-t", type=int, default=200,
                        help="Contour detection threshold (0-255, lower=more sensitive)")
    parser.add_argument("--padding", "-p", type=int, default=10,
                        help="Padding px around each sprite")
    parser.add_argument("--sort", choices=["position", "area"], default="position",
                        help="Sort order for extracted sprites")
    parser.add_argument("--base64", action="store_true",
                        help="Output base64 strings instead of saving files")
    parser.add_argument("--json", action="store_true",
                        help="Print results as JSON")

    args = parser.parse_args()

    try:
        sprites = slice_sprite_sheet(
            image_path=args.image,
            output_dir=args.output,
            threshold=args.threshold,
            padding=args.padding,
            sort_by=args.sort,
            base64_output=args.base64,
        )
    except (FileNotFoundError, ValueError) as e:
        print("ERROR: %s" % e)
        raise SystemExit(1) from e

    if args.json or args.base64:
        print(json.dumps(sprites, indent=2))
    else:
        print("Sliced %d sprites into %s/" % (len(sprites), args.output))
        for s in sprites:
            print("  [%04d] %s  (%dx%d, %dpx)" % (
                s["index"], Path(s["path"]).name,
                s["bounds"][2], s["bounds"][3], s["area"],
            ))
