#!/usr/bin/env python3
"""Apply stable structural gates to the configured award routes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from award_profiles import load_profiles


STATUS_ORDER = {"Eligible": 0, "Unknown": 1, "Ineligible": 2}


def _read_payload(path: str | None) -> dict[str, Any]:
    if path:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    else:
        payload = json.load(sys.stdin)
    if not isinstance(payload, dict):
        raise ValueError("Input must be a JSON object.")
    project = payload.get("project", payload)
    if not isinstance(project, dict):
        raise ValueError("'project' must be a JSON object.")
    return project


def _constraint_passes(value: Any, constraint: dict[str, Any]) -> bool:
    operator = constraint["operator"]
    if operator == "equals":
        return value == constraint.get("value")
    if operator == "in":
        return value in constraint.get("values", [])
    if operator == "truthy":
        return bool(value)
    if operator == "falsy":
        return not bool(value)
    raise ValueError(f"Unsupported constraint operator: {operator}")


def evaluate_route(
    profile: dict[str, Any], route: dict[str, Any], project: dict[str, Any]
) -> dict[str, Any]:
    missing: list[str] = []
    failures: list[str] = []

    applicant = project.get("applicant_type")
    state = project.get("project_state")
    if applicant is None:
        missing.append("applicant_type")
    elif applicant not in route["entrant_types"]:
        failures.append(
            f"Applicant type '{applicant}' is outside this route's stable entrant scope."
        )

    if state is None:
        missing.append("project_state")
    elif state not in route["project_states"]:
        failures.append(
            f"Project state '{state}' is outside this route's stable project scope."
        )

    for field in route.get("required_project_fields", []):
        value = project.get(field)
        if (value is None or value == "" or value == []) and field not in missing:
            missing.append(field)

    for constraint in route.get("stable_constraints", []):
        field = constraint["field"]
        if field not in project or project[field] is None:
            if field not in missing:
                missing.append(field)
            continue
        if not _constraint_passes(project[field], constraint):
            failures.append(constraint["message"])

    live_checks = list(dict.fromkeys(route.get("dynamic_gates", [])))
    if failures:
        eligibility = "Ineligible"
        structural_status = "Ineligible"
    elif missing:
        eligibility = "Unknown"
        structural_status = "Unknown"
    elif live_checks:
        eligibility = "Unknown"
        structural_status = "Eligible"
    else:
        eligibility = "Eligible"
        structural_status = "Eligible"

    return {
        "award_id": profile["award_id"],
        "award": profile["program"],
        "route_id": route["route_id"],
        "route": route["label"],
        "eligibility": eligibility,
        "structural_status": structural_status,
        "missing_project_facts": sorted(missing),
        "failed_gates": failures,
        "needs_live_verification": live_checks,
        "official_sources": profile["official_sources"],
    }


def filter_awards(
    project: dict[str, Any], award_ids: list[str] | None = None
) -> list[dict[str, Any]]:
    results = []
    for profile in load_profiles(award_ids):
        if profile.get("status") == "disabled":
            continue
        for route in profile["routes"]:
            results.append(evaluate_route(profile, route, project))
    return sorted(
        results,
        key=lambda item: (
            STATUS_ORDER[item["eligibility"]],
            item["award_id"],
            item["route_id"],
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply structural award eligibility gates.")
    parser.add_argument("input", nargs="?", help="UTF-8 JSON file; reads stdin if omitted")
    parser.add_argument("--award", action="append", dest="awards", help="Award id filter")
    parser.add_argument("--include-ineligible", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    try:
        project = _read_payload(args.input)
        results = filter_awards(project, args.awards)
        if not args.include_ineligible:
            results = [item for item in results if item["eligibility"] != "Ineligible"]
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    json.dump(
        {"project": project, "routes": results},
        sys.stdout,
        ensure_ascii=False,
        indent=2 if args.pretty else None,
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
