# `design-award-match` Skill

[中文说明](README.md)

Matches a project to programs, routes, and categories across 11 configured design awards, applying structural eligibility gates before comparing published criteria with project evidence.

## What To Use It For

- Decide which award, program, or category fits a design.
- Compare award fit, eligibility risk, and submission priority.
- Route student concepts, mature products, and professional projects appropriately.

## Typical Requests

- “Compare iF Student, Red Dot Concept, DIA, and James Dyson.”
- “Should this mature product enter Red Dot Product or IDEA?”
- “Check whether applicant type, launch state, and timing create hard eligibility risks.”

## What You Need To Provide

- Project state, primary function, applicant type, timing, and available evidence.
- Optional awards to compare; otherwise the skill builds a supported candidate set.

## Workflow

The skill normalizes the project category, applies structural eligibility gates, verifies dynamic rules, and scores five fit dimensions against published criteria. Eligibility, fit, and evidence confidence remain separate.

## Outputs

- Primary recommendation, alternatives, and routes not recommended.
- Eligibility state, dynamic checks, and fit rationale for each award.
- Submission priority, evidence confidence, and next information needed.

## Built-In References

Versioned configurations and official sources for iF, iF Student, Red Dot Product, Red Dot Concept, IDEA, DIA, K-Design, GOOD DESIGN Japan, Core77, James Dyson, and EPDA.

## Boundaries

- Does not interpret fit as winning probability.
- Does not assume missing eligibility information passes; it returns `Unknown`.
- Does not retrieve winners, perform a full design evaluation, or audit final files.

## Related Skills

After selection, use `design-information-prep`; before submission, use `design-submission-check`.
