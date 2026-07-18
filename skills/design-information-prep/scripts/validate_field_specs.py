#!/usr/bin/env python3
"""Validate all local design-award submission field specifications."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from field_spec_utils import AWARD_DIR, load_json, validate_spec


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate design award field specifications.")
    parser.add_argument("paths", nargs="*", help="Optional specification JSON files")
    parser.add_argument("--pretty", action="store_true", help="Indent JSON output")
    args = parser.parse_args()
    paths = [Path(value) for value in args.paths] if args.paths else sorted(AWARD_DIR.glob("*.json"))
    errors: list[str] = []
    checked: list[str] = []
    for path in paths:
        try:
            spec = load_json(path)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"{path}: {exc}")
            continue
        errors.extend(validate_spec(spec, str(path)))
        checked.append(str(spec.get("award_id", path.stem)))
    result = {"valid": not errors, "spec_count": len(checked), "award_ids": checked, "errors": errors}
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2 if args.pretty else None)
    sys.stdout.write("\n")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

