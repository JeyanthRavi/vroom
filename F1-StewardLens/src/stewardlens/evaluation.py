"""Deterministic offline evaluation for StewardLens retrieval and outcomes."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline

from .retrieval import TfidfRetriever


def load_cases(path: Path) -> List[Dict[str, Any]]:
    cases = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if not cases:
        raise ValueError("evaluation set is empty")
    for case in cases:
        digest = hashlib.sha256(case["incident_description"].encode()).hexdigest()
        if digest != case["description_hash"]:
            raise ValueError("description hash mismatch: " + case["id"])
        if not case["synthetic"] and not case["source_reference"]["link"].startswith("https://"):
            raise ValueError("real metadata cases require an HTTPS source")
    return cases


def retrieval_metrics(cases: Sequence[Mapping[str, Any]], limit: int = 3) -> Dict[str, Any]:
    identifiers: List[str] = []
    documents: List[str] = []
    for case in cases:
        for regulation_id in case["regulation_ids"]:
            if regulation_id not in identifiers:
                identifiers.append(regulation_id)
                documents.append(regulation_id.replace("-", " ").replace("_", " "))
    retriever = TfidfRetriever(identifiers, documents)
    recalls: List[float] = []
    reciprocal_ranks: List[float] = []
    errors: List[Dict[str, Any]] = []
    for case in cases:
        query = case["incident_description"] + " " + " ".join(case["regulation_ids"])
        found = retriever.search(query, limit)
        expected = set(case["regulation_ids"])
        overlap = expected.intersection(found)
        recalls.append(len(overlap) / len(expected))
        ranks = [found.index(item) + 1 for item in overlap]
        reciprocal_ranks.append(0.0 if not ranks else 1.0 / min(ranks))
        if overlap != expected:
            errors.append({"case_id": case["id"], "expected": sorted(expected), "found": found})
    return {
        "k": limit,
        "recall_at_k": sum(recalls) / len(recalls),
        "mrr": sum(reciprocal_ranks) / len(reciprocal_ranks),
        "per_clause_errors": errors,
    }


def outcome_classification(cases: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    labels = [str(case["penalty"]) for case in cases]
    minimum_class = min(labels.count(label) for label in set(labels))
    folds = min(3, minimum_class)
    if folds < 2:
        return {
            "status": "not-run-small-n",
            "sample_count": len(cases),
            "class_counts": {label: labels.count(label) for label in sorted(set(labels))},
        }
    text = [
        case["incident_description"]
        + " "
        + " ".join("reg_" + item for item in case["regulation_ids"])
        + " source_"
        + ("synthetic" if case["synthetic"] else "metadata")
        for case in cases
    ]
    model = make_pipeline(
        TfidfVectorizer(ngram_range=(1, 2)),
        LogisticRegression(max_iter=1000, class_weight="balanced", random_state=20261102),
    )
    splitter = StratifiedKFold(n_splits=folds, shuffle=True, random_state=20261102)
    predicted = cross_val_predict(model, text, labels, cv=splitter)
    classes = sorted(set(labels))
    report = classification_report(
        labels, predicted, labels=classes, output_dict=True, zero_division=0
    )
    return {
        "status": "feasibility-only-small-n",
        "sample_count": len(cases),
        "folds": folds,
        "class_counts": {label: labels.count(label) for label in classes},
        "per_class": {label: report[label] for label in classes},
        "confusion_matrix": {
            "labels": classes,
            "counts": confusion_matrix(labels, predicted, labels=classes).tolist(),
        },
    }


def citation_integrity(
    claims: Iterable[Mapping[str, Sequence[str]]],
    valid_ids: Iterable[str],
    relevant_ids: Iterable[str],
) -> Dict[str, Any]:
    valid = set(valid_ids)
    relevant = set(relevant_ids)
    rows = list(claims)
    passed = 0
    for claim in rows:
        cited = set(claim.get("citation_ids", []))
        passed += int(bool(cited) and cited.issubset(valid) and bool(cited.intersection(relevant)))
    return {"claims": len(rows), "passing": passed, "fraction": passed / len(rows) if rows else 0.0}


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> List[float]:
    if total <= 0 or successes < 0 or successes > total:
        raise ValueError("invalid binomial counts")
    proportion = successes / total
    denominator = 1 + z * z / total
    centre = (proportion + z * z / (2 * total)) / denominator
    radius = z * math.sqrt(proportion * (1 - proportion) / total + z * z / (4 * total * total)) / denominator
    return [max(0.0, centre - radius), min(1.0, centre + radius)]


def bias_audit_report(flipped: Sequence[bool]) -> Dict[str, Any]:
    flips = sum(bool(item) for item in flipped)
    return {
        "swaps": len(flipped),
        "flips": flips,
        "flip_rate": flips / len(flipped) if flipped else 0.0,
        "wilson_95": wilson_interval(flips, len(flipped)) if flipped else None,
        "limitation": "Identity swaps probe name sensitivity in these cases only; they do not establish fairness across people or contexts.",
    }


def measured_agent_metrics() -> Dict[str, Any]:
    """Run the existing sample tribunal and score groundedness/swap stability."""

    from .orchestrator import review_incident
    from .repository import get_incident_packet, list_incidents

    claims: List[Dict[str, Sequence[str]]] = []
    valid: List[str] = []
    relevant: List[str] = []
    flips: List[bool] = []
    for incident in list_incidents():
        packet = get_incident_packet(incident.id)
        verdict = review_incident(packet, audit_bias=True)
        packet_ids = [item.id for item in packet.evidence] + [
            item.id for item in packet.regulations
        ]
        valid.extend(packet_ids)
        relevant.extend(packet_ids)
        for finding in verdict.agent_outputs.values():
            cited = finding.evidence_ids + finding.regulation_ids
            claims.extend({"citation_ids": cited} for _ in finding.claims)
        flips.append(verdict.bias_audit_passed is not True)
    return {
        "citation_integrity": citation_integrity(claims, valid, relevant),
        "bias_audit": bias_audit_report(flips),
    }


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def run(cases_path: Path, output: Path) -> Path:
    output.mkdir(parents=True, exist_ok=False)
    _write_json(output / "protocol.json", {"seed": 20261102, "labels_opened_after_protocol": True})
    cases = load_cases(cases_path)
    results = {
        "evidence_status": "mixed metadata and synthetic; feasibility demonstration",
        "retrieval": retrieval_metrics(cases),
        "outcome_classifier": outcome_classification(cases),
        "agent_evaluation": measured_agent_metrics(),
    }
    _write_json(output / "results.json", results)
    with (output / "per_case.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["case_id", "synthetic", "outcome_category", "penalty"])
        for case in cases:
            writer.writerow([case["id"], case["synthetic"], case["outcome_category"], case["penalty"]])
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "unknown"
    _write_json(output / "environment.json", {"python": platform.python_version(), "git_commit": commit, "cpu_only": True})
    (output / "REPORT.md").write_text(
        "# StewardLens evaluation\n\n**Feasibility demonstration on a small mixed metadata/synthetic set.** "
        "The generated sample counts and metrics are in `results.json`; they are not a claim of FIA-decision performance.\n"
    )
    manifest = {}
    for path in sorted(output.iterdir()):
        if path.is_file() and path.name != "manifest.json":
            manifest[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    _write_json(output / "manifest.json", {"schema": 1, "files": manifest})
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    run(arguments.cases, arguments.output)


if __name__ == "__main__":
    main()
