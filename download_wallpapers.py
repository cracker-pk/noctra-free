#!/usr/bin/env python3
"""Download existing PC and phone preview images for wallpaper IDs 0..1000."""

from __future__ import annotations

import argparse
import concurrent.futures
import socket
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = "https://noctrawallpapers.co.za/api/catalog/image?id=w{image_id}&type={image_type}"
USER_AGENT = "WallpaperPreviewDownloader/1.0"
IMAGE_TYPES = {
    "device-preview": "wallpaper-pc",
    "phone-preview": "wallpaper-phone",
}
MIME_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "image/avif": ".avif",
    "image/bmp": ".bmp",
}


def image_extension(content_type: str, data: bytes) -> str | None:
    mime_type = content_type.split(";", 1)[0].strip().lower()
    if mime_type in MIME_EXTENSIONS:
        return MIME_EXTENSIONS[mime_type]
    # Some servers omit or mislabel the image content type; recognize common image signatures.
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return ".webp"
    if len(data) >= 12 and data[4:8] == b"ftyp" and data[8:12] in {b"avif", b"avis"}:
        return ".avif"
    return None


def download_one(image_id: int, image_type: str, folder: Path) -> tuple[str, int, str]:
    url = BASE_URL.format(image_id=image_id, image_type=image_type)
    headers = {"User-Agent": USER_AGENT, "Accept": "image/*"}
    for attempt in range(3):
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=25) as response:
                data = response.read()
                extension = image_extension(response.headers.get("Content-Type", ""), data)
                if not extension:
                    return "skipped", image_id, "response was not an image"
                destination = folder / f"w{image_id}{extension}"
                if not destination.exists():
                    destination.write_bytes(data)
                return "downloaded", image_id, ""
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return "missing", image_id, ""
            if error.code not in {408, 425, 429, 500, 502, 503, 504} or attempt == 2:
                return "error", image_id, f"HTTP {error.code}"
            time.sleep(1.5 * (attempt + 1))
        except urllib.error.URLError as error:
            if isinstance(error.reason, socket.gaierror):
                return "error", image_id, "could not resolve the website hostname (DNS/network unavailable)"
            if attempt == 2:
                return "error", image_id, str(error)
            time.sleep(1.5 * (attempt + 1))
        except (TimeoutError, OSError) as error:
            if attempt == 2:
                return "error", image_id, str(error)
            time.sleep(1.5 * (attempt + 1))
    return "error", image_id, "request failed"


def main() -> int:
    parser = argparse.ArgumentParser(description="Download existing wallpaper preview images.")
    parser.add_argument("--start", type=int, default=0, help="First ID to check (default: 0)")
    parser.add_argument("--end", type=int, default=1000, help="Last ID to check, inclusive (default: 1000)")
    parser.add_argument("--workers", type=int, default=4, help="Parallel downloads (default: 4)")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent,
                        help="Folder in which the wallpaper-pc and wallpaper-phone folders are created")
    args = parser.parse_args()
    if args.start < 0 or args.end < args.start:
        parser.error("IDs must be non-negative, and --end must be at least --start")
    if args.workers < 1 or args.workers > 8:
        parser.error("--workers must be between 1 and 8")

    folders = {image_type: args.output / folder_name for image_type, folder_name in IMAGE_TYPES.items()}
    for folder in folders.values():
        folder.mkdir(parents=True, exist_ok=True)

    jobs = [
        (image_id, image_type, folder)
        for image_type, folder in folders.items()
        for image_id in range(args.start, args.end + 1)
    ]
    totals = {"downloaded": 0, "missing": 0, "skipped": 0, "error": 0}
    errors: list[str] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(download_one, image_id, image_type, folder)
                   for image_id, image_type, folder in jobs]
        for completed, future in enumerate(concurrent.futures.as_completed(futures), start=1):
            status, image_id, detail = future.result()
            totals[status] += 1
            if status == "error":
                errors.append(f"{image_id}: {detail}")
            if completed % 100 == 0 or completed == len(jobs):
                print(f"Checked {completed}/{len(jobs)} URLs...", flush=True)

    print(f"Checked {len(jobs)} image URLs (IDs {args.start} through {args.end}).")
    print(f"Downloaded: {totals['downloaded']}; missing: {totals['missing']}; "
          f"non-image responses: {totals['skipped']}; errors: {totals['error']}.")
    print(f"PC images: {folders['device-preview']}")
    print(f"Phone images: {folders['phone-preview']}")
    if errors:
        print("First errors: " + "; ".join(errors[:10]))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
