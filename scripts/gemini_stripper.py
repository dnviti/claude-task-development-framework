#!/usr/bin/env python3
"""
Remove the Gemini sparkle watermark from images using inpainting.

The Gemini watermark is a small four-pointed star typically located
in the bottom-right corner of generated images. It appears as a
desaturated/lighter patch blending into the background.

Usage:
    python remove_gemini_logo.py image1.png image2.jpg ...
    python remove_gemini_logo.py *.png
    python remove_gemini_logo.py --dir ./my_images
    python remove_gemini_logo.py --dir ./my_images --output-dir ./cleaned
"""

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np


def find_gemini_sparkle(image: np.ndarray) -> np.ndarray | None:
    """
    Detect the Gemini sparkle watermark in the bottom-right corner.

    Uses saturation-drop detection: the sparkle is a desaturated four-pointed
    star against the local background. Falls back to luminance contrast for
    grayscale or low-saturation images.

    Returns a full-image-sized binary mask, or None if not found.
    """
    h, w = image.shape[:2]
    # Corner region: ~15% of image from bottom-right, minimum 150px
    corner_size = max(int(min(h, w) * 0.18), 150)
    roi_y = h - corner_size
    roi_x = w - corner_size
    roi = image[roi_y:, roi_x:]
    roi_h, roi_w = roi.shape[:2]

    mask_full = np.zeros((h, w), dtype=np.uint8)

    # --- Primary: saturation drop ---
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    sat = hsv[:, :, 1].astype(np.float32)
    # Large blur to estimate local background saturation
    blur_k = max(roi_h // 4, 31) | 1  # ensure odd
    local_sat = cv2.GaussianBlur(sat, (blur_k, blur_k), 0)
    sat_drop = local_sat - sat  # positive where less saturated than surroundings

    # --- Secondary: luminance contrast ---
    lab = cv2.cvtColor(roi, cv2.COLOR_BGR2LAB)
    l_chan = lab[:, :, 0].astype(np.float32)
    local_l = cv2.GaussianBlur(l_chan, (blur_k, blur_k), 0)
    l_diff = np.abs(l_chan - local_l)

    # Combine both signals
    combined_signal = np.maximum(sat_drop, l_diff * 1.5)

    # Try progressive thresholds from strict to loose
    for thresh in [35, 25, 18, 12]:
        binary = (combined_signal > thresh).astype(np.uint8) * 255

        # Morphological cleanup
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)

        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        candidates = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            min_side = min(roi_h, roi_w)

            # Size filter: sparkle is small but visible
            min_area = min_side * min_side * 0.005
            max_area = min_side * min_side * 0.30
            if area < min_area or area > max_area:
                continue

            # Aspect ratio: sparkle is roughly equilateral
            x, y, bw, bh = cv2.boundingRect(cnt)
            aspect = max(bw, bh) / (min(bw, bh) + 1e-5)
            if aspect > 2.5:
                continue

            # Score by proximity to bottom-right corner of the ROI
            # (the Gemini watermark is always near the corner)
            cx = (x + bw / 2) / roi_w  # normalized 0-1
            cy = (y + bh / 2) / roi_h
            corner_score = (cx + cy) / 2  # higher = closer to bottom-right

            candidates.append((corner_score, area, cnt, x, y, bw, bh))

        if not candidates:
            continue  # try next threshold

        # Pick the candidate closest to the bottom-right corner
        best = max(candidates, key=lambda c: c[0])
        _, area, cnt, x, y, bw, bh = best

        # Build mask from this contour
        roi_mask = np.zeros((roi_h, roi_w), dtype=np.uint8)
        cv2.drawContours(roi_mask, [cnt], -1, 255, -1)

        # Dilate to cover antialiased edges and semi-transparent halo
        sparkle_size = max(bw, bh)
        dilate_r = max(13, sparkle_size // 4)
        dilate_kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (dilate_r, dilate_r)
        )
        roi_mask = cv2.dilate(roi_mask, dilate_kernel, iterations=2)

        # Smooth mask edges for cleaner inpainting
        roi_mask = cv2.GaussianBlur(roi_mask, (9, 9), 0)
        _, roi_mask = cv2.threshold(roi_mask, 40, 255, cv2.THRESH_BINARY)

        mask_full[roi_y:, roi_x:] = roi_mask
        return mask_full

    return None


def remove_watermark(image: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Remove the watermark region using dual inpainting with blending."""
    radius = 12
    result_telea = cv2.inpaint(image, mask, inpaintRadius=radius, flags=cv2.INPAINT_TELEA)
    result_ns = cv2.inpaint(image, mask, inpaintRadius=radius, flags=cv2.INPAINT_NS)

    # Blend based on local edge density
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 30, 100)
    edge_region = cv2.dilate(edges, np.ones((5, 5), np.uint8), iterations=2)
    blend = cv2.GaussianBlur(edge_region.astype(np.float32) / 255, (15, 15), 0)
    blend = blend[:, :, np.newaxis]

    result = (result_ns * blend + result_telea * (1 - blend)).astype(np.uint8)
    return result


def process_image(input_path: Path, output_path: Path) -> bool:
    """Process a single image: detect and remove Gemini watermark."""
    image = cv2.imread(str(input_path), cv2.IMREAD_UNCHANGED)
    if image is None:
        print(f"  [SKIP] Cannot read: {input_path}")
        return False

    has_alpha = len(image.shape) == 3 and image.shape[2] == 4
    if has_alpha:
        alpha = image[:, :, 3]
        bgr = image[:, :, :3]
    else:
        bgr = image

    mask = find_gemini_sparkle(bgr)
    if mask is None:
        print(f"  [SKIP] No Gemini watermark detected: {input_path}")
        return False

    masked_px = cv2.countNonZero(mask)
    pct = masked_px / (mask.shape[0] * mask.shape[1]) * 100

    result = remove_watermark(bgr, mask)

    if has_alpha:
        result = np.dstack([result, alpha])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), result)
    print(f"  [DONE] {input_path.name} -> {output_path.name}  ({pct:.2f}% masked)")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Remove Gemini sparkle watermark from images."
    )
    parser.add_argument("images", nargs="*", help="Image files to process")
    parser.add_argument("--dir", "-d", type=Path, help="Process all images in directory")
    parser.add_argument("--output-dir", "-o", type=Path, help="Output directory")
    parser.add_argument(
        "--suffix", "-s", default="_clean",
        help="Suffix for output filenames (default: _clean). Use '' to overwrite."
    )
    parser.add_argument("--recursive", "-r", action="store_true", help="Recurse into subdirs")
    args = parser.parse_args()

    extensions = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"}
    files: list[Path] = []

    if args.dir:
        pattern = "**/*" if args.recursive else "*"
        files = [f for f in args.dir.glob(pattern) if f.suffix.lower() in extensions and f.is_file()]
    if args.images:
        files += [Path(f) for f in args.images]

    if not files:
        print("No images specified. Use --help for usage.")
        sys.exit(1)

    print(f"Processing {len(files)} image(s)...\n")
    success = 0
    for img_path in sorted(files):
        if args.output_dir:
            out_path = args.output_dir / img_path.name
        elif args.suffix:
            out_path = img_path.with_stem(img_path.stem + args.suffix)
        else:
            out_path = img_path

        if process_image(img_path, out_path):
            success += 1

    print(f"\nDone: {success}/{len(files)} images cleaned.")


if __name__ == "__main__":
    main()
