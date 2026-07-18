#!/usr/bin/env python3
"""Build a focused award-route shortlist before evidence scoring."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from award_profiles import load_profiles
from filter_eligible_awards import evaluate_route


RELATION_ORDER = {"exact": 0, "adjacent": 1, "broad": 2, "live-lookup": 3}
ELIGIBILITY_ORDER = {"Eligible": 0, "Unknown": 1, "Ineligible": 2}


def _read_project(path: str | None) -> dict[str, Any]:
    if path:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    else:
        payload = json.load(sys.stdin)
    if not isinstance(payload, dict):
        raise ValueError("Input must be a JSON object.")
    project = payload.get("project", payload)
    if not isinstance(project, dict):
        raise ValueError("'project' must be a JSON object.")
    if not project.get("canonical_category"):
        raise ValueError("Project requires 'canonical_category'.")
    return project


def _hint_for(
    profile: dict[str, Any], canonical: str, route_id: str
) -> dict[str, str]:
    for hint in profile.get("category_hints", {}).get(canonical, []):
        if hint["route_id"] == route_id:
            return hint
    return {
        "route_id": route_id,
        "track": "Needs current official lookup",
        "category": "Needs current official category mapping",
        "relation": "live-lookup",
    }


def build_candidates(
    project: dict[str, Any], award_ids: list[str] | None = None
) -> list[dict[str, Any]]:
    canonical = project["canonical_category"]
    candidates = []
    for profile in load_profiles(award_ids):
        if profile.get("status") == "disabled":
            continue
        for route in profile["routes"]:
            gate = evaluate_route(profile, route, project)
            if gate["eligibility"] == "Ineligible":
                continue
            hint = _hint_for(profile, canonical, route["route_id"])
            candidates.append(
                {
                    **gate,
                    "canonical_category": canonical,
                    "track": hint["track"],
                    "category": hint["category"],
                    "category_relation": hint["relation"],
                    "published_criteria": profile["criteria"],
                    "profile_notes": profile.get("notes", []),
                    "profile_last_reviewed": profile["last_profile_reviewed"],
                }
            )
    return sorted(
        candidates,
        key=lambda item: (
            ELIGIBILITY_ORDER[item["eligibility"]],
            RELATION_ORDER[item["category_relation"]],
            len(item["missing_project_facts"]),
            len(item["needs_live_verification"]),
            item["award_id"],
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build award candidates from the allowlist.")
    parser.add_argument("input", nargs="?", help="UTF-8 JSON file; reads stdin if omitted")
    parser.add_argument("--award", action="append", dest="awards", help="Award id filter")
    parser.add_argument("--limit", type=int, default=5, help="Maximum candidates (default 5)")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    if args.limit < 1:
        print("error: --limit must be positive", file=sys.stderr)
        return 2
    try:
        project = _read_project(args.input)
        candidates = build_candidates(project, args.awards)[: args.limit]
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    json.dump(
        {"project": project, "candidates": candidates},
        sys.stdout,
        ensure_ascii=False,
        indent=2 if args.pretty else None,
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
