"""Reproducible ingestion of official FIA steward-decision PDFs.

Only ``https`` URLs hosted by FIA are accepted.  The checked-in manifest pins
each source artifact by SHA-256 so a changed or corrupted document is rejected
instead of being silently accepted as the same decision.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class FIAIngestionError(RuntimeError):
    """Raised when an FIA source cannot be safely imported or parsed."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_official_fia_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in {"fia.com", "www.fia.com", "api.fia.com"}:
        raise FIAIngestionError(f"Source is not an approved official FIA HTTPS URL: {url}")


def download_official_pdf(url: str, destination: Path) -> None:
    """Download an FIA PDF to ``destination`` using an atomic replacement."""

    validate_official_fia_url(url)
    request = Request(url, headers={"User-Agent": "StewardLens/0.1 educational-research"})
    try:
        with urlopen(request, timeout=45) as response:  # nosec: URL host is allow-listed above
            content_type = response.headers.get_content_type()
            payload = response.read()
    except OSError as exc:
        raise FIAIngestionError(f"Unable to download FIA document: {url}") from exc
    if content_type != "application/pdf" or not payload.startswith(b"%PDF-"):
        raise FIAIngestionError(f"FIA source did not return a PDF: {url}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_bytes(payload)
    temporary.replace(destination)


def extract_pdf_text(path: Path) -> str:
    """Extract PDF text using the optional ``pypdf`` runtime dependency."""

    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - depends on local environment
        raise FIAIngestionError(
            "PDF parsing requires pypdf; install it before refreshing FIA data"
        ) from exc
    try:
        return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
    except Exception as exc:  # pragma: no cover - pypdf exposes several parse errors
        raise FIAIngestionError(f"Unable to extract text from {path}") from exc


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).replace("\u00a0", " ")
    return "\n".join(" ".join(line.split()) for line in text.splitlines() if line.strip())


def _field(text: str, label: str, following_labels: str) -> str:
    match = re.search(
        rf"(?:^|\n){re.escape(label)}\s+(.+?)(?=\n(?:{following_labels})\s+|\Z)",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if not match:
        raise FIAIngestionError(f"Required FIA decision field was not found: {label}")
    return " ".join(match.group(1).split())


def parse_fia_decision_text(text: str) -> Dict[str, Any]:
    """Parse the stable labelled fields in an FIA Formula 1 steward decision."""

    normalized = _normalize(text)
    event_match = re.match(r"(?P<season>20\d{2})\s+(?P<event>.+?GRAND PRIX)\n", normalized)
    driver_match = re.search(
        r"(?:^|\n)No\s*/\s*Driver\s+(?P<number>\d+)\s*-\s*(?P<name>[^\n]+)", normalized
    )
    document_match = re.search(r"(?:^|\n)Document\s+(?P<number>\d+)", normalized)
    date_match = re.search(r"(?:^|\n)Date\s+([^\n]+)", normalized)
    time_matches = re.findall(r"(?:^|\n)Time\s+([^\n]+)", normalized)
    if not all((event_match, driver_match, document_match, date_match)) or len(time_matches) < 2:
        raise FIAIngestionError("Document header is incomplete or is not a supported FIA decision")

    fact = _field(normalized, "Fact", "Infringement")
    infringement = _field(normalized, "Infringement", "Decision")
    decision = _field(normalized, "Decision", r"\d+ penalty points|Reason")
    reason = _field(normalized, "Reason", "Competitors are reminded")
    penalty_match = re.search(r"(?:^|\n)(\d+) penalty points", normalized, re.IGNORECASE)

    return {
        "season": int(event_match.group("season")),
        "event": event_match.group("event").title(),
        "document_number": int(document_match.group("number")),
        "document_date": date_match.group(1),
        "document_time": time_matches[0],
        "incident_time": time_matches[1],
        "session": _field(normalized, "Session", "Fact"),
        "driver_number": int(driver_match.group("number")),
        "driver_name": driver_match.group("name"),
        "competitor": _field(normalized, "Competitor", "Time"),
        "fact": fact,
        "infringement": infringement,
        "decision": decision,
        "penalty_points": int(penalty_match.group(1)) if penalty_match else 0,
        "reason": reason,
    }


def load_manifest(path: Path) -> Dict[str, Any]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FIAIngestionError(f"Unable to read FIA manifest: {path}") from exc
    if manifest.get("schema_version") != 1 or not isinstance(manifest.get("documents"), list):
        raise FIAIngestionError("Unsupported FIA manifest schema")
    return manifest


def ingest_manifest(
    manifest_path: Path,
    *,
    refresh: bool = False,
    downloader: Callable[[str, Path], None] = download_official_pdf,
    extractor: Callable[[Path], str] = extract_pdf_text,
) -> List[Dict[str, Any]]:
    """Verify, parse and materialize all documents declared in a manifest."""

    manifest_path = manifest_path.resolve()
    manifest = load_manifest(manifest_path)
    corpus_root = manifest_path.parent
    results: List[Dict[str, Any]] = []
    for entry in manifest["documents"]:
        source_url = entry["source_document_url"]
        validate_official_fia_url(source_url)
        pdf_path = corpus_root / entry["local_pdf"]
        if refresh or not pdf_path.exists():
            downloader(source_url, pdf_path)
        actual_checksum = sha256_file(pdf_path)
        if actual_checksum != entry["sha256"]:
            raise FIAIngestionError(
                f"Checksum mismatch for {entry['id']}: expected {entry['sha256']}, "
                f"received {actual_checksum}"
            )
        parsed = parse_fia_decision_text(extractor(pdf_path))
        expected = entry.get("expected", {})
        for field, value in expected.items():
            if parsed.get(field) != value:
                raise FIAIngestionError(
                    f"Parsed {field} mismatch for {entry['id']}: "
                    f"expected {value!r}, received {parsed.get(field)!r}"
                )
        results.append(
            {
                "id": entry["id"],
                **parsed,
                "published_at": entry["published_at"],
                "source_page_url": entry["source_page_url"],
                "source_document_url": source_url,
                "local_pdf": entry["local_pdf"],
                "sha256": actual_checksum,
                "retrieved_at": manifest["retrieved_at"],
            }
        )

    output_path = corpus_root / manifest.get("output", "decisions.json")
    serialized = json.dumps(results, indent=2, ensure_ascii=False) + "\n"
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary.write_text(serialized, encoding="utf-8")
    temporary.replace(output_path)
    return results


def default_manifest_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "real" / "manifest.json"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Verify and import official FIA decisions")
    parser.add_argument("--manifest", type=Path, default=default_manifest_path())
    parser.add_argument("--refresh", action="store_true", help="redownload official PDFs")
    arguments = parser.parse_args(argv)
    imported = ingest_manifest(arguments.manifest, refresh=arguments.refresh)
    print(f"Imported {len(imported)} verified FIA decisions")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

