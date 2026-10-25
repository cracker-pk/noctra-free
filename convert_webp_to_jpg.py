#!/usr/bin/env python3
"""Convert WebP images in the PC and phone wallpaper folders to JPEG."""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError as error:
    raise SystemExit("Pillow is required. Install it with: python -m pip install Pillow") from error

FOLDER_NAMES = ("wallpaper-pc", "wallpaper-phone")


def to_rgb(image: Image.Image) -> Image.Image:
    """Convert to RGB, placing transparent pixels on a white background."""
    image = ImageOps.exif_transpose(image)
    if "A" in image.getbands() or "transparency" in image.info:
        rgba = image.convert("RGBA")
        background = Image.new("RGBA", rgba.size, "white")
        return Image.alpha_composite(background, rgba).convert("RGB")
    return image.convert("RGB")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert WebP files in wallpaper-pc and wallpaper-phone into JPG files."
    )
    parser.add_argument("--quality", type=int, default=95, help="JPEG quality from 1 to 100 (default: 95)")
    parser.add_argument("--overwrite", action="store_true", help="Replace JPG files that already exist")
    args = parser.parse_args()
    if not 1 <= args.quality <= 100:
        parser.error("--quality must be between 1 and 100")

    root = Path(__file__).resolve().parent
    converted = 0
    skipped = 0
    errors: list[str] = []

    for folder_name in FOLDER_NAMES:
        folder = root / folder_name
        if not folder.is_dir():
            print(f"Folder not found, skipping: {folder}")
            continue
        webp_files = sorted(
            (path for path in folder.rglob("*") if path.is_file() and path.suffix.lower() == ".webp"),
            key=lambda path: str(path).lower(),
        )
        for source in webp_files:
            destination = source.with_suffix(".jpg")
            if destination.exists() and not args.overwrite:
                skipped += 1
                continue
            try:
                with Image.open(source) as image:
                    rgb = to_rgb(image)
                    rgb.save(destination, format="JPEG", quality=args.quality, optimize=True)
                converted += 1
            except Exception as error:  # report a bad file and continue with the rest
                errors.append(f"{source}: {error}")

    print(f"Converted {converted} WebP file(s) to JPG.")
    if skipped:
        print(f"Skipped {skipped} file(s) because the JPG already exists; use --overwrite to replace it.")
    if errors:
        print(f"Could not convert {len(errors)} file(s):")
        for error in errors[:20]:
            print(f"  {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
