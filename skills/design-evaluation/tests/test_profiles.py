import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from evaluation_profiles import (  # noqa: E402
    load_award_lenses,
    load_classification,
    load_core,
    load_maturity,
    validate_profiles,
)


class EvaluationProfileTests(unittest.TestCase):
    def test_all_profiles_validate(self):
        self.assertEqual(validate_profiles(), [])

    def test_weight_totals_are_50_plus_50(self):
        core = load_core()
        self.assertEqual(sum(core["presentation_weights"].values()), 50)
        for maturity in ("student_concept", "mature_work"):
            self.assertEqual(sum(load_maturity(maturity)["design_weights"].values()), 50)

    def test_controlled_vocabulary_is_present(self):
        classification = load_classification()
        self.assertIn("physical_product", classification["disciplines"])
        self.assertIn("healthcare", classification["sectors"])
        self.assertIn("connected_iot", classification["focus_tags"])

    def test_award_lenses_are_explicitly_non_official(self):
        lenses = load_award_lenses()
        self.assertEqual(len(lenses), 4)
        for profile in lenses.values():
            self.assertIn("not an official jury simulation", profile["not_official_notice"])


if __name__ == "__main__":
    unittest.main()
