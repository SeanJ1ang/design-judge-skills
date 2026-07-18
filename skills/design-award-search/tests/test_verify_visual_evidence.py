from __future__ import annotations

import io
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import verify_visual_evidence as visual  # noqa: E402
import cleanup_visual_review as cleanup_review  # noqa: E402


PNG_SIGNATURE_PAYLOAD = b"\x89PNG\r\n\x1a\n" + (b"0" * 32)


class VisualEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = visual.Config(
            request_timeout=1.0,
            candidate_timeout=5.0,
            total_timeout=10.0,
            max_images=3,
        )
        self.reporter = visual.ProgressReporter("none", io.StringIO())

    def test_extracts_meta_then_lazy_images_and_filters_hosts(self) -> None:
        html = b"""
        <html><head>
          <meta property="og:image" content="/hero.jpg">
        </head><body>
          <img data-src="https://www.red-dot.org/thumb.jpg">
          <img src="https://example.com/unofficial.jpg">
        </body></html>
        """
        urls, extracted_count = visual.extract_official_images(
            html,
            "https://www.red-dot.org/project/example-1",
            ("red-dot.org",),
        )
        self.assertEqual(
            urls,
            [
                "https://www.red-dot.org/hero.jpg",
                "https://www.red-dot.org/thumb.jpg",
            ],
        )
        self.assertEqual(extracted_count, 3)

    def test_accessible_image_remains_pending_visual_inspection(self) -> None:
        project = "https://www.red-dot.org/project/example-1"
        image_url = "https://www.red-dot.org/fileadmin/example.jpg"

        def fake_fetch(url: str, **_: object) -> visual.FetchResult:
            if url == project:
                return visual.FetchResult(
                    True,
                    url,
                    body=f'<meta property="og:image" content="{image_url}">'.encode(),
                    content_type="text/html",
                )
            return visual.FetchResult(
                True,
                url,
                body=PNG_SIGNATURE_PAYLOAD,
                content_type="image/png",
                http_status=200,
            )

        with patch.object(visual, "Image", None):
            result = visual.verify_candidate(
                project,
                config=self.config,
                candidate_deadline=time.monotonic() + 5,
                index=1,
                total=1,
                reporter=self.reporter,
                fetcher=fake_fetch,
            )

        self.assertEqual(result["status"], "Official image accessible")
        self.assertEqual(result["verification_state"], "Pending visual inspection")
        self.assertEqual(result["reason"], "official_image_ready")
        self.assertFalse(result["pixels_decoded"])
        self.assertEqual(result["official_image_url"], image_url)

    def test_asset_failure_returns_reason_code(self) -> None:
        project = "https://www.red-dot.org/project/example-1"
        image_url = "https://www.red-dot.org/fileadmin/example.jpg"

        def fake_fetch(url: str, **_: object) -> visual.FetchResult:
            if url == project:
                return visual.FetchResult(
                    True,
                    url,
                    body=f'<meta property="og:image" content="{image_url}">'.encode(),
                    content_type="text/html",
                )
            return visual.FetchResult(
                False,
                url,
                reason="asset_403",
                http_status=403,
            )

        result = visual.verify_candidate(
            project,
            config=self.config,
            candidate_deadline=time.monotonic() + 5,
            index=1,
            total=1,
            reporter=self.reporter,
            fetcher=fake_fetch,
        )
        self.assertEqual(result["status"], "Candidate - image inaccessible")
        self.assertEqual(result["reason"], "asset_403")
        self.assertTrue(result["page_accessible"])

    def test_external_only_image_is_not_accepted(self) -> None:
        project = "https://ifdesign.com/en/winner-ranking/project/example/1"

        def fake_fetch(url: str, **_: object) -> visual.FetchResult:
            self.assertEqual(url, project)
            return visual.FetchResult(
                True,
                url,
                body=b'<meta property="og:image" content="https://example.com/image.jpg">',
                content_type="text/html",
            )

        result = visual.verify_candidate(
            project,
            config=self.config,
            candidate_deadline=time.monotonic() + 5,
            index=1,
            total=1,
            reporter=self.reporter,
            fetcher=fake_fetch,
        )
        self.assertEqual(result["status"], "Candidate - image inaccessible")
        self.assertEqual(result["reason"], "unsupported_asset_host")

    def test_progress_jsonl_is_immediate_and_structured(self) -> None:
        stream = io.StringIO()
        reporter = visual.ProgressReporter("jsonl", stream)
        reporter.emit(
            "candidate_start",
            index=1,
            total=2,
            project_url="https://www.red-dot.org/project/example-1",
        )
        value = stream.getvalue()
        self.assertIn('"event": "candidate_start"', value)
        self.assertTrue(value.endswith("\n"))

    def test_review_handoff_writes_ephemeral_asset_and_stays_pending(self) -> None:
        project = "https://www.red-dot.org/project/example-1"
        image_url = "https://www.red-dot.org/fileadmin/example.jpg"

        def fake_fetch(url: str, **_: object) -> visual.FetchResult:
            if url == project:
                return visual.FetchResult(
                    True,
                    url,
                    body=f'<meta property="og:image" content="{image_url}">'.encode(),
                    content_type="text/html",
                )
            return visual.FetchResult(
                True,
                url,
                body=PNG_SIGNATURE_PAYLOAD,
                content_type="image/png",
                http_status=200,
            )

        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as parent:
            review_dir = Path(parent) / "review"
            handoff = visual.ReviewHandoff(review_dir)
            with patch.object(visual, "Image", None):
                result = visual.verify_candidate(
                    project,
                    config=self.config,
                    candidate_deadline=time.monotonic() + 5,
                    index=1,
                    total=1,
                    reporter=self.reporter,
                    fetcher=fake_fetch,
                    review_handoff=handoff,
                )

            self.assertEqual(result["verification_state"], "Pending visual inspection")
            review_path = Path(result["visual_handoff"]["review_path"])
            self.assertTrue(review_path.is_file())
            self.assertEqual(review_path.read_bytes(), PNG_SIGNATURE_PAYLOAD)
            cleaned = cleanup_review.cleanup(review_dir)
            self.assertEqual(cleaned["status"], "cleaned")
            self.assertFalse(review_dir.exists())

    def test_cleanup_refuses_unmarked_directory(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            with self.assertRaises(ValueError):
                cleanup_review.cleanup(directory)

    def test_cleanup_refuses_unrelated_files_without_deleting_review_asset(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as parent:
            review_dir = Path(parent) / "review"
            handoff = visual.ReviewHandoff(review_dir)
            record = handoff.write_asset(
                body=PNG_SIGNATURE_PAYLOAD,
                image_format="PNG",
                project_url="https://www.red-dot.org/project/example-1",
                image_url="https://www.red-dot.org/fileadmin/example.png",
                index=1,
            )
            review_path = Path(record["review_path"])
            unrelated = review_dir / "keep.txt"
            unrelated.write_text("keep", encoding="utf-8")

            with self.assertRaises(ValueError):
                cleanup_review.cleanup(review_dir)

            self.assertTrue(review_path.is_file())
            self.assertTrue(unrelated.is_file())
            self.assertTrue(handoff.marker_path.is_file())


if __name__ == "__main__":
    unittest.main()
