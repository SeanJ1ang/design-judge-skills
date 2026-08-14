from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "validate_repository.py"
SPEC = importlib.util.spec_from_file_location("validate_repository", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class RepositoryValidatorTests(unittest.TestCase):
    def test_frontmatter_rejects_extra_keys(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "SKILL.md"
            path.write_text(
                "---\nname: example\ndescription: useful skill\nversion: 1\n---\n",
                encoding="utf-8",
            )
            validation = validator.Validation()
            validator.frontmatter(path, validation)
            self.assertTrue(any("only name and description" in error for error in validation.errors))

    def test_workflow_rejects_moving_action_tags(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workflows = Path(directory)
            (workflows / "test.yml").write_text(
                """name: Test
on: push
permissions:
  contents: read
jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v5
""",
                encoding="utf-8",
            )
            validation = validator.Validation()
            with mock.patch.object(validator, "WORKFLOWS", workflows):
                validator.validate_workflows(validation)
            self.assertTrue(any("40-character commit SHA" in error for error in validation.errors))

    def test_long_reference_requires_contents(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skills = Path(directory) / "skills"
            reference = skills / "example" / "references" / "guide.md"
            reference.parent.mkdir(parents=True)
            reference.write_text("# Guide\n" + "detail\n" * 101, encoding="utf-8")
            validation = validator.Validation()
            with mock.patch.object(validator, "SKILLS", skills):
                validator.validate_reference_navigation(validation)
            self.assertTrue(any("need a Contents section" in error for error in validation.errors))

    def test_routing_cases_reject_unknown_skills(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evals = root / "evals"
            evals.mkdir()
            (evals / "routing-cases.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "cases": [
                            {
                                "id": "bad-route",
                                "prompt": "Do the thing",
                                "expected_skill": "missing-skill",
                                "must_not_route_to": "support-skill",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            validation = validator.Validation()
            with mock.patch.object(validator, "ROOT", root):
                validator.validate_evals(
                    {"user-skill"}, {"user-skill", "support-skill"}, validation
                )
            self.assertTrue(any("unknown expected_skill" in error for error in validation.errors))


if __name__ == "__main__":
    unittest.main()
