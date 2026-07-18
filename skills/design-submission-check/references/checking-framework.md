# Submission Checking Framework

## Check statuses

Assign one status to every requirement:

| Status | Meaning |
|---|---|
| Pass | Directly checked and compliant |
| Fail | Directly checked and noncompliant |
| Not checked | Required evidence, access, or measurable metadata is unavailable |
| Not applicable | The official rule does not apply to this entry; explain why |

Do not use `Pass` for an inferred or assumed result.

## Finding severity

| Severity | Definition | Typical examples |
|---|---|---|
| Blocker | Confirmed hard-rule failure, missing mandatory item, unreadable required file, unresolved official-rule conflict, or eligibility-invalidating issue | missing board; video over hard duration limit; prohibited applicant name in anonymous material |
| Important | Material credibility, consistency, rights-readiness, or comprehension risk without a confirmed automatic rejection rule | conflicting metric; license pending; unclear role attribution; mandatory technical metadata not measured |
| Optimization | Optional improvement with no basic compliance impact | clearer filename ordering; redundant caption; nonessential wording refinement |

If an official rule explicitly says a condition causes rejection or upload failure, classify its violation as a Blocker. Do not promote stylistic preferences to Blockers.

## Final decision

Use the highest unresolved severity:

```text
Blocker present -> Not ready
No Blocker, Important present -> Conditionally ready
Only Optimization or no findings -> Ready
```

An audit can be `Partial` in coverage while still giving a provisional decision. When mandatory rule groups were not verified, do not return an unconditional `Ready`.

## Coverage

Report coverage separately from readiness:

- `Rule coverage`: checked requirements / applicable requirements.
- `Material coverage`: inspected supplied items / supplied items.
- `Portal coverage`: checked or not checked.
- `Rights coverage`: cleared assets / identified third-party assets.

Coverage is descriptive. It is not a quality score and must not override findings.

## Finding record

Every finding should contain:

```yaml
id: F-001
severity: Blocker | Important | Optimization
requirement_id: R-001
affected_items: []
finding: concise observable issue
evidence: measured value or source fact
required_action: one testable fix
verification: how to confirm the fix
```

Merge duplicate symptoms into one root finding and list all affected items.

