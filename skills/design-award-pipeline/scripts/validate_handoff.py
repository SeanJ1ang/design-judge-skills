#!/usr/bin/env python3
"""Validate a Design Award Pipeline handoff without external dependencies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


STAGES = {
    "search",
    "evaluation",
    "match",
    "information_prep",
    "submission_check",
}
NEXT_STAGES = STAGES | {"complete"}
MATURITY_TRACKS = {"student_concept", "mature_work", None}
PROVENANCE = {"user_material", "official_source", "user_confirmed"}
SEVERITIES = {"blocker", "important", "optional"}
TOP_LEVEL_KEYS = {
    "schema_version",
    "project_id",
    "target_award",
    "target_cycle",
    "maturity_track",
    "completed_stages",
    "next_stage",
    "facts",
    "inferences",
    "decisions",
    "artifacts",
    "open_items",
}
REQUIRED_KEYS = {
    "schema_version",
    "project_id",
    "completed_stages",
    "next_stage",
    "facts",
    "open_items",
}


def _is_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_handoff(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return ["handoff must be a JSON object"]

    errors: list[str] = []
    missing = sorted(REQUIRED_KEYS - set(payload))
    unknown = sorted(set(payload) - TOP_LEVEL_KEYS)
    if missing:
        errors.append("missing required fields: " + ", ".join(missing))
    if unknown:
        errors.append("unknown fields: " + ", ".join(unknown))

    if payload.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if not _is_text(payload.get("project_id")):
        errors.append("project_id must be a non-empty string")
    for key in ("target_award", "target_cycle"):
        value = payload.get(key)
        if value is not None and not _is_text(value):
            errors.append(f"{key} must be a non-empty string or null")
    if payload.get("maturity_track") not in MATURITY_TRACKS:
        errors.append("maturity_track must be student_concept, mature_work, or null")

    completed = payload.get("completed_stages")
    if not isinstance(completed, list):
        errors.append("completed_stages must be an array")
        completed = []
    else:
        invalid = [stage for stage in completed if stage not in STAGES]
        if invalid:
            errors.append("completed_stages contains invalid stages")
        if len(completed) != len(set(completed)):
            errors.append("completed_stages must not contain duplicates")

    next_stage = payload.get("next_stage")
    if next_stage not in NEXT_STAGES:
        errors.append("next_stage is invalid")
    elif next_stage != "complete" and next_stage in completed:
        errors.append("next_stage must not already be completed")

    facts = payload.get("facts")
    if not isinstance(facts, list):
        errors.append("facts must be an array")
    else:
        fact_ids: list[str] = []
        for index, fact in enumerate(facts):
            if not isinstance(fact, dict):
                errors.append(f"facts[{index}] must be an object")
                continue
            if set(fact) != {"id", "value", "provenance"}:
                errors.append(f"facts[{index}] must contain only id, value, and provenance")
            if not _is_text(fact.get("id")):
                errors.append(f"facts[{index}].id must be a non-empty string")
            else:
                fact_ids.append(fact["id"])
            if fact.get("provenance") not in PROVENANCE:
                errors.append(f"facts[{index}].provenance is invalid")
        if len(fact_ids) != len(set(fact_ids)):
            errors.append("fact ids must be unique")

    inferences = payload.get("inferences", [])
    if not isinstance(inferences, list):
        errors.append("inferences must be an array")
    else:
        inference_ids: list[str] = []
        for index, inference in enumerate(inferences):
            if not isinstance(inference, dict):
                errors.append(f"inferences[{index}] must be an object")
                continue
            required = {"id", "value", "basis", "confidence"}
            if set(inference) != required:
                errors.append(
                    f"inferences[{index}] must contain only id, value, basis, and confidence"
                )
            if not _is_text(inference.get("id")):
                errors.append(f"inferences[{index}].id must be a non-empty string")
            else:
                inference_ids.append(inference["id"])
            if not _is_text(inference.get("basis")):
                errors.append(f"inferences[{index}].basis must be a non-empty string")
            if inference.get("confidence") not in {"low", "medium", "high"}:
                errors.append(f"inferences[{index}].confidence is invalid")
        if len(inference_ids) != len(set(inference_ids)):
            errors.append("inference ids must be unique")

    for key in ("decisions", "artifacts"):
        values = payload.get(key, [])
        if not isinstance(values, list) or any(not _is_text(value) for value in values):
            errors.append(f"{key} must be an array of non-empty strings")

    open_items = payload.get("open_items")
    if not isinstance(open_items, list):
        errors.append("open_items must be an array")
    else:
        for index, item in enumerate(open_items):
            if not isinstance(item, dict):
                errors.append(f"open_items[{index}] must be an object")
                continue
            if set(item) != {"item", "severity"}:
                errors.append(f"open_items[{index}] must contain only item and severity")
            if not _is_text(item.get("item")):
                errors.append(f"open_items[{index}].item must be a non-empty string")
            if item.get("severity") not in SEVERITIES:
                errors.append(f"open_items[{index}].severity is invalid")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("handoff", type=Path, help="Handoff JSON file to validate")
    args = parser.parse_args()
    try:
        payload = json.loads(args.handoff.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "invalid", "errors": [str(exc)]}, ensure_ascii=False))
        return 2

    errors = validate_handoff(payload)
    print(
        json.dumps(
            {"status": "valid" if not errors else "invalid", "errors": errors},
            ensure_ascii=False,
        )
    )
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
