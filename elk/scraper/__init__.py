"""Scraper package implementing downloader and parser components."""

from importlib.metadata import PackageNotFoundError, version

__all__ = ["get_version"]


def get_version() -> str:
    """Return the package version if installed, else ``"0.0.0"``."""
    try:
        return version("scraper")
    except PackageNotFoundError:
        return "0.0.0"
