import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from award_profiles import load_profiles  # noqa: E402
from build_candidate_set import build_candidates  # noqa: E402
from filter_eligible_awards import evaluate_route  # noqa: E402


def profile(award_id):
    return load_profiles([award_id])[0]


def route(award_id, route_id):
    item = profile(award_id)
    return item, next(route for route in item["routes"] if route["route_id"] == route_id)


class EligibilityAndRoutingTests(unittest.TestCase):
    def test_red_dot_product_rejects_concept_state(self):
        award, award_route = route("red-dot-product", "product")
        result = evaluate_route(
            award,
            award_route,
            {"applicant_type": "professional", "project_state": "professional_concept"},
        )
        self.assertEqual(result["eligibility"], "Ineligible")

    def test_dia_concept_rejects_render_only_entry(self):
        award, award_route = route("dia", "concept")
        result = evaluate_route(
            award,
            award_route,
            {
                "applicant_type": "student",
                "project_state": "student_concept",
                "functional_prototype_available_if_shortlisted": False,
            },
        )
        self.assertEqual(result["eligibility"], "Ineligible")
        self.assertTrue(result["failed_gates"])

    def test_k_design_complete_structural_facts_remain_live_unknown(self):
        award, award_route = route("k-design", "student")
        result = evaluate_route(
            award,
            award_route,
            {
                "applicant_type": "student",
                "project_state": "student_concept",
                "student_or_graduation_status_date": "2026-06-01",
            },
        )
        self.assertEqual(result["structural_status"], "Eligible")
        self.assertEqual(result["eligibility"], "Unknown")
        self.assertTrue(result["needs_live_verification"])

    def test_professional_is_not_routed_to_james_dyson(self):
        award, award_route = route("james-dyson", "individual")
        result = evaluate_route(
            award,
            award_route,
            {"applicant_type": "professional", "project_state": "working_prototype"},
        )
        self.assertEqual(result["eligibility"], "Ineligible")

    def test_student_concept_candidate_set_uses_student_and_concept_routes(self):
        project = {
            "canonical_category": "Medical and Health",
            "applicant_type": "student",
            "project_state": "student_concept",
        }
        candidates = build_candidates(project)
        pairs = {(item["award_id"], item["route_id"]) for item in candidates}
        self.assertIn(("if-student", "student-concept"), pairs)
        self.assertIn(("red-dot-design-concept", "next-gen"), pairs)
        self.assertIn(("idea", "student"), pairs)
        self.assertNotIn(("if-design", "professional-realized"), pairs)
        self.assertNotIn(("red-dot-product", "product"), pairs)

    def test_candidates_include_published_criteria(self):
        candidates = build_candidates(
            {
                "canonical_category": "Medical and Health",
                "applicant_type": "student",
                "project_state": "student_concept",
            },
            ["iF Student"],
        )
        self.assertTrue(candidates[0]["published_criteria"])


if __name__ == "__main__":
    unittest.main()
