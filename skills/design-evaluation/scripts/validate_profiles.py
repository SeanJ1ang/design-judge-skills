#!/usr/bin/env python3
"""Validate all design-evaluation configuration profiles."""

from __future__ import annotations

import argparse
import json
import sys

from evaluation_profiles import (
    load_award_lenses,
    load_classification,
    load_maturity,
    validate_profiles,
)
from benchmark_profiles import (
    load_if_manifest,
    load_if_student_manifest,
    load_idea_manifest,
    load_red_dot_manifest,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate design-evaluation profiles and weight totals."
    )
    parser.add_argument("--pretty", action="store_true", help="Indent JSON output")
    args = parser.parse_args()

    try:
        errors = validate_profiles()
        classification = load_classification()
        summary = {
            "valid": not errors,
            "errors": errors,
            "maturity_profiles": {
                maturity: load_maturity(maturity)["design_weights"]
                for maturity in ("student_concept", "mature_work")
            },
            "discipline_count": len(classification["disciplines"]),
            "sector_count": len(classification["sectors"]),
            "focus_tag_count": len(classification["focus_tags"]),
            "award_lenses": sorted(load_award_lenses()),
            "if_benchmark": load_if_manifest()["dataset"],
            "if_student_benchmark": {
                "dataset": load_if_student_manifest()["dataset"],
                "maturity_gate": load_if_student_manifest()["maturity_gate"],
            },
            "red_dot_benchmark": load_red_dot_manifest()["dataset"],
            "idea_benchmark": {
                "dataset": load_idea_manifest()["dataset"],
                "maturity_gate": load_idea_manifest()["maturity_gate"],
            },
        }
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    json.dump(
        summary,
        sys.stdout,
        ensure_ascii=False,
        indent=2 if args.pretty else None,
    )
    sys.stdout.write("\n")
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
