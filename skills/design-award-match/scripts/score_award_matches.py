#!/usr/bin/env python3
"""Calculate transparent design-award fit scores from structured ratings."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


WEIGHTS = {
    "category_track_fit": 30,
    "criteria_alignment": 30,
    "award_positioning_fit": 15,
    "competitive_evidence": 15,
    "entry_feasibility": 10,
}

ELIGIBILITY = {"eligible", "unknown", "ineligible"}
CONFIDENCE = {"high", "medium", "low"}


def base_label(score: float) -> str:
    if score >= 80:
        return "Priority"
    if score >= 65:
        return "Strong candidate"
    if score >= 50:
        return "Conditional"
    return "Weak fit"


def score_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    name = str(candidate.get("award", "")).strip()
    if not name:
        raise ValueError("Each candidate requires a non-empty 'award'.")

    eligibility = str(candidate.get("eligibility", "unknown")).lower()
    if eligibility not in ELIGIBILITY:
        raise ValueError(
            f"{name}: eligibility must be eligible, unknown, or ineligible."
        )

    confidence = str(candidate.get("confidence", "low")).lower()
    if confidence not in CONFIDENCE:
        raise ValueError(f"{name}: confidence must be high, medium, or low.")

    ratings = candidate.get("ratings")
    if not isinstance(ratings, dict):
        raise ValueError(f"{name}: 'ratings' must be an object.")

    contributions: dict[str, float] = {}
    for dimension, weight in WEIGHTS.items():
        if dimension not in ratings:
            raise ValueError(f"{name}: missing rating '{dimension}'.")
        value = ratings[dimension]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{name}: rating '{dimension}' must be numeric.")
        if not 0 <= float(value) <= 5:
            raise ValueError(f"{name}: rating '{dimension}' must be from 0 to 5.")
        contributions[dimension] = round((float(value) / 5) * weight, 2)

    score = round(sum(contributions.values()), 2)
    label = base_label(score)
    if eligibility == "ineligible":
        label = "Excluded"
    elif eligibility == "unknown" and label in {"Priority", "Strong candidate"}:
        label = "Conditional"

    result = dict(candidate)
    result.update(
        {
            "eligibility": eligibility.capitalize(),
            "confidence": confidence.capitalize(),
            "fit_score": score,
            "recommendation": label,
            "weighted_contributions": contributions,
            "score_notice": "Strategic fit score; not a probability of winning.",
        }
    )
    return result


def rank_key(candidate: dict[str, Any]) -> tuple[int, float]:
    gate_order = {"Eligible": 0, "Unknown": 1, "Ineligible": 2}
    return (gate_order[candidate["eligibility"]], -candidate["fit_score"])


def load_candidates(path: str | None) -> list[dict[str, Any]]:
    if path:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    else:
        payload = json.load(sys.stdin)

    if isinstance(payload, dict):
        payload = payload.get("candidates")
    if not isinstance(payload, list) or not payload:
        raise ValueError("Input must be a non-empty list or an object with 'candidates'.")
    if not all(isinstance(item, dict) for item in payload):
        raise ValueError("Every candidate must be a JSON object.")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Calculate and rank transparent design-award fit scores."
    )
    parser.add_argument("input", nargs="?", help="UTF-8 JSON file; reads stdin if omitted")
    parser.add_argument("--pretty", action="store_true", help="Indent JSON output")
    args = parser.parse_args()

    try:
        candidates = load_candidates(args.input)
        results = sorted((score_candidate(item) for item in candidates), key=rank_key)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    json.dump(
        {"candidates": results, "weights": WEIGHTS},
        sys.stdout,
        ensure_ascii=False,
        indent=2 if args.pretty else None,
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

