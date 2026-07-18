#!/usr/bin/env python3
"""Validate award-result URLs against a small official-source allowlist."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit


@dataclass(frozen=True)
class Rule:
    source: str
    domains: tuple[str, ...]
    path_prefixes: tuple[str, ...]


RULES = (
    Rule("iF Design", ("ifdesign.com",), ("/en/winner-ranking/project/",)),
    Rule("Red Dot", ("red-dot.org",), ("/project/",)),
    Rule(
        "IDEA by IDSA",
        ("idsa.org",),
        ("/awards-recognition/idea/idea-gallery/",),
    ),
)


def canonicalize(url: str) -> str:
    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower()
    host = (parts.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    path = parts.path or "/"
    return urlunsplit((scheme, host, path, parts.query, ""))


def validate(url: str) -> dict:
    try:
        normalized = canonicalize(url)
        parts = urlsplit(normalized)
    except ValueError as exc:
        return {"url": url, "valid": False, "reason": f"malformed URL: {exc}"}

    if parts.scheme != "https":
        return {"url": url, "valid": False, "reason": "HTTPS is required"}

    host = parts.hostname or ""
    for rule in RULES:
        if host in rule.domains:
            if any(parts.path.startswith(prefix) for prefix in rule.path_prefixes):
                return {
                    "url": url,
                    "canonical_url": normalized,
                    "valid": True,
                    "source": rule.source,
                }
            return {
                "url": url,
                "canonical_url": normalized,
                "valid": False,
                "source": rule.source,
                "reason": "official domain but not an accepted project or IDEA award path",
            }

    return {"url": url, "valid": False, "reason": "unsupported or unofficial domain"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate official award project URLs.")
    parser.add_argument("urls", nargs="+", help="One or more candidate URLs")
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = [validate(url) for url in args.urls]
    payload = {
        "valid_count": sum(bool(result.get("valid")) for result in results),
        "invalid_count": sum(not bool(result.get("valid")) for result in results),
        "results": results,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=None if args.compact else 2))
    return 0 if payload["invalid_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
