#!/usr/bin/env python3
"""Validate the supported-award index and all award profile files."""

from __future__ import annotations

import json
import sys

from award_profiles import load_index, validate_all


def main() -> int:
    errors = validate_all()
    index = load_index()
    result = {
        "valid": not errors,
        "profile_count": len(index.get("supported_awards", [])),
        "errors": errors,
    }
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

