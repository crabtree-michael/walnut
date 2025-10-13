"""Entrypoint for running scraper components via ``python -m scraper``."""

from __future__ import annotations

import sys

from . import downloader, parser as parser_module, transformer as transformer_module


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("Usage: python -m scraper <download|parse> [component arguments...]", file=sys.stderr)
        return 1

    command, *rest = args
    if command == "download":
        return downloader.main(rest)
    if command == "parse":
        return parser_module.main(rest)
    if command == "transform":
        return transformer_module.main(rest)

    print(f"Unknown command: {command}", file=sys.stderr)
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
