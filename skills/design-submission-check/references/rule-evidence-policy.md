# Submission Rule Evidence Policy

## Exact-target rule

Bind every audit to one exact combination:

```text
award program + cycle + track + category + applicant type + submission stage
```

Rules from another combination are not controlling evidence.

## Source precedence

1. Current official terms, regulations, or entry guide.
2. Current category- or stage-specific official instructions.
3. Current official portal help and upload instructions.
4. Current official FAQ or organizer clarification.
5. Archived official material, clearly dated.
6. Third-party summaries for discovery only.

Search snippets, prior winners, community posts, and remembered rules cannot prove current compliance.

## Requirement ledger

Record:

| ID | Requirement | Applies to | Constraint | Required? | Source | Checked on | Status |
|---|---|---|---|---|---|---|---|

Use one stable requirement ID per independently testable rule. Split combined prose into separate checks where different fixes or severities apply.

## Rule facts

Capture exact values without interpretation:

- allowed extensions and actual media type;
- minimum and maximum count;
- file-size unit and whether the organizer means MB or MiB when stated;
- pixel dimensions, resolution, aspect ratio, color space, and orientation;
- duration, word, character, page, or slide limit;
- filename, language, caption, credit, logo, and anonymity requirements;
- deadline as an absolute date plus official timezone;
- required declarations and who must accept or sign them.

When the unit or wording is ambiguous, preserve the original term, state the interpretation, and flag the uncertainty.

## Freshness and conflicts

Record `checked on: YYYY-MM-DD` for every time-sensitive source. Recheck shortly before final upload. If two current official pages conflict:

1. prefer the more specific track/category/stage instruction;
2. prefer the later explicit revision when dates are available;
3. otherwise classify the conflict as a Blocker and request organizer confirmation.

Do not silently choose the more convenient rule.

## Deadline handling

Distinguish:

- submission deadline;
- payment deadline;
- edit-lock deadline;
- physical delivery deadline;
- timezone and daylight-saving basis;
- portal closure or grace-period language.

The skill may report timing risk but must not claim a submission occurred or was accepted without direct confirmation.

