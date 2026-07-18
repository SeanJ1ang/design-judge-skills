# Retrieval and Ranking Policy

## Candidate gate

Include a candidate only when:

- an official award source verifies the project;
- winner or recognized status and award year are explicit;
- the project is in the same canonical category, or one declared adjacent category after fallback;
- official text or accessible official images support at least one selected relevance dimension;
- a stable official project URL is available.

Reject third-party reposts, unverified nominees, category landing pages, search pages, duplicate variants, and visually similar objects outside the permitted category boundary.

## Dimension-first retrieval

Read [relevance-dimensions.md](relevance-dimensions.md). Search each selected dimension independently. Do not use one global weighted score.

For each candidate, record:

- `Primary relation`: exactly one of the eight dimensions;
- `Secondary relations`: zero to two additional dimensions;
- `Relation evidence`: one concise fact from the official project page;
- `Match`: `High`, `Medium`, or `Broad` within the primary dimension.

Use these labels:

- `High`: direct evidence matches the selected dimension within the same canonical category.
- `Medium`: related evidence matches the dimension within the same canonical category.
- `Broad`: evidence is useful only after broadening to one adjacent category.

Do not award relevance for prestige, recency, visual attractiveness, or image quantity.

## Visual verification states

Assign one internal state to every candidate considered for `visual-language`:

- `Verified`: Inspect at least one visible image on the official project page or one official page-hosted thumbnail, and record at least two directly observable matching attributes. Only this state may use `visual-language` as a primary or secondary relation and count toward visual coverage.
- `Candidate - image inaccessible`: Verify the award, category, identity, and official project URL, but fail to inspect an official image after the ordered attempts in `SKILL.md`. Exclude it from result counts and list at most three such candidates under `Limitations` when useful.
- `Rejected`: Inspect an official image but fail the category gate or find fewer than two supported visual attributes. Exclude it from the results and visual coverage.

Use `Pending visual inspection` only as a transient acquisition state. It means official pixels were acquired but have not yet been observed by a visual-capable tool. It is not a verified result and does not count toward visual coverage. If no tool can observe the pixels, report `Pending visual inspection - visual_tool_unavailable` under `Limitations`; do not mislabel it as `Candidate - image inaccessible`.

Keep these states distinct from `High`, `Medium`, and `Broad`. Those match labels apply only after a candidate passes verification. Text descriptions, image alt text, search snippets, and third-party images can discover candidates but cannot produce `Verified` status.

### Acquisition is not verification

Use `scripts/verify_visual_evidence.py` to test whether an official image can be read in memory. Its successful state, `Official image accessible`, means only that the official asset is ready for direct visual inspection. Keep the visual verification state `Pending visual inspection` until a visual-capable tool observes the pixels and records at least two matching attributes.

Never emit, cache, or return raw image bytes or base64 payloads. Prefer direct remote-image inspection. If the visual tool requires a local path, use `--review-dir` to create a marked session-scoped file, inspect it in the same task, and immediately run `scripts/cleanup_visual_review.py`. Do not retain the file between tasks or use it as a corpus.

### Required visual comparison record

Before changing `Pending visual inspection` to `Verified`, record internally:

- the user-supplied image reference actually observed;
- the official project URL and official image URL actually observed;
- the visual tool observation that exposed both pixel sets;
- at least two paired attributes, each describing the user image and official image separately;
- any material visual difference that limits the match.

Use only these attribute keys: `silhouette`, `proportion`, `color-material`, `surface-treatment`, and `medical-low-stigma-expression`. Count an attribute only when both sides contain a concrete observation. For example, `user: white rounded capsule with cyan perimeter; official: white rounded sensor with blue perimeter` is supported; `both are minimal` is not.

Fail closed. If either pixel set was not observed, official pixels were replaced by alt text or prose, fewer than two paired attributes were recorded, or a temporary handoff remains uncleared, do not assign `Verified`.

### Visual failure reason codes

Record one primary reason code and retain per-attempt reasons internally:

- `unsupported_project_url`: the URL fails the official project-page allowlist; use `Rejected`.
- `page_timeout`: the official project page exceeds its request budget.
- `page_http_error`: the project page returns an unsupported HTTP error.
- `page_network_error`: the project page cannot be reached.
- `no_official_image_found`: the official page exposes no usable image URL.
- `unsupported_asset_host`: page images resolve only to non-allowlisted hosts.
- `asset_cache_miss`: the official image service reports a cache miss.
- `asset_403`: the official image rejects access.
- `asset_404`: the official image is missing.
- `asset_timeout`: the official image exceeds its request budget.
- `asset_network_error`: the image host cannot be reached.
- `asset_http_error`: the image host returns another HTTP error.
- `asset_too_large`: the image exceeds the in-memory safety limit.
- `asset_not_image`: the returned payload is not an image.
- `image_decode_failed`: the payload cannot be validated as an image.
- `candidate_timeout`: one candidate exceeds its total budget.
- `total_timeout`: the visual stage exhausts its total budget before this candidate starts.
- `visual_handoff_setup_failed`: the marked handoff directory could not be created.
- `visual_handoff_failed`: official pixels were acquired but the temporary local-path file could not be written.
- `visual_tool_unavailable`: official pixels were acquired but no visual-capable tool observed them.
- `review_cleanup_failed`: the handoff directory could not be safely removed; do not assign `Verified` until cleanup succeeds.

Map every reason except `unsupported_project_url` to `Candidate - image inaccessible` when award, identity, category, and official URL have already passed the candidate gate. Do not collapse a reason code into a generic timeout in diagnostic output.

### Time and progress policy

- Emit a candidate-start event immediately.
- Emit an event before every official page or image request.
- Emit a completion event for every candidate, including skipped candidates after total timeout.
- Default to five seconds per request, twelve seconds per candidate, and sixty seconds for the full visual stage.
- Continue with the next candidate after any inaccessible-image result.
- Keep visual-stage failure independent from the other seven relevance dimensions.

## Balanced mode

Use balanced mode when the user requests results without selecting dimensions:

1. Activate every dimension supported by the supplied text or images.
2. Seek at least one verified result per active dimension.
3. Allocate remaining result slots to the dimensions with the strongest direct evidence.
4. Do not add weak candidates merely to fill every dimension.
5. Report any dimension with no verified result in `Limitations`.

When the user selects dimensions, search only those dimensions and distribute the requested count as evenly as evidence permits.

## Deduplication and diversification

- Keep each project once and assign it to the dimension with the strongest evidence.
- Keep at most two results from one named product series.
- Prefer at least two official award sources when relevance is comparable.
- Rank by within-dimension relevance first; use source and year diversity only as tie-breakers.

## Output evidence

Group results by `Primary relation`. For each group, use:

| Award-winning project | Award / year | Official category | Secondary relations | Relation evidence | Match | Official source |
|---|---|---|---|---|---|---|

Link directly to the official project page. Paraphrase minimally. Do not reproduce full descriptions or official images.

After all groups, include only:

- `Search coverage`: sources, selected dimensions, filters, and result counts per dimension.
- `Limitations`: inaccessible evidence, unsupported visual comparison, broadened categories, and dimensions without verified results.

## Search stopping rule

Stop when the requested total is reached with verified `High` or `Medium` results and every active dimension has been checked. If fewer than three verified candidates remain overall, broaden exactly one taxonomy level and label those additions `Broad`.
