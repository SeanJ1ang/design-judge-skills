import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "check_submission_manifest.py"
SPEC = importlib.util.spec_from_file_location("check_submission_manifest", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def rules():
    return {
        "target": {"award": "Example", "cycle": "2026"},
        "official_source_url": "https://example.org/rules",
        "checked_on": "2026-07-13",
        "requirements": [
            {
                "id": "R-1",
                "label": "Board",
                "required": True,
                "min_count": 1,
                "max_count": 1,
                "allowed_extensions": [".pdf"],
                "max_size_bytes": 1000,
                "filename_pattern": r"^Final_[A-Za-z]+\.pdf$",
            }
        ],
    }


def manifest():
    return {
        "canonical_facts": {"project_title": "Project A"},
        "items": [
            {
                "requirement_id": "R-1",
                "path": "Final_Project.pdf",
                "exists": True,
                "readable": True,
                "size_bytes": 900,
                "facts": {"project_title": "Project A"},
            }
        ],
        "third_party_assets": [],
    }


class SubmissionManifestTests(unittest.TestCase):
    def test_clean_manifest_is_ready(self):
        result = MODULE.audit(rules(), manifest())
        self.assertEqual(result["decision"], "Ready")
        self.assertEqual(result["checklist"][0]["status"], "Pass")

    def test_missing_required_item_is_blocker(self):
        data = manifest()
        data["items"] = []
        result = MODULE.audit(rules(), data)
        self.assertEqual(result["decision"], "Not ready")
        self.assertEqual(result["finding_counts"]["Blocker"], 1)

    def test_unreadable_required_item_is_blocker(self):
        data = manifest()
        data["items"][0]["readable"] = False
        result = MODULE.audit(rules(), data)
        self.assertEqual(result["decision"], "Not ready")

    def test_hard_limit_failure_is_blocker(self):
        data = manifest()
        data["items"][0]["size_bytes"] = 1001
        result = MODULE.audit(rules(), data)
        self.assertEqual(result["decision"], "Not ready")
        self.assertTrue(any("max_size_bytes" in item["finding"] for item in result["findings"]))

    def test_missing_measurement_is_important(self):
        data = manifest()
        del data["items"][0]["size_bytes"]
        result = MODULE.audit(rules(), data)
        self.assertEqual(result["decision"], "Conditionally ready")
        self.assertEqual(result["checklist"][0]["status"], "Not checked")

    def test_inconsistent_fact_is_important(self):
        data = manifest()
        data["items"][0]["facts"]["project_title"] = "Project B"
        result = MODULE.audit(rules(), data)
        self.assertEqual(result["decision"], "Conditionally ready")
        self.assertTrue(any(item["requirement_id"] == "CONSISTENCY" for item in result["findings"]))

    def test_restricted_asset_is_blocker(self):
        data = manifest()
        data["third_party_assets"] = [
            {"name": "Stock image", "rights_status": "restricted"}
        ]
        result = MODULE.audit(rules(), data)
        self.assertEqual(result["decision"], "Not ready")

    def test_pending_asset_is_important(self):
        data = manifest()
        data["third_party_assets"] = [
            {"name": "Music", "rights_status": "pending"}
        ]
        result = MODULE.audit(rules(), data)
        self.assertEqual(result["decision"], "Conditionally ready")

    def test_cleared_asset_without_basis_is_important(self):
        data = manifest()
        data["third_party_assets"] = [
            {"name": "Font", "rights_status": "cleared"}
        ]
        result = MODULE.audit(rules(), data)
        self.assertEqual(result["decision"], "Conditionally ready")

    def test_required_rule_cannot_have_zero_minimum(self):
        rule_data = rules()
        rule_data["requirements"][0]["min_count"] = 0
        with self.assertRaisesRegex(ValueError, "min_count"):
            MODULE.audit(rule_data, manifest())

    def test_missing_official_source_is_blocker(self):
        rule_data = rules()
        rule_data["official_source_url"] = ""
        result = MODULE.audit(rule_data, manifest())
        self.assertEqual(result["decision"], "Not ready")

    def test_duplicate_requirement_ids_fail(self):
        rule_data = rules()
        rule_data["requirements"].append(dict(rule_data["requirements"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate requirement IDs"):
            MODULE.audit(rule_data, manifest())


if __name__ == "__main__":
    unittest.main()
