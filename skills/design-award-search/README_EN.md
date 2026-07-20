# `design-award-search` Skill

[中文说明](README.md)

Finds and verifies same-category award winners from official sources for precedent research, design benchmarking, and visual comparison.

## What To Use It For

- Find winners related by user, function, technology, intervention, form, context, system, or visual language.
- Verify that a case is an actual winner with an official project page and inspectable official imagery.
- Build a small, high-relevance set instead of a broad list of search results.

## Typical Requests

- “Find comparable iF and Red Dot winners for this rehabilitation product.”
- “Find award-winning products with similar visual language and describe observable similarities.”
- “Verify whether these cases are official winners.”

## What You Need To Provide

- Design images, core function, users, and use context.
- Optional award, year, or relevance priorities.

## Workflow

The skill fixes the primary functional category, searches across eight relevance dimensions, and retains only candidates verified through official domains, project pages, and visual evidence. It assigns a primary relation, limited secondary relations, and a relevance level.

## Outputs

- High-precision winner table with official links.
- Relevance dimensions, evidence state, and inclusion rationale.
- Observable visual comparison and unresolved verification gaps.

## Built-In References

- Shared functional taxonomy and official-source registry.
- Query building, official-URL validation, and visual-evidence scripts.
- Retrieval policy and eight-dimension relevance model.

## Boundaries

- Does not judge, optimize, or match the user's design to an award.
- Does not treat search snippets or third-party collections as final evidence.
- Does not persist or redistribute official images, text, or private case data.

## Related Skills

Use `design-evaluation` for critique and `design-award-match` for target selection.
