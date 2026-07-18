#!/usr/bin/env python3
"""Check a submission manifest against structured award requirements."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any


SEVERITY_ORDER = {"Blocker": 0, "Important": 1, "Optimization": 2}
RIGHTS_STATUSES = {"cleared", "pending", "unknown", "restricted"}


def finding(
    severity: str,
    requirement_id: str,
    item: str,
    message: str,
    action: str,
) -> dict[str, str]:
    return {
        "severity": severity,
        "requirement_id": requirement_id,
        "item": item,
        "finding": message,
        "required_action": action,
    }


def load_json(path: str) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: top-level JSON value must be an object.")
    return payload


def validate_rules(rules: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if not str(rules.get("official_source_url", "")).strip():
        findings.append(
            finding(
                "Blocker",
                "RULE-SOURCE",
                "rules",
                "No current official rule source is recorded.",
                "Record the direct official rule URL for this exact cycle and stage.",
            )
        )
    checked_on = str(rules.get("checked_on", "")).strip()
    try:
        date.fromisoformat(checked_on)
    except ValueError:
        findings.append(
            finding(
                "Important",
                "RULE-FRESHNESS",
                "rules",
                "The rule check date is missing or is not YYYY-MM-DD.",
                "Verify the official rules and record the check date.",
            )
        )

    requirements = rules.get("requirements")
    if not isinstance(requirements, list) or not requirements:
        raise ValueError("Rules require a non-empty 'requirements' list.")
    ids = [str(rule.get("id", "")).strip() for rule in requirements if isinstance(rule, dict)]
    if len(ids) != len(requirements) or any(not value for value in ids):
        raise ValueError("Every requirement must be an object with a non-empty 'id'.")
    duplicates = [key for key, count in Counter(ids).items() if count > 1]
    if duplicates:
        raise ValueError(f"Duplicate requirement IDs: {', '.join(duplicates)}")
    for rule in requirements:
        if rule.get("required") and int(rule.get("min_count", 1)) < 1:
            raise ValueError(
                f"{rule['id']}: a required item must have min_count of at least 1."
            )
    return findings


def observed(item: dict[str, Any], key: str, base_dir: Path | None) -> Any:
    if key in item:
        return item[key]
    path_text = str(item.get("path", "")).strip()
    if not path_text or base_dir is None:
        return None
    root = base_dir.resolve()
    path = (root / path_text).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Manifest path escapes base directory: {path_text}") from exc
    if key == "exists":
        return path.is_file()
    if key == "size_bytes" and path.is_file():
        return path.stat().st_size
    return None


def check_item(
    item: dict[str, Any], rule: dict[str, Any], base_dir: Path | None
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    requirement_id = str(rule["id"])
    path_text = str(item.get("path", "")).strip() or "unnamed item"
    suffix = Path(path_text).suffix.lower()

    exists = observed(item, "exists", base_dir)
    if exists is False:
        findings.append(
            finding("Blocker", requirement_id, path_text, "File is missing.", "Restore the final file and rerun the check.")
        )
        return findings
    if exists is None:
        findings.append(
            finding("Important", requirement_id, path_text, "File existence was not checked.", "Provide an accessible path or declare verified existence.")
        )

    if item.get("readable") is False:
        findings.append(
            finding("Blocker", requirement_id, path_text, "Required file is declared unreadable.", "Export a readable final file and inspect it again.")
        )
    elif "readable" not in item:
        findings.append(
            finding("Important", requirement_id, path_text, "Readable/openable status was not checked.", "Open and inspect the final file.")
        )

    allowed = [str(ext).lower() for ext in rule.get("allowed_extensions", [])]
    if allowed and suffix not in allowed:
        findings.append(
            finding("Blocker", requirement_id, path_text, f"Extension {suffix or '[none]'} is not allowed; expected {allowed}.", "Export the file in an allowed format.")
        )

    numeric_checks = (
        ("max_size_bytes", "size_bytes", lambda value, limit: value <= limit, "maximum file size"),
        ("min_width_px", "width_px", lambda value, limit: value >= limit, "minimum width"),
        ("min_height_px", "height_px", lambda value, limit: value >= limit, "minimum height"),
        ("max_duration_seconds", "duration_seconds", lambda value, limit: value <= limit, "maximum duration"),
        ("max_words", "word_count", lambda value, limit: value <= limit, "maximum word count"),
        ("max_characters", "character_count", lambda value, limit: value <= limit, "maximum character count"),
    )
    for rule_key, item_key, comparator, label in numeric_checks:
        if rule_key not in rule:
            continue
        value = observed(item, item_key, base_dir)
        limit = rule[rule_key]
        if value is None:
            findings.append(
                finding("Important", requirement_id, path_text, f"{label.capitalize()} was not checked.", f"Measure {item_key} and rerun the check.")
            )
        elif not isinstance(value, (int, float)) or isinstance(value, bool):
            findings.append(
                finding("Important", requirement_id, path_text, f"{item_key} is not numeric.", f"Record a numeric {item_key} value.")
            )
        elif not comparator(value, limit):
            findings.append(
                finding("Blocker", requirement_id, path_text, f"Observed {item_key}={value} violates {rule_key}={limit}.", f"Revise the file to satisfy the {label}.")
            )

    pattern = rule.get("filename_pattern")
    if pattern:
        try:
            matches = re.fullmatch(str(pattern), Path(path_text).name) is not None
        except re.error as exc:
            raise ValueError(f"{requirement_id}: invalid filename_pattern: {exc}") from exc
        if not matches:
            findings.append(
                finding("Blocker", requirement_id, path_text, "Filename does not match the required pattern.", "Rename the final file to match the official rule.")
            )
    return findings


def check_consistency(manifest: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    canonical = manifest.get("canonical_facts", {})
    if not isinstance(canonical, dict):
        raise ValueError("'canonical_facts' must be an object.")
    for item in manifest.get("items", []):
        facts = item.get("facts", {})
        if not isinstance(facts, dict):
            raise ValueError("Each item's 'facts' must be an object.")
        for key, value in facts.items():
            if key in canonical and canonical[key] != value:
                path_text = str(item.get("path", "unnamed item"))
                findings.append(
                    finding(
                        "Important",
                        "CONSISTENCY",
                        path_text,
                        f"Fact '{key}' is {value!r}, but canonical value is {canonical[key]!r}.",
                        "Confirm the canonical value and update every affected material.",
                    )
                )
    return findings


def check_rights(manifest: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    assets = manifest.get("third_party_assets", [])
    if not isinstance(assets, list):
        raise ValueError("'third_party_assets' must be a list.")
    for asset in assets:
        if not isinstance(asset, dict):
            raise ValueError("Every third-party asset must be an object.")
        name = str(asset.get("name", "unnamed asset"))
        status = str(asset.get("rights_status", "unknown")).lower()
        if status not in RIGHTS_STATUSES:
            raise ValueError(f"{name}: invalid rights_status '{status}'.")
        if status == "cleared" and not str(asset.get("basis", "")).strip():
            findings.append(
                finding(
                    "Important",
                    "RIGHTS",
                    name,
                    "Rights status is cleared, but no ownership, license, or consent basis is recorded.",
                    "Record the permission basis and proof location before treating the asset as cleared.",
                )
            )
            continue
        if status == "restricted":
            severity = "Blocker"
        elif status in {"pending", "unknown"}:
            severity = "Important"
        else:
            continue
        findings.append(
            finding(
                severity,
                "RIGHTS",
                name,
                f"Rights status is {status}.",
                "Resolve permission and any required disclosure before submission.",
            )
        )
    return findings


def audit(
    rules: dict[str, Any], manifest: dict[str, Any], base_dir: Path | None = None
) -> dict[str, Any]:
    findings = validate_rules(rules)
    requirements = {str(rule["id"]): rule for rule in rules["requirements"]}
    items = manifest.get("items")
    if not isinstance(items, list):
        raise ValueError("Manifest requires an 'items' list.")
    if not all(isinstance(item, dict) for item in items):
        raise ValueError("Every manifest item must be an object.")

    grouped: dict[str, list[dict[str, Any]]] = {key: [] for key in requirements}
    for item in items:
        requirement_id = str(item.get("requirement_id", ""))
        if requirement_id not in requirements:
            findings.append(
                finding("Important", "UNMAPPED", str(item.get("path", "unnamed item")), f"Unknown requirement ID '{requirement_id}'.", "Map the item to a valid requirement ID.")
            )
            continue
        grouped[requirement_id].append(item)

    checklist: list[dict[str, Any]] = []
    for requirement_id, rule in requirements.items():
        matched = grouped[requirement_id]
        count = len(matched)
        minimum = int(rule.get("min_count", 1 if rule.get("required") else 0))
        maximum = rule.get("max_count")
        before = len(findings)
        if count < minimum:
            findings.append(
                finding("Blocker", requirement_id, str(rule.get("label", requirement_id)), f"Found {count} item(s); minimum is {minimum}.", "Add the missing final material(s).")
            )
        if maximum is not None and count > int(maximum):
            findings.append(
                finding("Blocker", requirement_id, str(rule.get("label", requirement_id)), f"Found {count} item(s); maximum is {maximum}.", "Remove extra items from the upload set.")
            )
        for item in matched:
            findings.extend(check_item(item, rule, base_dir))
        checklist.append(
            {
                "requirement_id": requirement_id,
                "label": rule.get("label", requirement_id),
                "observed_count": count,
                "status": "Fail" if any(f["requirement_id"] == requirement_id and f["severity"] == "Blocker" for f in findings[before:]) else ("Not checked" if any(f["requirement_id"] == requirement_id and f["severity"] == "Important" for f in findings[before:]) else "Pass"),
            }
        )

    findings.extend(check_consistency(manifest))
    findings.extend(check_rights(manifest))
    findings.sort(key=lambda item: (SEVERITY_ORDER[item["severity"]], item["requirement_id"], item["item"]))
    counts = Counter(item["severity"] for item in findings)
    if counts["Blocker"]:
        decision = "Not ready"
    elif counts["Important"]:
        decision = "Conditionally ready"
    else:
        decision = "Ready"
    return {
        "decision": decision,
        "target": rules.get("target", {}),
        "finding_counts": {key: counts[key] for key in SEVERITY_ORDER},
        "checklist": checklist,
        "findings": findings,
        "notice": "Rights findings are risk screening, not legal clearance.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a design-award submission manifest.")
    parser.add_argument("--rules", required=True, help="UTF-8 JSON rules file")
    parser.add_argument("--manifest", required=True, help="UTF-8 JSON package manifest")
    parser.add_argument("--base-dir", help="Optional directory for file existence and size checks")
    parser.add_argument("--pretty", action="store_true", help="Indent JSON output")
    args = parser.parse_args()
    try:
        rules = load_json(args.rules)
        manifest = load_json(args.manifest)
        result = audit(rules, manifest, Path(args.base_dir) if args.base_dir else None)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2 if args.pretty else None)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
