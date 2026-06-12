#!/usr/bin/env python3
"""
Optical Illusion Forge – Advanced Geometric Packing Engine
Author: AI Orchestrator
Version: 2.0.0
"""

import os
import argparse
import numpy as np
import cv2
from PIL import Image
from scipy.spatial import KDTree
from pathlib import Path
import random

# ------------------------------
# 1. ADVANCED COMPUTER VISION UTILITIES
# ------------------------------
def load_macro(path, target_size=(2048, 2048)):
    """Loads and normalizes the macro distance target."""
    img = Image.open(path).convert('L')
    img = img.resize(target_size, Image.Resampling.LANCZOS)
    return np.array(img) / 255.0  # 0.0 (Black) to 1.0 (White)

def compute_guidance_fields(macro):
    """Computes Sobel gradient directions and local luminance maps."""
    smoothed = cv2.GaussianBlur(macro, (5, 5), 0)
    gx = cv2.Sobel(smoothed, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(smoothed, cv2.CV_64F, 0, 1, ksize=3)

    magnitude = np.hypot(gx, gy)
    direction = np.arctan2(gy, gx) + (np.pi / 2.0)
    return magnitude, direction

def get_asset_principal_angle(mask):
    """Uses image moments to determine the true orientation of a micro asset."""
    moments = cv2.moments(mask.astype(np.uint8))
    m11 = moments['mu11']
    m20 = moments['mu20']
    m02 = moments['mu02']

    if abs(m20 - m02) < 1e-5:
        return 0.0
    angle = 0.5 * np.arctan2(2 * m11, m20 - m02)
    return angle

# ------------------------------
# 2. MICRO ASSET MANAGEMENT
# ------------------------------
def load_assets(asset_dir):
    """Loads transparent PNGs and profiles their physical dimensions and moments."""
    assets = []
    for f in Path(asset_dir).glob('*.png'):
        try:
            img = Image.open(f).convert('RGBA')
            mask = np.array(img)[:, :, 3] > 50

            if not np.any(mask):
                continue

            y_indices, x_indices = np.where(mask)
            x_min, x_max = x_indices.min(), x_indices.max()
            y_min, y_max = y_indices.min(), y_indices.max()

            cropped_img = img.crop((x_min, y_min, x_max + 1, y_max + 1))
            cropped_mask = mask[y_min:y_max + 1, x_min:x_max + 1]

            base_angle = get_asset_principal_angle(cropped_mask)
            fill_factor = np.sum(cropped_mask) / cropped_mask.size
            radius = np.sqrt(cropped_mask.size) / 2.0

            assets.append({
                'img': cropped_img,
                'mask': cropped_mask,
                'base_angle': base_angle,
                'fill_factor': fill_factor,
                'radius': radius
            })
        except Exception as e:
            print(f"Skipping corrupt or invalid asset {f.name}: {e}")

    assets.sort(key=lambda a: a['fill_factor'])
    return assets

# ------------------------------
# 3. DETERMINISTIC SPATIAL PACKING ENGINE
# ------------------------------
def clip(val, min_v, max_v):
    return max(min_v, min(val, max_v))

def generate_illusion(macro, assets, grad_dir, output_size, min_r=8, max_r=48, k_candidates=30):
    """
    Packs assets smoothly across continuous space via adaptive Poisson-Disk Sampling.
    Darker areas get smaller, higher-density assets; lighter areas get larger, sparse assets.
    """
    h, w = macro.shape
    canvas = Image.new('RGBA', output_size, (255, 255, 255, 255))

    placed_points = []
    placed_radii = []
    spatial_tree = None

    active_list = []
    rng = random.Random(42)

    print("Initiating adaptive spatial distribution...")
    y_indices, x_indices = np.where(macro < 0.7)
    if len(y_indices) > 0:
        for _ in range(100):
            idx = rng.randint(0, len(y_indices) - 1)
            pt = (x_indices[idx], y_indices[idx])
            active_list.append(pt)

    if not active_list:
        active_list.append((w // 2, h // 2))

    while active_list:
        idx = rng.randint(0, len(active_list) - 1)
        cx, cy = active_list.pop(idx)

        local_lum = macro[int(clip(cy, 0, h - 1)), int(clip(cx, 0, w - 1))]

        if local_lum > 0.95:
            continue

        r = min_r + (max_r - min_r) * local_lum

        for _ in range(k_candidates):
            angle = rng.uniform(0, 2 * np.pi)
            distance = rng.uniform(r * 1.1, r * 2.5)
            nx = cx + distance * np.cos(angle)
            ny = cy + distance * np.sin(angle)

            if 0 <= nx < w and 0 <= ny < h:
                nlum = macro[int(ny), int(nx)]
                target_r = min_r + (max_r - min_r) * nlum

                if len(placed_points) > 0:
                    if spatial_tree is None:
                        spatial_tree = KDTree(placed_points)

                    neighbors = spatial_tree.query_ball_point([nx, ny], target_r * 1.5)
                    collision = False
                    for n_idx in neighbors:
                        dist = np.hypot(nx - placed_points[n_idx][0], ny - placed_points[n_idx][1])
                        if dist < (target_r + placed_radii[n_idx]) * 0.82:
                            collision = True
                            break
                    if collision:
                        continue

                pt = (nx, ny)
                placed_points.append(pt)
                placed_radii.append(target_r)
                active_list.append(pt)
                spatial_tree = None

                target_fill = 1.0 - nlum
                best_asset = min(assets, key=lambda a: abs(a['fill_factor'] - target_fill))

                target_angle = grad_dir[int(ny), int(nx)]
                rotation_angle = target_angle - best_asset['base_angle']

                transformed_img = best_asset['img'].rotate(
                    -np.degrees(rotation_angle), expand=True, resample=Image.Resampling.BICUBIC)

                scale_factor = (target_r * 2.0) / max(transformed_img.width, transformed_img.height)
                final_w = int(max(1, transformed_img.width * scale_factor))
                final_h = int(max(1, transformed_img.height * scale_factor))
                transformed_img = transformed_img.resize((final_w, final_h), Image.Resampling.LANCZOS)

                px = int(nx - final_w // 2)
                py = int(ny - final_h // 2)
                canvas.paste(transformed_img, (px, py), transformed_img)

    return canvas

# ------------------------------
# 4. ORCHESTRATION PIPELINE
# ------------------------------
def main():
    parser = argparse.ArgumentParser(description="Optical Illusion Forge v2.0")
    parser.add_argument('--macro', required=True, help='Path to distance silhouette image')
    parser.add_argument('--micro-dir', required=True, help='Directory containing transparent close-up PNGs')
    parser.add_argument('--output', default='illusion_output.png', help='Output filepath')
    parser.add_argument('--size', type=int, default=2048, help='Canvas bounding square constraint')
    args = parser.parse_args()

    if not os.path.exists(args.micro_dir):
        print(f"Error: Asset directory '{args.micro_dir}' does not exist.")
        return

    print("[1/4] Loading high-contrast macro frame...")
    macro = load_macro(args.macro, (args.size, args.size))

    print("[2/4] Resolving vector fields and edge trajectories...")
    _, grad_dir = compute_guidance_fields(macro)

    print("[3/4] Parsing structural attributes of micro library...")
    assets = load_assets(args.micro_dir)
    if not assets:
        print("Execution halted: No valid micro assets resolved.")
        return
    print(f"Loaded {len(assets)} unique structural micro assets.")

    print("[4/4] Executing spatial geometric composition pipeline...")
    final_canvas = generate_illusion(
        macro=macro,
        assets=assets,
        grad_dir=grad_dir,
        output_size=(args.size, args.size),
        min_r=10,
        max_r=56
    )

    final_canvas.convert('RGB').save(args.output, "PNG")
    print(f"Sovereign composition complete. File deployed to: {args.output}")


if __name__ == '__main__':
    main()
