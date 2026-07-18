#!/usr/bin/env python3
"""Load and validate aggregate benchmark context bundled with design-evaluation."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


PROFILE_ROOT = Path(__file__).parents[1] / "references" / "profiles"
IF_ROOT = PROFILE_ROOT / "benchmarks" / "if"
IF_STUDENT_ROOT = PROFILE_ROOT / "benchmarks" / "if-student"
RED_DOT_ROOT = PROFILE_ROOT / "benchmarks" / "red-dot"
IDEA_ROOT = PROFILE_ROOT / "benchmarks" / "idea"

FORBIDDEN_KEYS = {
    "title",
    "name",
    "description",
    "designer",
    "designers",
    "company",
    "client",
    "clients",
    "source_url",
    "canonical_url",
    "entry_key",
    "raw_payload",
    "image_hash",
    "sha256",
}


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: top-level JSON must be an object.")
    return payload


def normalize_if_category(value: str) -> str:
    normalized = re.sub(r"\s+", " ", str(value or "")).strip()
    return re.sub(r"^\d+(?:\.\d+)*\s+", "", normalized).strip()


RED_DOT_CATEGORY_ALIASES = {
    "Brand Design & Identity": "Brand Design and Identity",
    "Exhibition and Installations": "Exhibitions and Installations",
    "Haushaltsgeräte und Haushaltszubehör": "Household Appliances and Household Accessories",
    "Household Appliances and Accessories": "Household Appliances and Household Accessories",
    "Kitchen Appliances and Accessories": "Kitchen Appliances and Kitchen Accessories",
    "Lamps and luminaires": "Lamps and Luminaires",
    "Lichtsysteme": "Lighting Systems",
    "Material and Surfaces": "Materials and Surfaces",
    "Personal Care, Wellness und Beauty": "Personal Care, Wellness and Beauty",
    "Smart Phones, Tablets and Wearable Technology": "Mobile Phones, Tablets and Wearables",
    "Trains and Planes + Watercraft": "Trains, Planes and Watercraft",
    "TV, Audio and Home Entertainment": "TV and Home Entertainment",
    "Wohnmobile und Caravans": "Motorhomes and Caravans",
    "Bathroom Taps, Shower Heads and Equipment": "Bathroom Taps and Shower Heads",
    "Cameras, Drones and Camera Equipment": "Cameras and Camera Equipment",
    "Heating and Air Conditioning": "Heating and Air Conditioning Technology",
    "Luggage, Bags and Travel Accessories": "Luggage and Bags",
    "Tools, Industrial Equipment and Machinery": "Industrial Equipment, Machinery and Automation",
}


def normalize_red_dot_category(value: str) -> str:
    normalized = re.sub(r"\s+", " ", str(value or "")).strip()
    normalized = re.sub(
        r"\s*/\s*Red Dot:\s*Junior Award\s*$", "", normalized, flags=re.I
    )
    return RED_DOT_CATEGORY_ALIASES.get(normalized, normalized)


def normalize_idea_category(value: str) -> str:
    normalized = re.sub(r"\s+", " ", str(value or "")).strip()
    return {"Kitchen & Accessories": "Kitchens"}.get(normalized, normalized)


def load_if_manifest() -> dict[str, Any]:
    return load_json(IF_ROOT / "manifest.json")


def load_if_category_crosswalk() -> dict[str, Any]:
    return load_json(IF_ROOT / "category-crosswalk.json")


def load_if_discipline_profiles() -> dict[str, Any]:
    return load_json(IF_ROOT / "discipline-profiles.json")


def load_if_category_profiles() -> dict[str, Any]:
    return load_json(IF_ROOT / "category-profiles.json")


def load_if_student_manifest() -> dict[str, Any]:
    return load_json(IF_STUDENT_ROOT / "manifest.json")


def load_if_student_category_crosswalk() -> dict[str, Any]:
    return load_json(IF_STUDENT_ROOT / "category-crosswalk.json")


def load_if_student_competition_profile() -> dict[str, Any]:
    return load_json(IF_STUDENT_ROOT / "competition-profile.json")


def load_if_student_category_profiles() -> dict[str, Any]:
    return load_json(IF_STUDENT_ROOT / "category-profiles.json")


def load_red_dot_manifest() -> dict[str, Any]:
    return load_json(RED_DOT_ROOT / "manifest.json")


def load_red_dot_category_crosswalk() -> dict[str, Any]:
    return load_json(RED_DOT_ROOT / "category-crosswalk.json")


def load_red_dot_competition_profiles() -> dict[str, Any]:
    return load_json(RED_DOT_ROOT / "competition-profiles.json")


def load_red_dot_discipline_profiles() -> dict[str, Any]:
    return load_json(RED_DOT_ROOT / "discipline-profiles.json")


def load_red_dot_category_profiles() -> dict[str, Any]:
    return load_json(RED_DOT_ROOT / "category-profiles.json")


def load_idea_manifest() -> dict[str, Any]:
    return load_json(IDEA_ROOT / "manifest.json")


def load_idea_category_crosswalk() -> dict[str, Any]:
    return load_json(IDEA_ROOT / "category-crosswalk.json")


def load_idea_program_profile() -> dict[str, Any]:
    return load_json(IDEA_ROOT / "program-profile.json")


def load_idea_discipline_profiles() -> dict[str, Any]:
    return load_json(IDEA_ROOT / "discipline-profiles.json")


def load_idea_category_profiles() -> dict[str, Any]:
    return load_json(IDEA_ROOT / "category-profiles.json")


def _majority_key(counts: Any) -> str | None:
    if not isinstance(counts, dict) or not counts:
        return None
    return max(counts, key=lambda key: counts[key])


def resolve_if_benchmark(
    *, category: str | None = None, discipline: str | None = None
) -> dict[str, Any]:
    """Resolve category context first, then discipline context, then core fallback."""
    manifest = load_if_manifest()
    crosswalk = load_if_category_crosswalk()["categories"]
    category_profiles = load_if_category_profiles()["profiles"]
    discipline_profiles = load_if_discipline_profiles()["profiles"]

    normalized_category = normalize_if_category(category or "")
    crosswalk_entry = crosswalk.get(normalized_category) if normalized_category else None

    if normalized_category and normalized_category in category_profiles:
        profile = category_profiles[normalized_category]
        return {
            "matched_profile_type": "category_profile",
            "matched_profile_id": profile["profile_id"],
            "normalized_category": normalized_category,
            "profile": profile,
            "fallback_used": False,
            "score_effect": "none",
            "source_profile_set": manifest["profile_set_id"],
        }

    requested_discipline = discipline
    if not requested_discipline and crosswalk_entry:
        requested_discipline = _majority_key(crosswalk_entry.get("evaluation_disciplines"))

    if requested_discipline in discipline_profiles:
        profile = discipline_profiles[requested_discipline]
        return {
            "matched_profile_type": "discipline_profile",
            "matched_profile_id": profile["profile_id"],
            "normalized_category": normalized_category or None,
            "profile": profile,
            "fallback_used": bool(normalized_category),
            "fallback_reason": (
                "No category profile met the minimum sample threshold."
                if normalized_category
                else None
            ),
            "score_effect": "none",
            "source_profile_set": manifest["profile_set_id"],
        }

    return {
        "matched_profile_type": "core_fallback",
        "matched_profile_id": "design-evaluation-core",
        "normalized_category": normalized_category or None,
        "profile": None,
        "fallback_used": True,
        "fallback_reason": "No reviewed category or discipline benchmark matched.",
        "score_effect": "none",
        "source_profile_set": manifest["profile_set_id"],
    }


def resolve_if_student_benchmark(
    *, maturity: str, category: str | None = None
) -> dict[str, Any]:
    """Resolve iF Student context only for a user-selected student concept."""
    manifest = load_if_student_manifest()
    allowed = manifest.get("maturity_gate", {}).get("allowed", [])
    if maturity not in allowed:
        raise ValueError(
            "iF Student benchmark is allowed only when "
            f"maturity='student_concept'; received '{maturity}'."
        )

    crosswalk = load_if_student_category_crosswalk()["categories"]
    category_profiles = load_if_student_category_profiles()["profiles"]
    competition_profile = load_if_student_competition_profile()
    normalized_category = normalize_if_category(category or "")

    if normalized_category and normalized_category in category_profiles:
        profile = category_profiles[normalized_category]
        return {
            "matched_profile_type": "category_profile",
            "matched_profile_id": profile["profile_id"],
            "normalized_category": normalized_category,
            "profile": profile,
            "fallback_used": False,
            "maturity_gate_applied": True,
            "discipline_inference": "not_allowed_from_sdg_category",
            "score_effect": "none",
            "source_profile_set": manifest["profile_set_id"],
        }

    if normalized_category in crosswalk:
        fallback_reason = (
            "The matched SDG theme did not meet the minimum sample threshold; "
            "using the competition-wide student-concept profile."
        )
    elif normalized_category:
        fallback_reason = (
            "No bundled iF Student SDG theme matched; using the "
            "competition-wide student-concept profile."
        )
    else:
        fallback_reason = "No SDG theme was supplied; using the competition-wide profile."

    return {
        "matched_profile_type": "competition_profile",
        "matched_profile_id": competition_profile["profile_id"],
        "normalized_category": normalized_category or None,
        "profile": competition_profile,
        "fallback_used": True,
        "fallback_reason": fallback_reason,
        "maturity_gate_applied": True,
        "discipline_inference": "not_allowed_from_sdg_category",
        "score_effect": "none",
        "source_profile_set": manifest["profile_set_id"],
    }


def resolve_red_dot_benchmark(
    *,
    category: str | None = None,
    competition: str | None = None,
    discipline: str | None = None,
) -> dict[str, Any]:
    """Resolve Red Dot category, competition, discipline, then core context."""
    manifest = load_red_dot_manifest()
    crosswalk = load_red_dot_category_crosswalk()["categories"]
    category_profiles = load_red_dot_category_profiles()["profiles"]
    competition_profiles = load_red_dot_competition_profiles()["profiles"]
    discipline_profiles = load_red_dot_discipline_profiles()["profiles"]
    normalized_category = normalize_red_dot_category(category or "")
    crosswalk_entry = crosswalk.get(normalized_category) if normalized_category else None

    if normalized_category and normalized_category in category_profiles:
        profile = category_profiles[normalized_category]
        return {
            "matched_profile_type": "category_profile",
            "matched_profile_id": profile["profile_id"],
            "normalized_category": normalized_category,
            "profile": profile,
            "fallback_used": False,
            "score_effect": "none",
            "source_profile_set": manifest["profile_set_id"],
        }

    if competition:
        competition = re.sub(r"\s+", " ", competition).strip()
        if competition not in competition_profiles:
            allowed = ", ".join(sorted(competition_profiles))
            raise ValueError(f"Unknown Red Dot competition line: {competition}. Allowed: {allowed}.")
        profile = competition_profiles[competition]
        return {
            "matched_profile_type": "competition_profile",
            "matched_profile_id": profile["profile_id"],
            "normalized_category": normalized_category or None,
            "profile": profile,
            "fallback_used": True,
            "fallback_reason": (
                "No category profile met the minimum sample threshold; using the "
                "explicitly selected Red Dot competition line."
                if normalized_category
                else "No category was supplied; using the explicitly selected competition line."
            ),
            "score_effect": "none",
            "source_profile_set": manifest["profile_set_id"],
        }

    requested_discipline = discipline
    if not requested_discipline and crosswalk_entry:
        requested_discipline = crosswalk_entry.get("primary_evaluation_discipline")
    if requested_discipline in discipline_profiles:
        profile = discipline_profiles[requested_discipline]
        return {
            "matched_profile_type": "discipline_profile",
            "matched_profile_id": profile["profile_id"],
            "normalized_category": normalized_category or None,
            "profile": profile,
            "fallback_used": True,
            "fallback_reason": (
                "No category profile met the minimum sample threshold and no Red Dot "
                "competition line was supplied; using discipline context."
            ),
            "score_effect": "none",
            "source_profile_set": manifest["profile_set_id"],
        }

    return {
        "matched_profile_type": "core_fallback",
        "matched_profile_id": "design-evaluation-core",
        "normalized_category": normalized_category or None,
        "profile": None,
        "fallback_used": True,
        "fallback_reason": "No reviewed Red Dot category, competition, or discipline benchmark matched.",
        "score_effect": "none",
        "source_profile_set": manifest["profile_set_id"],
    }


def resolve_idea_benchmark(
    *,
    maturity: str | None = None,
    category: str | None = None,
    discipline: str | None = None,
) -> dict[str, Any]:
    """Resolve IDEA category, discipline, then program-wide context."""
    manifest = load_idea_manifest()
    crosswalk = load_idea_category_crosswalk()["categories"]
    category_profiles = load_idea_category_profiles()["profiles"]
    discipline_profiles = load_idea_discipline_profiles()["profiles"]
    program_profile = load_idea_program_profile()
    normalized_category = normalize_idea_category(category or "")
    crosswalk_entry = crosswalk.get(normalized_category) if normalized_category else None
    is_student_category = normalized_category == "Student Designs"

    if is_student_category:
        if maturity is None:
            raise ValueError(
                "IDEA Student Designs context requires user-selected maturity='student_concept'."
            )
        if maturity != "student_concept":
            raise ValueError(
                "IDEA Student Designs benchmark is allowed only when "
                f"maturity='student_concept'; received '{maturity}'."
            )

    if normalized_category and normalized_category in category_profiles:
        profile = category_profiles[normalized_category]
        result = {
            "matched_profile_type": "category_profile",
            "matched_profile_id": profile["profile_id"],
            "normalized_category": normalized_category,
            "profile": profile,
            "fallback_used": False,
            "score_effect": "none",
            "source_profile_set": manifest["profile_set_id"],
        }
        if is_student_category:
            result.update(
                {
                    "maturity_gate_applied": True,
                    "discipline_inference": "not_allowed_from_student_category",
                }
            )
        return result

    requested_discipline = discipline
    if not requested_discipline and crosswalk_entry:
        requested_discipline = crosswalk_entry.get("primary_evaluation_discipline")
    if requested_discipline in discipline_profiles:
        profile = discipline_profiles[requested_discipline]
        return {
            "matched_profile_type": "discipline_profile",
            "matched_profile_id": profile["profile_id"],
            "normalized_category": normalized_category or None,
            "profile": profile,
            "fallback_used": True,
            "fallback_reason": (
                "No IDEA category profile met the minimum sample threshold; using "
                "the supplied or provisionally mapped evaluation discipline."
            ),
            "score_effect": "none",
            "source_profile_set": manifest["profile_set_id"],
        }

    return {
        "matched_profile_type": "program_profile",
        "matched_profile_id": program_profile["profile_id"],
        "normalized_category": normalized_category or None,
        "profile": program_profile,
        "fallback_used": True,
        "fallback_reason": (
            "No IDEA high-sample category or discipline profile matched; using the "
            "program-wide observed context."
        ),
        "score_effect": "none",
        "source_profile_set": manifest["profile_set_id"],
    }


def _forbidden_paths(value: Any, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in FORBIDDEN_KEYS:
                findings.append(f"{path}.{key}")
            findings.extend(_forbidden_paths(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_forbidden_paths(child, f"{path}[{index}]"))
    return findings


def validate_if_benchmark_profiles() -> list[str]:
    errors: list[str] = []
    try:
        manifest = load_if_manifest()
        crosswalk_payload = load_if_category_crosswalk()
        discipline_payload = load_if_discipline_profiles()
        category_payload = load_if_category_profiles()
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return [str(exc)]

    files = {
        "manifest": manifest,
        "category_crosswalk": crosswalk_payload,
        "discipline_profiles": discipline_payload,
        "category_profiles": category_payload,
    }
    for label, payload in files.items():
        forbidden = _forbidden_paths(payload)
        if forbidden:
            errors.append(f"{label}: forbidden raw-data keys: {', '.join(forbidden[:5])}.")

    dataset = manifest.get("dataset", {})
    if manifest.get("score_effect") != "none":
        errors.append("if manifest: score_effect must be 'none'.")
    if manifest.get("profile_type") != "observed_winner_context":
        errors.append("if manifest: profile_type must be observed_winner_context.")
    snapshot_hash = str(manifest.get("source_snapshot_sha256", ""))
    if not re.fullmatch(r"[0-9a-f]{64}", snapshot_hash):
        errors.append("if manifest: source_snapshot_sha256 must be a SHA-256 hex digest.")

    crosswalk = crosswalk_payload.get("categories")
    if not isinstance(crosswalk, dict) or not crosswalk:
        errors.append("if crosswalk: categories must be a non-empty object.")
        crosswalk = {}
    if crosswalk_payload.get("category_count") != len(crosswalk):
        errors.append("if crosswalk: category_count does not match categories.")
    if dataset.get("normalized_category_count") != len(crosswalk):
        errors.append("if manifest: normalized_category_count does not match crosswalk.")

    disciplines = discipline_payload.get("profiles")
    if not isinstance(disciplines, dict):
        errors.append("if disciplines: profiles must be an object.")
        disciplines = {}
    if len(disciplines) != 9 or discipline_payload.get("profile_count") != 9:
        errors.append(f"if disciplines: expected 9 profiles, found {len(disciplines)}.")
    if dataset.get("discipline_profile_count") != len(disciplines):
        errors.append("if manifest: discipline_profile_count does not match profiles.")
    for profile_id, profile in disciplines.items():
        if profile.get("evaluation_discipline") != profile_id:
            errors.append(f"if discipline {profile_id}: evaluation_discipline mismatch.")
        if profile.get("score_effect") != "none":
            errors.append(f"if discipline {profile_id}: score_effect must be none.")

    categories = category_payload.get("profiles")
    if not isinstance(categories, dict):
        errors.append("if categories: profiles must be an object.")
        categories = {}
    minimum = category_payload.get("minimum_sample_size")
    if not isinstance(minimum, int) or minimum < 30:
        errors.append("if categories: minimum_sample_size must be an integer >= 30.")
        minimum = 30
    if category_payload.get("profile_count") != len(categories):
        errors.append("if categories: profile_count does not match profiles.")
    if dataset.get("category_profile_count") != len(categories):
        errors.append("if manifest: category_profile_count does not match profiles.")
    for category, profile in categories.items():
        if category not in crosswalk:
            errors.append(f"if category {category}: missing crosswalk entry.")
        sample_size = profile.get("observed_metrics", {}).get("sample_size")
        if not isinstance(sample_size, int) or sample_size < minimum:
            errors.append(f"if category {category}: sample size below threshold.")
        if profile.get("score_effect") != "none":
            errors.append(f"if category {category}: score_effect must be none.")

    privacy = manifest.get("privacy", {})
    if privacy.get("aggregate_only") is not True or privacy.get("raw_records_published") is not False:
        errors.append("if manifest: aggregate-only privacy policy is required.")
    return errors


def validate_if_student_benchmark_profiles() -> list[str]:
    errors: list[str] = []
    try:
        manifest = load_if_student_manifest()
        crosswalk_payload = load_if_student_category_crosswalk()
        competition = load_if_student_competition_profile()
        category_payload = load_if_student_category_profiles()
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return [str(exc)]

    files = {
        "manifest": manifest,
        "category_crosswalk": crosswalk_payload,
        "competition_profile": competition,
        "category_profiles": category_payload,
    }
    for label, payload in files.items():
        forbidden = _forbidden_paths(payload)
        if forbidden:
            errors.append(
                f"if student {label}: forbidden raw-data keys: {', '.join(forbidden[:5])}."
            )

    dataset = manifest.get("dataset", {})
    if manifest.get("profile_type") != "observed_student_winner_context":
        errors.append(
            "if student manifest: profile_type must be observed_student_winner_context."
        )
    if manifest.get("score_effect") != "none":
        errors.append("if student manifest: score_effect must be 'none'.")
    if manifest.get("maturity_gate") != {
        "allowed": ["student_concept"],
        "rejected": ["mature_work"],
        "on_rejected": "raise_error",
    }:
        errors.append("if student manifest: exact student-concept maturity gate is required.")
    snapshot_hash = str(manifest.get("source_snapshot_sha256", ""))
    if not re.fullmatch(r"[0-9a-f]{64}", snapshot_hash):
        errors.append(
            "if student manifest: source_snapshot_sha256 must be a SHA-256 hex digest."
        )

    if dataset.get("row_count") != 427:
        errors.append("if student manifest: expected 427 rows.")
    if dataset.get("normalized_category_count") != 15:
        errors.append("if student manifest: expected 15 normalized SDG themes.")
    if dataset.get("category_profile_count") != 6:
        errors.append("if student manifest: expected 6 high-sample theme profiles.")
    if dataset.get("minimum_category_sample_size") != 30:
        errors.append("if student manifest: minimum category sample must be 30.")

    crosswalk = crosswalk_payload.get("categories")
    if not isinstance(crosswalk, dict):
        errors.append("if student crosswalk: categories must be an object.")
        crosswalk = {}
    if len(crosswalk) != 15 or crosswalk_payload.get("category_count") != 15:
        errors.append(
            f"if student crosswalk: expected 15 SDG themes, found {len(crosswalk)}."
        )
    for category, mapping in crosswalk.items():
        if mapping.get("discipline_inference") != "not_allowed_from_sdg_category":
            errors.append(
                f"if student category {category}: discipline inference must be disabled."
            )

    if competition.get("allowed_maturity") != "student_concept":
        errors.append("if student competition profile: student_concept is required.")
    if competition.get("score_effect") != "none":
        errors.append("if student competition profile: score_effect must be none.")
    if competition.get("observed_metrics", {}).get("sample_size") != 427:
        errors.append("if student competition profile: expected sample size 427.")

    profiles = category_payload.get("profiles")
    if not isinstance(profiles, dict):
        errors.append("if student categories: profiles must be an object.")
        profiles = {}
    if len(profiles) != 6 or category_payload.get("profile_count") != 6:
        errors.append(
            f"if student categories: expected 6 profiles, found {len(profiles)}."
        )
    if category_payload.get("minimum_sample_size") != 30:
        errors.append("if student categories: minimum_sample_size must equal 30.")
    for category, profile in profiles.items():
        if category not in crosswalk:
            errors.append(f"if student category {category}: missing crosswalk entry.")
        if profile.get("allowed_maturity") != "student_concept":
            errors.append(f"if student category {category}: student_concept is required.")
        if profile.get("discipline_inference") != "not_allowed_from_sdg_category":
            errors.append(f"if student category {category}: discipline inference is enabled.")
        sample_size = profile.get("observed_metrics", {}).get("sample_size")
        if not isinstance(sample_size, int) or sample_size < 30:
            errors.append(f"if student category {category}: sample size below 30.")
        if profile.get("score_effect") != "none":
            errors.append(f"if student category {category}: score_effect must be none.")

    privacy = manifest.get("privacy", {})
    if (
        privacy.get("aggregate_only") is not True
        or privacy.get("raw_records_published") is not False
    ):
        errors.append("if student manifest: aggregate-only privacy policy is required.")
    return errors


def validate_red_dot_benchmark_profiles() -> list[str]:
    errors: list[str] = []
    try:
        manifest = load_red_dot_manifest()
        crosswalk_payload = load_red_dot_category_crosswalk()
        competition_payload = load_red_dot_competition_profiles()
        discipline_payload = load_red_dot_discipline_profiles()
        category_payload = load_red_dot_category_profiles()
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return [str(exc)]

    files = {
        "manifest": manifest,
        "category_crosswalk": crosswalk_payload,
        "competition_profiles": competition_payload,
        "discipline_profiles": discipline_payload,
        "category_profiles": category_payload,
    }
    for label, payload in files.items():
        forbidden = _forbidden_paths(payload)
        if forbidden:
            errors.append(
                f"red dot {label}: forbidden raw-data keys: {', '.join(forbidden[:5])}."
            )

    dataset = manifest.get("dataset", {})
    if manifest.get("profile_type") != "observed_winner_context":
        errors.append("red dot manifest: profile_type must be observed_winner_context.")
    if manifest.get("score_effect") != "none":
        errors.append("red dot manifest: score_effect must be 'none'.")
    if dataset.get("row_count") != 10030:
        errors.append("red dot manifest: expected 10030 usable rows.")
    snapshot_hash = str(manifest.get("source_snapshot_sha256", ""))
    if not re.fullmatch(r"[0-9a-f]{64}", snapshot_hash):
        errors.append("red dot manifest: source_snapshot_sha256 must be a SHA-256 hex digest.")

    expected_competitions = {
        "Product Design",
        "Brands & Communication Design",
        "Design Concept",
    }
    competitions = competition_payload.get("profiles")
    if not isinstance(competitions, dict):
        errors.append("red dot competitions: profiles must be an object.")
        competitions = {}
    if set(competitions) != expected_competitions or competition_payload.get("profile_count") != 3:
        errors.append("red dot competitions: exact three official competition lines are required.")
    for competition, profile in competitions.items():
        if profile.get("source_competition") != competition:
            errors.append(f"red dot competition {competition}: source_competition mismatch.")
        if profile.get("score_effect") != "none":
            errors.append(f"red dot competition {competition}: score_effect must be none.")

    crosswalk = crosswalk_payload.get("categories")
    if not isinstance(crosswalk, dict) or not crosswalk:
        errors.append("red dot crosswalk: categories must be a non-empty object.")
        crosswalk = {}
    if crosswalk_payload.get("category_count") != len(crosswalk):
        errors.append("red dot crosswalk: category_count does not match categories.")
    if dataset.get("normalized_category_count") != len(crosswalk):
        errors.append("red dot manifest: normalized_category_count does not match crosswalk.")

    disciplines = discipline_payload.get("profiles")
    if not isinstance(disciplines, dict):
        errors.append("red dot disciplines: profiles must be an object.")
        disciplines = {}
    if len(disciplines) != 9 or discipline_payload.get("profile_count") != 9:
        errors.append(f"red dot disciplines: expected 9 profiles, found {len(disciplines)}.")
    for profile_id, profile in disciplines.items():
        if profile.get("evaluation_discipline") != profile_id:
            errors.append(f"red dot discipline {profile_id}: evaluation_discipline mismatch.")
        if profile.get("score_effect") != "none":
            errors.append(f"red dot discipline {profile_id}: score_effect must be none.")

    categories = category_payload.get("profiles")
    if not isinstance(categories, dict):
        errors.append("red dot categories: profiles must be an object.")
        categories = {}
    minimum = category_payload.get("minimum_sample_size")
    if not isinstance(minimum, int) or minimum < 30:
        errors.append("red dot categories: minimum_sample_size must be an integer >= 30.")
        minimum = 30
    if category_payload.get("profile_count") != len(categories):
        errors.append("red dot categories: profile_count does not match profiles.")
    for category, profile in categories.items():
        if category not in crosswalk:
            errors.append(f"red dot category {category}: missing crosswalk entry.")
        sample_size = profile.get("observed_metrics", {}).get("sample_size")
        if not isinstance(sample_size, int) or sample_size < minimum:
            errors.append(f"red dot category {category}: sample size below threshold.")
        if profile.get("score_effect") != "none":
            errors.append(f"red dot category {category}: score_effect must be none.")

    privacy = manifest.get("privacy", {})
    if privacy.get("aggregate_only") is not True or privacy.get("raw_records_published") is not False:
        errors.append("red dot manifest: aggregate-only privacy policy is required.")
    return errors


def validate_idea_benchmark_profiles() -> list[str]:
    errors: list[str] = []
    try:
        manifest = load_idea_manifest()
        crosswalk_payload = load_idea_category_crosswalk()
        program = load_idea_program_profile()
        discipline_payload = load_idea_discipline_profiles()
        category_payload = load_idea_category_profiles()
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return [str(exc)]

    files = {
        "manifest": manifest,
        "category_crosswalk": crosswalk_payload,
        "program_profile": program,
        "discipline_profiles": discipline_payload,
        "category_profiles": category_payload,
    }
    for label, payload in files.items():
        forbidden = _forbidden_paths(payload)
        if forbidden:
            errors.append(
                f"idea {label}: forbidden raw-data keys: {', '.join(forbidden[:5])}."
            )

    dataset = manifest.get("dataset", {})
    if manifest.get("profile_type") != "observed_recognized_context":
        errors.append("idea manifest: profile_type must be observed_recognized_context.")
    if manifest.get("score_effect") != "none":
        errors.append("idea manifest: score_effect must be 'none'.")
    if dataset.get("row_count") != 1024:
        errors.append("idea manifest: expected 1024 usable rows.")
    expected_counts = {
        "source_category_count": 25,
        "normalized_category_count": 24,
        "program_profile_count": 1,
        "discipline_profile_count": 9,
        "category_profile_count": 12,
        "minimum_category_sample_size": 30,
        "student_category_count": 74,
    }
    for key, expected in expected_counts.items():
        if dataset.get(key) != expected:
            errors.append(f"idea manifest: expected {key}={expected}.")
    snapshot_hash = str(manifest.get("source_snapshot_sha256", ""))
    if not re.fullmatch(r"[0-9a-f]{64}", snapshot_hash):
        errors.append("idea manifest: source_snapshot_sha256 must be a SHA-256 hex digest.")
    if manifest.get("maturity_gate") != {
        "category": "Student Designs",
        "allowed": ["student_concept"],
        "rejected": ["mature_work"],
        "on_rejected": "raise_error",
    }:
        errors.append("idea manifest: exact Student Designs maturity gate is required.")

    crosswalk = crosswalk_payload.get("categories")
    if not isinstance(crosswalk, dict) or not crosswalk:
        errors.append("idea crosswalk: categories must be a non-empty object.")
        crosswalk = {}
    if len(crosswalk) != 24 or crosswalk_payload.get("category_count") != 24:
        errors.append(f"idea crosswalk: expected 24 normalized categories, found {len(crosswalk)}.")
    student_mapping = crosswalk.get("Student Designs", {})
    if student_mapping.get("evaluation_disciplines") != []:
        errors.append("idea Student Designs: evaluation disciplines must be empty.")
    if student_mapping.get("discipline_inference") != "not_allowed_from_student_category":
        errors.append("idea Student Designs: discipline inference must be disabled.")
    if student_mapping.get("allowed_maturity") != "student_concept":
        errors.append("idea Student Designs: student_concept maturity is required.")

    if program.get("observed_metrics", {}).get("sample_size") != 1024:
        errors.append("idea program profile: expected sample size 1024.")
    if program.get("score_effect") != "none":
        errors.append("idea program profile: score_effect must be none.")

    disciplines = discipline_payload.get("profiles")
    if not isinstance(disciplines, dict):
        errors.append("idea disciplines: profiles must be an object.")
        disciplines = {}
    if len(disciplines) != 9 or discipline_payload.get("profile_count") != 9:
        errors.append(f"idea disciplines: expected 9 profiles, found {len(disciplines)}.")
    if discipline_payload.get("membership_rule") != "multi_label_non_additive":
        errors.append("idea disciplines: multi-label non-additive membership is required.")
    for profile_id, profile in disciplines.items():
        if profile.get("evaluation_discipline") != profile_id:
            errors.append(f"idea discipline {profile_id}: evaluation_discipline mismatch.")
        if profile.get("membership_rule") != "multi_label_non_additive":
            errors.append(f"idea discipline {profile_id}: membership rule mismatch.")
        if profile.get("score_effect") != "none":
            errors.append(f"idea discipline {profile_id}: score_effect must be none.")

    categories = category_payload.get("profiles")
    if not isinstance(categories, dict):
        errors.append("idea categories: profiles must be an object.")
        categories = {}
    if len(categories) != 12 or category_payload.get("profile_count") != 12:
        errors.append(f"idea categories: expected 12 profiles, found {len(categories)}.")
    if category_payload.get("minimum_sample_size") != 30:
        errors.append("idea categories: minimum sample size must equal 30.")
    for category, profile in categories.items():
        if category not in crosswalk:
            errors.append(f"idea category {category}: missing crosswalk entry.")
        sample_size = profile.get("observed_metrics", {}).get("sample_size")
        if not isinstance(sample_size, int) or sample_size < 30:
            errors.append(f"idea category {category}: sample size below 30.")
        if profile.get("score_effect") != "none":
            errors.append(f"idea category {category}: score_effect must be none.")
    student_profile = categories.get("Student Designs", {})
    if student_profile.get("allowed_maturity") != "student_concept":
        errors.append("idea Student Designs profile: student_concept maturity is required.")
    if student_profile.get("discipline_inference") != "not_allowed_from_student_category":
        errors.append("idea Student Designs profile: discipline inference must be disabled.")

    privacy = manifest.get("privacy", {})
    if privacy.get("aggregate_only") is not True or privacy.get("raw_records_published") is not False:
        errors.append("idea manifest: aggregate-only privacy policy is required.")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve bundled iF benchmark context.")
    parser.add_argument(
        "--source",
        choices=(
            "if_observed_winners",
            "if_student_observed_winners",
            "red_dot_observed_winners",
            "idea_observed_recognized",
        ),
        default="if_observed_winners",
    )
    parser.add_argument("--category")
    parser.add_argument("--discipline")
    parser.add_argument("--competition")
    parser.add_argument("--maturity", choices=("student_concept", "mature_work"))
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    if args.validate:
        errors = [
            *(f"if: {error}" for error in validate_if_benchmark_profiles()),
            *(
                f"if_student: {error}"
                for error in validate_if_student_benchmark_profiles()
            ),
            *(
                f"red_dot: {error}"
                for error in validate_red_dot_benchmark_profiles()
            ),
            *(
                f"idea: {error}"
                for error in validate_idea_benchmark_profiles()
            ),
        ]
        payload: dict[str, Any] = {"valid": not errors, "errors": errors}
        exit_code = 0 if not errors else 2
    elif args.source == "if_student_observed_winners":
        if not args.maturity:
            parser.error("--maturity is required for iF Student benchmark context")
        payload = resolve_if_student_benchmark(
            maturity=args.maturity, category=args.category
        )
        exit_code = 0
    elif args.source == "red_dot_observed_winners":
        payload = resolve_red_dot_benchmark(
            category=args.category,
            competition=args.competition,
            discipline=args.discipline,
        )
        exit_code = 0
    elif args.source == "idea_observed_recognized":
        payload = resolve_idea_benchmark(
            maturity=args.maturity,
            category=args.category,
            discipline=args.discipline,
        )
        exit_code = 0
    else:
        payload = resolve_if_benchmark(category=args.category, discipline=args.discipline)
        exit_code = 0
    json.dump(payload, fp=__import__("sys").stdout, ensure_ascii=False, indent=2 if args.pretty else None)
    print()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
