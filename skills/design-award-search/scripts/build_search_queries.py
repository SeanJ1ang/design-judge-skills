#!/usr/bin/env python3
"""Build dimension-specific official award-site search queries without network access."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    key: str
    name: str
    prefix: str


@dataclass(frozen=True)
class Dimension:
    key: str
    name: str
    anchors: tuple[str, ...]
    fields: tuple[str, ...]


SOURCES = (
    Source("if", "iF Design Award", "site:ifdesign.com/en/winner-ranking/project"),
    Source("reddot", "Red Dot", "site:red-dot.org/project"),
    Source("idea", "IDEA by IDSA", "site:idsa.org/awards-recognition/idea/idea-gallery"),
)

DIMENSIONS = (
    Dimension("problem-user", "Problem and user", ("problem", "user"), ("problem", "user")),
    Dimension("core-function", "Core function", ("function",), ("function", "object")),
    Dimension(
        "sensing-technology",
        "Sensing technology",
        ("sensing",),
        ("sensing", "function"),
    ),
    Dimension(
        "intervention-mechanism",
        "Intervention mechanism",
        ("intervention",),
        ("intervention", "function"),
    ),
    Dimension("physical-form", "Physical form", ("form", "object"), ("form", "object")),
    Dimension(
        "use-context",
        "Use context and workflow",
        ("context",),
        ("context", "function", "user"),
    ),
    Dimension(
        "system-architecture",
        "System architecture",
        ("system",),
        ("system", "object"),
    ),
    Dimension("visual-language", "Visual language", ("visual",), ("visual", "form")),
)

QUERY_STOPWORDS = {
    "a",
    "an",
    "and",
    "at",
    "by",
    "for",
    "from",
    "in",
    "into",
    "of",
    "on",
    "the",
    "through",
    "to",
    "with",
}


def clean(value: str | None) -> str:
    if not value:
        return ""
    value = re.sub(r"[\r\n\t]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def quoted(value: str) -> str:
    normalized = clean(value).replace('"', "")
    return f'"{normalized}"' if normalized else ""


def unique_terms(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = clean(value)
        key = normalized.casefold()
        if normalized and key not in seen:
            seen.add(key)
            result.append(normalized)
    return result


def compact_tokens(value: str, limit: int) -> list[str]:
    """Return a short list of searchable words without quoting the whole input phrase."""
    tokens = re.findall(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)?", clean(value))
    result: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        key = token.casefold()
        if key in QUERY_STOPWORDS or key in seen:
            continue
        seen.add(key)
        result.append(token)
        if len(result) == limit:
            break
    return result


def compact_phrase(value: str, limit: int) -> str:
    return " ".join(compact_tokens(value, limit))


def build_visual_queries(source: Source, profile: dict[str, str], extras: list[str]) -> list[str]:
    """Build high-recall visual queries from short object, form, and descriptor terms."""
    object_phrase = compact_phrase(profile["object"], 4)
    form_phrase = compact_phrase(profile["form"], 3)
    descriptors = compact_tokens(profile["visual"], 6)
    extra_descriptors = [
        token
        for extra in extras
        for token in compact_tokens(extra, 2)
    ]
    descriptors = unique_terms([*descriptors, *extra_descriptors])
    expanded_descriptors = descriptors[3:6] or descriptors[:3]

    precise = " ".join(
        part
        for part in [
            source.prefix,
            quoted(object_phrase or profile["category"]),
            quoted(form_phrase),
            *descriptors[:3],
        ]
        if part
    )
    expanded = " ".join(
        part
        for part in [
            source.prefix,
            quoted(profile["category"]),
            quoted(object_phrase or form_phrase),
            *expanded_descriptors,
        ]
        if part
    )
    return unique_terms([precise, expanded])


def parse_selection(raw: str, known: tuple[str, ...], label: str) -> set[str]:
    requested = {part.strip().lower() for part in raw.split(",") if part.strip()}
    if requested == {"all"}:
        return set(known)
    unknown = requested - set(known)
    if unknown:
        raise ValueError(f"Unsupported {label}: {', '.join(sorted(unknown))}")
    if not requested:
        raise ValueError(f"At least one {label} is required")
    return requested


def build_queries(args: argparse.Namespace) -> dict:
    source_keys = tuple(source.key for source in SOURCES)
    dimension_keys = tuple(dimension.key for dimension in DIMENSIONS)
    selected_sources = parse_selection(args.sources, source_keys, "sources")
    selected_dimensions = parse_selection(args.dimensions, dimension_keys, "dimensions")

    profile = {
        "category": clean(args.category),
        "object": clean(args.object),
        "problem": clean(args.problem),
        "user": clean(args.user),
        "function": clean(args.function),
        "sensing": clean(args.sensing),
        "intervention": clean(args.intervention),
        "form": clean(args.form),
        "context": clean(args.context),
        "system": clean(args.system),
        "visual": clean(args.visual),
    }
    extras = unique_terms(args.extra or [])[:3]

    if not profile["category"] or not profile["function"]:
        raise ValueError("Both --category and --function are required")

    active: list[tuple[Dimension, list[str]]] = []
    skipped: list[dict[str, str]] = []
    for dimension in DIMENSIONS:
        if dimension.key not in selected_dimensions:
            continue
        anchors = unique_terms([profile[field] for field in dimension.anchors])
        if not anchors:
            skipped.append(
                {
                    "dimension": dimension.key,
                    "reason": "no dimension-specific input was supplied or inferred",
                }
            )
            continue
        terms = unique_terms([profile[field] for field in dimension.fields])
        active.append((dimension, terms[:3]))

    output_sources: list[dict] = []
    for source in SOURCES:
        if source.key not in selected_sources:
            continue
        dimension_queries: list[dict] = []
        for dimension, terms in active:
            if dimension.key == "visual-language":
                queries = build_visual_queries(source, profile, extras)
            else:
                precise = " ".join(
                    [
                        source.prefix,
                        *[quoted(term) for term in terms[:2]],
                        *[quoted(x) for x in extras[:1]],
                    ]
                )
                expanded = " ".join(
                    [
                        source.prefix,
                        quoted(profile["category"]),
                        *terms[:2],
                        *extras[1:2],
                    ]
                )
                queries = unique_terms([precise, expanded])
            dimension_queries.append(
                {
                    "dimension": dimension.key,
                    "dimension_name": dimension.name,
                    "queries": queries,
                }
            )
        output_sources.append(
            {
                "source": source.key,
                "source_name": source.name,
                "dimensions": dimension_queries,
            }
        )

    return {
        "profile": {**profile, "extra_terms": extras},
        "active_dimensions": [dimension.key for dimension, _ in active],
        "skipped_dimensions": skipped,
        "sources": output_sources,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate official award-site queries for eight relevance dimensions."
    )
    parser.add_argument("--category", required=True, help="Canonical category in English")
    parser.add_argument("--function", required=True, help="Primary function or user job")
    parser.add_argument("--object", default="", help="Designed object or service")
    parser.add_argument("--problem", default="", help="Problem, condition, or unmet need")
    parser.add_argument("--user", default="", help="Target user or stakeholder")
    parser.add_argument("--sensing", default="", help="Sensing or state-inference technology")
    parser.add_argument("--intervention", default="", help="Intervention or feedback mechanism")
    parser.add_argument("--form", default="", help="Physical form, attachment, or wear mode")
    parser.add_argument("--context", default="", help="Use context, moment, or workflow")
    parser.add_argument("--system", default="", help="System components and information flow")
    parser.add_argument("--visual", default="", help="Visible form and CMF descriptors")
    parser.add_argument(
        "--dimensions",
        default="all",
        help="Comma-separated dimension keys or all",
    )
    parser.add_argument(
        "--extra", action="append", default=[], help="Extra English synonym; repeat up to three times"
    )
    parser.add_argument(
        "--sources", default="if,reddot,idea", help="Comma-separated: if,reddot,idea"
    )
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        payload = build_queries(args)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(payload, ensure_ascii=False, indent=None if args.compact else 2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
