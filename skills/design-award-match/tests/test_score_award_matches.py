import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "score_award_matches.py"
SPEC = importlib.util.spec_from_file_location("score_award_matches", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def candidate(eligibility="eligible", confidence="high", rating=4):
    return {
        "award": "Example Award",
        "track": "Product",
        "category": "Healthcare",
        "eligibility": eligibility,
        "confidence": confidence,
        "ratings": {key: rating for key in MODULE.WEIGHTS},
    }


class ScoreAwardMatchesTests(unittest.TestCase):
    def test_weighted_score_and_priority_label(self):
        result = MODULE.score_candidate(candidate(rating=5))
        self.assertEqual(result["fit_score"], 100)
        self.assertEqual(result["recommendation"], "Priority")

    def test_unknown_eligibility_caps_label(self):
        result = MODULE.score_candidate(candidate(eligibility="unknown", rating=5))
        self.assertEqual(result["fit_score"], 100)
        self.assertEqual(result["recommendation"], "Conditional")

    def test_ineligible_candidate_is_excluded(self):
        result = MODULE.score_candidate(candidate(eligibility="ineligible", rating=5))
        self.assertEqual(result["recommendation"], "Excluded")

    def test_missing_dimension_fails(self):
        item = candidate()
        del item["ratings"]["entry_feasibility"]
        with self.assertRaisesRegex(ValueError, "missing rating"):
            MODULE.score_candidate(item)

    def test_out_of_range_rating_fails(self):
        item = candidate()
        item["ratings"]["criteria_alignment"] = 6
        with self.assertRaisesRegex(ValueError, "0 to 5"):
            MODULE.score_candidate(item)

    def test_ranking_places_unknown_after_eligible(self):
        eligible = MODULE.score_candidate(candidate(eligibility="eligible", rating=3))
        unknown = MODULE.score_candidate(candidate(eligibility="unknown", rating=5))
        ranked = sorted([unknown, eligible], key=MODULE.rank_key)
        self.assertEqual(ranked[0]["eligibility"], "Eligible")

    def test_confidence_is_separate_from_numeric_score(self):
        high = MODULE.score_candidate(candidate(confidence="high", rating=4))
        low = MODULE.score_candidate(candidate(confidence="low", rating=4))
        self.assertEqual(high["fit_score"], low["fit_score"])
        self.assertNotEqual(high["confidence"], low["confidence"])

    def test_scoring_is_deterministic(self):
        item = candidate(rating=3.5)
        self.assertEqual(MODULE.score_candidate(item), MODULE.score_candidate(item))


if __name__ == "__main__":
    unittest.main()
