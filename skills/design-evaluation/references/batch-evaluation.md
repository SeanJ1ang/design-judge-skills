# Batch Evaluation Contract

Use this contract when a fixed corpus is evaluated with `design-evaluation`. The
batch runner orchestrates records; `score_evaluation.py` remains the only numeric
scoring authority. A project adapter may read a private database or object store,
but credentials, database rows, images, and signed URLs must not be bundled with
the public Skill.

## Required manifest

Freeze the evaluation population before processing begins. The manifest must
record:

- `batch_id` and immutable `snapshot_id`;
- the complete list of expected record identifiers;
- the adapter name and its completeness policy version;
- the user-approved maturity mapping and `maturity_source: user`;
- model name/version, prompt version, rubric version, and runner version;
- an input fingerprint for every record;
- the shortlist ratio (normally `0.10`) and retry policy.

Do not silently add newly discovered records to an active batch. Start a new
snapshot when the corpus, source material, mapping, or any evaluation version
changes.

## Adapter boundary

For each expected identifier, the adapter returns a JSON-serializable record with
the stable work identifier, project name, raw maturity value, supplied text,
material references, and non-secret source metadata. It must also return a
deterministic input fingerprint over the evaluation-relevant content.

The adapter is responsible for private access and for turning inaccessible or
unsafe material references into explicit gate failures. The evaluator must not
persist credentials or expiring signed URLs in its payload or result.

## Confirmed K-Design maturity mapping

For the confirmed K-Design batch, apply the following exact mapping to the source
`submission_type` value after trimming surrounding whitespace:

| Source value | Evaluation maturity |
|---|---|
| `Student` | `student_concept` |
| `Company` | `mature_work` |
| `Professional` | `mature_work` |

Every matched record must store `maturity_source: user` and retain both the raw
value and mapping-rule version in the manifest or payload. Blank, null, or any
other value is unmatched: do not infer maturity from affiliation, authorship,
visual finish, or other metadata. Unmatched records finish as `not_evaluable`
with reason `unmatched_maturity`.

## Completeness gate

Run the gate before requesting model evaluation. The project adapter defines its
versioned field rules. For the confirmed K-Design corpus, a record is evaluable
only when all of the following are true:

1. The work row and stable `document_id` exist, and the title is non-empty.
2. `scrape_status` is `complete`.
3. At least one project narrative field is usable (`summary_english`,
   `description_english`, `summary_native`, or `description_native`).
4. At least one linked project image can be read and decoded.
5. The raw maturity value matches the confirmed mapping above.

Reject navigation graphics, placeholders, duplicate-only image sets, and corrupt
files as usable visual evidence. A gate failure is not a zero score. Store it as
`not_evaluable` with one or more stable reason codes and preserve it in the batch
accounting.

## Per-record lifecycle

Allowed states are:

- `queued`: frozen in the manifest but not yet attempted;
- `running`: claimed by one worker;
- `completed`: passed the gate and produced a validated deterministic score;
- `not_evaluable`: failed the completeness or maturity gate;
- `failed`: an adapter, model, validation, or persistence error remains after the
  configured retries.

For a gate-passing record, build the ordinary single-work payload, including all
13 ratings, evidence states, rationales, evidence references, findings,
classification, selected maturity, and `maturity_source: user`. Validate and
score it with `score_evaluation.py`. Persist both the submitted payload and its
validated result. Errors for one record must not stop unrelated records.

A corpus-wide shortlist may be finalized only after every expected identifier is
in a terminal state (`completed`, `not_evaluable`, or `failed`). Always report all
three terminal counts and list failed and non-evaluable records separately.

## Confidence and Critical findings

Keep numeric score, evidence confidence, and Critical status separate.

- `completed` records with `critical_count > 0` go to the Critical review queue.
- `completed` records with `evidence.confidence == Low` go to the low-confidence
  review queue.
- Neither queue is eligible for the primary shortlist, regardless of score.
- `High` and `Medium` confidence records with no unresolved Critical finding form
  the primary eligible population.

Do not delete excluded records or turn missing evidence into an invented defect.
If a human resolves a Critical finding or materially changes the evidence, create
a new versioned evaluation rather than modifying the historical result in place.

## Separate-track top 10%

Never cross-rank `student_concept` and `mature_work`. For each track independently:

1. Let `N` be all successfully evaluated records in the track and calculate
   `k = ceil(N * ratio)`; for the requested top decile, `ratio = 0.10`.
2. Form the primary eligible population defined above and sort it by deterministic
   `score_summary.total_score` descending.
3. Select up to the first `k` eligible records. If fewer than `k` are eligible,
   return all eligible records and report the shortfall rather than admitting a
   Critical or Low-confidence record.
4. Use the score at the last selected position as the cutoff and include every
   eligible work whose total score is equal to or greater than that cutoff.

Exact score ties at the cutoff are all included, so the returned count may exceed
`k`. A stable identifier may order tied rows for display, but must not break the
tie. Report evaluated `N`, eligible count, nominal `k`, cutoff score, actual
returned count, and the number of extra tied works or eligibility shortfall for
each track.

The output name is `evidence-aligned evaluation shortlist` or `within-track top
decile`. A score, rank, percentile, or top-decile flag is not a probability and
must never be written to a field named `predicted_win_probability` or described
as an award forecast.

## Resume, idempotency, and versioning

Build a unique idempotency key from at least:

```text
snapshot_id + work_id + input_fingerprint + maturity + mapping_version
+ model_name/model_version + prompt_version + rubric_version + runner_version
```

Hash the canonical representation for storage. Reuse a terminal row only when
the entire key matches. A changed source fingerprint or version creates a new
evaluation; it does not overwrite the prior result.

Workers must claim rows atomically, increment `attempt_count`, and write terminal
state plus timestamps in one transaction. On resume, skip matching terminal rows,
retry eligible `failed` rows within policy, and reclaim `running` rows only after
a declared stale-worker timeout. Recompute the shortlist only from the fixed
snapshot after all expected rows are terminal. Persist the manifest and summary
so the run can be reproduced and audited.
