import hashlib
import json
from pathlib import Path

import pytest

from stewardlens.fia_ingestion import (
    FIAIngestionError,
    ingest_manifest,
    parse_fia_decision_text,
    validate_official_fia_url,
)
from stewardlens.repository import JsonRepository


SAMPLE_DECISION = """
2024 ITALIAN GRAND PRIX
30 August - 01 September 2024
From The Stewards
Document 55
Date 01 September 2024
Time 16:27
No / Driver 27 - Nico Hulkenberg
Competitor MoneyGram Haas F1 Team
Time 15:09
Session Race
Fact Car 27 collided with Car 22 at the entry to Turn 1.
Infringement Breach of Appendix L, Chapter IV, Article 2 d) of the FIA International Sporting Code.
Decision 10 second time penalty.
2 penalty points (total of 4 for the 12 month period).
Reason The Stewards reviewed video and in-car video evidence.
Car 27 locked up and collided with Car 22.
Competitors are reminded that they have the right to appeal certain decisions.
"""


def test_parser_extracts_labelled_fia_decision_fields():
    decision = parse_fia_decision_text(SAMPLE_DECISION)

    assert decision["season"] == 2024
    assert decision["document_number"] == 55
    assert decision["driver_name"] == "Nico Hulkenberg"
    assert decision["fact"].startswith("Car 27 collided")
    assert decision["decision"] == "10 second time penalty."
    assert decision["penalty_points"] == 2


def test_only_official_fia_https_sources_are_allowed():
    validate_official_fia_url("https://api.fia.com/document.pdf")
    with pytest.raises(FIAIngestionError, match="official FIA"):
        validate_official_fia_url("https://example.com/document.pdf")
    with pytest.raises(FIAIngestionError, match="official FIA"):
        validate_official_fia_url("http://www.fia.com/document.pdf")


def test_ingestion_verifies_checksum_parses_and_writes_output(tmp_path):
    pdf_bytes = b"%PDF-educational-test-fixture"
    checksum = hashlib.sha256(pdf_bytes).hexdigest()
    manifest = {
        "schema_version": 1,
        "retrieved_at": "2026-10-25",
        "output": "decisions.json",
        "documents": [
            {
                "id": "verified-test",
                "published_at": "2024-09-01T16:28:00+02:00",
                "source_page_url": "https://www.fia.com/documents/test",
                "source_document_url": "https://api.fia.com/test.pdf",
                "local_pdf": "documents/test.pdf",
                "sha256": checksum,
                "expected": {"document_number": 55},
            }
        ],
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    def fake_download(url: str, destination: Path) -> None:
        destination.parent.mkdir(parents=True)
        destination.write_bytes(pdf_bytes)

    decisions = ingest_manifest(
        manifest_path,
        refresh=True,
        downloader=fake_download,
        extractor=lambda path: SAMPLE_DECISION,
    )

    assert decisions[0]["id"] == "verified-test"
    assert decisions[0]["sha256"] == checksum
    assert json.loads((tmp_path / "decisions.json").read_text()) == decisions


def test_ingestion_rejects_checksum_drift(tmp_path):
    (tmp_path / "document.pdf").write_bytes(b"%PDF-changed")
    manifest = {
        "schema_version": 1,
        "retrieved_at": "2026-10-25",
        "documents": [
            {
                "id": "changed",
                "published_at": "2024-09-01T16:28:00+02:00",
                "source_page_url": "https://www.fia.com/documents/test",
                "source_document_url": "https://api.fia.com/test.pdf",
                "local_pdf": "document.pdf",
                "sha256": "0" * 64,
            }
        ],
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(FIAIngestionError, match="Checksum mismatch"):
        ingest_manifest(manifest_path, extractor=lambda path: SAMPLE_DECISION)


def test_repository_exposes_real_corpus_separately_from_fictional_incidents():
    repository = JsonRepository()

    real_decisions = repository.list_real_decisions()

    assert {decision["document_number"] for decision in real_decisions} == {55, 57}
    assert all(decision["source_document_url"].startswith("https://api.fia.com/") for decision in real_decisions)
    assert all(len(decision["sha256"]) == 64 for decision in real_decisions)
    assert all(incident.id.startswith("sample-") for incident in repository.list_incidents())
