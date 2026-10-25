#!/usr/bin/env python3
"""Create enhanced PC, tablet, and mobile wallpaper files for the static gallery."""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import shutil
from pathlib import Path
from urllib.parse import quote

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "public"
INPUTS = {"pc": ROOT / "wallpaper-pc", "mobile": ROOT / "wallpaper-phone"}
SIZES = {"pc": (3840, 2160), "tablet": (3840, 2560), "mobile": (2160, 3840)}
SUPPORTED = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


def natural_key(value: str):
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", value)]


def find_images(folder: Path) -> dict[str, Path]:
    found = {}
    if folder.is_dir():
        for path in folder.rglob("*"):
            if path.is_file() and path.suffix.lower() in SUPPORTED:
                found[path.stem.lower()] = path
    return found


def load_rgb(path: Path) -> Image.Image:
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
    image = ImageEnhance.Color(image).enhance(1.025)
    return ImageEnhance.Contrast(image).enhance(1.025)


def make_variant(source: Image.Image, destination: Path, size: tuple[int, int], quality: int) -> None:
    image = ImageOps.fit(source, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    image = image.filter(ImageFilter.UnsharpMask(radius=1.4, percent=110, threshold=3))
    image.save(destination, "WEBP", quality=quality, method=3)


def make_thumbnail(source: Image.Image, destination: Path, size: tuple[int, int]) -> None:
    thumb = ImageOps.contain(source, size, method=Image.Resampling.LANCZOS)
    thumb = thumb.filter(ImageFilter.UnsharpMask(radius=0.8, percent=90, threshold=4))
    thumb.save(destination, "WEBP", quality=72, method=3)


def safe_file_stem(stem: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", stem)


def process_one(image_id: str, pc_path: Path, mobile_path: Path, quality: int):
    pc_image = load_rgb(pc_path)
    mobile_image = load_rgb(mobile_path)
    pc_size, mobile_size = pc_image.size, mobile_image.size
    stem = safe_file_stem(image_id)
    variants = {}
    for kind, size in SIZES.items():
        source = mobile_image if kind == "mobile" else pc_image
        relative = Path("images") / "formats" / kind / f"{stem}.webp"
        destination = PUBLIC / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        make_variant(source, destination, size, quality)
        variants[kind] = {"src": quote(relative.as_posix(), safe="/"), "width": size[0], "height": size[1]}

    pc_thumb = Path("images") / "thumbs" / "pc" / f"{stem}.webp"
    mobile_thumb = Path("images") / "thumbs" / "mobile" / f"{stem}.webp"
    for thumb in (pc_thumb, mobile_thumb):
        (PUBLIC / thumb).parent.mkdir(parents=True, exist_ok=True)
    make_thumbnail(pc_image, PUBLIC / pc_thumb, (1000, 620))
    make_thumbnail(mobile_image, PUBLIC / mobile_thumb, (620, 1100))
    return {
        "id": image_id,
        "variants": variants,
        "sourcePc": list(pc_size),
        "sourceMobile": list(mobile_size),
        "pcThumb": quote(pc_thumb.as_posix(), safe="/"),
        "mobileThumb": quote(mobile_thumb.as_posix(), safe="/"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Upscale each wallpaper into PC, tablet, and mobile WebP files.")
    parser.add_argument("--quality", type=int, default=78, help="WebP quality from 1 to 100 (default: 78)")
    parser.add_argument("--workers", type=int, default=6, help="Images to process in parallel (default: 6)")
    parser.add_argument("--clean", action="store_true", help="Remove the existing generated public output before rebuilding")
    args = parser.parse_args()
    if not 1 <= args.quality <= 100:
        parser.error("--quality must be between 1 and 100")
    if not 1 <= args.workers <= 8:
        parser.error("--workers must be between 1 and 8")
    if args.clean and PUBLIC.exists():
        shutil.rmtree(PUBLIC)
    PUBLIC.mkdir(parents=True, exist_ok=True)

    pc_files, mobile_files = find_images(INPUTS["pc"]), find_images(INPUTS["mobile"])
    ids = sorted(set(pc_files) | set(mobile_files), key=natural_key)
    if not ids:
        raise SystemExit("No source images found in wallpaper-pc or wallpaper-phone.")

    completed = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        jobs = {
            pool.submit(process_one, image_id, pc_files.get(image_id) or mobile_files[image_id],
                        mobile_files.get(image_id) or pc_files[image_id], args.quality): image_id
            for image_id in ids
        }
        for count, future in enumerate(concurrent.futures.as_completed(jobs), start=1):
            image_id = jobs[future]
            completed[image_id] = future.result()
            if count % 25 == 0 or count == len(ids):
                print(f"Processed {count}/{len(ids)} wallpaper IDs...", flush=True)

    catalog = {"pc": [], "phone": []}
    for image_id in ids:
        item = completed[image_id]
        common = {
            "filename": image_id,
            "title": f"Wallpaper {image_id}",
            "variants": item["variants"],
            "sourcePc": item["sourcePc"],
            "sourceMobile": item["sourceMobile"],
        }
        catalog["pc"].append({**common, "number": len(catalog["pc"]) + 1, "src": item["pcThumb"]})
        catalog["phone"].append({**common, "number": len(catalog["phone"]) + 1, "src": item["mobileThumb"]})

    public_data = "window.GALLERY_DATA = " + json.dumps(catalog, separators=(",", ":")) + ";\n"
    (PUBLIC / "gallery-data.js").write_text(public_data, encoding="utf-8")
    root_catalog = json.loads(json.dumps(catalog))
    for category in root_catalog.values():
        for item in category:
            item["src"] = "public/" + item["src"]
            for variant in item["variants"].values():
                variant["src"] = "public/" + variant["src"]
    (ROOT / "gallery-data.js").write_text("window.GALLERY_DATA = " + json.dumps(root_catalog, separators=(",", ":")) + ";\n", encoding="utf-8")
    for filename in ("index.html", "styles.css", "app.js"):
        shutil.copy2(ROOT / filename, PUBLIC / filename)
    (PUBLIC / ".nojekyll").write_text("", encoding="utf-8")

    total = sum(path.stat().st_size for path in PUBLIC.rglob("*") if path.is_file())
    print(f"Created {len(ids) * 3} upscaled format files and {len(ids) * 2} previews.")
    print(f"PC: 3840x2160; tablet: 3840x2560; mobile: 2160x3840; WebP quality {args.quality}.")
    print(f"Public site files total: {total / 1024 / 1024:.1f} MB at {PUBLIC}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
