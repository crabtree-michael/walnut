"""Parser component: transforms HTML downloads into structured JSON via an on-device LLM."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from itertools import chain
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Set

import requests
from bs4 import BeautifulSoup

LOGGER = logging.getLogger(__name__)

DEFAULT_HTML_DIR = Path(__file__).resolve().parent / "data" / "html"
DEFAULT_JSON_DIR = Path(__file__).resolve().parent / "data" / "json"
DEFAULT_LLM_HOST = "127.0.0.1"
DEFAULT_LLM_PORT = 11434
DEFAULT_MODEL = "gpt-oss:20b"


@dataclass(frozen=True)
class ParseResult:
    """Represents the outcome for a single HTML document."""

    html_path: Path
    json_path: Optional[Path]
    error: Optional[str] = None

    @property
    def succeeded(self) -> bool:
        return self.error is None and self.json_path is not None


PROMPT_TEMPLATE = """You are assisting the Elk project, which centralises park safety information.
Elk exposes Hazards, Tips, and Locations as defined below. Produce data that can be inserted
into the Elk API without inventing unsupported structure.

Model definitions:
- Hazard: name (string), severity (low|medium|high), type (animal|event|weather|disease), presentations (optional array of presentation objects). Each presentation represents how the hazard manifests at a particular location and may contain: location (string name), description (string), boundary (collection of GPS coordinates if explicitly specified). Include the presentations array whenever the hazard occurs at one or more mentioned locations.
- Tip: name (string) and description (HTML allowed). Tips should be associated with hazards when appropriate.
- Location: name (string), type (National Park|Region), optional coordinates (latitude and longitude), optional description (string), optional image (string URL).

Objective:
Extract Hazards, Tips, and Locations that are explicitly grounded in the provided document.
Only report information present in the text. Omit coordinates when the document does not
state them. If a field is not present in the document, leave it out.

Output instructions:
- Return a JSON object with exactly the keys "hazards", "tips", and "locations".
- Use arrays for each key, even when empty.
- Ensure the JSON is valid and does not include code fences or commentary.

<document>
{document}
</document>
"""


def configure_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s %(message)s")


def list_html_documents(input_dir: Optional[Path], explicit_files: Sequence[Path]) -> List[Path]:
    candidates: Iterable[Path] = []
    if input_dir:
        candidates = chain(candidates, sorted(input_dir.rglob("*.html")))
    if explicit_files:
        candidates = chain(candidates, explicit_files)
    seen: Set[Path] = set()
    documents: List[Path] = []
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        if not resolved.exists():
            LOGGER.warning("Skipping missing HTML document: %s", resolved)
            continue
        if resolved.is_dir():
            LOGGER.warning("Skipping directory input: %s", resolved)
            continue
        seen.add(resolved)
        documents.append(resolved)
    return documents


def strip_html_to_text(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")
    for element in soup(["script", "style", "noscript", "code", "pre"]):
        element.decompose()
    text = soup.get_text(separator="\n")
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def build_prompt(document_text: str) -> str:
    return PROMPT_TEMPLATE.format(document=document_text)


def call_llm(prompt: str, *, host: str, port: int, model: str, timeout: float = 60.0) -> str:
    url = f"http://{host}:{port}/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": False}
    try:
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"LLM request failed: {exc}") from exc

    try:
        data = response.json()
    except ValueError as exc:
        print(response)
        raise RuntimeError("LLM response was not valid JSON") from exc

    if "response" not in data:
        raise RuntimeError("LLM response missing 'response' field")

    return data["response"].strip()


def parse_llm_json(content: str) -> dict:
    stripped = content.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`").strip()
        if stripped.lower().startswith("json"):
            stripped = stripped[4:].strip()
    return json.loads(stripped)


def derive_output_path(html_path: Path, *, html_root: Optional[Path], output_dir: Path) -> Path:
    if html_root and html_path.is_relative_to(html_root):
        relative = html_path.relative_to(html_root).with_suffix(".json")
        return output_dir / relative
    return output_dir / html_path.with_suffix(".json").name


def parse_document(
    html_path: Path,
    *,
    html_root: Optional[Path],
    output_dir: Path,
    host: str,
    port: int,
    model: str,
    timeout: float,
    log_prompt: bool,
) -> ParseResult:
    try:
        html_content = html_path.read_text(encoding="utf-8")
    except OSError as exc:
        error = f"Unable to read {html_path}: {exc}"
        LOGGER.error(error)
        return ParseResult(html_path=html_path, json_path=None, error=error)

    document_text = strip_html_to_text(html_content)
    prompt = build_prompt(document_text)

    if log_prompt:
        LOGGER.info("Prompt for %s:\n%s", html_path, prompt)

    try:
        llm_output = call_llm(prompt, host=host, port=port, model=model, timeout=timeout)
    except RuntimeError as exc:
        error = str(exc)
        LOGGER.error("LLM invocation failed for %s: %s", html_path, error)
        return ParseResult(html_path=html_path, json_path=None, error=error)

    try:
        parsed = parse_llm_json(llm_output)
    except json.JSONDecodeError as exc:
        error = f"Invalid JSON from LLM for {html_path}: {exc}"
        LOGGER.error(error)
        return ParseResult(html_path=html_path, json_path=None, error=error)

    output_path = derive_output_path(html_path, html_root=html_root, output_dir=output_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(parsed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    LOGGER.info("Generated %s", output_path)
    return ParseResult(html_path=html_path, json_path=output_path, error=None)


def run_parser(
    html_documents: Sequence[Path],
    *,
    html_root: Optional[Path],
    output_dir: Path,
    host: str,
    port: int,
    model: str,
    timeout: float,
    log_first_prompt: bool,
) -> List[ParseResult]:
    results: List[ParseResult] = []
    for index, html_path in enumerate(html_documents):
        log_prompt = log_first_prompt and index == 0
        results.append(
            parse_document(
                html_path,
                html_root=html_root,
                output_dir=output_dir,
                host=host,
                port=port,
                model=model,
                timeout=timeout,
                log_prompt=log_prompt,
            )
        )
    return results


def main(argv: Optional[Iterable[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Parse downloaded HTML into Elk JSON structures")
    parser.add_argument("html", nargs="*", type=Path, help="Explicit HTML files to parse")
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_HTML_DIR, help="Directory containing HTML files")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_JSON_DIR, help="Directory to write JSON output")
    parser.add_argument("--host", default=DEFAULT_LLM_HOST, help="LLM host")
    parser.add_argument("--port", type=int, default=DEFAULT_LLM_PORT, help="LLM port")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="LLM model identifier")
    parser.add_argument("--timeout", type=float, default=90.0, help="LLM request timeout in seconds")
    parser.add_argument("--log-first-prompt", action="store_true", help="Log the full prompt for the first document")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args(list(argv) if argv is not None else None)

    configure_logging(args.verbose)

    html_root = args.input_dir.resolve() if args.input_dir else None
    documents = list_html_documents(args.input_dir, [path.resolve() for path in args.html])
    if not documents:
        LOGGER.warning("No HTML documents found to parse")
        return 0

    results = run_parser(
        documents,
        html_root=html_root,
        output_dir=args.output_dir.resolve(),
        host=args.host,
        port=args.port,
        model=args.model,
        timeout=args.timeout,
        log_first_prompt=args.log_first_prompt,
    )

    failures = [result for result in results if result.error]
    if failures:
        LOGGER.warning("%d documents failed to parse", len(failures))
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
