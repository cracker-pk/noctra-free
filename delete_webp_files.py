#!/usr/bin/env python3
"""Delete WebP files from the PC and phone wallpaper folders after confirmation."""

from __future__ import annotations

import argparse
from pathlib import Path

FOLDER_NAMES = ("wallpaper-pc", "wallpaper-phone")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Find and delete WebP files in wallpaper-pc and wallpaper-phone."
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    files: list[Path] = []

    for folder_name in FOLDER_NAMES:
        folder = root / folder_name
        if folder.is_dir():
            files.extend(
                path for path in folder.rglob("*")
                if path.is_file() and path.suffix.lower() == ".webp"
            )

    files.sort(key=lambda path: str(path).lower())
    if not files:
        print("No WebP files found in wallpaper-pc or wallpaper-phone.")
        return 0

    print(f"Found {len(files)} WebP file(s):")
    for path in files:
        print(f"  {path}")
    answer = input("Type DELETE to permanently remove these files: ").strip()
    if answer != "DELETE":
        print("Cancelled; no files were deleted.")
        return 0

    deleted = 0
    errors: list[str] = []
    for path in files:
        try:
            path.unlink()
            deleted += 1
        except OSError as error:
            errors.append(f"{path}: {error}")

    print(f"Deleted {deleted} WebP file(s).")
    if errors:
        print(f"Could not delete {len(errors)} file(s):")
        for error in errors:
            print(f"  {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
