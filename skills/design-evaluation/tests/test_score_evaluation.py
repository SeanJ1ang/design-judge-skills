import copy
import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from evaluation_profiles import DESIGN_DIMENSIONS, PRESENTATION_DIMENSIONS  # noqa: E402
from score_evaluation import score_evaluation  # noqa: E402


def rating(score=5, evidence_status="verified"):
    evidence = ["Direct test evidence."] if evidence_status in {"verified", "supported"} else []
    return {
        "score": score,
        "evidence_status": evidence_status,
        "evidence": evidence,
        "rationale": "A concise evidence-based reason.",
    }


def payload(maturity="student_concept", score=5, evidence_status="verified"):
    return {
        "project_name": "Example",
        "maturity": maturity,
        "maturity_source": "user",
        "classification": {
            "primary_discipline": "physical_product",
            "secondary_disciplines": [],
            "primary_sector": "healthcare",
            "secondary_sectors": [],
            "focus_tags": [],
        },
        "ratings": {
            "design": {
                key: rating(score, evidence_status) for key in DESIGN_DIMENSIONS
            },
            "presentation": {
                key: rating(score, evidence_status) for key in PRESENTATION_DIMENSIONS
            },
        },
        "findings": [],
    }


class ScoreEvaluationTests(unittest.TestCase):
    def test_perfect_student_concept_scores_100(self):
        result = score_evaluation(payload())
        self.assertEqual(result["score_summary"]["design_score"], 50)
        self.assertEqual(result["score_summary"]["presentation_score"], 50)
        self.assertEqual(result["score_summary"]["total_score"], 100)

    def test_perfect_mature_work_scores_100(self):
        result = score_evaluation(payload(maturity="mature_work"))
        self.assertEqual(result["score_summary"]["total_score"], 100)

    def test_maturity_must_be_user_selected(self):
        item = payload()
        item["maturity_source"] = "inferred"
        with self.assertRaisesRegex(ValueError, "must equal 'user'"):
            score_evaluation(item)

    def test_maturity_is_required(self):
        item = payload()
        del item["maturity"]
        with self.assertRaisesRegex(ValueError, "maturity"):
            score_evaluation(item)

    def test_claimed_feasibility_is_capped(self):
        item = payload(maturity="mature_work")
        item["ratings"]["design"]["implementation_feasibility"] = rating(5, "claimed")
        result = score_evaluation(item)
        record = next(
            row
            for row in result["dimension_results"]["design"]
            if row["dimension"] == "implementation_feasibility"
        )
        self.assertEqual(record["applied_score"], 2)
        self.assertTrue(record["adjustments"])
        self.assertLess(result["score_summary"]["total_score"], 100)

    def test_claimed_evidence_has_global_cap(self):
        item = payload()
        item["ratings"]["design"]["innovation_differentiation"] = rating(5, "claimed")
        result = score_evaluation(item)
        record = next(
            row
            for row in result["dimension_results"]["design"]
            if row["dimension"] == "innovation_differentiation"
        )
        self.assertEqual(record["applied_score"], 2)

    def test_missing_evidence_has_global_cap(self):
        item = payload()
        item["ratings"]["design"]["problem_value"] = rating(4, "missing")
        result = score_evaluation(item)
        record = result["dimension_results"]["design"][0]
        self.assertEqual(record["applied_score"], 1)

    def test_mismatch_forces_low_confidence_without_reclassification(self):
        item = payload(maturity="mature_work")
        item["maturity_evidence_mismatch"] = True
        result = score_evaluation(item)
        self.assertEqual(result["maturity"], "mature_work")
        self.assertEqual(result["evidence"]["confidence"], "Low")

    def test_critical_finding_overrides_label_not_score(self):
        item = payload()
        item["findings"] = [
            {
                "severity": "critical",
                "finding": "Unsafe failure mode.",
                "evidence": "The supplied flow has no safe stop state.",
            }
        ]
        result = score_evaluation(item)
        self.assertEqual(result["score_summary"]["total_score"], 100)
        self.assertEqual(result["score_summary"]["competitiveness"], "Critical risk")

    def test_invalid_classification_fails(self):
        item = payload()
        item["classification"]["primary_sector"] = "unknown"
        with self.assertRaisesRegex(ValueError, "unknown primary_sector"):
            score_evaluation(item)

    def test_missing_dimension_fails(self):
        item = payload()
        del item["ratings"]["design"]["problem_value"]
        with self.assertRaisesRegex(ValueError, "design ratings mismatch"):
            score_evaluation(item)

    def test_boolean_score_fails(self):
        item = payload()
        item["ratings"]["design"]["problem_value"]["score"] = True
        with self.assertRaisesRegex(ValueError, "must be numeric"):
            score_evaluation(item)

    def test_unknown_award_lens_fails(self):
        item = payload()
        item["award_lens"] = "fake_award"
        with self.assertRaisesRegex(ValueError, "unknown award_lens"):
            score_evaluation(item)

    def test_if_benchmark_context_does_not_change_score(self):
        item = payload()
        baseline = score_evaluation(copy.deepcopy(item))
        item["benchmark_context"] = {
            "source": "if_observed_winners",
            "category": "1.01 Automobiles / Vehicles",
        }
        result = score_evaluation(item)
        self.assertEqual(result["score_summary"], baseline["score_summary"])
        self.assertEqual(
            result["benchmark_context"]["matched_profile_type"], "category_profile"
        )
        self.assertEqual(result["benchmark_context"]["score_effect"], "none")

    def test_if_student_context_is_student_only_and_does_not_change_score(self):
        item = payload(maturity="student_concept")
        baseline = score_evaluation(copy.deepcopy(item))
        item["benchmark_context"] = {
            "source": "if_student_observed_winners",
            "category": "03 Goodhealth + Well-Being",
        }
        result = score_evaluation(item)
        self.assertEqual(result["score_summary"], baseline["score_summary"])
        self.assertEqual(
            result["benchmark_context"]["matched_profile_type"], "category_profile"
        )
        self.assertEqual(
            result["benchmark_context"]["discipline_inference"],
            "not_allowed_from_sdg_category",
        )
        self.assertEqual(result["benchmark_context"]["score_effect"], "none")

    def test_if_student_context_rejects_mature_work(self):
        item = payload(maturity="mature_work")
        item["benchmark_context"] = {
            "source": "if_student_observed_winners",
            "category": "03 Goodhealth + Well-Being",
        }
        with self.assertRaisesRegex(ValueError, "student_concept"):
            score_evaluation(item)

    def test_if_student_sparse_theme_falls_back_without_score_change(self):
        item = payload(maturity="student_concept")
        baseline = score_evaluation(copy.deepcopy(item))
        item["benchmark_context"] = {
            "source": "if_student_observed_winners",
            "category": "15 Life on Land",
        }
        result = score_evaluation(item)
        self.assertEqual(result["score_summary"], baseline["score_summary"])
        self.assertEqual(
            result["benchmark_context"]["matched_profile_type"],
            "competition_profile",
        )
        self.assertTrue(result["benchmark_context"]["fallback_used"])

    def test_red_dot_context_does_not_change_score(self):
        item = payload()
        baseline = score_evaluation(copy.deepcopy(item))
        item["benchmark_context"] = {
            "source": "red_dot_observed_winners",
            "category": "Computer and Information Technology",
            "competition": "Product Design",
        }
        result = score_evaluation(item)
        self.assertEqual(result["score_summary"], baseline["score_summary"])
        self.assertEqual(
            result["benchmark_context"]["matched_profile_type"], "category_profile"
        )
        self.assertEqual(result["benchmark_context"]["score_effect"], "none")

    def test_red_dot_sparse_category_uses_explicit_competition(self):
        item = payload()
        item["benchmark_context"] = {
            "source": "red_dot_observed_winners",
            "category": "AI Products",
            "competition": "Design Concept",
        }
        result = score_evaluation(item)
        self.assertEqual(
            result["benchmark_context"]["matched_profile_type"],
            "competition_profile",
        )
        self.assertEqual(
            result["benchmark_context"]["profile"]["source_competition"],
            "Design Concept",
        )

    def test_idea_context_does_not_change_score(self):
        item = payload(maturity="mature_work")
        baseline = score_evaluation(copy.deepcopy(item))
        item["benchmark_context"] = {
            "source": "idea_observed_recognized",
            "category": "Medical & Health",
        }
        result = score_evaluation(item)
        self.assertEqual(result["score_summary"], baseline["score_summary"])
        self.assertEqual(
            result["benchmark_context"]["matched_profile_type"], "category_profile"
        )
        self.assertEqual(result["benchmark_context"]["score_effect"], "none")

    def test_idea_student_designs_is_student_only(self):
        student = payload(maturity="student_concept")
        student["benchmark_context"] = {
            "source": "idea_observed_recognized",
            "category": "Student Designs",
        }
        result = score_evaluation(student)
        self.assertTrue(result["benchmark_context"]["maturity_gate_applied"])
        self.assertEqual(
            result["benchmark_context"]["discipline_inference"],
            "not_allowed_from_student_category",
        )

        mature = payload(maturity="mature_work")
        mature["benchmark_context"] = {
            "source": "idea_observed_recognized",
            "category": "Student Designs",
        }
        with self.assertRaisesRegex(ValueError, "student_concept"):
            score_evaluation(mature)

    def test_unknown_benchmark_source_fails(self):
        item = payload()
        item["benchmark_context"] = {"source": "fake_benchmark"}
        with self.assertRaisesRegex(ValueError, "unknown benchmark_context.source"):
            score_evaluation(item)

    def test_scoring_is_deterministic(self):
        item = payload(score=3.5, evidence_status="supported")
        self.assertEqual(score_evaluation(copy.deepcopy(item)), score_evaluation(item))


if __name__ == "__main__":
    unittest.main()
