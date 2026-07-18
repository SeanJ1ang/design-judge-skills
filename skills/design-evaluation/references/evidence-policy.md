# Evidence Policy

## Evidence states

| State | Meaning | Typical evidence |
|---|---|---|
| Verified | Directly observable or directly measured | visible feature, working prototype, test result, production record, documented deployment |
| Supported | Consistent indirect support from more than one supplied item | coherent drawings plus prototype photos; process description plus interface states |
| Claimed | Stated by the author but not independently demonstrated in supplied materials | performance statement, sustainability claim, intended behaviour |
| Missing | Required evidence is absent or inaccessible | no mechanism, no key screen, unreadable figure, no implementation evidence |

## Evidence ledger record

Every dimension record should contain:

```yaml
dimension: implementation_feasibility
state: Supported
evidence:
  - Prototype photo shows the enclosure and sensor placement.
  - Exploded diagram identifies replaceable modules.
rationale: The construction is coherent, but no functional or durability test is supplied.
limitations:
  - Battery life is claimed but not measured.
```

## Interpretation rules

- Separate `Observed`, `Author claim`, and `Evaluator inference` in the reasoning.
- A polished rendering verifies visible composition, not manufacture, function, safety, or market readiness.
- An award-winning precedent verifies that the precedent won; it does not validate the user's design.
- Search snippets and inaccessible thumbnails do not verify visual evidence.
- Absence of evidence is a material limitation, not automatic proof that the feature does not exist.
- Conflicting materials reduce confidence and should be cited explicitly.

## Maturity mismatch

Maturity always remains the user's choice.

Record `Maturity evidence mismatch` when:

- Mature Work is selected but the supplied materials contain no implementation, real-use, test, manufacture, or operational evidence; or
- the materials explicitly describe the work as an unrealised concept while Mature Work is selected.

Do not automatically reclassify the entry. Apply the selected profile, record the mismatch, and enforce relevant evidence caps.

