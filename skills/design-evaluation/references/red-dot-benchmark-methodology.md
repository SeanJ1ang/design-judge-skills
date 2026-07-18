# Red Dot Observed-Winner Benchmark Method

Use the bundled Red Dot profiles as contextual evidence only. They summarize 10,030 usable awarded entries from 2024–2026. They do not represent official jury weights, non-winner comparisons, or winning probability.

## Public outputs

- `profiles/benchmarks/red-dot/category-crosswalk.json`: 106 normalized categories with source variants, competition mix, internal evaluation-discipline mapping, canonical category, sector, and focus tags.
- `profiles/benchmarks/red-dot/competition-profiles.json`: separate aggregate profiles for Product Design, Brands & Communication Design, and Design Concept.
- `profiles/benchmarks/red-dot/discipline-profiles.json`: nine internal evaluation-discipline profiles with sample, year, award-level, evidence-field, and image-count summaries.
- `profiles/benchmarks/red-dot/category-profiles.json`: 35 high-sample category profiles with at least 100 awarded entries each.
- `profiles/benchmarks/red-dot/manifest.json`: snapshot identity, thresholds, quality gates, privacy policy, and limitations.

## Extraction method

1. Read only `complete` and `partial` Red Dot records from the private source; exclude three invalid failed records.
2. Require 10,030 unique records with complete year, award level, category, and official competition line.
3. Preserve Product Design, Brands & Communication Design, and Design Concept as separate source contexts.
4. Normalize whitespace, remove the Junior Award suffix, and merge only explicit multilingual or historical category aliases.
5. Map each category provisionally to one of the nine shared evaluation disciplines, a canonical search category, sector, and focus tags.
6. Aggregate counts, years, award levels, competition mix, evidence-field coverage, and image-count distributions.
7. Publish a category profile only when `sample_size >= 100`.
8. Reject any public output containing titles, descriptions, URLs, identities, entry keys, raw payloads, images, or image hashes.

## Runtime use

Resolve context in this order:

1. exact normalized high-sample category profile;
2. explicitly supplied Red Dot competition-line profile;
3. mapped or supplied evaluation-discipline profile;
4. core rubric.

The competition line must come from the user or target-award context; do not infer it from maturity. Keep `score_effect: none`. Use the profile to select evidence questions and assess presentation coverage, never to alter the 50-point design and 50-point presentation structure.

Example:

```text
python scripts/benchmark_profiles.py \
  --source red_dot_observed_winners \
  --category "Medical Devices and Technology" \
  --competition "Product Design" \
  --discipline physical_product \
  --pretty
```

## Interpretation limits

- Frequency among winners does not establish a causal winning factor.
- Award-level distributions are descriptive and must not become score weights.
- Evidence-field and image-count coverage describe source metadata, not objective design quality.
- Category aliases and internal discipline, canonical-category, sector, and focus mappings remain provisional until human review.
- Category taxonomies differ across years and competition lines; source variants and competition mix remain visible in aggregate form.
- Winner-only data cannot support behavioral scoring anchors or award predictions.
