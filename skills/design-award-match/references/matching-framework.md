# Award Matching Framework

## Stage 1: Eligibility gate

Assign the gate before scoring.

| Status | Meaning | Ranking treatment |
|---|---|---|
| Eligible | All checked hard rules are satisfied | Rank normally |
| Unknown | One or more required facts or current rules are missing | Keep as conditional; never rank as an unconditional first choice |
| Ineligible | A confirmed hard rule excludes the entry | Exclude from recommendation ranking |

Common gates include applicant type, geography, student status, project completion or launch window, prior publication, commercial availability, authorship, and category-specific restrictions. A closed current cycle is a timing status, not necessarily structural ineligibility.

## Stage 2: Weighted fit score

Rate each dimension from 0 to 5 and attach one concise evidence sentence. The weighted total is 0-100.

| Dimension | Weight | Rating question |
|---|---:|---|
| Category and track fit | 30 | Does the project's primary function clearly fall inside the exact published track and category? |
| Judging-criteria alignment | 30 | How strongly does supplied project evidence address the award's published criteria? |
| Award-positioning fit | 15 | Does the project's maturity, ambition, impact, and design discipline match the stated purpose of the award program? |
| Competitive evidence | 15 | Is the differentiation credible and supported relative to a small, category-consistent sample of past winners or comparable entries? |
| Entry feasibility | 10 | Can the applicant plausibly prepare the requested evidence and core material types within the known timing and resource constraints? |

Formula:

```text
fit_score = sum((rating / 5) * weight)
```

Do not include prestige, popularity, or presumed jury taste unless the award officially publishes a relevant factor.

## Rating anchors

| Rating | Meaning |
|---:|---|
| 5 | Direct, specific, and well-supported fit |
| 4 | Strong fit with a minor limitation |
| 3 | Meaningful but incomplete or mixed fit |
| 2 | Weak fit requiring substantial reframing or evidence |
| 1 | Marginal relation only |
| 0 | Contradictory, absent, or outside scope |

## Recommendation labels

| Score | Base label |
|---:|---|
| 80-100 | Priority |
| 65-79 | Strong candidate |
| 50-64 | Conditional |
| 0-49 | Weak fit |

Overrides:

- `Ineligible` -> `Excluded`, regardless of score.
- `Unknown` -> no higher than `Conditional`, regardless of score.
- Scores within five points are effectively tied; prefer higher confidence and fewer unresolved risks.

## Evidence confidence

Assess confidence separately from fit:

- `High`: exact official category, eligibility, current criteria, and project evidence are available.
- `Medium`: official core rules are available, but one non-gating dimension has limited evidence.
- `Low`: criteria, category definition, or several material project facts are incomplete.

Confidence changes how firmly to state the recommendation; it does not mathematically change the fit score.

## Past-winner trend safeguards

- Use a category-consistent, official-source sample whenever possible.
- Report sample size, covered years, and selection method.
- Separate observation from inference.
- Use language such as `the reviewed sample frequently shows...`.
- Never call a pattern a jury preference unless the award itself publishes that preference.
- Never estimate winning probability from the fit score or a winner sample.

