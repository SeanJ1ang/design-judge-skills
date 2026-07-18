# Evaluation Output Template

## Evaluation conclusion

State in the first paragraph:

`{project} | user-selected maturity: {maturity} | {primary discipline} / {primary sector} | {score}/100 | evidence confidence: {confidence} | Critical status: {status}`

Add one sentence explaining the strongest dimension and the decisive risk.

## Score summary

| Result | Score / status |
|---|---:|
| Design quality | `{design_score}/50` |
| Presentation quality | `{presentation_score}/50` |
| General total | `{total}/100` |
| Competitiveness | `{label}` |
| Evidence confidence | `{High / Medium / Low}` |
| Maturity evidence mismatch | `{Yes / No}` |

## Dimension assessment

| Dimension | Raw score | Weighted score | Evidence state | Reason |
|---|---:|---:|---|---|

List all thirteen dimensions. If a cap changes a supplied raw score, show both and explain the cap.

## Findings

### Critical

List only fundamental or harm-critical findings. Write `None identified from supplied evidence` when empty.

### Major

List material weaknesses and their consequence.

### Minor

List local weaknesses concisely.

## Strengths

List no more than four evidence-supported strengths.

## Evidence gaps

List missing evidence that could materially change the score or confidence. Do not turn this section into a redesign plan.

## Optional award-aligned lens

Include only when the user already specified a supported target. State the profile version, official source, check date, mapped criteria, and limitations. Keep it separate from the general numeric score.

## Optional benchmark context

State:

- source profile set and matched profile ID;
- user-selected maturity and whether a benchmark maturity gate was applied;
- matched category or discipline and whether fallback was used;
- sample size, years, award-level distribution, and review status;
- observed structured-evidence coverage and presentation expectations;
- observable similarities, differences, and evidence gaps;
- `score_effect: none` and winner-only sample limitations.

Do not reproduce winner titles, descriptions, URLs, designers, companies, or images.

For iF Student, explicitly state `student_concept only` and `discipline_inference: not_allowed_from_sdg_category`. If the work is `mature_work`, omit the benchmark section and report that iF Student context is ineligible.

For Red Dot, state the explicitly selected competition line when present. If a sparse or unmatched category falls back, distinguish `competition_profile`, `discipline_profile`, and `core_fallback`; never infer the competition line from maturity.

For IDEA, state whether a `category_profile`, `discipline_profile`, or `program_profile` was used. Label discipline membership `multi_label_non_additive`. For `Student Designs`, explicitly state `student_concept only` and `discipline_inference: not_allowed_from_student_category`; reject it for `mature_work`.

## Limitations

End with:

`This is an evidence-based design-quality assessment, not an official jury decision, award recommendation, or probability of winning.`
