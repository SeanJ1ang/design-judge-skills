#!/usr/bin/env python3
"""Shared local utilities for design-information-prep field specifications."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


SKILL_DIR = Path(__file__).resolve().parents[1]
AWARD_DIR = SKILL_DIR / "references" / "awards"
VALID_UNITS = {"words", "characters"}
VALID_VALUE_TYPES = {"string", "list"}
VALID_PUBLICITY = {"public_if_awarded", "jury_only", "not_stated", "administrative"}


def load_json(path: Path | str) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: top-level JSON value must be an object.")
    return payload


def spec_path(award_id: str) -> Path:
    if not award_id or any(char not in "abcdefghijklmnopqrstuvwxyz0123456789-" for char in award_id):
        raise ValueError("award id must use lowercase letters, digits, and hyphens only.")
    path = AWARD_DIR / f"{award_id}.json"
    if not path.is_file():
        supported = ", ".join(sorted(item.stem for item in AWARD_DIR.glob("*.json")))
        raise ValueError(f"Unsupported award id {award_id!r}. Supported: {supported}")
    return path


def load_spec(award_id: str) -> dict[str, Any]:
    return load_json(spec_path(award_id))


def select_route(spec: dict[str, Any], route_id: str | None) -> dict[str, Any]:
    routes = spec.get("routes")
    if not isinstance(routes, list) or not routes:
        raise ValueError("Award specification has no routes.")
    if route_id is None:
        if len(routes) == 1:
            return routes[0]
        available = ", ".join(str(route.get("route_id")) for route in routes)
        raise ValueError(f"This award requires --route. Available routes: {available}")
    for route in routes:
        if route.get("route_id") == route_id:
            return route
    available = ", ".join(str(route.get("route_id")) for route in routes)
    raise ValueError(f"Unknown route {route_id!r}. Available routes: {available}")


def validate_spec(spec: dict[str, Any], source: str = "spec") -> list[str]:
    errors: list[str] = []
    required = ("schema_version", "award_id", "program", "cycle", "checked_on", "official_sources", "routes")
    for key in required:
        if key not in spec:
            errors.append(f"{source}: missing {key}")
    if spec.get("schema_version") != 1:
        errors.append(f"{source}: schema_version must be 1")
    try:
        date.fromisoformat(str(spec.get("checked_on", "")))
    except ValueError:
        errors.append(f"{source}: checked_on must be YYYY-MM-DD")

    sources = spec.get("official_sources")
    if not isinstance(sources, list) or not sources:
        errors.append(f"{source}: official_sources must be a non-empty list")
    else:
        for url in sources:
            parsed = urlparse(str(url))
            if parsed.scheme != "https" or not parsed.netloc:
                errors.append(f"{source}: invalid official source URL {url!r}")

    routes = spec.get("routes")
    if not isinstance(routes, list) or not routes:
        errors.append(f"{source}: routes must be a non-empty list")
        return errors
    route_ids: set[str] = set()
    for route in routes:
        if not isinstance(route, dict):
            errors.append(f"{source}: every route must be an object")
            continue
        route_id = str(route.get("route_id", ""))
        if not route_id:
            errors.append(f"{source}: route_id is required")
        elif route_id in route_ids:
            errors.append(f"{source}: duplicate route_id {route_id}")
        route_ids.add(route_id)
        fields = route.get("fields")
        if not isinstance(fields, list) or not fields:
            errors.append(f"{source}/{route_id}: fields must be a non-empty list")
            continue
        field_ids: set[str] = set()
        for field in fields:
            if not isinstance(field, dict):
                errors.append(f"{source}/{route_id}: every field must be an object")
                continue
            field_id = str(field.get("field_id", ""))
            prefix = f"{source}/{route_id}/{field_id or '[missing]'}"
            if not field_id:
                errors.append(f"{prefix}: field_id is required")
            elif field_id in field_ids:
                errors.append(f"{prefix}: duplicate field_id")
            field_ids.add(field_id)
            for key in ("label", "required", "value_type", "language", "source_facts", "essential_facts", "drafting_instructions"):
                if key not in field:
                    errors.append(f"{prefix}: missing {key}")
            if field.get("value_type") not in VALID_VALUE_TYPES:
                errors.append(f"{prefix}: invalid value_type")
            if "max_length" in field and field.get("length_unit") not in VALID_UNITS:
                errors.append(f"{prefix}: max_length requires a valid length_unit")
            if "min_length" in field and field.get("length_unit") not in VALID_UNITS:
                errors.append(f"{prefix}: min_length requires a valid length_unit")
            if "length_unit" in field and not ({"min_length", "max_length"} & set(field)):
                errors.append(f"{prefix}: length_unit requires min_length or max_length")
            if "min_length" in field and "max_length" in field:
                if int(field["min_length"]) > int(field["max_length"]):
                    errors.append(f"{prefix}: min_length cannot exceed max_length")
            if field.get("value_type") == "list":
                if int(field.get("max_items", 0)) < 1:
                    errors.append(f"{prefix}: list fields require max_items")
                if "item_max_length" in field and field.get("item_length_unit") not in VALID_UNITS:
                    errors.append(f"{prefix}: item_max_length requires item_length_unit")
            if field.get("publicity") not in VALID_PUBLICITY:
                errors.append(f"{prefix}: invalid or missing publicity")
            source_facts = field.get("source_facts", [])
            essential = field.get("essential_facts", [])
            if not isinstance(source_facts, list) or not isinstance(essential, list):
                errors.append(f"{prefix}: source_facts and essential_facts must be lists")
            elif not set(essential).issubset(source_facts):
                errors.append(f"{prefix}: essential_facts must be a subset of source_facts")
    return errors
