# IDEA Observed-Award Benchmark Method

Use the bundled IDEA profiles as contextual evidence only. They summarize 1,024 repaired IDEA records from 2022–2025, including Gold, Silver, Bronze, and Featured Finalist entries. They do not represent official jury weights, non-selected comparisons, or winning probability.

The source taxonomy is checked against the [official IDEA category descriptions](https://www.idsa.org/awards-recognitions/idea/idea-categories/).

## Public outputs

- `profiles/benchmarks/idea/category-crosswalk.json`: 24 normalized categories with source variants, provisional multi-label evaluation disciplines, canonical category, sector, focus tags, and maturity eligibility.
- `profiles/benchmarks/idea/program-profile.json`: program-wide aggregate context for all 1,024 records.
- `profiles/benchmarks/idea/discipline-profiles.json`: nine internal evaluation-discipline profiles. Membership is multi-label and non-additive.
- `profiles/benchmarks/idea/category-profiles.json`: 12 category profiles with at least 30 entries each.
- `profiles/benchmarks/idea/manifest.json`: snapshot identity, thresholds, maturity gate, quality gates, privacy policy, and limitations.

## Extraction method

1. Read 1,024 repaired `complete` IDEA records from the private source in memory.
2. Require unique entry keys and complete year, category, and award-level values.
3. Accept only Gold, Silver, Bronze, and Featured Finalist as award levels.
4. Normalize whitespace and merge the one-record historical `Kitchen & Accessories` alias into `Kitchens`; retain all other source categories.
5. Map source categories provisionally to the shared canonical category, sector, focus, and evaluation-discipline vocabularies.
6. Use multi-label discipline membership for categories spanning multiple practices: Digital Interaction, Environments, Furniture & Lighting, and Social Impact Design.
7. Exclude Student Designs from discipline inference because it is a student-status grouping covering physical products, digital work, services, and experiences.
8. Aggregate sample counts, years, award levels, evidence-field coverage, and image-count distributions.
9. Publish category profiles only when `sample_size >= 30`.
10. Reject public outputs containing titles, descriptions, URLs, identities, entry keys, raw payloads, images, or image hashes.

## Runtime use

Resolve context in this order:

1. exact normalized high-sample category profile;
2. supplied or provisionally mapped evaluation-discipline profile;
3. IDEA program-wide profile;
4. core rubric if the profile set is unavailable.

`Student Designs` is available only when the user selected `student_concept`. Reject it for `mature_work`, and never infer project discipline from that category.

Keep `score_effect: none`. Use the profile to select evidence questions and assess presentation coverage, never to alter the 50-point design and 50-point presentation structure.

Example:

```text
python scripts/benchmark_profiles.py \
  --source idea_observed_recognized \
  --maturity mature_work \
  --category "Medical & Health" \
  --discipline physical_product \
  --pretty
```

For Student Designs:

```text
python scripts/benchmark_profiles.py \
  --source idea_observed_recognized \
  --maturity student_concept \
  --category "Student Designs" \
  --pretty
```

## Interpretation limits

- Featured Finalist is not interchangeable with Gold, Silver, or Bronze; all award-level counts remain descriptive.
- Frequency among awarded and finalist entries does not establish a causal success factor.
- Multi-label discipline sample sizes overlap and must not be summed.
- The single 2022 record is insufficient for year-specific inference; the main comparable coverage is 2023–2025.
- Evidence-field and image-count coverage describe source metadata, not objective design quality.
- Internal mappings remain `machine_generated_needs_human_review` until manually approved.
- Winner-only and finalist-only data cannot support behavioral scoring anchors or award predictions.
