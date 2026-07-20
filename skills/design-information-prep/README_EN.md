# `design-information-prep` Skill

[中文说明](README.md)

Extracts traceable facts from user-authorized design materials, builds a reusable project dossier, and prepares entry text for the exact fields of a selected award.

## What To Use It For

- Organize project facts from briefs, boards, reports, manuals, patents, or prior copy.
- Find missing information and conflicting claims before drafting.
- Draft or adapt entry text to award-specific fields, language, and length limits.

## Typical Requests

- “Prepare the IDEA entry from these attachments and list missing facts first.”
- “Adapt this Chinese project description to the iF English fields.”
- “Build a reusable project dossier for several future award entries.”

## What You Need To Provide

- Project materials the user is authorized to use.
- Confirmed target award, route, category, and cycle.

## Workflow

The skill verifies the field specification, separates facts, inferences, and gaps in a project dossier, records fact IDs used by each output field, and runs deterministic requiredness, length, and provenance checks.

## Outputs

- Reusable project dossier with provenance.
- Missing-fact and clarification list.
- Chinese or English drafts organized by form field.
- Length, required-field, and provenance validation results.

## Built-In References

Includes field specifications for supported awards, project-dossier and entry-output JSON Schemas, evidence policy, and output templates.

## Boundaries

- Does not invent project facts from winner copy.
- Does not select the target award or replace final submission-file checks.
- Re-verifies dynamic fields and current-cycle limits from official sources.

## Related Skills

Use `design-award-match` first and `design-submission-check` after drafting.
