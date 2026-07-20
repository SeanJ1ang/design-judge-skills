#!/usr/bin/env python3
"""Generate bilingual benchmark-coverage pages from local manifests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_ROOT = Path("skills/design-evaluation/references/profiles/benchmarks")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--output-cn", type=Path, default=Path("docs/benchmark-coverage.md"))
    parser.add_argument(
        "--output-en", type=Path, default=Path("docs/benchmark-coverage_EN.md")
    )
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def load_manifests(root: Path) -> list[dict]:
    manifests: list[dict] = []
    for path in sorted(root.glob("*/manifest.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        dataset = payload.get("dataset", {})
        privacy = payload.get("privacy", {})
        if not isinstance(dataset.get("row_count"), int):
            raise ValueError(f"{path} is missing dataset.row_count")
        if privacy.get("aggregate_only") is not True:
            raise ValueError(f"{path} must declare aggregate_only privacy")
        programs = payload.get("source_programs") or [payload.get("source_program")]
        manifests.append(
            {
                "path": path.as_posix(),
                "program": " / ".join(str(item) for item in programs if item),
                "rows": dataset["row_count"],
                "years": sorted(str(year) for year in dataset.get("year_counts", {})),
                "categories": dataset.get("normalized_category_count", 0),
                "profiles": sum(
                    value
                    for key, value in dataset.items()
                    if key.endswith("_profile_count") and isinstance(value, int)
                ),
                "review": payload.get("review_status", "unspecified"),
                "score_effect": payload.get("score_effect", "unspecified"),
            }
        )
    if not manifests:
        raise ValueError(f"no manifests found under {root}")
    return manifests


def render_cn(items: list[dict]) -> str:
    total = sum(item["rows"] for item in items)
    rows = "\n".join(
        f"| {item['program']} | {item['rows']:,} | {item['years'][0]}–{item['years'][-1]} | "
        f"{item['categories']} | {item['profiles']} |"
        for item in items
    )
    return f"""# 获奖作品观察基准覆盖

[English](benchmark-coverage_EN.md)

Design Judge 当前包含 **{total:,} 条**来自公开设计奖来源的获奖或入围作品聚合观察记录。它们用于解释类别、学科与竞赛背景，不参与核心评分，也不代表官方评审权重或获奖概率。

## 覆盖范围

| 来源项目 | 观察记录 | 年份 | 规范类别 | 聚合配置 |
|---|---:|---|---:|---:|
{rows}

## 生成与质量约束

- 表格由四份版本化 `manifest.json` 自动生成，总量不是人工填写。
- 当前质量门均报告重复 entry key 为 0，类别和年份缺失为 0。
- 原始作品记录、标题、设计者、公司、图片和来源 URL 不在公共仓库发布。
- 所有聚合配置的 `score_effect` 均为 `none`；观察背景不得改变核心量表分数。
- 当前配置标记为 `machine_generated_needs_human_review`，映射结论应保持描述性和可复核。

## 不能推出的结论

- 样本只包含获奖或入围作品，没有未获奖对照组。
- 不能从这些数据估计获奖概率、官方权重或未公开评委偏好。
- 不同奖项的类别体系和年度覆盖不同，不能直接比较获奖数量。
- iF Student 观察背景只适用于 `student_concept`；不能用于成熟作品轨道。

## 可复现入口

运行以下命令可根据 manifests 重新生成本页：

```powershell
python tools/generate_benchmark_coverage.py
python tools/generate_benchmark_coverage.py --check
```
"""


def render_en(items: list[dict]) -> str:
    total = sum(item["rows"] for item in items)
    rows = "\n".join(
        f"| {item['program']} | {item['rows']:,} | {item['years'][0]}–{item['years'][-1]} | "
        f"{item['categories']} | {item['profiles']} |"
        for item in items
    )
    return f"""# Observed Award-Work Benchmark Coverage

[中文说明](benchmark-coverage.md)

Design Judge currently includes **{total:,} aggregate observations** from publicly available awarded or recognized design works. They provide category, discipline, and competition context; they do not affect the core score and are not official jury weights or winning probabilities.

## Coverage

| Source program | Observations | Years | Normalized categories | Aggregate profiles |
|---|---:|---|---:|---:|
{rows}

## Generation and Quality Constraints

- The table is generated from four versioned `manifest.json` files; totals are not maintained manually.
- Current quality gates report zero duplicate entry keys and no missing categories or years.
- Raw records, titles, designers, companies, images, and source URLs are not published in this repository.
- Every aggregate profile declares `score_effect: none`; observed context must not change the core rubric score.
- Current profiles are marked `machine_generated_needs_human_review`; mappings remain descriptive and reviewable.

## What The Data Cannot Establish

- Samples contain awarded or recognized works without a non-winning control group.
- They cannot estimate winning probability, official weights, or undisclosed jury preferences.
- Award taxonomies and year coverage differ, so raw award counts are not directly comparable.
- The iF Student context applies only to `student_concept`, never to mature-work evaluation.

## Reproducible Entry Point

Regenerate and check this page from the manifests:

```powershell
python tools/generate_benchmark_coverage.py
python tools/generate_benchmark_coverage.py --check
```
"""


def update_or_check(path: Path, content: str, check: bool) -> bool:
    current = path.read_text(encoding="utf-8") if path.exists() else None
    if check:
        if current != content:
            print(f"OUTDATED: {path}")
            return False
        print(f"OK: {path}")
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    print(f"Wrote {path}")
    return True


def main() -> int:
    args = parse_args()
    items = load_manifests(args.root)
    valid_cn = update_or_check(args.output_cn, render_cn(items), args.check)
    valid_en = update_or_check(args.output_en, render_en(items), args.check)
    return 0 if valid_cn and valid_en else 1


if __name__ == "__main__":
    raise SystemExit(main())
