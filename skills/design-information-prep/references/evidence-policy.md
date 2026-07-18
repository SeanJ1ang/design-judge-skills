# Evidence Policy

## Fact statuses

| Status | Use |
|---|---|
| `supported` | The attachment directly states or clearly demonstrates the fact. |
| `inferred` | The fact is a bounded interpretation of supplied material and must remain labeled. |
| `confirmed_by_user` | The user explicitly confirms the fact; record the confirmation as evidence. |
| `missing` | No sufficient source exists. Do not draft the fact as true. |

## Evidence records

For every non-missing fact, record at least one evidence item:

```json
{
  "source": "design-brief.pdf",
  "locator": "page 12",
  "evidence_type": "direct",
  "note": "Explains the replaceable sensor module."
}
```

Use `direct`, `derived`, or `user_confirmation`. Keep notes short; do not duplicate long copyrighted passages.

## Claim rules

- Preserve measurement units, population, denominator, date, test conditions, and source.
- Label intended, expected, estimated, simulated, and measured outcomes distinctly.
- Treat market size, cost, performance, environmental, health, safety, and social-impact claims as unsupported until evidence is supplied.
- Treat patents and awards as status claims: distinguish filed, pending, granted, shortlisted, and won.
- Do not infer commercial launch, manufacturing readiness, or user validation from polished renderings.
- Do not resolve contradictory versions silently. Ask the user which version is authoritative.
- Do not use other entrants' facts, winner descriptions, model scores, or aggregate benchmarks as project evidence.

## Confidentiality

- Inspect only user-authorized files.
- Do not place confidential project terms in external search queries.
- Record disclosure restrictions in the dossier.
- Warn when an award field may become public and the supplied fact is marked confidential.

