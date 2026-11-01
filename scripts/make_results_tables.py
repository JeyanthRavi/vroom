#!/usr/bin/env python3
"""Generate every experiment-number table from committed JSON artifacts."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, Tuple


ROOT = Path(__file__).resolve().parents[1]


def load(relative: str):
    return json.loads((ROOT / relative).read_text())


def number(value) -> str:
    return "—" if value is None else f"{float(value):.3f}"


def core_table(data: Dict) -> str:
    labels = {
        "rolling_median": "Rolling median",
        "restart_boosting": "Restart-aware boosting",
        "restart_gru": "Restart-aware GRU",
    }
    lines = [
        "Evaluated on previously examined 2026 races; not an independent holdout.",
        "The default was selected using 2025 validation only.",
        "",
        "| Model | Equal-race MAE (s) | Pooled RMSE (s) | R² | Rows |",
        "|---|---:|---:|---:|---:|",
    ]
    for key in ("rolling_median", "restart_boosting", "restart_gru"):
        row = data["regression"][key]
        lines.append(
            f"| {labels[key]} | {number(row['race_macro_mae_s'])} | "
            f"{number(row['rmse_s'])} | {number(row['r2'])} | {row['rows']} |"
        )
    lines.append("")
    lines.append(
        "The rolling median remains the pooled-RMSE/R² reference; learned models "
        "do not improve every metric. Source: `F1-Intelligence-Lab/public-results/aggregate-results.json`."
    )
    return "\n".join(lines)


def model_card(data: Dict) -> str:
    selected = data["validation"]["robust_tree_r1.5_l15"]
    baseline = data["validation"]["rolling_median"]
    regression = data["regression"]
    return "\n".join(
        [
            "| Evaluation | Model | Equal-race MAE (s) | Baseline MAE (s) | Pooled RMSE (s) | R² | Rows |",
            "|---|---|---:|---:|---:|---:|---:|",
            f"| 2025 validation | Selected restart boosting | {number(selected['race_macro_mae_s'])} | {number(baseline['race_macro_mae_s'])} | {number(selected['rmse_s'])} | {number(selected['r2'])} | {selected['rows']} |",
            f"| Examined 2026 regression | Restart boosting | {number(regression['restart_boosting']['race_macro_mae_s'])} | {number(regression['rolling_median']['race_macro_mae_s'])} | {number(regression['restart_boosting']['rmse_s'])} | {number(regression['restart_boosting']['r2'])} | {regression['restart_boosting']['rows']} |",
            f"| Examined 2026 regression | Restart GRU | {number(regression['restart_gru']['race_macro_mae_s'])} | {number(regression['rolling_median']['race_macro_mae_s'])} | {number(regression['restart_gru']['rmse_s'])} | {number(regression['restart_gru']['r2'])} | {regression['restart_gru']['rows']} |",
            "",
            "Source: `public-results/aggregate-results.json`; 2026 is previously examined and non-independent.",
        ]
    )


def rq1(result: Dict) -> str:
    lines = ["**Fixture-only: not evidence.**", "", "| Horizon | Model | Brier | PR-AUC | ECE |", "|---:|---|---:|---:|---:|"]
    for horizon in ("1", "3"):
        for key in ("base_rate", "logistic", "boosting", "small_tcn"):
            row = result["hazard"][horizon][key]
            lines.append(f"| {horizon} | {key} | {number(row['brier'])} | {number(row['pr_auc'])} | {number(row['ece_10'])} |")
    return "\n".join(lines)


def rq2(result: Dict) -> str:
    lines = ["**Fixture-only: not evidence.**", "", "| Method | Nominal | Coverage | Wilson 95% | Width (s) |", "|---|---:|---:|---|---:|"]
    for key, row in sorted(result["methods"].items()):
        interval = row["wilson95"]
        lines.append(f"| {key} | {number(row['nominal_coverage'])} | {number(row['coverage'])} | [{number(interval[0])}, {number(interval[1])}] | {number(row['mean_width_s'])} |")
    return "\n".join(lines)


def rq3(result: Dict) -> str:
    lines = ["**Fixture-only: deliberately injected shift; not evidence.**", "", "| Feature | PSI | KS statistic |", "|---|---:|---:|"]
    for key, row in sorted(result["feature_shift"].items()):
        lines.append(f"| {key} | {number(row['psi'])} | {number(row['ks_statistic'])} |")
    return "\n".join(lines)


def rq4(result: Dict) -> str:
    cell = next(item for item in result["cells"] if item["window"] == 10 and item["with_state"] and item["with_tyre"])
    lines = ["**Fixture-only: one pre-specified ablation cell; not evidence.**", "", "| Model | Parameters | Equal-race MAE (s) |", "|---|---:|---:|"]
    lines.append(f"| rolling_median_5 | — | {number(cell['rolling_median_5']['race_macro_mae_s'])} |")
    for key, row in sorted(cell["models"].items()):
        lines.append(f"| {key} | {row['parameters']} | {number(row['ensemble']['race_macro_mae_s'])} |")
    return "\n".join(lines)


def steward(result: Dict) -> str:
    retrieval = result["retrieval"]
    classifier = result["outcome_classifier"]
    citations = result["agent_evaluation"]["citation_integrity"]
    audit = result["agent_evaluation"]["bias_audit"]
    return "\n".join(
        [
            "**Small mixed metadata/synthetic feasibility set; not official-decision performance evidence.**",
            "",
            "| Cases | Retrieval recall@k | MRR | Citation integrity | Identity swaps | Flip rate |",
            "|---:|---:|---:|---:|---:|---:|",
            f"| {classifier['sample_count']} | {number(retrieval['recall_at_k'])} | {number(retrieval['mrr'])} | {number(citations['fraction'])} | {audit['swaps']} | {number(audit['flip_rate'])} |",
            "",
            "The per-class report in the source artifact includes a zero-recall class; no aggregate score is promoted as a claim.",
        ]
    )


def replace(path: Path, name: str, body: str, check: bool) -> bool:
    text = path.read_text()
    pattern = re.compile(
        rf"(<!-- BEGIN GENERATED: {re.escape(name)} -->\n).*?(\n<!-- END GENERATED: {re.escape(name)} -->)",
        re.DOTALL,
    )
    updated, count = pattern.subn(rf"\g<1>{body}\g<2>", text)
    if count != 1:
        raise RuntimeError(f"expected one marker {name} in {path}")
    if updated == text:
        return True
    if check:
        return False
    path.write_text(updated)
    return True


def sections() -> Dict[Tuple[str, str], str]:
    data = load("F1-Intelligence-Lab/public-results/aggregate-results.json")
    return {
        ("README.md", "core-results"): core_table(data),
        ("F1-Intelligence-Lab/MODEL-CARD.md", "model-card-metrics"): model_card(data),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    stale = []
    for (relative, name), body in sections().items():
        if not replace(ROOT / relative, name, body, arguments.check):
            stale.append(f"{relative}:{name}")
    if stale:
        raise SystemExit("generated result sections are stale: " + ", ".join(stale))
    print("Generated result sections: current" if arguments.check else "Generated result sections: updated")


if __name__ == "__main__":
    main()
