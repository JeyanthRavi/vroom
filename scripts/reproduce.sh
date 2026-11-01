#!/bin/sh
set -eu

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
stamp=$(date -u +%Y%m%dT%H%M%SZ)
run_root=${VROOM_RUN_ROOT:-"$repo_dir/reproductions/$stamp"}
mkdir -p "$run_root"

export PYTHONPATH="$repo_dir/F1-Intelligence-Lab/src:$repo_dir/F1-StewardLens/src:$repo_dir/F1-Telemetry-Pit-Crew/src"
python_bin=${PYTHON:-python3}

has_real=1
for variable in F1_DATA_ROOT F1_FROZEN_RUN F1_ORIGINAL_2026_EVAL; do
    eval "value=\${$variable:-}"
    if [ -z "$value" ]; then has_real=0; fi
done

if [ "$has_real" -eq 1 ]; then
    echo "Running rights-reviewed local audit, training, evaluation, and aggregate export."
    audit="$run_root/audit"
    train="$run_root/training"
    evaluation="$run_root/evaluation"
    aggregate="$run_root/aggregate"
    final_site="$run_root/site"
    "$python_bin" -m f1_intelligence_lab.ml_prep --data-root "$F1_DATA_ROOT" --output "$audit"
    "$python_bin" -m f1_intelligence_lab.robust_train --dataset "$audit" --source-root "$F1_DATA_ROOT" --frozen-run "$F1_FROZEN_RUN" --output "$train" --control-version 2
    "$python_bin" -m f1_intelligence_lab.restart_evaluate --dataset "$audit" --source-root "$F1_DATA_ROOT" --robust-run "$train" --original-evaluation "$F1_ORIGINAL_2026_EVAL" --output "$evaluation" --evaluate-2026
    "$python_bin" -m f1_intelligence_lab.export_demo --dataset "$audit" --source "$F1_DATA_ROOT" --training "$train" --evaluation "$evaluation" --output "$aggregate" --mode aggregate
    "$python_bin" -m f1_intelligence_lab.site_export --source "$aggregate" --output "$final_site" --root "$repo_dir"
else
    echo "Local audit inputs are incomplete; running fixture-only pipelines (not evidence)."
    "$python_bin" -m f1_intelligence_lab.research.hazard --fixture --output "$run_root/rq1-fixture"
    "$python_bin" -m f1_intelligence_lab.research.conformal --fixture --output "$run_root/rq2-fixture"
    "$python_bin" -m f1_intelligence_lab.research.drift --fixture --output "$run_root/rq3-fixture"
    if "$python_bin" -c 'import torch' >/dev/null 2>&1; then
        "$python_bin" -m f1_intelligence_lab.research.tcn --fixture --output "$run_root/rq4-fixture"
    else
        echo "PyTorch is absent; RQ4 fixture skipped explicitly."
    fi
    "$python_bin" -m stewardlens.evaluation --cases "$repo_dir/F1-StewardLens/data/eval/cases.jsonl" --output "$run_root/stewardlens-feasibility"
fi

echo "SHA-256 checksums:"
find "$run_root" -type f -print0 | sort -z | xargs -0 shasum -a 256
echo "Reproduction output: $run_root"
