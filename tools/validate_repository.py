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
WORKFLOWS = ROOT / ".github" / "workflows"
REQUIRED_AGENT_INTERFACE_KEYS = {
    "default_prompt",
    "display_name",
    "short_description",
}
REFERENCE_CONTENTS_RE = re.compile(
    r"^##\s+(?:Table of Contents|Contents|目录)\s*$",
    flags=re.IGNORECASE | re.MULTILINE,
)
PINNED_ACTION_RE = re.compile(r"^[^@\s]+@[0-9a-fA-F]{40}$")


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
        interface = {
            key: value
            for key, value in re.findall(
                r'^\s{2}(display_name|short_description|default_prompt):\s*"([^"]+)"\s*$',
                agent,
                flags=re.MULTILINE,
            )
        }
        missing_interface = REQUIRED_AGENT_INTERFACE_KEYS - set(interface)
        v.require(
            not missing_interface,
            f"{agent_file}: missing quoted interface keys: {', '.join(sorted(missing_interface))}",
        )
        short_description = interface.get("short_description", "")
        if short_description:
            v.require(
                25 <= len(short_description) <= 64,
                f"{agent_file}: short_description must be 25-64 characters",
            )
        default_prompt = interface.get("default_prompt", "")
        if default_prompt:
            v.require(
                f"${name}" in default_prompt,
                f"{agent_file}: default_prompt must mention ${name}",
            )
        if name in SUPPORT_SKILLS:
            v.require(
                re.search(
                    r"(?ms)^policy:\s*$.*?^\s{2}allow_implicit_invocation:\s*false\s*$",
                    agent,
                )
                is not None,
                f"{agent_file}: support package must disable implicit invocation",
            )

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


def validate_reference_navigation(v: Validation) -> None:
    for path in sorted(SKILLS.rglob("*.md")):
        if "references" not in path.relative_to(SKILLS).parts:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        if len(lines) <= 100:
            continue
        v.require(
            REFERENCE_CONTENTS_RE.search("\n".join(lines[:40])) is not None,
            f"{path}: reference files longer than 100 lines need a Contents section near the top",
        )


def validate_workflows(v: Validation) -> None:
    v.require(WORKFLOWS.is_dir(), f"{WORKFLOWS}: missing workflow directory")
    if not WORKFLOWS.is_dir():
        return
    workflows = sorted(WORKFLOWS.glob("*.yml")) + sorted(WORKFLOWS.glob("*.yaml"))
    v.require(bool(workflows), f"{WORKFLOWS}: no workflow files found")
    for path in workflows:
        text = path.read_text(encoding="utf-8")
        references = re.findall(
            r"^\s*(?:-\s*)?uses:\s*([^\s#]+)", text, flags=re.MULTILINE
        )
        for reference in references:
            if reference.startswith(("./", "docker://")):
                continue
            v.require(
                PINNED_ACTION_RE.fullmatch(reference) is not None,
                f"{path}: action reference must use a full 40-character commit SHA: {reference}",
            )
        v.require(
            re.search(r"(?m)^permissions:\s*$", text) is not None,
            f"{path}: declare least-privilege permissions",
        )
        v.require(
            re.search(r"(?m)^\s{4}timeout-minutes:\s*\d+\s*$", text) is not None,
            f"{path}: every job needs timeout-minutes",
        )


def validate_evals(user_skills: set[str], discovered: set[str], v: Validation) -> None:
    path = ROOT / "evals" / "routing-cases.json"
    v.require(path.is_file(), f"{path}: missing routing evaluation set")
    if not path.is_file():
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    v.require(payload.get("schema_version") == 1, f"{path}: schema_version must be 1")
    cases = payload.get("cases", [])
    v.require(isinstance(cases, list) and bool(cases), f"{path}: cases must be a non-empty list")
    if not isinstance(cases, list):
        return
    case_ids: list[str] = []
    prompts: list[str] = []
    for index, case in enumerate(cases):
        v.require(isinstance(case, dict), f"{path}: case {index} must be an object")
        if not isinstance(case, dict):
            continue
        for key in ("id", "prompt", "expected_skill", "must_not_route_to"):
            v.require(
                isinstance(case.get(key), str) and bool(case[key].strip()),
                f"{path}: case {index} needs a non-empty {key}",
            )
        case_id = case.get("id")
        prompt = case.get("prompt")
        expected = case.get("expected_skill")
        excluded = case.get("must_not_route_to")
        if isinstance(case_id, str):
            case_ids.append(case_id)
        if isinstance(prompt, str):
            prompts.append(prompt)
        if isinstance(expected, str):
            v.require(expected in user_skills, f"{path}: unknown expected_skill {expected}")
        if isinstance(excluded, str):
            v.require(excluded in discovered, f"{path}: unknown must_not_route_to {excluded}")
        if isinstance(expected, str) and isinstance(excluded, str):
            v.require(expected != excluded, f"{path}: a case cannot require and exclude {expected}")
    v.require(len(case_ids) == len(set(case_ids)), f"{path}: duplicate case ids")
    v.require(len(prompts) == len(set(prompts)), f"{path}: duplicate prompts")
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
    expected_badge = f"skills-{len(user_skills)}-"
    validation.require(
        expected_badge in root_cn and expected_badge in root_en,
        f"root skill badges must report {len(user_skills)}",
    )
    validation.require("22%2C125" in root_cn and "22%2C125" in root_en, "benchmark badges must report 22,125")
    validate_json(validation)
    validate_python(validation)
    validate_reference_navigation(validation)
    validate_workflows(validation)
    validate_evals(user_skills, discovered, validation)
    if validation.errors:
        for error in validation.errors:
            print(f"ERROR: {error}")
        print(f"Repository validation failed with {len(validation.errors)} error(s).")
        return 1
    print(f"Repository validation passed for {len(user_skills)} user-facing skills and {len(SUPPORT_SKILLS)} support package.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
