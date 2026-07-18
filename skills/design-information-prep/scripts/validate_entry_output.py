#!/usr/bin/env python3
"""Validate prepared award-entry text against limits and dossier provenance."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from field_spec_utils import load_json, load_spec, select_route, validate_spec
from prepare_entry_packet import has_value, validate_dossier


SEVERITY_ORDER = {"Blocker": 0, "Important": 1, "Optimization": 2}
WORD_PATTERN = re.compile(r"\b[\w]+(?:[-'’][\w]+)*\b", re.UNICODE)


def count_text(text: str, unit: str) -> int:
    if unit == "characters":
        return len(text)
    if unit == "words":
        return len(WORD_PATTERN.findall(text))
    raise ValueError(f"Unsupported length unit: {unit}")


def finding(severity: str, field_id: str, message: str, action: str) -> dict[str, str]:
    return {"severity": severity, "field_id": field_id, "finding": message, "required_action": action}


def is_empty_text(value: Any) -> bool:
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, list):
        return not value or not any(isinstance(item, str) and item.strip() for item in value)
    return True


def validate_entry(dossier: dict[str, Any], entry: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    errors = validate_dossier(dossier) + validate_spec(spec, str(spec.get("award_id", "spec")))
    if errors:
        raise ValueError("; ".join(errors))
    if entry.get("award_id") != spec.get("award_id"):
        raise ValueError("entry award_id does not match the selected specification")
    route = select_route(spec, str(entry.get("route_id", "")) or None)
    if entry.get("cycle") != spec.get("cycle"):
        raise ValueError("entry cycle does not match the selected specification")
    entry_fields = entry.get("fields")
    if not isinstance(entry_fields, dict):
        raise ValueError("entry fields must be an object")
    facts = dossier["facts"]
    rules = {field["field_id"]: field for field in route["fields"]}
    findings: list[dict[str, str]] = []
    measurements: dict[str, Any] = {}

    unknown_fields = sorted(set(entry_fields) - set(rules))
    for field_id in unknown_fields:
        findings.append(finding("Important", field_id, "Field is not defined for the selected award route.", "Remove it or select the correct route."))

    for field_id, rule in rules.items():
        payload = entry_fields.get(field_id)
        if payload is None:
            if rule["required"]:
                findings.append(finding("Blocker", field_id, "Required field is missing.", "Draft the required field from supported dossier facts."))
            continue
        if not isinstance(payload, dict):
            findings.append(finding("Blocker", field_id, "Field payload must be an object.", "Provide text and used_fact_ids."))
            continue
        text = payload.get("text")
        used_ids = payload.get("used_fact_ids")
        if is_empty_text(text):
            severity = "Blocker" if rule["required"] else "Optimization"
            findings.append(finding(severity, field_id, "Field text is empty.", "Add supported text or remove the optional field."))
            continue
        if not isinstance(used_ids, list) or not all(isinstance(item, str) for item in used_ids):
            findings.append(finding("Blocker", field_id, "used_fact_ids must be a list of fact ids.", "Record the dossier facts used to draft this field."))
            used_ids = []
        if rule["value_type"] == "string" and not isinstance(text, str):
            findings.append(finding("Blocker", field_id, "Field requires a string.", "Provide one text string."))
            continue
        if rule["value_type"] == "list" and not isinstance(text, list):
            findings.append(finding("Blocker", field_id, "Field requires a list.", "Provide a list of text items."))
            continue

        source_facts = set(rule.get("source_facts", []))
        essential = set(rule.get("essential_facts", []))
        used_set = set(used_ids)
        unsupported_ids = sorted(used_set - source_facts)
        if unsupported_ids:
            findings.append(finding("Blocker", field_id, f"Facts are not allowed by this field mapping: {unsupported_ids}.", "Use only the mapped dossier facts or update the verified field specification."))
        missing_used = sorted(fact_id for fact_id in used_set if not has_value(facts.get(fact_id)))
        if missing_used:
            findings.append(finding("Blocker", field_id, f"Used facts are absent or marked missing: {missing_used}.", "Supply evidence or remove the unsupported claims."))
        omitted_essential = sorted(fact_id for fact_id in essential if not has_value(facts.get(fact_id)))
        if omitted_essential and rule["required"]:
            findings.append(finding("Blocker", field_id, f"Essential dossier facts are missing: {omitted_essential}.", "Ask the user for the missing facts before finalizing."))
        if source_facts and not used_set:
            findings.append(finding("Blocker", field_id, "No dossier fact provenance is recorded.", "Add used_fact_ids for the claims in this field."))
        for fact_id in sorted(used_set & source_facts):
            fact = facts.get(fact_id, {})
            if fact.get("status") == "inferred" or fact.get("user_confirmation_required"):
                findings.append(finding("Important", field_id, f"Fact {fact_id!r} requires user confirmation.", "Confirm the fact and update its dossier status before submission."))
            if fact.get("status") not in {"missing", None} and not fact.get("evidence"):
                findings.append(finding("Important", field_id, f"Fact {fact_id!r} has no evidence record.", "Add an attachment locator or user confirmation."))

        if isinstance(text, str):
            observed: dict[str, int] = {}
            if "max_length" in rule or "min_length" in rule:
                unit = rule["length_unit"]
                count = count_text(text, unit)
                observed[unit] = count
                if "min_length" in rule and count < int(rule["min_length"]):
                    findings.append(finding("Blocker", field_id, f"Observed {count} {unit}; minimum is {rule['min_length']}.", "Add supported detail without inventing claims."))
                if "max_length" in rule and count > int(rule["max_length"]):
                    findings.append(finding("Blocker", field_id, f"Observed {count} {unit}; maximum is {rule['max_length']}.", "Shorten the field without removing required evidence."))
            measurements[field_id] = observed
        else:
            measurements[field_id] = {"items": len(text)}
            if len(text) > int(rule.get("max_items", len(text))):
                findings.append(finding("Blocker", field_id, f"Observed {len(text)} items; maximum is {rule['max_items']}.", "Remove or consolidate list items."))
            if "item_max_length" in rule:
                unit = rule["item_length_unit"]
                item_counts = [count_text(str(item), unit) for item in text]
                measurements[field_id][f"item_{unit}"] = item_counts
                for index, count in enumerate(item_counts, start=1):
                    if count > int(rule["item_max_length"]):
                        findings.append(finding("Blocker", field_id, f"Item {index} has {count} {unit}; maximum is {rule['item_max_length']}.", "Shorten that list item."))
            if "max_length" in rule or "min_length" in rule:
                unit = rule["length_unit"]
                total = count_text("\n".join(str(item) for item in text), unit)
                measurements[field_id][f"total_{unit}"] = total
                if "min_length" in rule and total < int(rule["min_length"]):
                    findings.append(finding("Blocker", field_id, f"List totals {total} {unit}; minimum is {rule['min_length']}.", "Add supported detail without inventing claims."))
                if "max_length" in rule and total > int(rule["max_length"]):
                    findings.append(finding("Blocker", field_id, f"List totals {total} {unit}; maximum is {rule['max_length']}.", "Shorten or consolidate the list items."))

    findings.sort(key=lambda item: (SEVERITY_ORDER[item["severity"]], item["field_id"], item["finding"]))
    counts = Counter(item["severity"] for item in findings)
    decision = "Not ready" if counts["Blocker"] else ("Conditionally ready" if counts["Important"] else "Ready")
    return {
        "decision": decision,
        "award_id": spec["award_id"],
        "route_id": route["route_id"],
        "cycle": spec["cycle"],
        "checked_on": spec["checked_on"],
        "finding_counts": {severity: counts[severity] for severity in SEVERITY_ORDER},
        "measurements": measurements,
        "findings": findings,
        "notice": "This validates field structure, limits, and provenance; it does not prove live portal acceptance or claim truth.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate prepared award-entry text.")
    parser.add_argument("--dossier", required=True, help="Project dossier JSON")
    parser.add_argument("--entry", required=True, help="Prepared entry JSON")
    parser.add_argument("--pretty", action="store_true", help="Indent JSON output")
    args = parser.parse_args()
    try:
        dossier = load_json(Path(args.dossier))
        entry = load_json(Path(args.entry))
        spec = load_spec(str(entry.get("award_id", "")))
        result = validate_entry(dossier, entry, spec)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2 if args.pretty else None)
    sys.stdout.write("\n")
    return 0 if result["decision"] == "Ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
