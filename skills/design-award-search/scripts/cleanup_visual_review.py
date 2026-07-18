#!/usr/bin/env python3
"""Safely remove only assets created by verify_visual_evidence.py --review-dir."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REVIEW_MARKER = ".design-award-visual-review.json"
SCHEMA = "design-award-visual-review/v1"


def cleanup(directory: str | Path) -> dict:
    root = Path(directory).expanduser().resolve()
    marker = root / REVIEW_MARKER
    if not root.is_dir() or not marker.is_file() or marker.is_symlink():
        raise ValueError("not a marked design-award visual-review directory")
    payload = json.loads(marker.read_text(encoding="utf-8"))
    if payload.get("schema") != SCHEMA or Path(payload.get("directory", "")).resolve() != root:
        raise ValueError("visual-review marker does not match this directory")

    assets = payload.get("assets", [])
    if not isinstance(assets, list):
        raise ValueError("visual-review marker assets must be a list")

    expected_names = {REVIEW_MARKER}
    validated: list[tuple[str, Path]] = []
    for record in assets:
        if not isinstance(record, dict):
            raise ValueError("invalid asset record in visual-review marker")
        filename = record.get("filename", "")
        if not filename or Path(filename).name != filename:
            raise ValueError("unsafe filename in visual-review marker")
        path = (root / filename).resolve()
        if path.parent != root:
            raise ValueError("asset path escapes visual-review directory")
        if path.is_symlink():
            raise ValueError("refusing to remove a symlink from visual-review directory")
        expected_names.add(filename)
        validated.append((filename, path))

    unexpected = sorted(path.name for path in root.iterdir() if path.name not in expected_names)
    if unexpected:
        raise ValueError(
            "visual-review directory contains unrelated files: " + ", ".join(unexpected)
        )

    removed: list[str] = []
    missing: list[str] = []
    for filename, path in validated:
        if path.is_file():
            path.unlink()
            removed.append(filename)
        else:
            missing.append(filename)

    marker.unlink()
    try:
        root.rmdir()
        directory_removed = True
    except OSError:
        directory_removed = False
    return {
        "status": "cleaned" if directory_removed else "partial_cleanup",
        "removed": removed,
        "missing": missing,
        "directory_removed": directory_removed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("review_dir", help="Marked review directory to clean")
    args = parser.parse_args()
    try:
        result = cleanup(args.review_dir)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {
                    "status": "cleanup_refused",
                    "reason": type(exc).__name__,
                    "detail": str(exc),
                },
                ensure_ascii=False,
            )
        )
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["directory_removed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
