#!/usr/bin/env python3
"""Calculate a transparent design-evaluation score from structured ratings."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from evaluation_profiles import (
    DESIGN_DIMENSIONS,
    PRESENTATION_DIMENSIONS,
    load_award_lenses,
    load_classification,
    load_core,
    load_if_benchmark_context,
    load_if_student_benchmark_context,
    load_idea_benchmark_context,
    load_red_dot_benchmark_context,
    load_maturity,
    validate_profiles,
)


FINDING_SEVERITIES = {"critical", "major", "minor"}
BENCHMARK_SOURCES = {
    "if_observed_winners",
    "if_student_observed_winners",
    "red_dot_observed_winners",
    "idea_observed_recognized",
}


def _require_nonempty_string(value: Any, field: str) -> str:
    result = str(value or "").strip()
    if not result:
        raise ValueError(f"'{field}' must be a non-empty string.")
    return result


def _validate_classification(value: Any, vocabulary: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("'classification' must be an object.")

    primary_discipline = _require_nonempty_string(
        value.get("primary_discipline"), "classification.primary_discipline"
    )
    if primary_discipline not in vocabulary["disciplines"]:
        raise ValueError(f"unknown primary_discipline: {primary_discipline}.")

    primary_sector = _require_nonempty_string(
        value.get("primary_sector"), "classification.primary_sector"
    )
    if primary_sector not in vocabulary["sectors"]:
        raise ValueError(f"unknown primary_sector: {primary_sector}.")

    secondary_disciplines = value.get("secondary_disciplines", [])
    secondary_sectors = value.get("secondary_sectors", [])
    focus_tags = value.get("focus_tags", [])
    for field, items, known, maximum in (
        (
            "secondary_disciplines",
            secondary_disciplines,
            vocabulary["disciplines"],
            2,
        ),
        ("secondary_sectors", secondary_sectors, vocabulary["sectors"], 1),
        ("focus_tags", focus_tags, vocabulary["focus_tags"], None),
    ):
        if not isinstance(items, list) or not all(isinstance(item, str) for item in items):
            raise ValueError(f"classification.{field} must be a list of strings.")
        if maximum is not None and len(items) > maximum:
            raise ValueError(f"classification.{field} allows at most {maximum} value(s).")
        unknown = sorted(set(items) - set(known))
        if unknown:
            raise ValueError(f"unknown classification.{field}: {', '.join(unknown)}.")
        if len(items) != len(set(items)):
            raise ValueError(f"classification.{field} must not contain duplicates.")

    if primary_discipline in secondary_disciplines:
        raise ValueError("primary_discipline must not repeat in secondary_disciplines.")
    if primary_sector in secondary_sectors:
        raise ValueError("primary_sector must not repeat in secondary_sectors.")
    return value


def _resolve_benchmark_context(
    value: Any, classification: dict[str, Any], maturity: str
) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError("'benchmark_context' must be an object.")
    source = _require_nonempty_string(value.get("source"), "benchmark_context.source")
    if source not in BENCHMARK_SOURCES:
        raise ValueError(f"unknown benchmark_context.source: {source}.")

    category = value.get("category")
    if category is not None:
        category = _require_nonempty_string(category, "benchmark_context.category")
    discipline = value.get("discipline", classification["primary_discipline"])
    if discipline is not None:
        discipline = _require_nonempty_string(
            discipline, "benchmark_context.discipline"
        )
    competition = value.get("competition")
    if competition is not None:
        competition = _require_nonempty_string(
            competition, "benchmark_context.competition"
        )
    if source == "if_student_observed_winners":
        resolved = load_if_student_benchmark_context(
            maturity=maturity, category=category
        )
        notice = (
            "Observed iF Student winner context for student concepts only; the SDG "
            "theme does not determine design discipline and does not change the score."
        )
    elif source == "red_dot_observed_winners":
        resolved = load_red_dot_benchmark_context(
            category=category,
            competition=competition,
            discipline=discipline,
        )
        notice = (
            "Observed Red Dot winner context only; not official jury weights, "
            "an official jury standard, or a probability model."
        )
    elif source == "idea_observed_recognized":
        resolved = load_idea_benchmark_context(
            maturity=maturity,
            category=category,
            discipline=discipline,
        )
        notice = (
            "Observed IDEA awarded and Featured Finalist context only; not official "
            "jury weights, an official jury standard, or a probability model."
        )
    else:
        resolved = load_if_benchmark_context(category=category, discipline=discipline)
        notice = (
            "Observed iF winner context only; not an official jury standard, "
            "score weight, or probability model."
        )
    return {
        "requested_source": source,
        "requested_category": category,
        "requested_discipline": discipline,
        "requested_competition": competition,
        **resolved,
        "notice": notice,
    }


def _score_record(
    dimension: str,
    value: Any,
    weight: float,
    evidence_states: set[str],
    global_caps: dict[str, Any],
    profile_caps: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"rating '{dimension}' must be an object.")
    score = value.get("score")
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        raise ValueError(f"rating '{dimension}'.score must be numeric.")
    score = float(score)
    if not 0 <= score <= 5:
        raise ValueError(f"rating '{dimension}'.score must be from 0 to 5.")

    state = str(value.get("evidence_status", "")).lower()
    if state not in evidence_states:
        allowed = ", ".join(sorted(evidence_states))
        raise ValueError(
            f"rating '{dimension}'.evidence_status must be one of: {allowed}."
        )
    rationale = _require_nonempty_string(value.get("rationale"), f"ratings.{dimension}.rationale")
    evidence = value.get("evidence", [])
    if not isinstance(evidence, list) or not all(isinstance(item, str) for item in evidence):
        raise ValueError(f"rating '{dimension}'.evidence must be a list of strings.")
    if state in {"verified", "supported"} and not evidence:
        raise ValueError(f"rating '{dimension}' with {state} evidence requires an evidence item.")

    applied_score = score
    adjustments: list[str] = []
    if state in global_caps and applied_score > float(global_caps[state]):
        applied_score = float(global_caps[state])
        adjustments.append(
            f"Global evidence cap applied for {state}: maximum {applied_score:g}/5."
        )
    dimension_caps = (
        profile_caps.get(dimension, {}) if isinstance(profile_caps, dict) else {}
    )
    if state in dimension_caps and applied_score > float(dimension_caps[state]):
        applied_score = float(dimension_caps[state])
        adjustments.append(
            f"Maturity-profile evidence cap applied for {state}: maximum {applied_score:g}/5."
        )

    weighted = round((applied_score / 5) * float(weight), 2)
    return {
        "dimension": dimension,
        "weight": weight,
        "submitted_score": score,
        "applied_score": applied_score,
        "weighted_score": weighted,
        "evidence_status": state.capitalize(),
        "evidence": evidence,
        "rationale": rationale,
        "adjustments": adjustments,
    }


def _competitiveness_label(score: float, thresholds: dict[str, Any]) -> str:
    if score >= thresholds["strong_competitiveness"]:
        return "Strong competitiveness"
    if score >= thresholds["competitive_with_gaps"]:
        return "Competitive with gaps"
    if score >= thresholds["developing"]:
        return "Developing"
    return "Weak or insufficiently evidenced"


def _validate_findings(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("'findings' must be a list.")
    results: list[dict[str, Any]] = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"finding {index} must be an object.")
        severity = str(item.get("severity", "")).lower()
        if severity not in FINDING_SEVERITIES:
            raise ValueError(
                f"finding {index}.severity must be critical, major, or minor."
            )
        finding = _require_nonempty_string(item.get("finding"), f"findings[{index}].finding")
        evidence = _require_nonempty_string(item.get("evidence"), f"findings[{index}].evidence")
        results.append({"severity": severity.capitalize(), "finding": finding, "evidence": evidence})
    return results


def score_evaluation(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Input must be a JSON object.")
    profile_errors = validate_profiles()
    if profile_errors:
        raise ValueError("Invalid evaluation profiles: " + " ".join(profile_errors))

    project_name = _require_nonempty_string(payload.get("project_name"), "project_name")
    maturity = _require_nonempty_string(payload.get("maturity"), "maturity").lower()
    if payload.get("maturity_source") != "user":
        raise ValueError("'maturity_source' must equal 'user'; maturity cannot be inferred.")

    core = load_core()
    maturity_profile = load_maturity(maturity)
    classification = _validate_classification(payload.get("classification"), load_classification())
    benchmark_context = _resolve_benchmark_context(
        payload.get("benchmark_context"), classification, maturity
    )

    ratings = payload.get("ratings")
    if not isinstance(ratings, dict):
        raise ValueError("'ratings' must be an object with design and presentation objects.")
    design_ratings = ratings.get("design")
    presentation_ratings = ratings.get("presentation")
    if not isinstance(design_ratings, dict) or not isinstance(presentation_ratings, dict):
        raise ValueError("ratings.design and ratings.presentation must be objects.")
    if set(design_ratings) != DESIGN_DIMENSIONS:
        missing = sorted(DESIGN_DIMENSIONS - set(design_ratings))
        extra = sorted(set(design_ratings) - DESIGN_DIMENSIONS)
        raise ValueError(f"design ratings mismatch; missing={missing}, extra={extra}.")
    if set(presentation_ratings) != PRESENTATION_DIMENSIONS:
        missing = sorted(PRESENTATION_DIMENSIONS - set(presentation_ratings))
        extra = sorted(set(presentation_ratings) - PRESENTATION_DIMENSIONS)
        raise ValueError(f"presentation ratings mismatch; missing={missing}, extra={extra}.")

    evidence_states = set(core["evidence_states"])
    design_records = [
        _score_record(
            dimension,
            design_ratings[dimension],
            maturity_profile["design_weights"][dimension],
            evidence_states,
            core.get("global_evidence_caps", {}),
            maturity_profile.get("caps", {}),
        )
        for dimension in maturity_profile["design_weights"]
    ]
    presentation_records = [
        _score_record(
            dimension,
            presentation_ratings[dimension],
            core["presentation_weights"][dimension],
            evidence_states,
            core.get("global_evidence_caps", {}),
            {},
        )
        for dimension in core["presentation_weights"]
    ]

    design_score = round(sum(item["weighted_score"] for item in design_records), 2)
    presentation_score = round(
        sum(item["weighted_score"] for item in presentation_records), 2
    )
    total_score = round(design_score + presentation_score, 2)

    all_records = design_records + presentation_records
    confidence_points = core["confidence_points"]
    confidence_index = round(
        sum(
            confidence_points[item["evidence_status"].lower()] * float(item["weight"])
            for item in all_records
        )
        / 100,
        2,
    )
    mismatch = bool(payload.get("maturity_evidence_mismatch", False))
    has_missing_design = any(
        item["evidence_status"] == "Missing" for item in design_records
    )
    if mismatch:
        evidence_confidence = "Low"
    elif (
        confidence_index >= core["confidence_thresholds"]["high"]
        and not has_missing_design
    ):
        evidence_confidence = "High"
    elif confidence_index >= core["confidence_thresholds"]["medium"]:
        evidence_confidence = "Medium"
    else:
        evidence_confidence = "Low"

    findings = _validate_findings(payload.get("findings"))
    critical_count = sum(item["severity"] == "Critical" for item in findings)
    competitiveness = _competitiveness_label(
        total_score, core["competitiveness_thresholds"]
    )
    if critical_count:
        competitiveness = "Critical risk"

    award_lens = payload.get("award_lens")
    award_lens_result = None
    if award_lens is not None:
        award_lens = str(award_lens)
        lenses = load_award_lenses()
        if award_lens not in lenses:
            raise ValueError(f"unknown award_lens: {award_lens}.")
        lens = lenses[award_lens]
        award_lens_result = {
            "profile_id": award_lens,
            "display_name": lens["display_name"],
            "official_source": lens["official_source"],
            "checked_on": lens["checked_on"],
            "criteria_mapping": lens["mapping"],
            "notice": lens["not_official_notice"],
            "runtime_rule": lens["runtime_rule"],
        }

    return {
        "project_name": project_name,
        "maturity": maturity,
        "maturity_source": "user",
        "classification": classification,
        "score_summary": {
            "design_score": design_score,
            "design_max": core["design_total"],
            "presentation_score": presentation_score,
            "presentation_max": core["presentation_total"],
            "total_score": total_score,
            "total_max": 100,
            "competitiveness": competitiveness,
            "critical_count": critical_count,
        },
        "evidence": {
            "confidence": evidence_confidence,
            "confidence_index": confidence_index,
            "maturity_evidence_mismatch": mismatch,
        },
        "dimension_results": {
            "design": design_records,
            "presentation": presentation_records,
        },
        "findings": findings,
        "award_lens": award_lens_result,
        "benchmark_context": benchmark_context,
        "score_notice": (
            "Evidence-based diagnostic score; not an official jury decision, "
            "award recommendation, or probability of winning."
        ),
    }


def load_input(path: str | None) -> dict[str, Any]:
    if path:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    else:
        payload = json.load(sys.stdin)
    if not isinstance(payload, dict):
        raise ValueError("Input must be a JSON object.")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Calculate a transparent design-evaluation score."
    )
    parser.add_argument("input", nargs="?", help="UTF-8 JSON file; reads stdin if omitted")
    parser.add_argument("--pretty", action="store_true", help="Indent JSON output")
    args = parser.parse_args()

    try:
        result = score_evaluation(load_input(args.input))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    json.dump(
        result,
        sys.stdout,
        ensure_ascii=False,
        indent=2 if args.pretty else None,
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
