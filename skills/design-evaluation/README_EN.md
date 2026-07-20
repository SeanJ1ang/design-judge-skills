# `design-evaluation` Skill

[中文说明](README.md)

Evaluates one design or a user-approved maturity-mapped batch with a transparent evidence-based rubric while keeping design quality, presentation quality, and evidence confidence separate.

## What To Use It For

- Diagnose strengths and weaknesses in the design and its presentation.
- Score student concepts or mature works reproducibly.
- Batch-evaluate, isolate failures, and shortlist within separate maturity tracks.
- Use observed iF, iF Student, Red Dot, or IDEA winners as descriptive context.

## Typical Requests

- “Evaluate this board as a student concept and identify Critical issues.”
- “Batch-evaluate these works without mixing student concepts and mature products.”
- “Explain the dimensions using the iF Product Design context.”

## What You Need To Provide

- Design images, boards, descriptions, research, or validation materials.
- A user-confirmed `student_concept` or `mature_work` track.
- Optional target award and category.

## Workflow

The skill classifies the work, builds an evidence ledger, and loads the core rubric, maturity profile, sector overlay, and optional award context. Deterministic scripts enforce weights, boundaries, and batch ranking.

## Outputs

- Dimension-level design and presentation scores.
- Evidence state and rationale for every rating.
- Critical risks, evidence confidence, and prioritized improvements.
- Separate-track shortlist and failure-isolation report for batches.

## Built-In References

Includes aggregate observed context from 22,125 iF, iF Student, Red Dot, and IDEA awarded or recognized works. These observations are descriptive, do not alter the core score, and are not official jury weights.

## Boundaries

- Does not simulate an official jury or predict winning probability.
- Does not directly rank different maturity tracks.
- Does not redesign the work or treat missing visual evidence as verified fact.

## Related Skills

Use `design-award-search` for precedents and `design-award-match` for target selection.
