# Observed Award-Work Benchmark Coverage

[中文说明](benchmark-coverage.md)

Design Judge currently includes **22,125 aggregate observations** from publicly available awarded or recognized design works. They provide category, discipline, and competition context; they do not affect the core score and are not official jury weights or winning probabilities.

## Coverage

| Source program | Observations | Years | Normalized categories | Aggregate profiles |
|---|---:|---|---:|---:|
| International Design Excellence Awards (IDEA) | 1,024 | 2022–2025 | 24 | 22 |
| iF DESIGN AWARD | 10,644 | 2024–2026 | 104 | 41 |
| iF DESIGN TALENT AWARD / iF DESIGN STUDENT AWARD | 427 | 2022–2026 | 15 | 6 |
| Red Dot Award | 10,030 | 2024–2026 | 106 | 47 |

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
