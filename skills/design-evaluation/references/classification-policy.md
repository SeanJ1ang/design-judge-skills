# Evaluation Classification Policy

## Four axes

Use four separate axes:

1. `Design discipline`: one primary, up to two secondary.
2. `Application sector`: one primary, up to one secondary.
3. `Focus tags`: zero or more.
4. `Work maturity`: exactly one value supplied by the user.

The controlled vocabulary is in `profiles/classification.json`.

## Classification order

1. Preserve the user-selected maturity.
2. Identify the primary function and direct user task.
3. Classify what is being designed as the primary discipline.
4. Classify where or for whom it operates as the primary sector.
5. Add focus tags for cross-cutting themes and technologies.

Primary function controls ambiguity. Visual resemblance, material, technology, and branding are secondary evidence.

## Selection rules

- A health application is primarily `user_experience` or `user_interface` by discipline and `healthcare` by sector.
- A rehabilitation device is `physical_product` by discipline and `healthcare` by sector; add `social_impact_inclusion` only when accessibility is central.
- Sustainable packaging is `packaging` by discipline, its product market by sector, and `sustainability_circularity` as a focus tag.
- A hospital wayfinding system is `brand_communication` by discipline, `healthcare` by sector, and `typography_wayfinding` as a tag.
- Experimental or speculative work keeps its underlying discipline and uses `experimental_speculative` as a tag.

## Relationship to the shared search taxonomy

This classification describes an evaluation profile. `skills/design-judge-shared/category-taxonomy.md` remains the functional retrieval taxonomy for `$design-award-search`. When benchmark retrieval is requested, translate the evaluation profile into one shared canonical search category and no more than two adjacent categories.
