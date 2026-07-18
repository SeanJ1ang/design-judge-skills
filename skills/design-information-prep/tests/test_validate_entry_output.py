from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "scripts"))

from field_spec_utils import load_json, load_spec  # noqa: E402
from validate_entry_output import validate_entry  # noqa: E402


def fact(value: object) -> dict[str, object]:
    return {
        "value": value,
        "status": "supported",
        "confidence": "high",
        "evidence": [{"source": "test-brief.pdf", "locator": "p.1", "evidence_type": "direct"}],
        "user_confirmation_required": False,
    }


class EntryValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dossier = load_json(SKILL_DIR / "examples" / "project-dossier.example.json")
        cls.entry = load_json(SKILL_DIR / "examples" / "idea-entry-output.example.json")

    def test_example_is_ready(self) -> None:
        result = validate_entry(self.dossier, self.entry, load_spec("idea"))
        self.assertEqual("Ready", result["decision"])
        self.assertEqual(0, result["finding_counts"]["Blocker"])

    def test_word_limit_overrun_is_blocking(self) -> None:
        entry = copy.deepcopy(self.entry)
        entry["fields"]["overview"]["text"] = "word " * 151
        result = validate_entry(self.dossier, entry, load_spec("idea"))
        self.assertEqual("Not ready", result["decision"])
        self.assertTrue(any(item["field_id"] == "overview" and "maximum is 150" in item["finding"] for item in result["findings"]))

    def test_inferred_fact_requires_confirmation(self) -> None:
        dossier = copy.deepcopy(self.dossier)
        dossier["facts"]["problem"]["status"] = "inferred"
        dossier["facts"]["problem"]["user_confirmation_required"] = True
        result = validate_entry(dossier, self.entry, load_spec("idea"))
        self.assertEqual("Conditionally ready", result["decision"])
        self.assertTrue(any("requires user confirmation" in item["finding"] for item in result["findings"]))

    def test_red_dot_minimum_character_limit_is_enforced(self) -> None:
        dossier = {
            "schema_version": 1,
            "project_id": "red-dot-min-test",
            "attachments": [{"source": "test-brief.pdf", "authorized": True}],
            "facts": {
                "project_name": fact("Test Product"),
                "product_type": fact("Wearable device"),
                "launch_date": fact("2026"),
                "core_functions": fact(["Guides movement"]),
                "competitive_difference": fact("Private on-device guidance"),
                "client_manufacturer": fact("Test Manufacturer"),
                "design_company": fact("Test Design Studio"),
            },
        }
        entry = {
            "award_id": "red-dot-product",
            "route_id": "product",
            "cycle": "2026",
            "fields": {
                "product-name": {"text": "Test Product", "used_fact_ids": ["project_name"]},
                "product-type": {"text": "Wearable device", "used_fact_ids": ["product_type"]},
                "launch-year": {"text": "2026", "used_fact_ids": ["launch_date"]},
                "description": {"text": "Short objective description.", "used_fact_ids": ["core_functions", "competitive_difference"]},
                "manufacturer": {"text": "Test Manufacturer", "used_fact_ids": ["client_manufacturer"]},
                "design-company": {"text": "Test Design Studio", "used_fact_ids": ["design_company"]},
            },
        }
        result = validate_entry(dossier, entry, load_spec("red-dot-product"))
        self.assertTrue(any(item["field_id"] == "description" and "minimum is 500" in item["finding"] for item in result["findings"]))


if __name__ == "__main__":
    unittest.main()
