import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from batch_evaluation import main, score_lines, shortlist_records  # noqa: E402
from evaluation_profiles import DESIGN_DIMENSIONS, PRESENTATION_DIMENSIONS  # noqa: E402


def rating(score=5, evidence_status="verified"):
    evidence = ["Direct evidence."] if evidence_status in {"verified", "supported"} else []
    return {
        "score": score,
        "evidence_status": evidence_status,
        "evidence": evidence,
        "rationale": "Evidence-based reason.",
    }


def payload(document_id, maturity="student_concept", score=5):
    return {
        "document_id": document_id,
        "project_name": f"Work {document_id}",
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
            "design": {key: rating(score) for key in DESIGN_DIMENSIONS},
            "presentation": {key: rating(score) for key in PRESENTATION_DIMENSIONS},
        },
        "findings": [],
    }


def scored(
    document_id,
    maturity,
    total,
    confidence="High",
    confidence_index=1.0,
    design=None,
    presentation=None,
    critical_count=0,
):
    design = total / 2 if design is None else design
    presentation = total - design if presentation is None else presentation
    return {
        "document_id": str(document_id),
        "maturity": maturity,
        "score_summary": {
            "total_score": total,
            "design_score": design,
            "presentation_score": presentation,
            "critical_count": critical_count,
        },
        "evidence": {
            "confidence": confidence,
            "confidence_index": confidence_index,
        },
    }


class BatchScoreTests(unittest.TestCase):
    def test_failures_are_isolated_and_document_id_is_preserved(self):
        invalid = payload("bad")
        invalid["maturity_source"] = "inferred"
        lines = [
            json.dumps(payload("ok")),
            "{not-json}\n",
            json.dumps(invalid),
            json.dumps(payload("ok-2", maturity="mature_work")),
        ]
        results, errors = score_lines(lines)
        self.assertEqual([item["document_id"] for item in results], ["ok", "ok-2"])
        self.assertEqual([item["line_number"] for item in errors], [2, 3])
        self.assertEqual(errors[1]["document_id"], "bad")

    def test_cli_score_writes_separate_jsonl_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "input.jsonl"
            output = root / "results.jsonl"
            errors = root / "errors.jsonl"
            source.write_text(
                json.dumps(payload("a")) + "\n" + "not json\n", encoding="utf-8"
            )
            exit_code = main(
                ["score", str(source), "--output", str(output), "--errors", str(errors)]
            )
            self.assertEqual(exit_code, 0)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["document_id"], "a")
            self.assertEqual(json.loads(errors.read_text(encoding="utf-8"))["line_number"], 2)


class ShortlistTests(unittest.TestCase):
    def test_tracks_are_ranked_independently(self):
        records = [
            scored("s1", "student_concept", 80),
            scored("s2", "student_concept", 70),
            scored("m1", "mature_work", 99),
            scored("m2", "mature_work", 98),
        ]
        selected = shortlist_records(records, ratio=0.5)
        self.assertEqual([item["document_id"] for item in selected], ["s1", "m1"])
        self.assertEqual([item["shortlist"]["track_rank"] for item in selected], [1, 1])

    def test_target_uses_all_evaluated_but_only_eligible_can_be_selected(self):
        records = [scored(str(i), "student_concept", 100 - i) for i in range(10)]
        records[0]["score_summary"]["critical_count"] = 1
        selected = shortlist_records(records, ratio=0.2)
        self.assertEqual([item["document_id"] for item in selected], ["1", "2"])
        self.assertEqual(selected[0]["shortlist"]["target_count"], 2)
        self.assertEqual(selected[0]["shortlist"]["evaluated_count"], 10)
        self.assertEqual(selected[0]["shortlist"]["eligible_count"], 9)

    def test_low_confidence_is_ineligible(self):
        records = [
            scored("low", "mature_work", 100, confidence="Low"),
            scored("medium", "mature_work", 90, confidence="Medium"),
        ]
        selected = shortlist_records(records, ratio=0.5)
        self.assertEqual([item["document_id"] for item in selected], ["medium"])

    def test_boundary_total_score_ties_are_all_included(self):
        records = [
            scored("a", "student_concept", 95),
            scored("b", "student_concept", 90, confidence_index=0.9),
            scored("c", "student_concept", 90, confidence_index=0.8),
            scored("d", "student_concept", 80),
        ]
        selected = shortlist_records(records, ratio=0.5)
        self.assertEqual([item["document_id"] for item in selected], ["a", "b", "c"])
        self.assertEqual(selected[0]["shortlist"]["selected_count"], 3)

    def test_tie_break_order_is_fully_deterministic(self):
        records = [
            scored("z", "mature_work", 90,  confidence_index=0.8, design=46),
            scored("d", "mature_work", 90, confidence_index=0.9, design=45),
            scored("p", "mature_work", 90, confidence_index=0.9, design=46, presentation=44),
            scored("b", "mature_work", 90, confidence_index=0.9, design=46, presentation=44),
        ]
        selected = shortlist_records(records, ratio=0.25)
        self.assertEqual([item["document_id"] for item in selected], ["b", "p", "d", "z"])

    def test_ratio_is_validated(self):
        with self.assertRaisesRegex(ValueError, "greater than 0"):
            shortlist_records([], ratio=0)


if __name__ == "__main__":
    unittest.main()
