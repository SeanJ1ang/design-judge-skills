from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "scripts"))

from validate_handoff import validate_handoff  # noqa: E402


class HandoffValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.payload = json.loads(
            (SKILL_DIR / "examples" / "handoff.example.json").read_text(encoding="utf-8")
        )

    def test_example_is_valid(self) -> None:
        self.assertEqual(validate_handoff(self.payload), [])

    def test_unknown_top_level_field_is_rejected(self) -> None:
        self.payload["private_note"] = "do not persist"
        self.assertIn("unknown fields: private_note", validate_handoff(self.payload))

    def test_completed_stage_cannot_be_next_stage(self) -> None:
        self.payload["next_stage"] = "evaluation"
        self.assertIn(
            "next_stage must not already be completed", validate_handoff(self.payload)
        )

    def test_duplicate_fact_ids_are_rejected(self) -> None:
        self.payload["facts"].append(dict(self.payload["facts"][0]))
        self.assertIn("fact ids must be unique", validate_handoff(self.payload))

    def test_inferred_provenance_is_not_persisted_as_fact(self) -> None:
        self.payload["facts"][0]["provenance"] = "model_inference"
        self.assertIn("facts[0].provenance is invalid", validate_handoff(self.payload))

    def test_inference_requires_basis_and_confidence(self) -> None:
        del self.payload["inferences"][0]["basis"]
        errors = validate_handoff(self.payload)
        self.assertTrue(any("inferences[0]" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
