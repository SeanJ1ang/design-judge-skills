# iF Observed-Winner Benchmark Method

Use the bundled iF profiles as contextual evidence only. They summarize 10,644 awarded entries from 2024–2026 and do not represent official jury weights, non-winner comparisons, or winning probability.

## Public outputs

- `profiles/benchmarks/if/category-crosswalk.json`: 104 normalized iF categories mapped to source disciplines, evaluation disciplines, canonical search categories, sectors, and focus tags.
- `profiles/benchmarks/if/discipline-profiles.json`: nine discipline profiles with sample size, year and award-level distribution, structured-field coverage, image-count summaries, attention dimensions, evidence prompts, and presentation expectations.
- `profiles/benchmarks/if/category-profiles.json`: 32 first-release category profiles with at least 100 awarded entries each.
- `profiles/benchmarks/if/manifest.json`: snapshot identity, thresholds, quality gates, privacy policy, and limitations.

## Extraction method

1. Read `iF DESIGN AWARD` records from the private source in memory.
2. Require unique entry keys and non-empty category and discipline values.
3. Normalize category whitespace and strip the leading numeric hierarchy.
4. Preserve the official source discipline and map it to the evaluation discipline vocabulary.
5. Map categories provisionally to the shared canonical category, sector, and focus tags.
6. Aggregate sample counts, years, award levels, country-region diversity, structured-field coverage, and image-count distributions.
7. Publish category profiles only when `sample_size >= 100`.
8. Reject public outputs containing raw-record fields, personal or company identity, URLs, text descriptions, entry keys, image hashes, or raw payloads.

## Runtime use

Resolve context in this order:

1. exact normalized category profile;
2. mapped discipline profile when the category is below the sample threshold;
3. core rubric when neither profile matches.

Keep `score_effect: none`. Use the profile to select questions, request relevant evidence, and explain presentation coverage. Do not alter the 50-point design and 50-point presentation structure.

## Interpretation limits

- High frequency among winners does not establish a causal winning factor.
- Gold versus Winner counts are descriptive and must not become score weights.
- Structured-field coverage describes what is present in the source metadata, not whether a design is objectively good.
- Sector and canonical-category mappings remain `machine_generated_needs_human_review` until manually approved.
- Winner-only data cannot support 1/3/5 behavioral anchors. Build such anchors from the general rubric, expert review, and future non-winner or blinded human-evaluation data instead.
