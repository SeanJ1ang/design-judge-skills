# Award Profile Guide

Use the JSON profiles under `awards/` as a stable routing layer. They are not cached copies of annual rules.

## Configuration layers

| Layer | Purpose | Update behavior |
|---|---|---|
| `awards/index.json` | Supported-program allowlist and aliases | Change only when support scope changes |
| `awards/*.json` | Stable routes, broad category hints, official source entry points, and dynamic-gate names | Review when an award changes its program structure |
| `category-crosswalk.json` | Shared project categories, states, and entrant types | Keep stable across awards |
| `criteria-crosswalk.json` | Cross-award comparison dimensions | Never replace official criterion wording |
| Live official pages | Dates, fees, windows, exact category labels, and current requirements | Verify for every user request |

## Profile semantics

- `routes`: distinct official applicant or project paths. Do not merge professional, student, concept, and realized routes when rules differ.
- `required_project_fields`: facts needed before structural eligibility can be resolved.
- `stable_constraints`: deterministic gates unlikely to change annually.
- `dynamic_gates`: current official facts that keep eligibility at `Unknown` until verified.
- `category_hints`: initial routing aids. `exact`, `adjacent`, `broad`, and `live-lookup` describe mapping strength, not eligibility.
- `criteria`: official labels paired with normalized comparison dimensions.
- `dynamic_fields`: items that must never be trusted from memory or treated as permanent configuration.
- `last_profile_reviewed`: profile review date, not proof that annual rules remain current.

## Add or change a profile

1. Use only public official sources.
2. Add or edit the program in `awards/index.json`.
3. Follow `award-profile-schema.json` and reuse canonical values from the crosswalks.
4. Put annual or ambiguous conditions in `dynamic_gates`, not stable constraints.
5. Validate:

```powershell
python scripts/validate_award_profiles.py --pretty
```

6. Add routing and eligibility tests before treating the profile as supported.

Do not add scraped winner content, images, private datasets, or remembered annual dates to profiles.
