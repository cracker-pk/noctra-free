#!/usr/bin/env python3
"""Extract request URLs from a browser DevTools HAR export."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def find_requests(data: Any) -> list[dict[str, Any]]:
    """Return HAR request objects in their recorded order."""
    if isinstance(data, dict):
        log = data.get("log")
        if isinstance(log, dict) and isinstance(log.get("entries"), list):
            requests = []
            for entry in log["entries"]:
                if isinstance(entry, dict) and isinstance(entry.get("request"), dict):
                    requests.append(entry["request"])
            return requests

        # Also accept Chrome DevTools Protocol Network logs, if saved as JSON.
        messages = data.get("messages")
        if isinstance(messages, list):
            requests = []
            for message in messages:
                if not isinstance(message, dict):
                    continue
                payload = message.get("message", message)
                if not isinstance(payload, dict):
                    continue
                request = payload.get("params", {}).get("request") if isinstance(payload.get("params"), dict) else None
                if isinstance(request, dict):
                    requests.append(request)
            return requests
    raise ValueError("This file does not look like a HAR export or DevTools Network log.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract request URLs from a DevTools Network HAR export."
    )
    parser.add_argument("har_file", help="HAR file exported from the browser Network panel")
    parser.add_argument("output", nargs="?", default="urls.txt", help="Output text file (default: urls.txt)")
    parser.add_argument("--keep-duplicates", action="store_true", help="Keep repeated request URLs")
    args = parser.parse_args()

    data = json.loads(Path(args.har_file).read_text(encoding="utf-8-sig"))
    requests = find_requests(data)
    urls = [request.get("url", "").strip() for request in requests]
    urls = [url for url in urls if url]
    if not args.keep_duplicates:
        urls = list(dict.fromkeys(urls))

    output_path = Path(args.output)
    output_path.write_text("\n".join(urls) + ("\n" if urls else ""), encoding="utf-8")
    print(f"Saved {len(urls)} URL(s) to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
