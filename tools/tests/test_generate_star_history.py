from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "generate_star_history.py"
SPEC = importlib.util.spec_from_file_location("generate_star_history", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
star_history = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(star_history)


class StarHistoryTests(unittest.TestCase):
    def test_nice_axis_uses_readable_steps(self) -> None:
        self.assertEqual(star_history.nice_y_axis(0), (1, 1))
        self.assertEqual(star_history.nice_y_axis(1156), (250, 1250))

    def test_update_replaces_same_day_and_skips_unchanged_counts(self) -> None:
        observations = [(date(2026, 7, 18), 0), (date(2026, 7, 19), 33)]
        self.assertEqual(
            star_history.update_observations(observations, date(2026, 7, 19), 35),
            [(date(2026, 7, 18), 0), (date(2026, 7, 19), 35)],
        )
        self.assertEqual(
            star_history.update_observations(observations, date(2026, 7, 20), 33),
            observations,
        )

    def test_update_rejects_invalid_time_and_count(self) -> None:
        observations = [(date(2026, 7, 19), 33)]
        with self.assertRaises(ValueError):
            star_history.update_observations(observations, date(2026, 7, 18), 40)
        with self.assertRaises(ValueError):
            star_history.update_observations(observations, date(2026, 7, 20), -1)

    def test_load_rejects_duplicate_dates(self) -> None:
        payload = {
            "repository": "owner/repo",
            "observations": [
                {"date": "2026-07-18", "stars": 0},
                {"date": "2026-07-18", "stars": 1},
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "history.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "duplicate observation dates"):
                star_history.load_observations(path, "owner/repo")

    def test_render_is_deterministic_and_escapes_repository(self) -> None:
        observations = [(date(2026, 7, 18), 0), (date(2026, 7, 19), 33)]
        first = star_history.render_svg("owner/repo&demo", observations)
        second = star_history.render_svg("owner/repo&demo", observations)
        self.assertEqual(first, second)
        self.assertIn("owner/repo&amp;demo", first)
        self.assertIn("★ 33", first)
        self.assertIn('role="img"', first)

    def test_serialization_preserves_metadata_and_order(self) -> None:
        observations = [(date(2026, 7, 18), 0), (date(2026, 7, 19), 33)]
        payload = json.loads(
            star_history.serialize_observations(
                "owner/repo", date(2026, 7, 18), observations
            )
        )
        self.assertEqual(payload["tracking_started"], "2026-07-18")
        self.assertEqual(payload["observations"][-1]["stars"], 33)


if __name__ == "__main__":
    unittest.main()
