#!/usr/bin/env python3
"""Load and validate design-evaluation profiles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from benchmark_profiles import (
    resolve_if_benchmark,
    resolve_if_student_benchmark,
    resolve_idea_benchmark,
    resolve_red_dot_benchmark,
    validate_if_benchmark_profiles,
    validate_if_student_benchmark_profiles,
    validate_idea_benchmark_profiles,
    validate_red_dot_benchmark_profiles,
)


PROFILE_ROOT = Path(__file__).parents[1] / "references" / "profiles"

DESIGN_DIMENSIONS = {
    "problem_value",
    "user_function_usability",
    "innovation_differentiation",
    "solution_integrity",
    "implementation_feasibility",
    "form_interaction_quality",
    "responsibility_sustainability",
}

PRESENTATION_DIMENSIONS = {
    "first_glance_message",
    "information_hierarchy",
    "function_flow_visualization",
    "scenario_narrative",
    "detail_evidence_presentation",
    "visual_consistency",
}

MATURITY_FILES = {
    "student_concept": "student-concept.json",
    "mature_work": "mature-work.json",
}


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: top-level JSON must be an object.")
    return payload


def load_core() -> dict[str, Any]:
    return load_json(PROFILE_ROOT / "core.json")


def load_maturity(maturity: str) -> dict[str, Any]:
    try:
        filename = MATURITY_FILES[maturity]
    except KeyError as exc:
        allowed = ", ".join(sorted(MATURITY_FILES))
        raise ValueError(f"maturity must be one of: {allowed}.") from exc
    return load_json(PROFILE_ROOT / "maturity" / filename)


def load_classification() -> dict[str, Any]:
    return load_json(PROFILE_ROOT / "classification.json")


def load_sector_overlays() -> dict[str, Any]:
    return load_json(PROFILE_ROOT / "sector-overlays.json")


def load_award_lenses() -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for path in sorted((PROFILE_ROOT / "award-lenses").glob("*.json")):
        profile = load_json(path)
        profile_id = str(profile.get("profile_id", "")).strip()
        if not profile_id:
            raise ValueError(f"{path}: missing profile_id.")
        if profile_id in results:
            raise ValueError(f"duplicate award-lens profile_id: {profile_id}.")
        results[profile_id] = profile
    return results


def load_if_benchmark_context(
    *, category: str | None = None, discipline: str | None = None
) -> dict[str, Any]:
    return resolve_if_benchmark(category=category, discipline=discipline)


def load_if_student_benchmark_context(
    *, maturity: str, category: str | None = None
) -> dict[str, Any]:
    return resolve_if_student_benchmark(maturity=maturity, category=category)


def load_red_dot_benchmark_context(
    *,
    category: str | None = None,
    competition: str | None = None,
    discipline: str | None = None,
) -> dict[str, Any]:
    return resolve_red_dot_benchmark(
        category=category, competition=competition, discipline=discipline
    )


def load_idea_benchmark_context(
    *, maturity: str, category: str | None = None, discipline: str | None = None
) -> dict[str, Any]:
    return resolve_idea_benchmark(
        maturity=maturity, category=category, discipline=discipline
    )


def _validate_weight_map(
    name: str, weights: Any, expected_keys: set[str], expected_total: int
) -> list[str]:
    errors: list[str] = []
    if not isinstance(weights, dict):
        return [f"{name}: weights must be an object."]
    keys = set(weights)
    if keys != expected_keys:
        missing = sorted(expected_keys - keys)
        extra = sorted(keys - expected_keys)
        if missing:
            errors.append(f"{name}: missing dimensions: {', '.join(missing)}.")
        if extra:
            errors.append(f"{name}: unknown dimensions: {', '.join(extra)}.")
    total = 0.0
    for key, value in weights.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors.append(f"{name}: weight '{key}' must be numeric.")
            continue
        if value <= 0:
            errors.append(f"{name}: weight '{key}' must be positive.")
        total += float(value)
    if total != expected_total:
        errors.append(f"{name}: weights total {total:g}; expected {expected_total}.")
    return errors


def validate_profiles() -> list[str]:
    errors: list[str] = []
    core = load_core()
    errors.extend(
        _validate_weight_map(
            "core.presentation_weights",
            core.get("presentation_weights"),
            PRESENTATION_DIMENSIONS,
            50,
        )
    )
    if core.get("design_total") != 50:
        errors.append("core.design_total must equal 50.")
    if core.get("presentation_total") != 50:
        errors.append("core.presentation_total must equal 50.")

    for maturity in MATURITY_FILES:
        profile = load_maturity(maturity)
        if profile.get("profile_id") != maturity:
            errors.append(f"{maturity}: profile_id must equal '{maturity}'.")
        errors.extend(
            _validate_weight_map(
                f"{maturity}.design_weights",
                profile.get("design_weights"),
                DESIGN_DIMENSIONS,
                50,
            )
        )

    classification = load_classification()
    for field in ("disciplines", "sectors", "focus_tags"):
        values = classification.get(field)
        if not isinstance(values, dict) or not values:
            errors.append(f"classification.{field} must be a non-empty object.")

    all_dimensions = DESIGN_DIMENSIONS | PRESENTATION_DIMENSIONS
    for profile_id, profile in load_award_lenses().items():
        source = str(profile.get("official_source", ""))
        if not source.startswith("https://"):
            errors.append(f"{profile_id}: official_source must be HTTPS.")
        mapping = profile.get("mapping")
        if not isinstance(mapping, dict) or not mapping:
            errors.append(f"{profile_id}: mapping must be a non-empty object.")
            continue
        criteria = profile.get("criteria")
        if not isinstance(criteria, list) or set(mapping) != set(criteria):
            errors.append(f"{profile_id}: criteria and mapping keys must match.")
        for criterion, dimensions in mapping.items():
            if not isinstance(dimensions, list) or not dimensions:
                errors.append(f"{profile_id}.{criterion}: mapping must be a non-empty list.")
                continue
            unknown = sorted(set(dimensions) - all_dimensions)
            if unknown:
                errors.append(
                    f"{profile_id}.{criterion}: unknown dimensions: {', '.join(unknown)}."
                )
    errors.extend(validate_if_benchmark_profiles())
    errors.extend(validate_if_student_benchmark_profiles())
    errors.extend(validate_red_dot_benchmark_profiles())
    errors.extend(validate_idea_benchmark_profiles())
    return errors
