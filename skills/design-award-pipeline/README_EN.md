# `design-award-pipeline` Skill

[中文说明](README.md)

Routes a request to the right Design Judge module and maintains a compact, resumable handoff across multiple stages.

## What To Use It For

- Plan a complete award journey from the available design materials.
- Decide whether to start with search, evaluation, matching, or entry preparation.
- Continue across stages without losing confirmed facts, decisions, and blockers.

## Typical Requests

- “Plan the complete award journey for this student concept.”
- “I only have a board and manual. What should I do next?”
- “Continue from the award-match result and prepare the entry text.”

## What You Need To Provide

- The materials currently available and the outcome you want.
- Any confirmed maturity track, target award, or timing constraint; these may be unknown.

## Workflow

The skill selects the smallest sufficient route, delegates to a specialist Skill, and maintains a structured handoff containing facts, decisions, artifact paths, unresolved items, and the next stage.

## Outputs

- Recommended route and rationale.
- Completed-stage and decision summary.
- Blockers, live-rule checks, and next action.

## Boundaries

- Does not replace the rules or outputs of the five specialist Skills.
- Does not force a full pipeline when one Skill is sufficient.
- Does not predict winning probability or treat observed winners as official jury weights.

## Related Skills

`design-award-search`, `design-evaluation`, `design-award-match`, `design-information-prep`, and `design-submission-check`.
