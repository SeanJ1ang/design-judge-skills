"""Load and validate the dependency-free JSON award profiles."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse


SKILL_ROOT = Path(__file__).resolve().parents[1]
REFERENCES = SKILL_ROOT / "references"
AWARDS_DIR = REFERENCES / "awards"
INDEX_PATH = AWARDS_DIR / "index.json"
CRITERIA_PATH = REFERENCES / "criteria-crosswalk.json"
CATEGORY_PATH = REFERENCES / "category-crosswalk.json"

REQUIRED_PROFILE_KEYS = {
    "award_id",
    "brand",
    "program",
    "status",
    "official_domains",
    "official_sources",
    "routes",
    "category_hints",
    "criteria",
    "dynamic_fields",
    "last_profile_reviewed",
}
REQUIRED_SOURCE_KEYS = {
    "overview",
    "eligibility",
    "categories",
    "criteria",
    "submission",
    "winners",
}
REQUIRED_ROUTE_KEYS = {
    "route_id",
    "label",
    "entrant_types",
    "project_states",
    "required_project_fields",
    "dynamic_gates",
}
RELATIONS = {"exact", "adjacent", "broad", "live-lookup"}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_index() -> dict[str, Any]:
    return read_json(INDEX_PATH)


def resolve_award_ids(values: Iterable[str]) -> set[str]:
    """Resolve profile ids and declared aliases case-insensitively."""
    index = load_index()
    lookup: dict[str, str] = {}
    for entry in index["supported_awards"]:
        award_id = entry["award_id"]
        for value in [award_id, *entry.get("aliases", [])]:
            key = str(value).strip().casefold()
            existing = lookup.get(key)
            if existing and existing != award_id:
                raise ValueError(f"Ambiguous award alias: {value}")
            lookup[key] = award_id

    resolved: set[str] = set()
    unknown: list[str] = []
    for value in values:
        key = str(value).strip().casefold()
        if key in lookup:
            resolved.add(lookup[key])
        else:
            unknown.append(str(value))
    if unknown:
        raise ValueError(f"Unsupported award id or alias(es): {', '.join(sorted(unknown))}")
    return resolved


def load_profiles(award_ids: Iterable[str] | None = None) -> list[dict[str, Any]]:
    index = load_index()
    requested = resolve_award_ids(award_ids or [])

    profiles = []
    for entry in index["supported_awards"]:
        if requested and entry["award_id"] not in requested:
            continue
        profile = read_json(AWARDS_DIR / entry["file"])
        profiles.append(profile)
    return profiles


def _host_matches(host: str, domains: list[str]) -> bool:
    host = host.lower().split(":", 1)[0]
    return any(host == domain or host.endswith("." + domain) for domain in domains)


def validate_profile(profile: dict[str, Any], normalized: set[str]) -> list[str]:
    errors: list[str] = []
    award_id = str(profile.get("award_id", "<missing>"))

    missing = REQUIRED_PROFILE_KEYS - profile.keys()
    if missing:
        errors.append(f"{award_id}: missing profile keys: {', '.join(sorted(missing))}")
        return errors

    domains = profile["official_domains"]
    if not isinstance(domains, list) or not domains:
        errors.append(f"{award_id}: official_domains must be a non-empty list")

    sources = profile["official_sources"]
    missing_sources = REQUIRED_SOURCE_KEYS - sources.keys()
    if missing_sources:
        errors.append(
            f"{award_id}: missing official source keys: {', '.join(sorted(missing_sources))}"
        )
    for key, value in sources.items():
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            errors.append(f"{award_id}: invalid URL for official_sources.{key}")
        elif domains and not _host_matches(parsed.netloc, domains):
            errors.append(f"{award_id}: source host outside official_domains: {value}")

    routes = profile["routes"]
    category_config = read_json(CATEGORY_PATH)
    allowed_entrants = set(category_config["entrant_types"])
    allowed_states = set(category_config["project_states"])
    allowed_categories = set(category_config["canonical_categories"])
    route_ids: set[str] = set()
    if not isinstance(routes, list) or not routes:
        errors.append(f"{award_id}: routes must be a non-empty list")
    else:
        for route in routes:
            route_missing = REQUIRED_ROUTE_KEYS - route.keys()
            route_id = str(route.get("route_id", "<missing>"))
            if route_missing:
                errors.append(
                    f"{award_id}/{route_id}: missing route keys: "
                    + ", ".join(sorted(route_missing))
                )
            if route_id in route_ids:
                errors.append(f"{award_id}: duplicate route_id {route_id}")
            route_ids.add(route_id)
            if not route.get("entrant_types"):
                errors.append(f"{award_id}/{route_id}: entrant_types is empty")
            else:
                unknown_entrants = set(route["entrant_types"]) - allowed_entrants
                if unknown_entrants:
                    errors.append(
                        f"{award_id}/{route_id}: unknown entrant types: "
                        + ", ".join(sorted(unknown_entrants))
                    )
            if not route.get("project_states"):
                errors.append(f"{award_id}/{route_id}: project_states is empty")
            else:
                unknown_states = set(route["project_states"]) - allowed_states
                if unknown_states:
                    errors.append(
                        f"{award_id}/{route_id}: unknown project states: "
                        + ", ".join(sorted(unknown_states))
                    )

    for canonical, hints in profile["category_hints"].items():
        if canonical not in allowed_categories:
            errors.append(f"{award_id}: unknown canonical category {canonical}")
        if not isinstance(hints, list):
            errors.append(f"{award_id}: category_hints.{canonical} must be a list")
            continue
        for hint in hints:
            if hint.get("route_id") not in route_ids:
                errors.append(
                    f"{award_id}: category hint references unknown route {hint.get('route_id')}"
                )
            if hint.get("relation") not in RELATIONS:
                errors.append(f"{award_id}: invalid category relation {hint.get('relation')}")

    for criterion in profile["criteria"]:
        dimension = criterion.get("normalized_dimension")
        if dimension not in normalized:
            errors.append(f"{award_id}: unknown normalized criterion {dimension}")

    if not isinstance(profile["dynamic_fields"], list) or not profile["dynamic_fields"]:
        errors.append(f"{award_id}: dynamic_fields must be a non-empty list")

    for value in profile.get("winner_sources", []):
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            errors.append(f"{award_id}: invalid winner source URL: {value}")
        elif domains and not _host_matches(parsed.netloc, domains):
            errors.append(f"{award_id}: winner source host outside official_domains: {value}")

    try:
        date.fromisoformat(profile["last_profile_reviewed"])
    except (TypeError, ValueError):
        errors.append(f"{award_id}: last_profile_reviewed must be YYYY-MM-DD")

    return errors


def validate_all() -> list[str]:
    index = load_index()
    errors: list[str] = []
    entries = index.get("supported_awards", [])
    ids = [entry.get("award_id") for entry in entries]
    files = [entry.get("file") for entry in entries]
    if len(ids) != len(set(ids)):
        errors.append("index: duplicate award_id")
    if len(files) != len(set(files)):
        errors.append("index: duplicate profile file")
    alias_owners: dict[str, str] = {}
    for entry in entries:
        award_id = str(entry.get("award_id"))
        for alias in [award_id, *entry.get("aliases", [])]:
            key = str(alias).strip().casefold()
            owner = alias_owners.get(key)
            if owner and owner != award_id:
                errors.append(f"index: alias '{alias}' maps to both {owner} and {award_id}")
            alias_owners[key] = award_id

    normalized = set(read_json(CRITERIA_PATH)["normalized_dimensions"])
    for entry in entries:
        path = AWARDS_DIR / entry["file"]
        if not path.is_file():
            errors.append(f"index: missing profile file {entry['file']}")
            continue
        try:
            profile = read_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{entry['file']}: cannot read JSON: {exc}")
            continue
        if profile.get("award_id") != entry.get("award_id"):
            errors.append(f"{entry['file']}: award_id does not match index")
        errors.extend(validate_profile(profile, normalized))
    return errors
