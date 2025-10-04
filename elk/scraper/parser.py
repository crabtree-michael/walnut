"""Parser component: transforms HTML downloads into structured JSON via an on-device LLM."""

from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dataclasses import dataclass
from itertools import chain
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Set

from bs4 import BeautifulSoup
from ollama import Client

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


@dataclass(frozen=True)
class LLMOutput:
    """Captures the LLM content and any optional reasoning."""

    content: str
    thinking: Optional[str] = None


PROMPT_TEMPLATE = """
<document>
{document}
</document>


You are assisting the Elk project, which centralises park safety information.

Required output:
- Return a JSON object with exactly the keys "hazards", "tips", and "locations".
- Use arrays for each key. Emit an empty array when no entries exist.
- Reply with raw JSON only. Do not include code fences or commentary.

Model definitions:
- Hazard: name (string), severity (low|medium|high), type (animal|event|weather|disease), presentations (array when present). Each presentation describes how the hazard manifests at a specific location and may include: location (string), description (string), boundary (explicit GPS coordinate collection when the document states it).
- Tip: name (string) and description (HTML allowed). Tips may reference applicable hazards.
- Location: name (string), type (National Park|Region), optional coordinates (latitude and longitude), optional description (string), optional image (URL).

Objective:
- Extract Hazards, Tips, and Locations grounded in the document content.
- Omit coordinates unless the document explicitly states them.
- Include the presentations array on hazards whenever they relate to one or more mentioned locations.

Return the JSON definition for this document now.
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


def call_llm(prompt: str, *, client: Client, model: str, timeout: float) -> LLMOutput:
    def _generate() -> dict:
        return client.generate(model=model, prompt=prompt, stream=False)

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_generate)
        try:
            data = future.result(timeout=timeout)
        except FuturesTimeoutError as exc:
            future.cancel()
            raise RuntimeError(f"LLM request exceeded timeout of {timeout} seconds") from exc
        except Exception as exc:  # pragma: no cover - network errors depend on runtime
            raise RuntimeError(f"LLM request failed: {exc}") from exc

    if not isinstance(data, dict) or "response" not in data:
        raise RuntimeError("LLM response missing 'response' field")

    content = str(data.get("response", "")).strip()
    if not content:
        raise RuntimeError("LLM response was empty")

    thinking_raw = data.get("thinking")
    thinking = thinking_raw.strip() if isinstance(thinking_raw, str) and thinking_raw.strip() else None

    return LLMOutput(content=content, thinking=thinking)


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
    client: Client,
    model: str,
    timeout: float,
    log_prompt: bool,
    show_thinking: bool,
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
        llm_output = call_llm(prompt, client=client, model=model, timeout=timeout)
    except RuntimeError as exc:
        error = str(exc)
        LOGGER.error("LLM invocation failed for %s: %s", html_path, error)
        return ParseResult(html_path=html_path, json_path=None, error=error)

    if show_thinking and llm_output.thinking:
        LOGGER.info("Model thinking for %s:\n%s", html_path, llm_output.thinking)

    try:
        parsed = parse_llm_json(llm_output.content)
    except json.JSONDecodeError:
        error = f"Invalid JSON from LLM for {html_path}: {llm_output.content}"
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
    client: Client,
    model: str,
    timeout: float,
    log_first_prompt: bool,
    show_thinking: bool,
) -> List[ParseResult]:
    results: List[ParseResult] = []
    for index, html_path in enumerate(html_documents):
        log_prompt = log_first_prompt and index == 0
        results.append(
            parse_document(
                html_path,
                html_root=html_root,
                output_dir=output_dir,
                client=client,
                model=model,
                timeout=timeout,
                log_prompt=log_prompt,
                show_thinking=show_thinking,
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
    parser.add_argument("--thinking", action="store_true", help="Output model thinking when provided")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args(list(argv) if argv is not None else None)

    configure_logging(args.verbose)

    client_kwargs = {"host": f"http://{args.host}:{args.port}"}
    try:
        client = Client(timeout=args.timeout, **client_kwargs)
    except TypeError:
        client = Client(**client_kwargs)

    html_root = args.input_dir.resolve() if args.input_dir else None
    documents = list_html_documents(args.input_dir, [path.resolve() for path in args.html])
    if not documents:
        LOGGER.warning("No HTML documents found to parse")
        return 0

    results = run_parser(
        documents,
        html_root=html_root,
        output_dir=args.output_dir.resolve(),
        client=client,
        model=args.model,
        timeout=args.timeout,
        log_first_prompt=args.log_first_prompt,
        show_thinking=args.thinking,
    )

    failures = [result for result in results if result.error]
    if failures:
        LOGGER.warning("%d documents failed to parse", len(failures))
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
