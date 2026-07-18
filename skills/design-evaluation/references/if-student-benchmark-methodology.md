# iF Student Aggregate Benchmark Methodology

## Purpose and eligibility

This benchmark adds observed iF Student winner context to `design-evaluation`. It is available only when the user has explicitly selected `student_concept`. The resolver must reject `mature_work`; it must not silently fall back to ordinary iF data.

The profiles have `score_effect: none`. They guide evidence questions and presentation coverage. They are not official iF criteria, jury simulation, award recommendations, or winning-probability estimates.

## Source snapshot

The private builder read 427 award records across two historical program names:

- `iF DESIGN TALENT AWARD`: 85 records from 2022;
- `iF DESIGN STUDENT AWARD`: 342 records from 2023–2026.

The snapshot contains 384 Winner and 43 Gold records. It covers 15 United Nations Sustainable Development Goal themes. Public files contain aggregate counts and guidance only; they exclude project titles, descriptions, URLs, names, designers, companies, images, entry keys, and raw payloads.

## Category semantics

iF Student categories in this snapshot are SDG issue themes, not design disciplines. The source has no populated discipline field. Consequently:

- preserve the discipline selected through the normal project classification workflow;
- never infer a design discipline from an SDG category;
- use the SDG crosswalk only for thematic category, sector, focus-tag, and evidence-question context.

All 15 themes have an explicit provisional crosswalk marked `machine_generated_needs_human_review`.

## Profile construction and resolution

The public profile set contains:

- one competition-wide profile based on all 427 records;
- 15 SDG crosswalk entries;
- six first-release SDG theme profiles with at least 30 records.

Resolution order:

1. reject unless `maturity` is exactly `student_concept`;
2. normalize the supplied category by removing its numeric SDG prefix;
3. load an exact SDG theme profile when its sample size is at least 30;
4. otherwise load the competition-wide student profile;
5. keep the normal evaluation core and user-selected discipline unchanged.

The six high-sample themes are Goodhealth + Well-Being, Responsible Consumption + Production, Industry, Innovation + Infrastructure, Quality Education, Reduced Inequalities, and Sustainable Cities + Communities.

## Extracted guidance

The benchmark emphasizes problem value, innovation and differentiation, solution integrity, and responsibility and sustainability. It asks for:

- credible problem and beneficiary evidence;
- a clear mechanism connecting the concept to the claimed outcome;
- stakeholder, dependency, exclusion, and unintended-harm analysis;
- a prototype, scenario test, or realistic validation plan appropriate to a student concept;
- bounded social and environmental impact claims.

Suggested presentation coverage includes problem evidence, beneficiary scenario, concept principle, stakeholder or system logic, prototype or scenario test, and validation and impact plan.

## Data interpretation limits

This is a winner-only sample with no non-winning comparison group. Structured-field coverage describes what exists in the source records, not what caused an award result. In this source, `winnerStatement` is a creator statement, not a jury comment. Correlations must not be presented as jury preferences or causal requirements.

Each generated profile retains its sample size, year distribution, award-level distribution, review status, limitations, and source snapshot hash. Rebuilds should preserve the maturity gate and rerun profile, privacy, and regression tests.
