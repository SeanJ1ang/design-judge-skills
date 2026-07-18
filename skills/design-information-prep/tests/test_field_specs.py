from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from field_spec_utils import AWARD_DIR, validate_spec  # noqa: E402


class FieldSpecTests(unittest.TestCase):
    def test_all_ten_award_specs_are_valid(self) -> None:
        paths = sorted(AWARD_DIR.glob("*.json"))
        self.assertEqual(10, len(paths))
        expected = {
            "core77", "dia", "epda", "good-design-japan", "idea",
            "if-design", "if-student", "james-dyson", "k-design", "red-dot-product",
        }
        self.assertEqual(expected, {path.stem for path in paths})
        errors: list[str] = []
        for path in paths:
            spec = json.loads(path.read_text(encoding="utf-8"))
            errors.extend(validate_spec(spec, path.name))
        self.assertEqual([], errors)

    def test_runtime_scripts_have_no_database_client(self) -> None:
        forbidden = ("supabase_url", "supabase_service", "create_client(", "award_entries")
        for path in SCRIPTS_DIR.glob("*.py"):
            source = path.read_text(encoding="utf-8").lower()
            for token in forbidden:
                self.assertNotIn(token, source, f"{token!r} found in {path.name}")


if __name__ == "__main__":
    unittest.main()
