"""Compatibility shim for the transform command defined in scraper.llm.yaml."""

from __future__ import annotations

from .transformer import main


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
