#!/usr/bin/env python3
"""Deterministic JSONL scoring and track-local shortlisting.

The batch layer deliberately remains a rubric-ranking utility.  It does not
estimate award outcomes and it never compares student concepts with mature
works.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from contextlib import nullcontext
from pathlib import Path
from typing import Any, Iterable, Iterator, TextIO

from score_evaluation import score_evaluation


TRACKS = ("student_concept", "mature_work")
ELIGIBLE_CONFIDENCE = {"Medium", "High"}


def _document_id(payload: Any) -> str:
    if not isinstance(payload, dict):
        raise ValueError("Input line must be a JSON object.")
    value = payload.get("document_id")
    if value is None or isinstance(value, (dict, list, bool)):
        raise ValueError("'document_id' must be a non-empty string or number.")
    result = str(value).strip()
    if not result:
        raise ValueError("'document_id' must be a non-empty string or number.")
    return result


def score_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Score one database document while preserving its stable identifier."""
    document_id = _document_id(payload)
    return {"document_id": document_id, **score_evaluation(payload)}


def iter_jsonl(stream: TextIO) -> Iterator[tuple[int, Any]]:
    """Yield non-blank JSONL records with their physical line numbers."""
    for line_number, raw_line in enumerate(stream, start=1):
        if not raw_line.strip():
            continue
        yield line_number, json.loads(raw_line)


def error_record(line_number: int, exc: Exception, payload: Any = None) -> dict[str, Any]:
    error: dict[str, Any] = {
        "line_number": line_number,
        "error_type": type(exc).__name__,
        "error": str(exc),
    }
    if isinstance(payload, dict) and payload.get("document_id") is not None:
        error["document_id"] = str(payload["document_id"])
    return error


def score_lines(lines: Iterable[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Score JSONL lines independently, returning successes and failures."""
    results: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(lines, start=1):
        if not raw_line.strip():
            continue
        payload: Any = None
        try:
            payload = json.loads(raw_line)
            results.append(score_payload(payload))
        except Exception as exc:
            errors.append(error_record(line_number, exc, payload))
    return results, errors


def _number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"'{field}' must be numeric.")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"'{field}' must be finite.")
    return result


def _shortlist_fields(record: Any) -> tuple[str, str, float, float, float, float, int]:
    document_id = _document_id(record)
    maturity = str(record.get("maturity", "")).strip().lower()
    if maturity not in TRACKS:
        raise ValueError("'maturity' must be student_concept or mature_work.")

    summary = record.get("score_summary")
    evidence = record.get("evidence")
    if not isinstance(summary, dict) or not isinstance(evidence, dict):
        raise ValueError("Scored record requires score_summary and evidence objects.")
    total = _number(summary.get("total_score"), "score_summary.total_score")
    design = _number(summary.get("design_score"), "score_summary.design_score")
    presentation = _number(
        summary.get("presentation_score"), "score_summary.presentation_score"
    )
    confidence_index = _number(
        evidence.get("confidence_index"), "evidence.confidence_index"
    )
    critical_count = summary.get("critical_count")
    if isinstance(critical_count, bool) or not isinstance(critical_count, int):
        raise ValueError("'score_summary.critical_count' must be an integer.")
    if critical_count < 0:
        raise ValueError("'score_summary.critical_count' must not be negative.")
    confidence = str(evidence.get("confidence", "")).strip()
    return (
        document_id,
        maturity,
        total,
        confidence_index,
        design,
        presentation,
        critical_count,
    )


def is_eligible(record: dict[str, Any]) -> bool:
    """Return whether a valid scored record may enter a shortlist."""
    *_, critical_count = _shortlist_fields(record)
    return (
        critical_count == 0
        and record["evidence"]["confidence"] in ELIGIBLE_CONFIDENCE
    )


def _sort_key(record: dict[str, Any]) -> tuple[Any, ...]:
    document_id, _, total, confidence, design, presentation, _ = _shortlist_fields(record)
    return (-total, -confidence, -design, -presentation, document_id)


def shortlist_records(
    records: Iterable[dict[str, Any]], ratio: float = 0.10
) -> list[dict[str, Any]]:
    """Select each track independently, extending selection across score ties.

    The target for a track is ``ceil(successfully evaluated count * ratio)``.
    Ineligible evaluations remain in that denominator but cannot be selected.
    Output is grouped by track in ``TRACKS`` order; no global rank is created.
    """
    if isinstance(ratio, bool) or not isinstance(ratio, (int, float)):
        raise ValueError("ratio must be numeric.")
    ratio = float(ratio)
    if not math.isfinite(ratio) or not 0 < ratio <= 1:
        raise ValueError("ratio must be greater than 0 and at most 1.")

    grouped: dict[str, list[dict[str, Any]]] = {track: [] for track in TRACKS}
    for record in records:
        _, maturity, *_ = _shortlist_fields(record)
        grouped[maturity].append(record)

    selected: list[dict[str, Any]] = []
    for track in TRACKS:
        evaluated = grouped[track]
        if not evaluated:
            continue
        target = math.ceil(len(evaluated) * ratio)
        eligible = sorted((item for item in evaluated if is_eligible(item)), key=_sort_key)
        if not eligible:
            continue
        provisional = eligible[:target]
        boundary = provisional[-1]["score_summary"]["total_score"]
        chosen = [
            item
            for item in eligible
            if item["score_summary"]["total_score"] >= boundary
        ]
        for rank, item in enumerate(chosen, start=1):
            output = dict(item)
            output["shortlist"] = {
                "track": track,
                "track_rank": rank,
                "ratio": ratio,
                "evaluated_count": len(evaluated),
                "eligible_count": len(eligible),
                "target_count": target,
                "selected_count": len(chosen),
                "boundary_total_score": boundary,
            }
            selected.append(output)
    return selected


def shortlist_lines(
    lines: Iterable[str], ratio: float = 0.10
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Parse scored JSONL with isolation, then create track-local shortlists."""
    records: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(lines, start=1):
        if not raw_line.strip():
            continue
        payload: Any = None
        try:
            payload = json.loads(raw_line)
            _shortlist_fields(payload)
            records.append(payload)
        except Exception as exc:
            errors.append(error_record(line_number, exc, payload))
    return shortlist_records(records, ratio), errors


def _open_input(path: str) -> Any:
    return nullcontext(sys.stdin) if path == "-" else Path(path).open(encoding="utf-8")


def _open_output(path: str | None, fallback: TextIO) -> Any:
    if path in (None, "-"):
        return nullcontext(fallback)
    return Path(path).open("w", encoding="utf-8", newline="\n")


def _write_jsonl(stream: TextIO, records: Iterable[dict[str, Any]]) -> None:
    for record in records:
        json.dump(record, stream, ensure_ascii=False, sort_keys=False)
        stream.write("\n")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Score and shortlist design evaluations in deterministic JSONL batches."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    score = subparsers.add_parser("score", help="Score independent work payloads.")
    score.add_argument("input", nargs="?", default="-", help="Input JSONL or - for stdin.")
    score.add_argument("-o", "--output", "--results", default="-", help="Result JSONL.")
    score.add_argument("--errors", help="Error JSONL; defaults to stderr.")

    shortlist = subparsers.add_parser(
        "shortlist", help="Select eligible top works separately within each track."
    )
    shortlist.add_argument("input", nargs="?", default="-", help="Scored JSONL or -.")
    shortlist.add_argument("-o", "--output", default="-", help="Shortlist JSONL.")
    shortlist.add_argument("--errors", help="Error JSONL; defaults to stderr.")
    shortlist.add_argument("--ratio", type=float, default=0.10, help="Track-local ratio.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.output == "-" and args.errors == "-":
        print("error: output and errors cannot both use stdout.", file=sys.stderr)
        return 2
    try:
        with _open_input(args.input) as source:
            if args.command == "score":
                results, errors = score_lines(source)
            else:
                results, errors = shortlist_lines(source, args.ratio)
        with _open_output(args.output, sys.stdout) as result_stream:
            _write_jsonl(result_stream, results)
        with _open_output(args.errors, sys.stderr) as error_stream:
            _write_jsonl(error_stream, errors)
    except (OSError, TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
