"""Build the rights-safe static site with generated research methodology views."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict


def _json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text())


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def research_payload(root: Path) -> Dict[str, Any]:
    rq1 = _json(root / "research/runs/rq1-fixture/results.json")
    rq2 = _json(root / "research/runs/rq2-fixture/results.json")
    rq3 = _json(root / "research/runs/rq3-fixture/results.json")
    return {
        "evidence_status": "fixture-only: not evidence",
        "evaluated_on": {
            "development": "deterministic synthetic fixture",
            "examined_2026": "not used in these fixture views",
            "forward_holdout": "pending",
        },
        "hazard": {
            horizon: {
                "model": "boosting",
                "reliability": rq1["hazard"][horizon]["boosting"]["reliability"],
                "brier": rq1["hazard"][horizon]["boosting"]["brier"],
                "baseline_brier": rq1["hazard"][horizon]["base_rate"]["brier"],
            }
            for horizon in ("1", "3")
        },
        "intervals": rq2["methods"],
        "drift": {
            "rolling_origin": rq3["rolling_origin"],
            "feature_shift": rq3["feature_shift"],
        },
    }


def methodology_html(root: Path) -> str:
    protocol = html.escape((root / "research/PROTOCOL.md").read_text())
    results = html.escape((root / "research/RESULTS.md").read_text())
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Vroom methodology</title><style>:root{{color-scheme:dark;font-family:system-ui;background:#101216;color:#f2f3f5}}body{{max-width:980px;margin:auto;padding:24px}}a{{color:#5eead4}}pre{{white-space:pre-wrap;line-height:1.55;background:#191d24;border:1px solid #465266;padding:20px;border-radius:12px}}a:focus{{outline:3px solid #5eead4;outline-offset:3px}}footer{{color:#bbc3ce;margin-top:32px}}@media(max-width:420px){{body{{padding:14px}}pre{{padding:14px;font-size:12px}}}}</style></head><body><a href="./">← Historical replay</a><h1>Methodology and limitations</h1><p>This page is generated at export time. Fixture research verifies the pipeline only; the independent forward holdout is pending.</p><h2>Pre-registered protocol</h2><pre>{protocol}</pre><h2>Current research results</h2><pre>{results}</pre><footer>Unofficial educational project. Not affiliated with Formula 1, the FIA, or any team. See the repository NOTICE and data-rights review.</footer></body></html>"""


def _verified_source(source: Path) -> Dict[str, Any]:
    manifest = _json(source / "manifest.json")
    files = manifest.get("files", manifest)
    for name, expected in files.items():
        if not (source / name).is_file() or _digest(source / name) != expected:
            raise ValueError("source export checksum mismatch: " + name)
    return manifest


def build(source: Path, output: Path, root: Path) -> Path:
    source_manifest = _verified_source(source)
    output.mkdir(parents=True, exist_ok=False)
    static = root / "F1-Intelligence-Lab/src/f1_intelligence_lab/static"
    shutil.copyfile(source / "data.json", output / "data.json")
    shutil.copyfile(static / "model-demo.html", output / "index.html")
    shutil.copyfile(static / "model-demo.js", output / "demo.js")
    (output / "research.json").write_text(
        json.dumps(research_payload(root), indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    (output / "methodology.html").write_text(methodology_html(root))
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "unknown"
    data = _json(output / "data.json")
    files = {
        path.name: _digest(path)
        for path in sorted(output.iterdir())
        if path.is_file() and path.name != "manifest.json"
    }
    manifest = {
        "schema": 2,
        "export_mode": source_manifest.get("export_mode", data.get("export_mode", "legacy_full")),
        "version": data.get("model_version", "unknown"),
        "git_commit": commit,
        "files": files,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    build(arguments.source, arguments.output, arguments.root)


if __name__ == "__main__":
    main()
