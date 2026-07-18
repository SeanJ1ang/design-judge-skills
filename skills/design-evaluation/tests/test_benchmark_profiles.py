import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from benchmark_profiles import (  # noqa: E402
    load_if_category_crosswalk,
    load_if_category_profiles,
    load_if_discipline_profiles,
    load_if_manifest,
    load_if_student_category_crosswalk,
    load_if_student_category_profiles,
    load_if_student_manifest,
    load_idea_category_crosswalk,
    load_idea_category_profiles,
    load_idea_discipline_profiles,
    load_idea_manifest,
    load_idea_program_profile,
    load_red_dot_category_crosswalk,
    load_red_dot_category_profiles,
    load_red_dot_competition_profiles,
    load_red_dot_discipline_profiles,
    load_red_dot_manifest,
    resolve_if_benchmark,
    resolve_if_student_benchmark,
    resolve_idea_benchmark,
    resolve_red_dot_benchmark,
    validate_if_benchmark_profiles,
    validate_if_student_benchmark_profiles,
    validate_idea_benchmark_profiles,
    validate_red_dot_benchmark_profiles,
)


class IfBenchmarkProfileTests(unittest.TestCase):
    def test_profiles_validate(self):
        self.assertEqual(validate_if_benchmark_profiles(), [])

    def test_snapshot_counts_are_internally_expected(self):
        dataset = load_if_manifest()["dataset"]
        self.assertEqual(dataset["row_count"], 10644)
        self.assertEqual(dataset["normalized_category_count"], 104)
        self.assertEqual(dataset["discipline_profile_count"], 9)
        self.assertEqual(dataset["category_profile_count"], 32)
        self.assertEqual(dataset["minimum_category_sample_size"], 100)

    def test_all_nine_disciplines_are_present(self):
        profiles = load_if_discipline_profiles()["profiles"]
        self.assertEqual(len(profiles), 9)
        self.assertIn("physical_product", profiles)
        self.assertIn("design_strategy_research", profiles)
        self.assertTrue(all(profile["score_effect"] == "none" for profile in profiles.values()))

    def test_high_sample_categories_have_canonical_mapping(self):
        profiles = load_if_category_profiles()["profiles"]
        self.assertTrue(profiles)
        self.assertTrue(all(profile["canonical_category"] for profile in profiles.values()))
        self.assertTrue(
            all(profile["sector_scope"] != "unmapped_requires_review" for profile in profiles.values())
        )
        self.assertTrue(
            all(profile["observed_metrics"]["sample_size"] >= 100 for profile in profiles.values())
        )

    def test_all_normalized_categories_have_canonical_mapping(self):
        crosswalk = load_if_category_crosswalk()["categories"]
        self.assertTrue(all(entry["canonical_category"] for entry in crosswalk.values()))

    def test_raw_if_category_resolves_exact_profile(self):
        context = resolve_if_benchmark(category="1.01 Automobiles / Vehicles")
        self.assertEqual(context["matched_profile_type"], "category_profile")
        self.assertEqual(context["normalized_category"], "Automobiles / Vehicles")
        self.assertEqual(context["profile"]["observed_metrics"]["sample_size"], 318)
        self.assertEqual(context["score_effect"], "none")

    def test_sparse_category_falls_back_to_discipline(self):
        crosswalk = load_if_category_crosswalk()["categories"]
        category_profiles = load_if_category_profiles()["profiles"]
        sparse_category = next(category for category in crosswalk if category not in category_profiles)
        context = resolve_if_benchmark(category=sparse_category)
        self.assertEqual(context["matched_profile_type"], "discipline_profile")
        self.assertTrue(context["fallback_used"])

    def test_unknown_context_falls_back_to_core(self):
        context = resolve_if_benchmark(category="Unknown Future Category")
        self.assertEqual(context["matched_profile_type"], "core_fallback")
        self.assertEqual(context["matched_profile_id"], "design-evaluation-core")


class IfStudentBenchmarkProfileTests(unittest.TestCase):
    def test_profiles_validate(self):
        self.assertEqual(validate_if_student_benchmark_profiles(), [])

    def test_snapshot_counts_and_gate_are_expected(self):
        manifest = load_if_student_manifest()
        self.assertEqual(manifest["dataset"]["row_count"], 427)
        self.assertEqual(manifest["dataset"]["normalized_category_count"], 15)
        self.assertEqual(manifest["dataset"]["category_profile_count"], 6)
        self.assertEqual(manifest["dataset"]["minimum_category_sample_size"], 30)
        self.assertEqual(manifest["maturity_gate"]["allowed"], ["student_concept"])
        self.assertEqual(manifest["maturity_gate"]["rejected"], ["mature_work"])

    def test_sdg_theme_never_infers_design_discipline(self):
        crosswalk = load_if_student_category_crosswalk()["categories"]
        self.assertEqual(len(crosswalk), 15)
        self.assertTrue(
            all(
                item["discipline_inference"] == "not_allowed_from_sdg_category"
                for item in crosswalk.values()
            )
        )

    def test_high_sample_theme_resolves_category_profile(self):
        context = resolve_if_student_benchmark(
            maturity="student_concept", category="03 Goodhealth + Well-Being"
        )
        self.assertEqual(context["matched_profile_type"], "category_profile")
        self.assertEqual(context["normalized_category"], "Goodhealth + Well-Being")
        self.assertEqual(context["profile"]["observed_metrics"]["sample_size"], 123)
        self.assertTrue(context["maturity_gate_applied"])
        self.assertEqual(context["score_effect"], "none")

    def test_sparse_theme_falls_back_to_competition_profile(self):
        profiles = load_if_student_category_profiles()["profiles"]
        self.assertNotIn("Life on Land", profiles)
        context = resolve_if_student_benchmark(
            maturity="student_concept", category="15 Life on Land"
        )
        self.assertEqual(context["matched_profile_type"], "competition_profile")
        self.assertEqual(context["profile"]["observed_metrics"]["sample_size"], 427)
        self.assertTrue(context["fallback_used"])

    def test_mature_work_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "student_concept"):
            resolve_if_student_benchmark(
                maturity="mature_work", category="03 Goodhealth + Well-Being"
            )


class RedDotBenchmarkProfileTests(unittest.TestCase):
    def test_profiles_validate(self):
        self.assertEqual(validate_red_dot_benchmark_profiles(), [])

    def test_snapshot_counts_are_expected(self):
        dataset = load_red_dot_manifest()["dataset"]
        self.assertEqual(dataset["row_count"], 10030)
        self.assertEqual(dataset["normalized_category_count"], 106)
        self.assertEqual(dataset["competition_profile_count"], 3)
        self.assertEqual(dataset["discipline_profile_count"], 9)
        self.assertEqual(dataset["category_profile_count"], 35)
        self.assertEqual(dataset["minimum_category_sample_size"], 100)

    def test_three_competition_lines_and_nine_disciplines_are_present(self):
        competitions = load_red_dot_competition_profiles()["profiles"]
        disciplines = load_red_dot_discipline_profiles()["profiles"]
        self.assertEqual(
            set(competitions),
            {"Product Design", "Brands & Communication Design", "Design Concept"},
        )
        self.assertEqual(len(disciplines), 9)
        self.assertTrue(all(p["score_effect"] == "none" for p in disciplines.values()))

    def test_all_categories_have_canonical_mapping(self):
        crosswalk = load_red_dot_category_crosswalk()["categories"]
        self.assertTrue(all(item["canonical_category"] for item in crosswalk.values()))

    def test_high_sample_category_resolves_exact_profile_and_alias(self):
        context = resolve_red_dot_benchmark(
            category="Smart Phones, Tablets and Wearable Technology"
        )
        self.assertEqual(context["matched_profile_type"], "category_profile")
        self.assertEqual(
            context["normalized_category"], "Mobile Phones, Tablets and Wearables"
        )
        self.assertEqual(context["profile"]["observed_metrics"]["sample_size"], 366)
        self.assertEqual(context["score_effect"], "none")

    def test_sparse_category_prefers_explicit_competition_line(self):
        profiles = load_red_dot_category_profiles()["profiles"]
        crosswalk = load_red_dot_category_crosswalk()["categories"]
        sparse = next(category for category in crosswalk if category not in profiles)
        context = resolve_red_dot_benchmark(
            category=sparse, competition="Design Concept"
        )
        self.assertEqual(context["matched_profile_type"], "competition_profile")
        self.assertEqual(context["profile"]["source_competition"], "Design Concept")

    def test_sparse_category_falls_back_to_mapped_discipline(self):
        profiles = load_red_dot_category_profiles()["profiles"]
        crosswalk = load_red_dot_category_crosswalk()["categories"]
        sparse = next(category for category in crosswalk if category not in profiles)
        context = resolve_red_dot_benchmark(category=sparse)
        self.assertEqual(context["matched_profile_type"], "discipline_profile")
        self.assertTrue(context["fallback_used"])

    def test_unknown_competition_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown Red Dot competition"):
            resolve_red_dot_benchmark(competition="Imaginary Competition")


class IdeaBenchmarkProfileTests(unittest.TestCase):
    def test_profiles_validate(self):
        self.assertEqual(validate_idea_benchmark_profiles(), [])

    def test_snapshot_counts_are_expected(self):
        dataset = load_idea_manifest()["dataset"]
        self.assertEqual(dataset["row_count"], 1024)
        self.assertEqual(dataset["source_category_count"], 25)
        self.assertEqual(dataset["normalized_category_count"], 24)
        self.assertEqual(dataset["discipline_profile_count"], 9)
        self.assertEqual(dataset["category_profile_count"], 12)
        self.assertEqual(dataset["minimum_category_sample_size"], 30)
        self.assertEqual(dataset["student_category_count"], 74)

    def test_all_nine_multilabel_disciplines_are_present(self):
        payload = load_idea_discipline_profiles()
        self.assertEqual(payload["membership_rule"], "multi_label_non_additive")
        self.assertEqual(len(payload["profiles"]), 9)
        self.assertTrue(
            all(
                profile["membership_rule"] == "multi_label_non_additive"
                and profile["score_effect"] == "none"
                for profile in payload["profiles"].values()
            )
        )

    def test_student_designs_never_infers_discipline(self):
        mapping = load_idea_category_crosswalk()["categories"]["Student Designs"]
        self.assertEqual(mapping["evaluation_disciplines"], [])
        self.assertEqual(
            mapping["discipline_inference"],
            "not_allowed_from_student_category",
        )
        self.assertEqual(mapping["allowed_maturity"], "student_concept")

    def test_high_sample_category_resolves_exact_profile(self):
        context = resolve_idea_benchmark(
            maturity="mature_work", category="Consumer Technology"
        )
        self.assertEqual(context["matched_profile_type"], "category_profile")
        self.assertEqual(context["profile"]["observed_metrics"]["sample_size"], 142)
        self.assertEqual(context["score_effect"], "none")

    def test_historical_kitchen_alias_is_normalized(self):
        context = resolve_idea_benchmark(
            maturity="mature_work",
            category="Kitchen & Accessories",
            discipline="physical_product",
        )
        self.assertEqual(context["normalized_category"], "Kitchens")
        self.assertEqual(context["matched_profile_type"], "discipline_profile")

    def test_student_designs_is_student_only(self):
        context = resolve_idea_benchmark(
            maturity="student_concept", category="Student Designs"
        )
        self.assertEqual(context["matched_profile_type"], "category_profile")
        self.assertTrue(context["maturity_gate_applied"])
        self.assertEqual(
            context["discipline_inference"],
            "not_allowed_from_student_category",
        )
        with self.assertRaisesRegex(ValueError, "student_concept"):
            resolve_idea_benchmark(
                maturity="mature_work", category="Student Designs"
            )

    def test_unknown_context_falls_back_to_program(self):
        context = resolve_idea_benchmark(category="Unknown IDEA Category")
        self.assertEqual(context["matched_profile_type"], "program_profile")
        self.assertEqual(
            context["profile"]["observed_metrics"]["sample_size"], 1024
        )
        self.assertEqual(load_idea_program_profile()["score_effect"], "none")


if __name__ == "__main__":
    unittest.main()
