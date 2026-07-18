#!/usr/bin/env python3
"""Acquire official award images and report visual-evidence readiness.

The default mode never writes or prints image payloads. ``--review-dir`` creates a
marked, short-lived local-path handoff only for visual tools that cannot inspect a
remote asset directly. A separate visual-capable tool must inspect the pixels, and
the caller must run ``cleanup_visual_review.py`` in the same task, before a
candidate can receive the ``Verified`` visual state.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import time
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable, Iterable, TextIO
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen

try:
    from PIL import Image, UnidentifiedImageError
except ImportError:  # pragma: no cover - exercised through the signature fallback
    Image = None

    class UnidentifiedImageError(Exception):
        pass

from verify_official_urls import validate as validate_project_url


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
)

IMAGE_HOSTS = {
    "iF Design": ("ifdesign.com", "ifdalivestorage.blob.core.windows.net"),
    "Red Dot": ("red-dot.org",),
    "IDEA by IDSA": ("idsa.org",),
}

REVIEW_MARKER = ".design-award-visual-review.json"
FORMAT_SUFFIXES = {
    "JPEG": ".jpg",
    "PNG": ".png",
    "GIF": ".gif",
    "WEBP": ".webp",
    "AVIF": ".avif",
    "HEIC": ".heic",
    "HEIX": ".heic",
}
FORMAT_MIME_TYPES = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "GIF": "image/gif",
    "WEBP": "image/webp",
    "AVIF": "image/avif",
    "HEIC": "image/heic",
    "HEIX": "image/heic",
}


@dataclass(frozen=True)
class Config:
    request_timeout: float = 5.0
    candidate_timeout: float = 12.0
    total_timeout: float = 60.0
    max_images: int = 3
    max_html_bytes: int = 2 * 1024 * 1024
    max_image_bytes: int = 10 * 1024 * 1024


@dataclass(frozen=True)
class FetchResult:
    ok: bool
    url: str
    body: bytes = b""
    content_type: str = ""
    reason: str = ""
    http_status: int | None = None


class ReviewHandoff:
    """Write short-lived review assets for a visual tool, never for caching."""

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory).expanduser().resolve()
        if self.directory.exists():
            raise ValueError("review directory must not already exist")
        self.directory.mkdir(parents=True, exist_ok=False)
        self.assets: list[dict] = []
        self._write_marker()

    @property
    def marker_path(self) -> Path:
        return self.directory / REVIEW_MARKER

    def write_asset(
        self,
        *,
        body: bytes,
        image_format: str,
        project_url: str,
        image_url: str,
        index: int,
    ) -> dict:
        normalized_format = image_format.upper()
        suffix = FORMAT_SUFFIXES.get(normalized_format)
        if not suffix:
            raise ValueError(f"unsupported review image format: {image_format}")
        digest = hashlib.sha256(image_url.encode("utf-8")).hexdigest()[:12]
        filename = f"{index:02d}-{digest}{suffix}"
        path = self.directory / filename
        with path.open("xb") as stream:
            stream.write(body)
        mime_type = FORMAT_MIME_TYPES[normalized_format]
        record = {
            "filename": filename,
            "project_url": project_url,
            "official_image_url": image_url,
            "mime_type": mime_type,
            "bytes": len(body),
        }
        self.assets.append(record)
        self._write_marker()
        return {
            "review_path": str(path),
            "review_mime_type": mime_type,
            "review_bytes": len(body),
            "cleanup_marker": str(self.marker_path),
        }

    def _write_marker(self) -> None:
        payload = {
            "schema": "design-award-visual-review/v1",
            "created_unix": round(time.time(), 3),
            "directory": str(self.directory),
            "assets": self.assets,
            "cleanup_required": True,
        }
        self.marker_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


class OfficialImageParser(HTMLParser):
    """Collect likely hero and gallery image URLs in evidence-priority order."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.meta_images: list[str] = []
        self.link_images: list[str] = []
        self.element_images: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.casefold(): (value or "").strip() for key, value in attrs}
        tag = tag.casefold()

        if tag == "meta":
            key = (values.get("property") or values.get("name") or "").casefold()
            if key in {"og:image", "og:image:url", "twitter:image"}:
                self._append(self.meta_images, values.get("content", ""))
            return

        if tag == "link":
            rel = values.get("rel", "").casefold().split()
            if "image_src" in rel or (
                "preload" in rel and values.get("as", "").casefold() == "image"
            ):
                self._append(self.link_images, values.get("href", ""))
            return

        if tag != "img":
            return

        for key in ("src", "data-src", "data-lazy-src", "data-original"):
            self._append(self.element_images, values.get(key, ""))
        for key in ("srcset", "data-srcset"):
            for url in parse_srcset(values.get(key, "")):
                self._append(self.element_images, url)

    @staticmethod
    def _append(target: list[str], value: str) -> None:
        if value and not value.startswith("data:"):
            target.append(value)

    def ordered(self) -> list[str]:
        return unique([*self.meta_images, *self.link_images, *self.element_images])


class ProgressReporter:
    def __init__(self, mode: str = "text", stream: TextIO = sys.stderr) -> None:
        self.mode = mode
        self.stream = stream

    def emit(self, event: str, **payload: object) -> None:
        if self.mode == "none":
            return
        record = {"event": event, **payload}
        if self.mode == "jsonl":
            message = json.dumps(record, ensure_ascii=False)
        else:
            index = payload.get("index", "?")
            total = payload.get("total", "?")
            project = payload.get("project_url", "")
            detail = payload.get("detail") or payload.get("reason") or ""
            message = f"[visual {index}/{total}] {event}: {project}"
            if detail:
                message += f" ({detail})"
        print(message, file=self.stream, flush=True)


def unique(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        key = value.strip()
        if key and key not in seen:
            seen.add(key)
            result.append(key)
    return result


def parse_srcset(value: str) -> list[str]:
    urls: list[str] = []
    for item in value.split(","):
        candidate = item.strip().split()
        if candidate:
            urls.append(candidate[0])
    return urls


def host_allowed(host: str, roots: tuple[str, ...]) -> bool:
    normalized = host.casefold().rstrip(".")
    return any(normalized == root or normalized.endswith(f".{root}") for root in roots)


def extract_official_images(
    html: bytes, project_url: str, allowed_hosts: tuple[str, ...]
) -> tuple[list[str], int]:
    parser = OfficialImageParser()
    parser.feed(html.decode("utf-8", errors="replace"))
    extracted = [urljoin(project_url, value) for value in parser.ordered()]
    official = [
        value
        for value in extracted
        if urlsplit(value).scheme == "https"
        and host_allowed(urlsplit(value).hostname or "", allowed_hosts)
    ]
    return unique(official), len(unique(extracted))


def _reason_for_http(status: int, body: bytes = b"") -> str:
    lowered = body[:256].decode("utf-8", errors="ignore").casefold()
    if "cache miss" in lowered:
        return "asset_cache_miss"
    if status == 403:
        return "asset_403"
    if status == 404:
        return "asset_404"
    return "asset_http_error"


def fetch_url(
    url: str,
    *,
    timeout: float,
    max_bytes: int,
    accept: str,
    referer: str | None = None,
) -> FetchResult:
    headers = {"User-Agent": USER_AGENT, "Accept": accept}
    if referer:
        headers["Referer"] = referer
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=max(0.1, timeout)) as response:
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip()
            declared = response.headers.get("Content-Length")
            if declared and declared.isdigit() and int(declared) > max_bytes:
                return FetchResult(False, url, content_type=content_type, reason="asset_too_large")
            body = response.read(max_bytes + 1)
            if len(body) > max_bytes:
                return FetchResult(False, url, content_type=content_type, reason="asset_too_large")
            return FetchResult(
                True,
                response.geturl(),
                body=body,
                content_type=content_type,
                http_status=getattr(response, "status", 200),
            )
    except HTTPError as exc:
        try:
            body = exc.read(256)
        except Exception:
            body = b""
        return FetchResult(
            False,
            url,
            body=body,
            reason=_reason_for_http(exc.code, body),
            http_status=exc.code,
        )
    except (TimeoutError, URLError) as exc:
        detail = str(getattr(exc, "reason", exc)).casefold()
        reason = "asset_timeout" if "timed out" in detail or "timeout" in detail else "asset_network_error"
        return FetchResult(False, url, reason=reason)


def detect_image_format(body: bytes) -> str | None:
    if body.startswith(b"\xff\xd8\xff"):
        return "JPEG"
    if body.startswith(b"\x89PNG\r\n\x1a\n"):
        return "PNG"
    if body.startswith((b"GIF87a", b"GIF89a")):
        return "GIF"
    if len(body) >= 12 and body[:4] == b"RIFF" and body[8:12] == b"WEBP":
        return "WEBP"
    if len(body) >= 12 and body[4:8] == b"ftyp" and body[8:12] in {
        b"avif",
        b"avis",
        b"heic",
        b"heix",
    }:
        return body[8:12].decode("ascii").upper()
    return None


def validate_image_payload(body: bytes, content_type: str) -> tuple[bool, str, str]:
    if not body:
        return False, "", "image_decode_failed"
    image_format = detect_image_format(body)
    if not image_format and not content_type.casefold().startswith("image/"):
        return False, "", "asset_not_image"
    if Image is None:
        return (
            bool(image_format),
            image_format or "",
            "signature" if image_format else "image_decode_failed",
        )
    try:
        with Image.open(io.BytesIO(body)) as image:
            image.verify()
            return True, (image.format or image_format or "").upper(), "pillow"
    except (UnidentifiedImageError, OSError, ValueError):
        return False, image_format or "", "image_decode_failed"


def remaining_seconds(deadline: float, request_timeout: float) -> float:
    return max(0.0, min(request_timeout, deadline - time.monotonic()))


def verify_candidate(
    project_url: str,
    *,
    config: Config,
    candidate_deadline: float,
    index: int,
    total: int,
    reporter: ProgressReporter,
    fetcher: Callable[..., FetchResult] = fetch_url,
    review_handoff: ReviewHandoff | None = None,
) -> dict:
    started = time.monotonic()
    reporter.emit("candidate_start", index=index, total=total, project_url=project_url)
    validation = validate_project_url(project_url)
    if not validation.get("valid"):
        result = {
            "project_url": project_url,
            "status": "Rejected",
            "reason": "unsupported_project_url",
            "detail": validation.get("reason", "official URL validation failed"),
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }
        reporter.emit(
            "candidate_complete",
            index=index,
            total=total,
            project_url=project_url,
            reason=result["reason"],
        )
        return result

    source = str(validation["source"])
    page_timeout = remaining_seconds(candidate_deadline, config.request_timeout)
    if page_timeout <= 0:
        return _timeout_result(project_url, source, started, "candidate_timeout", index, total, reporter)

    reporter.emit("page_fetch", index=index, total=total, project_url=project_url)
    page = fetcher(
        project_url,
        timeout=page_timeout,
        max_bytes=config.max_html_bytes,
        accept="text/html,application/xhtml+xml",
        referer=None,
    )
    if not page.ok:
        if page.reason == "asset_timeout":
            reason = "page_timeout"
        elif page.reason == "asset_network_error":
            reason = "page_network_error"
        else:
            reason = "page_http_error"
        result = {
            "project_url": project_url,
            "source": source,
            "status": "Candidate - image inaccessible",
            "reason": reason,
            "page_accessible": False,
            "pixels_decoded": False,
            "attempts": [],
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }
        reporter.emit(
            "candidate_complete",
            index=index,
            total=total,
            project_url=project_url,
            reason=reason,
        )
        return result

    allowed_hosts = IMAGE_HOSTS[source]
    image_urls, extracted_count = extract_official_images(page.body, project_url, allowed_hosts)
    if not image_urls:
        reason = "unsupported_asset_host" if extracted_count else "no_official_image_found"
        result = {
            "project_url": project_url,
            "source": source,
            "status": "Candidate - image inaccessible",
            "reason": reason,
            "page_accessible": True,
            "pixels_decoded": False,
            "attempts": [],
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }
        reporter.emit(
            "candidate_complete",
            index=index,
            total=total,
            project_url=project_url,
            reason=reason,
        )
        return result

    attempts: list[dict] = []
    for image_index, image_url in enumerate(image_urls[: config.max_images], start=1):
        timeout = remaining_seconds(candidate_deadline, config.request_timeout)
        if timeout <= 0:
            break
        reporter.emit(
            "image_fetch",
            index=index,
            total=total,
            project_url=project_url,
            detail=f"asset {image_index}/{min(len(image_urls), config.max_images)}",
        )
        fetched = fetcher(
            image_url,
            timeout=timeout,
            max_bytes=config.max_image_bytes,
            accept="image/avif,image/webp,image/png,image/jpeg,image/gif,*/*;q=0.8",
            referer=project_url,
        )
        attempt = {
            "image_url": image_url,
            "accessible": False,
            "reason": fetched.reason,
            "http_status": fetched.http_status,
        }
        if fetched.ok:
            valid, image_format, method = validate_image_payload(fetched.body, fetched.content_type)
            if valid:
                attempt.update(
                    {
                        "accessible": True,
                        "reason": "",
                        "content_type": fetched.content_type,
                        "image_format": image_format,
                        "bytes_read": len(fetched.body),
                        "validation_method": method,
                    }
                )
                attempts.append(attempt)
                handoff: dict = {}
                handoff_error = ""
                if review_handoff is not None:
                    try:
                        handoff = review_handoff.write_asset(
                            body=fetched.body,
                            image_format=image_format,
                            project_url=project_url,
                            image_url=image_url,
                            index=index,
                        )
                    except (OSError, ValueError) as exc:
                        handoff_error = f"{type(exc).__name__}: {exc}"
                result = {
                    "project_url": project_url,
                    "source": source,
                    "status": "Official image accessible",
                    "verification_state": "Pending visual inspection",
                    "reason": "official_image_ready",
                    "page_accessible": True,
                    "official_image_url": image_url,
                    "pixels_decoded": method == "pillow",
                    "image_format": image_format,
                    "attempts": attempts,
                    "elapsed_seconds": round(time.monotonic() - started, 3),
                }
                if handoff:
                    result["visual_handoff"] = handoff
                    reporter.emit(
                        "review_handoff_ready",
                        index=index,
                        total=total,
                        project_url=project_url,
                        detail=handoff["review_path"],
                    )
                elif review_handoff is not None:
                    result["handoff_reason"] = "visual_handoff_failed"
                    result["handoff_detail"] = handoff_error
                reporter.emit(
                    "candidate_complete",
                    index=index,
                    total=total,
                    project_url=project_url,
                    detail="official image ready for visual inspection",
                )
                return result
            attempt["reason"] = method
        attempts.append(attempt)

    reason = "candidate_timeout" if time.monotonic() >= candidate_deadline else (
        attempts[-1]["reason"] if attempts else "no_official_image_found"
    )
    result = {
        "project_url": project_url,
        "source": source,
        "status": "Candidate - image inaccessible",
        "reason": reason,
        "page_accessible": True,
        "pixels_decoded": False,
        "attempts": attempts,
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }
    reporter.emit(
        "candidate_complete",
        index=index,
        total=total,
        project_url=project_url,
        reason=reason,
    )
    return result


def _timeout_result(
    project_url: str,
    source: str,
    started: float,
    reason: str,
    index: int,
    total: int,
    reporter: ProgressReporter,
) -> dict:
    result = {
        "project_url": project_url,
        "source": source,
        "status": "Candidate - image inaccessible",
        "reason": reason,
        "page_accessible": False,
        "pixels_decoded": False,
        "attempts": [],
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }
    reporter.emit(
        "candidate_complete",
        index=index,
        total=total,
        project_url=project_url,
        reason=reason,
    )
    return result


def verify_urls(
    urls: list[str],
    config: Config,
    reporter: ProgressReporter,
    review_handoff: ReviewHandoff | None = None,
) -> dict:
    started = time.monotonic()
    total_deadline = started + config.total_timeout
    results: list[dict] = []
    for index, project_url in enumerate(urls, start=1):
        if time.monotonic() >= total_deadline:
            for remaining_url in urls[index - 1 :]:
                results.append(
                    {
                        "project_url": remaining_url,
                        "status": "Candidate - image inaccessible",
                        "reason": "total_timeout",
                        "page_accessible": False,
                        "pixels_decoded": False,
                        "attempts": [],
                        "elapsed_seconds": 0.0,
                    }
                )
                reporter.emit(
                    "candidate_complete",
                    index=len(results),
                    total=len(urls),
                    project_url=remaining_url,
                    reason="total_timeout",
                )
            break
        candidate_deadline = min(total_deadline, time.monotonic() + config.candidate_timeout)
        results.append(
            verify_candidate(
                project_url,
                config=config,
                candidate_deadline=candidate_deadline,
                index=index,
                total=len(urls),
                reporter=reporter,
                review_handoff=review_handoff,
            )
        )

    accessible = sum(result["status"] == "Official image accessible" for result in results)
    return {
        "official_image_accessible_count": accessible,
        "image_inaccessible_count": sum(
            result["status"] == "Candidate - image inaccessible" for result in results
        ),
        "rejected_count": sum(result["status"] == "Rejected" for result in results),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "results": results,
    }


def positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Acquire official award-project images for direct visual review."
    )
    parser.add_argument("urls", nargs="+", help="Official award project URLs")
    parser.add_argument("--request-timeout", type=positive_float, default=5.0)
    parser.add_argument("--candidate-timeout", type=positive_float, default=12.0)
    parser.add_argument("--total-timeout", type=positive_float, default=60.0)
    parser.add_argument("--max-images", type=positive_int, default=3)
    parser.add_argument("--progress", choices=("text", "jsonl", "none"), default="text")
    parser.add_argument("--compact", action="store_true", help="Emit compact final JSON")
    parser.add_argument(
        "--review-dir",
        help=(
            "Create this new directory for short-lived image handoff to a visual tool. "
            "The caller must inspect and then remove it with cleanup_visual_review.py."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = Config(
        request_timeout=args.request_timeout,
        candidate_timeout=args.candidate_timeout,
        total_timeout=args.total_timeout,
        max_images=args.max_images,
    )
    review_handoff = None
    if args.review_dir:
        try:
            review_handoff = ReviewHandoff(args.review_dir)
        except (OSError, ValueError) as exc:
            print(
                json.dumps(
                    {
                        "status": "Rejected",
                        "reason": "visual_handoff_setup_failed",
                        "detail": f"{type(exc).__name__}: {exc}",
                    },
                    ensure_ascii=False,
                )
            )
            return 2
    payload = verify_urls(
        args.urls,
        config,
        ProgressReporter(args.progress),
        review_handoff=review_handoff,
    )
    if review_handoff is not None:
        payload["review_handoff"] = {
            "directory": str(review_handoff.directory),
            "marker": str(review_handoff.marker_path),
            "asset_count": len(review_handoff.assets),
            "cleanup_required": True,
        }
    print(json.dumps(payload, ensure_ascii=False, indent=None if args.compact else 2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
