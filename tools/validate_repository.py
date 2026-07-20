#!/usr/bin/env python3
"""Validate Design Judge skill metadata, human docs, JSON, and Python syntax."""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
SUPPORT_SKILLS = {"design-judge-shared"}


class Validation:
    def __init__(self) -> None:
        self.errors: list[str] = []

    def require(self, condition: bool, message: str) -> None:
        if not condition:
            self.errors.append(message)


def frontmatter(path: Path, validation: Validation) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    validation.require(match is not None, f"{path}: missing YAML frontmatter")
    if match is None:
        return {}
    values: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip('"\'')
    validation.require(
        set(values) == {"name", "description"},
        f"{path}: frontmatter must contain only name and description",
    )
    return values


def markdown_headings(path: Path) -> list[str]:
    return [
        line[3:].strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith("## ")
    ]


def validate_skill(skill_dir: Path, root_cn: str, root_en: str, v: Validation) -> str:
    skill_file = skill_dir / "SKILL.md"
    meta = frontmatter(skill_file, v)
    name = meta.get("name", "")
    v.require(name == skill_dir.name, f"{skill_file}: name must match folder")
    v.require(len(meta.get("description", "")) >= 80, f"{skill_file}: description is too short")

    agent_file = skill_dir / "agents" / "openai.yaml"
    v.require(agent_file.is_file(), f"{agent_file}: missing")
    if agent_file.is_file():
        agent = agent_file.read_text(encoding="utf-8")
        v.require("display_name:" in agent, f"{agent_file}: missing display_name")
        short_match = re.search(r'^\s*short_description:\s*"([^"]+)"', agent, re.MULTILINE)
        v.require(short_match is not None, f"{agent_file}: quote short_description")
        if short_match:
            v.require(25 <= len(short_match.group(1)) <= 64, f"{agent_file}: short_description must be 25-64 characters")
        v.require(f"${name}" in agent, f"{agent_file}: default_prompt must mention ${name}")

    if name not in SUPPORT_SKILLS:
        readme_cn = skill_dir / "README.md"
        readme_en = skill_dir / "README_EN.md"
        v.require(readme_cn.is_file(), f"{readme_cn}: missing human-facing detail page")
        v.require(readme_en.is_file(), f"{readme_en}: missing English detail page")
        if readme_cn.is_file() and readme_en.is_file():
            cn = readme_cn.read_text(encoding="utf-8")
            en = readme_en.read_text(encoding="utf-8")
            v.require("[English](README_EN.md)" in cn, f"{readme_cn}: missing language switch")
            v.require("[中文说明](README.md)" in en, f"{readme_en}: missing language switch")
            v.require(
                len(markdown_headings(readme_cn)) == len(markdown_headings(readme_en)),
                f"{skill_dir}: Chinese and English heading counts differ",
            )
        v.require(
            f"skills/{name}/README.md" in root_cn,
            f"README.md: skill index must link to {name}/README.md",
        )
        v.require(
            f"skills/{name}/README_EN.md" in root_en,
            f"README_EN.md: skill index must link to {name}/README_EN.md",
        )
    return name


def validate_json(v: Validation) -> None:
    for path in sorted(ROOT.rglob("*.json")):
        if ".git" in path.parts:
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            v.errors.append(f"{path}: invalid JSON: {exc}")


def validate_python(v: Validation) -> None:
    for base in (ROOT / "tools", ROOT / "skills"):
        for path in sorted(base.rglob("*.py")):
            try:
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except (OSError, UnicodeError, SyntaxError) as exc:
                v.errors.append(f"{path}: invalid Python: {exc}")


def validate_evals(user_skills: set[str], v: Validation) -> None:
    path = ROOT / "evals" / "routing-cases.json"
    v.require(path.is_file(), f"{path}: missing routing evaluation set")
    if not path.is_file():
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = payload.get("cases", [])
    case_ids = [case.get("id") for case in cases if isinstance(case, dict)]
    v.require(len(case_ids) == len(set(case_ids)), f"{path}: duplicate case ids")
    for skill in sorted(user_skills):
        count = sum(case.get("expected_skill") == skill for case in cases)
        v.require(count >= 2, f"{path}: {skill} needs at least two routing cases")


def main() -> int:
    validation = Validation()
    root_cn = (ROOT / "README.md").read_text(encoding="utf-8")
    root_en = (ROOT / "README_EN.md").read_text(encoding="utf-8")
    discovered: set[str] = set()
    for skill_dir in sorted(path for path in SKILLS.iterdir() if (path / "SKILL.md").is_file()):
        discovered.add(validate_skill(skill_dir, root_cn, root_en, validation))
    user_skills = discovered - SUPPORT_SKILLS
    validation.require(len(user_skills) == 6, f"expected 6 user-facing skills, found {len(user_skills)}")
    validation.require("skills-6-" in root_cn and "skills-6-" in root_en, "root skill badges must report 6")
    validation.require("22%2C125" in root_cn and "22%2C125" in root_en, "benchmark badges must report 22,125")
    validate_json(validation)
    validate_python(validation)
    validate_evals(user_skills, validation)
    if validation.errors:
        for error in validation.errors:
            print(f"ERROR: {error}")
        print(f"Repository validation failed with {len(validation.errors)} error(s).")
        return 1
    print(f"Repository validation passed for {len(user_skills)} user-facing skills and {len(SUPPORT_SKILLS)} support package.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
