# `design-submission-check` Skill

[中文说明](README.md)

Checks a concrete submission package for completeness, technical constraints, cross-material consistency, rights risks, and final readiness for an exact award, route, category, and cycle.

## What To Use It For

- Check whether boards, images, video, text, and evidence files are complete.
- Verify current format, size, duration, anonymity, and required-field rules.
- Find inconsistent names, numbers, statements, and facts across materials.
- Produce an actionable go, conditional-go, or no-go decision.

## Typical Requests

- “Check this package against the current iF Student rules.”
- “Find factual conflicts across the board, manual, and entry copy.”
- “Decide whether this is ready to submit and rank the issues by severity.”

## What You Need To Provide

- Exact award, route, category, and cycle.
- Actual submission files or a structured manifest.
- User-supplied official rules, or permission to verify current official sources.

## Workflow

The skill builds a dated, source-backed requirement ledger, checks inventory and technical constraints, audits facts, rights, and disclosure across materials, and classifies findings as Blocker, Important, or Advisory.

## Outputs

- `Ready`, `Conditional go`, or `No-go` decision.
- Rule evidence, pass state, and finding severity.
- Must-fix, should-fix, and human-confirmation lists.

## Built-In References

Includes a checking framework, rule-evidence policy, consistency and rights checklist, structured examples, and a deterministic manifest checker.

## Boundaries

- Does not choose an award, re-evaluate the design, or rewrite the whole entry.
- Does not provide legal clearance; rights findings need qualified review.
- Does not return `Ready` when dynamic official rules remain unverified.

## Related Skills

Use `design-information-prep` for entry text and `design-award-match` for target selection.
