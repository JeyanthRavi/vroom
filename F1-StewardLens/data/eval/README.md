# StewardLens evaluation cases

This mixed evaluation fixture uses only the checksum-verified metadata already
stored in `data/real/decisions.json` and clearly labelled synthetic cases. No
PDF was scraped or copied to create it.

For the real cases, `incident_description` is a fresh paraphrase of the local
metadata and `source_reference.hash` is the existing PDF checksum from the
verified manifest. For synthetic cases, the source uses the `sample://` scheme
and both hashes are the SHA-256 of the exact incident description. The file
contains no quotation copied from a decision document.

The corpus is deliberately small. Classifier output is a feasibility check,
not evidence that the system can reproduce steward decisions. Run
`python -m stewardlens.evaluation --cases data/eval/cases.jsonl --output <new-dir>`
to generate the literal sample counts, retrieval metrics, class metrics, and
confusion matrix.
