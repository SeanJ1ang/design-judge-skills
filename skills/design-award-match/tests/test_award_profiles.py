import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("award_profiles", SCRIPTS / "award_profiles.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class AwardProfileTests(unittest.TestCase):
    def test_all_eleven_profiles_validate(self):
        self.assertEqual(MODULE.validate_all(), [])
        self.assertEqual(len(MODULE.load_profiles()), 11)

    def test_alias_resolution(self):
        profiles = MODULE.load_profiles(["iF", "Red Dot Concept", "EPDA"])
        self.assertEqual(
            {profile["award_id"] for profile in profiles},
            {"if-design", "red-dot-design-concept", "epda"},
        )

    def test_unsupported_award_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsupported award"):
            MODULE.load_profiles(["imaginary-award"])

    def test_every_profile_has_public_official_sources(self):
        for profile in MODULE.load_profiles():
            self.assertTrue(profile["official_domains"])
            self.assertTrue(profile["official_sources"])
            self.assertTrue(profile["dynamic_fields"])


if __name__ == "__main__":
    unittest.main()
