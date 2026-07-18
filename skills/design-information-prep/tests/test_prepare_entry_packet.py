from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "scripts"))

from field_spec_utils import load_json, load_spec  # noqa: E402
from prepare_entry_packet import prepare_packet, validate_dossier  # noqa: E402


class PreparePacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dossier = load_json(SKILL_DIR / "examples" / "project-dossier.example.json")

    def test_idea_example_has_no_blocking_facts(self) -> None:
        packet = prepare_packet(self.dossier, load_spec("idea"), "general")
        self.assertEqual([], packet["blocking_fact_ids"])
        self.assertEqual([], packet["confirmation_fact_ids"])
        self.assertTrue(all(field["readiness"] == "ready_to_draft" for field in packet["fields"]))

    def test_missing_required_fact_is_reported(self) -> None:
        dossier = copy.deepcopy(self.dossier)
        dossier["facts"]["problem"] = {
            "value": None,
            "status": "missing",
            "confidence": "unknown",
            "evidence": [],
            "user_confirmation_required": False,
        }
        packet = prepare_packet(dossier, load_spec("idea"), "general")
        self.assertIn("problem", packet["blocking_fact_ids"])
        field = next(item for item in packet["fields"] if item["field_id"] == "design-innovation")
        self.assertEqual("needs_input", field["readiness"])

    def test_unauthorized_attachment_cannot_support_a_fact(self) -> None:
        dossier = copy.deepcopy(self.dossier)
        dossier["attachments"][0]["authorized"] = False
        errors = validate_dossier(dossier)
        self.assertTrue(any("not authorized" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
