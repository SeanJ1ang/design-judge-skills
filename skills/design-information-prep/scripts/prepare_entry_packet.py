#!/usr/bin/env python3
"""Compile a user project dossier into an award-specific evidence packet."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from field_spec_utils import load_json, load_spec, select_route, validate_spec


USABLE_STATUSES = {"supported", "inferred", "confirmed_by_user"}
DOSSIER_SCHEMA = load_json(Path(__file__).resolve().parents[1] / "references" / "project-dossier-schema.json")
ALLOWED_FACT_IDS = set(DOSSIER_SCHEMA["properties"]["facts"]["propertyNames"]["enum"])
VALID_EVIDENCE_TYPES = {"direct", "derived", "user_confirmation"}
VALID_CONFIDENCE = {"high", "medium", "low", "unknown"}


def has_value(fact: dict[str, Any] | None) -> bool:
    if not isinstance(fact, dict) or fact.get("status") not in USABLE_STATUSES:
        return False
    value = fact.get("value")
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(str(item).strip() for item in value)
    return value is not None


def validate_dossier(dossier: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if dossier.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if not str(dossier.get("project_id", "")).strip():
        errors.append("project_id is required")
    attachments = dossier.get("attachments")
    authorized_sources: set[str] = set()
    if not isinstance(attachments, list):
        errors.append("attachments must be a list")
    else:
        for index, attachment in enumerate(attachments):
            if not isinstance(attachment, dict):
                errors.append(f"attachments[{index}]: attachment must be an object")
                continue
            source = str(attachment.get("source", "")).strip()
            if not source:
                errors.append(f"attachments[{index}]: source is required")
            if not isinstance(attachment.get("authorized"), bool):
                errors.append(f"attachments[{index}]: authorized must be boolean")
            elif attachment["authorized"] and source:
                authorized_sources.add(source)
    facts = dossier.get("facts")
    if not isinstance(facts, dict):
        errors.append("facts must be an object")
        return errors
    for fact_id, fact in facts.items():
        if fact_id not in ALLOWED_FACT_IDS:
            errors.append(f"{fact_id}: unknown fact id")
        if not isinstance(fact, dict):
            errors.append(f"{fact_id}: fact must be an object")
            continue
        status = fact.get("status")
        evidence = fact.get("evidence")
        if status not in {"supported", "inferred", "confirmed_by_user", "missing"}:
            errors.append(f"{fact_id}: invalid status")
        if fact.get("confidence") not in VALID_CONFIDENCE:
            errors.append(f"{fact_id}: invalid confidence")
        if not isinstance(fact.get("user_confirmation_required"), bool):
            errors.append(f"{fact_id}: user_confirmation_required must be boolean")
        if not isinstance(evidence, list):
            errors.append(f"{fact_id}: evidence must be a list")
        elif status in USABLE_STATUSES and has_value(fact) and not evidence:
            errors.append(f"{fact_id}: usable fact requires evidence")
        else:
            for index, record in enumerate(evidence):
                prefix = f"{fact_id}: evidence[{index}]"
                if not isinstance(record, dict):
                    errors.append(f"{prefix} must be an object")
                    continue
                source = str(record.get("source", "")).strip()
                evidence_type = record.get("evidence_type")
                if not source:
                    errors.append(f"{prefix} source is required")
                if evidence_type not in VALID_EVIDENCE_TYPES:
                    errors.append(f"{prefix} has invalid evidence_type")
                elif evidence_type in {"direct", "derived"} and source not in authorized_sources:
                    errors.append(f"{prefix} cites an attachment that is not authorized")
        if status == "missing" and has_value(fact):
            errors.append(f"{fact_id}: missing fact cannot contain a usable value")
    return errors


def prepare_packet(dossier: dict[str, Any], spec: dict[str, Any], route_id: str | None) -> dict[str, Any]:
    dossier_errors = validate_dossier(dossier)
    spec_errors = validate_spec(spec, str(spec.get("award_id", "spec")))
    if dossier_errors or spec_errors:
        raise ValueError("; ".join(dossier_errors + spec_errors))
    route = select_route(spec, route_id)
    facts = dossier["facts"]
    fields: list[dict[str, Any]] = []
    blocking_facts: set[str] = set()
    confirmation_facts: set[str] = set()
    for field in route["fields"]:
        source_ids = list(field.get("source_facts", []))
        essential_ids = list(field.get("essential_facts", []))
        available: dict[str, Any] = {}
        for fact_id in source_ids:
            fact = facts.get(fact_id)
            if has_value(fact):
                available[fact_id] = fact
                if fact.get("status") == "inferred" or fact.get("user_confirmation_required"):
                    confirmation_facts.add(fact_id)
        missing_essential = [fact_id for fact_id in essential_ids if not has_value(facts.get(fact_id))]
        if field.get("required") and missing_essential:
            blocking_facts.update(missing_essential)
            readiness = "needs_input"
        elif available:
            readiness = "ready_to_draft"
        elif field.get("required"):
            readiness = "needs_input"
        else:
            readiness = "optional_no_evidence"
        fields.append({
            "field_id": field["field_id"],
            "label": field["label"],
            "required": field["required"],
            "value_type": field["value_type"],
            "language": field["language"],
            "limit": {key: field[key] for key in ("min_length", "max_length", "length_unit", "max_items", "item_max_length", "item_length_unit") if key in field},
            "publicity": field.get("publicity"),
            "drafting_instructions": field["drafting_instructions"],
            "readiness": readiness,
            "missing_essential_facts": missing_essential,
            "available_facts": available,
        })
    return {
        "award_id": spec["award_id"],
        "program": spec["program"],
        "cycle": spec["cycle"],
        "checked_on": spec["checked_on"],
        "route_id": route["route_id"],
        "route_label": route["label"],
        "project_id": dossier["project_id"],
        "confidentiality": dossier.get("confidentiality", "restricted"),
        "fields": fields,
        "blocking_fact_ids": sorted(blocking_facts),
        "confirmation_fact_ids": sorted(confirmation_facts),
        "official_sources": spec["official_sources"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare an award-specific evidence packet.")
    parser.add_argument("--dossier", required=True, help="Project dossier JSON")
    parser.add_argument("--award", required=True, help="Supported award id")
    parser.add_argument("--route", help="Award route id; required when the award has multiple routes")
    parser.add_argument("--pretty", action="store_true", help="Indent JSON output")
    args = parser.parse_args()
    try:
        dossier = load_json(Path(args.dossier))
        spec = load_spec(args.award)
        result = prepare_packet(dossier, spec, args.route)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2 if args.pretty else None)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
