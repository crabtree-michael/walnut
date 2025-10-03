"""Downloader component for fetching HTML documents.

The downloader satisfies the requirements defined in ``scraper.llm.yaml`` by:
- skipping downloads for URLs that have already been archived on disk (re-runnable)
- collecting errors without interrupting the overall process (graceful error handling)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

import requests

LOGGER = logging.getLogger(__name__)

DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "output" / "html"


@dataclass(frozen=True)
class DownloadResult:
    """Represents the outcome of downloading a single URL."""

    url: str
    path: Optional[Path]
    skipped: bool
    error: Optional[str] = None

    @property
    def succeeded(self) -> bool:
        return self.error is None and not self.skipped


def sanitize_component(component: str) -> str:
    """Return a filesystem-safe representation of a URL component."""

    clean = re.sub(r"[^A-Za-z0-9._-]+", "-", component.strip())
    clean = re.sub(r"-+", "-", clean).strip("-")
    return clean or "resource"


_SCHEME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")


def build_document_path(url: str, output_dir: Path) -> Path:
    """Map a URL to ``output/html/<sanitized_url_name>.html``."""

    normalized = _SCHEME_PATTERN.sub("", url).replace("/", "-")
    candidate = sanitize_component(normalized)
    if not candidate:
        candidate = "document"
    if not candidate.endswith(".html"):
        candidate = f"{candidate}.html"
    return output_dir / candidate


def ensure_directory(path: Path) -> None:
    """Create the parent directory for ``path`` if it does not already exist."""

    path.parent.mkdir(parents=True, exist_ok=True)


def download_url(url: str, output_dir: Path = DEFAULT_OUTPUT_DIR, *, session: Optional[requests.Session] = None, timeout: float = 20.0) -> DownloadResult:
    """Download a single URL, adhering to the re-runnable requirement."""

    target_path = build_document_path(url, output_dir)
    if target_path.exists():
        LOGGER.info("Skipping %s (already downloaded at %s)", url, target_path)
        return DownloadResult(url=url, path=target_path, skipped=True)

    ensure_directory(target_path)
    sess = session or requests.Session()
    try:
        response = sess.get(url, timeout=timeout)
        response.raise_for_status()
        target_path.write_text(response.text, encoding=response.encoding or "utf-8")
        LOGGER.info("Downloaded %s -> %s", url, target_path)
        return DownloadResult(url=url, path=target_path, skipped=False)
    except requests.RequestException as exc:  # network or HTTP error
        LOGGER.error("Failed to download %s: %s", url, exc)
        if target_path.exists():
            target_path.unlink(missing_ok=True)
        return DownloadResult(url=url, path=None, skipped=False, error=str(exc))
    finally:
        if session is None:
            sess.close()


def download_many(urls: Iterable[str], output_dir: Path = DEFAULT_OUTPUT_DIR, *, timeout: float = 20.0) -> List[DownloadResult]:
    """Download multiple URLs while collecting the results."""

    sess = requests.Session()
    try:
        return [download_url(url, output_dir, session=sess, timeout=timeout) for url in urls]
    finally:
        sess.close()


def read_urls(source: Path) -> List[str]:
    """Load newline-delimited URLs from ``source``."""

    return [line.strip() for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]


def configure_logging(verbose: bool = False) -> None:
    """Configure basic logging for CLI usage."""

    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s %(message)s")


def main(argv: Optional[Iterable[str]] = None) -> int:
    """Simple CLI for the downloader component."""

    import argparse

    parser = argparse.ArgumentParser(description="Download HTML pages for the Elk scraper")
    parser.add_argument("urls", nargs="*", help="URLs to download. Mutually exclusive with --urls-file.")
    parser.add_argument("--urls-file", type=Path, help="Path to a newline-delimited list of URLs")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Destination directory for HTML documents")
    parser.add_argument("--timeout", type=float, default=20.0, help="HTTP timeout in seconds")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args(list(argv) if argv is not None else None)

    configure_logging(args.verbose)

    urls: List[str] = []
    if args.urls_file:
        urls.extend(read_urls(args.urls_file))
    urls.extend(args.urls)

    if not urls:
        parser.error("No URLs provided. Supply positional URLs or --urls-file.")

    results = download_many(urls, args.output_dir, timeout=args.timeout)

    failures = [result for result in results if result.error]
    if failures:
        LOGGER.warning("%d URLs failed to download", len(failures))
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
