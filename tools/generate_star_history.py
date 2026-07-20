#!/usr/bin/env python3
"""Generate a deterministic SVG chart from local daily star-count snapshots."""

from __future__ import annotations

import argparse
import json
import math
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from xml.sax.saxutils import escape


API_ROOT = "https://api.github.com"
USER_AGENT = "design-judge-star-history-action"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a local GitHub star-history SVG."
    )
    parser.add_argument(
        "--repository",
        default=os.environ.get("GITHUB_REPOSITORY"),
        help="GitHub repository in owner/name form (default: GITHUB_REPOSITORY).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("assets/star-history.svg"),
        help="Output SVG path.",
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("assets/star-history.json"),
        help="Local star-count history (default: assets/star-history.json).",
    )
    args = parser.parse_args()
    if not args.repository or args.repository.count("/") != 1:
        parser.error("--repository must use the owner/name form")
    return args


def request_json(url: str, token: str | None, attempts: int = 3) -> object:
    headers = {
        "Accept": "application/vnd.github.star+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": USER_AGENT,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    for attempt in range(attempts):
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            retryable = error.code in {403, 429, 500, 502, 503, 504}
            if not retryable or attempt == attempts - 1:
                detail = error.read().decode("utf-8", errors="replace")
                raise RuntimeError(
                    f"GitHub API returned HTTP {error.code} for {url}: {detail}"
                ) from error

            retry_after = error.headers.get("Retry-After")
            reset_at = error.headers.get("X-RateLimit-Reset")
            if retry_after and retry_after.isdigit():
                delay = min(int(retry_after), 20)
            elif reset_at and reset_at.isdigit():
                delay = min(max(int(reset_at) - int(time.time()) + 1, 1), 20)
            else:
                delay = 2**attempt
            time.sleep(delay)
        except urllib.error.URLError as error:
            if attempt == attempts - 1:
                raise RuntimeError(f"Unable to reach GitHub API: {error}") from error
            time.sleep(2**attempt)

    raise AssertionError("retry loop exited unexpectedly")


def parse_github_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def fetch_repository_summary(repository: str, token: str | None) -> tuple[date, int]:
    encoded_repository = urllib.parse.quote(repository, safe="/")
    metadata = request_json(f"{API_ROOT}/repos/{encoded_repository}", token)
    if (
        not isinstance(metadata, dict)
        or not isinstance(metadata.get("created_at"), str)
        or not isinstance(metadata.get("stargazers_count"), int)
    ):
        raise RuntimeError(
            "GitHub repository metadata did not contain created_at and stargazers_count"
        )
    created_on = parse_github_time(metadata["created_at"]).date()
    return created_on, metadata["stargazers_count"]


def load_observations(path: Path, repository: str) -> list[tuple[date, int]]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("repository") != repository:
        raise RuntimeError(f"{path} belongs to a different repository")
    raw_observations = payload.get("observations")
    if not isinstance(raw_observations, list):
        raise RuntimeError(f"{path} does not contain an observations list")
    observations: list[tuple[date, int]] = []
    for item in raw_observations:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("date"), str)
            or not isinstance(item.get("stars"), int)
        ):
            raise RuntimeError(f"{path} contains an invalid observation")
        observations.append((date.fromisoformat(item["date"]), item["stars"]))
    return sorted(observations)


def update_observations(
    observations: list[tuple[date, int]], observed_on: date, stars: int
) -> list[tuple[date, int]]:
    if not observations:
        return [(observed_on, stars)]
    updated = list(observations)
    if updated[-1][0] == observed_on:
        updated[-1] = (observed_on, stars)
    elif updated[-1][1] != stars:
        updated.append((observed_on, stars))
    return updated


def serialize_observations(
    repository: str, created_on: date, observations: list[tuple[date, int]]
) -> str:
    payload = {
        "repository": repository,
        "repository_created": created_on.isoformat(),
        "tracking_started": observations[0][0].isoformat(),
        "observations": [
            {"date": observed_on.isoformat(), "stars": stars}
            for observed_on, stars in observations
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def nice_y_axis(total: int, target_ticks: int = 5) -> tuple[int, int]:
    if total <= 0:
        return 1, 1
    raw_step = total / target_ticks
    magnitude = 10 ** math.floor(math.log10(raw_step))
    normalized = raw_step / magnitude
    for candidate in (1, 2, 2.5, 5, 10):
        if normalized <= candidate:
            step = max(1, int(candidate * magnitude))
            break
    else:
        step = max(1, int(10 * magnitude))
    maximum = max(step, math.ceil(total / step) * step)
    return step, maximum


def render_svg(repository: str, observations: list[tuple[date, int]]) -> str:
    width, height = 1200, 640
    left, right, top, bottom = 105, 70, 145, 95
    plot_width = width - left - right
    plot_height = height - top - bottom

    tracking_started = observations[0][0]
    last_observation = observations[-1][0]
    end_on = max(last_observation, tracking_started + timedelta(days=1))
    span_days = max((end_on - tracking_started).days, 1)
    total_stars = observations[-1][1]
    peak_stars = max(stars for _, stars in observations)
    y_step, y_max = nice_y_axis(peak_stars)

    def x_position(day: date) -> float:
        return left + ((day - tracking_started).days / span_days) * plot_width

    def y_position(value: int) -> float:
        return top + plot_height - (value / y_max) * plot_height

    step_points: list[tuple[date, int]] = [observations[0]]
    previous_stars = observations[0][1]
    for observed_on, stars in observations[1:]:
        step_points.append((observed_on, previous_stars))
        step_points.append((observed_on, stars))
        previous_stars = stars
    step_points.append((end_on, previous_stars))

    line_commands = [
        f"{'M' if index == 0 else 'L'} {x_position(day):.2f} {y_position(value):.2f}"
        for index, (day, value) in enumerate(step_points)
    ]
    line_path = " ".join(line_commands)
    area_path = (
        f"{line_path} L {x_position(end_on):.2f} {top + plot_height:.2f} "
        f"L {x_position(tracking_started):.2f} {top + plot_height:.2f} Z"
    )

    y_grid: list[str] = []
    for value in range(0, y_max + 1, y_step):
        y = y_position(value)
        y_grid.append(
            f'<line x1="{left}" y1="{y:.2f}" x2="{left + plot_width}" '
            f'y2="{y:.2f}" class="grid" />'
        )
        y_grid.append(
            f'<text x="{left - 18}" y="{y + 5:.2f}" text-anchor="end" '
            f'class="axis-label">{value}</text>'
        )

    x_grid: list[str] = []
    seen_dates: set[date] = set()
    for index in range(5):
        tick_day = tracking_started + timedelta(days=round(span_days * index / 4))
        if tick_day in seen_dates:
            continue
        seen_dates.add(tick_day)
        x = x_position(tick_day)
        x_grid.append(
            f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" '
            f'y2="{top + plot_height}" class="grid vertical" />'
        )
        x_grid.append(
            f'<text x="{x:.2f}" y="{top + plot_height + 38}" text-anchor="middle" '
            f'class="axis-label">{tick_day.isoformat()}</text>'
        )

    safe_repository = escape(repository)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">
  <title id="title">GitHub Star History for {safe_repository}</title>
  <desc id="description">Recorded GitHub star count from {tracking_started.isoformat()} to {end_on.isoformat()}: {total_stars} stars.</desc>
  <defs>
    <linearGradient id="background" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#f8fbff" />
      <stop offset="1" stop-color="#eef5ff" />
    </linearGradient>
    <linearGradient id="line" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#155eef" />
      <stop offset="1" stop-color="#27b3e6" />
    </linearGradient>
    <linearGradient id="area" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#155eef" stop-opacity="0.24" />
      <stop offset="1" stop-color="#27b3e6" stop-opacity="0.02" />
    </linearGradient>
    <filter id="shadow" x="-10%" y="-10%" width="120%" height="130%">
      <feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="#0b1f44" flood-opacity="0.10" />
    </filter>
    <style>
      text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
      .grid {{ stroke: #cbdaf0; stroke-width: 1; }}
      .grid.vertical {{ stroke-dasharray: 4 8; opacity: 0.65; }}
      .axis-label {{ fill: #60708d; font-size: 16px; }}
    </style>
  </defs>
  <rect width="{width}" height="{height}" rx="28" fill="url(#background)" />
  <rect x="34" y="30" width="{width - 68}" height="{height - 60}" rx="22" fill="#ffffff" filter="url(#shadow)" />
  <circle cx="82" cy="82" r="8" fill="#ff5b4d" />
  <rect x="105" y="75" width="48" height="8" rx="4" fill="#155eef" />
  <rect x="162" y="75" width="30" height="8" rx="4" fill="#27b3e6" />
  <text x="{left}" y="112" fill="#081b3a" font-size="36" font-weight="750">GitHub Star History</text>
  <text x="{left + plot_width}" y="108" text-anchor="end" fill="#155eef" font-size="28" font-weight="700">★ {total_stars}</text>
  <text x="{left}" y="136" fill="#60708d" font-size="17">{safe_repository}</text>
  {''.join(y_grid)}
  {''.join(x_grid)}
  <path d="{area_path}" fill="url(#area)" />
  <path d="{line_path}" fill="none" stroke="url(#line)" stroke-width="6" stroke-linejoin="round" stroke-linecap="round" />
  <circle cx="{x_position(end_on):.2f}" cy="{y_position(total_stars):.2f}" r="8" fill="#ffffff" stroke="#155eef" stroke-width="5" />
  <text x="{left}" y="{height - 45}" fill="#7b8aa5" font-size="14">Local daily snapshots since {tracking_started.isoformat()} · Updated only when the star count changes</text>
</svg>
'''


def main() -> int:
    args = parse_args()
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    created_on, stars = fetch_repository_summary(args.repository, token)
    observations = load_observations(args.data, args.repository)
    observations = update_observations(
        observations, datetime.now(timezone.utc).date(), stars
    )
    svg = render_svg(args.repository, observations)

    args.data.parent.mkdir(parents=True, exist_ok=True)
    temporary_data = args.data.with_suffix(args.data.suffix + ".tmp")
    temporary_data.write_text(
        serialize_observations(args.repository, created_on, observations),
        encoding="utf-8",
        newline="\n",
    )
    temporary_data.replace(args.data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary_output = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary_output.write_text(svg, encoding="utf-8", newline="\n")
    temporary_output.replace(args.output)
    print(f"Wrote {args.output} and {args.data} with {stars} stars")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
