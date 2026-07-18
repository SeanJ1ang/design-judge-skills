# Official Source Registry

Use this file to discover and verify public official award pages. URL patterns can change; verify the current official site before relying on a pattern.

## Source precedence

1. Official project or winner page.
2. Official award gallery or category listing.
3. Official award-organization announcement.
4. Search-engine snippet for discovery only; never use it as final proof.

## Supported sources

| Source | Official domain | Preferred project path | Site-restricted query prefix |
|---|---|---|---|
| iF Design Award | `ifdesign.com` | `/en/winner-ranking/project/` | `site:ifdesign.com/en/winner-ranking/project` |
| iF Design Student Award | `ifdesign.com` | `/en/winner-ranking/project/` | `site:ifdesign.com/en/winner-ranking/project` |
| Red Dot Product Design | `red-dot.org` | `/project/` | `site:red-dot.org/project "Product Design"` |
| Red Dot Design Concept | `red-dot.org` | `/project/` | `site:red-dot.org/project "Design Concept"` |
| IDEA by IDSA | `idsa.org` | `/awards-recognitions/idea/idea-gallery/` | `site:idsa.org/awards-recognitions/idea/idea-gallery` |
| Design Intelligence Award | `di-award.org` | `/en/collections.html` | `site:di-award.org/en/collections` |
| K-Design Award | `kdesignaward.com` | `/index.php?mid=exhibition` | `site:kdesignaward.com exhibition` |
| GOOD DESIGN AWARD Japan | `g-mark.org` | `/gallery/winners` | `site:g-mark.org/gallery/winners` |
| Core77 Design Awards | `designawards.core77.com` | category and winner pages | `site:designawards.core77.com` |
| James Dyson Award | `jamesdysonaward.org` | `/past-winners/` | `site:jamesdysonaward.org past-winners` |
| European Product Design Award | `productdesignaward.eu` | `/winners/` | `site:productdesignaward.eu/winners` |

Accept `www.` and language or locale variations on the same official domain. Reject lookalike domains, copied galleries, Pinterest, social posts, portfolio reposts, press aggregators, and seller pages as final evidence.

## Query construction

Construct up to three queries per source, moving from precision to recall:

1. Exact functional query:

```text
{site prefix} "{primary function}" "{object or category}"
```

2. Unquoted functional recall query:

```text
{site prefix} {primary function} {object}
```

3. Expanded category query:

```text
{site prefix} "{canonical category}" {synonym 1} {use context}
```

Use English terms by default because the supported official galleries primarily index English project pages. Preserve distinctive product terminology in its original language only as an extra term.

## Verification checklist

Confirm on the official page:

- project title;
- official award organization;
- award year or edition when present;
- winner or recognized status;
- category, discipline, or documented primary function;
- stable official project URL.

If an official page does not expose a category, use its documented primary function as category evidence and disclose this in the match rationale.

## Access behavior

- Use normal public navigation and search.
- Keep requests proportional to a single user query.
- Do not enumerate whole galleries.
- Do not download or mirror images.
- Do not persist official page content after the task.
- Stop if automated access is prohibited or technically blocked.
