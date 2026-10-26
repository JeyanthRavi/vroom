# StewardLens sample data

Every person, team, event, incident, rule and decision in this directory is
**fictional educational sample data**. None is an FIA or Formula 1 fact, rule,
finding or historical decision. The `sample://` source references exist only to
make provenance explicit while developing the offline demonstration.

Real FIA regulations and decisions must be ingested, versioned and verified
before this project is used for historical research.

## Verified FIA corpus

`real/` is deliberately separate from the fictional fixtures above. Its
manifest contains the original official FIA event-page and PDF URLs,
publication metadata, retrieval date, byte size and SHA-256 for each raw PDF.
The corresponding `decisions.json` is generated from those checksum-pinned
PDFs and should not be edited manually.

Refresh and verify the corpus from the project root with:

```bash
PYTHONPATH=src python -m stewardlens.fia_ingestion --refresh
```

Running without `--refresh` verifies and reparses the checked-in PDFs without
network access. PDF text extraction requires `pypdf` in the local environment
(kept optional so the core offline demo has no additional dependency). The FIA
remains the source and rights holder of its documents; the local copies are
retained for educational provenance and reproducibility.


