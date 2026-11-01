# Run the registered experiments on audited real data

The audited split files required by the new RQ1–RQ4 adapters were not present in the repository. Existing `.local-data/ml-runs/` artifacts are sufficient to inspect earlier results but not to reconstruct every new cutoff-safe target. Therefore the committed Phase 4 runs are **fixture-only: not evidence**.

After generating the audited datasets documented in `F1-Intelligence-Lab/ML-DATA-PREPARATION.md`, implement/verify the real-data adapter against `ml_dataset.load_split`, then run each command into a new directory:

```bash
python -m f1_intelligence_lab.research.hazard --output .local-data/research/rq1-$(date +%Y%m%d-%H%M%S)
python -m f1_intelligence_lab.research.conformal --output .local-data/research/rq2-$(date +%Y%m%d-%H%M%S)
python -m f1_intelligence_lab.research.drift --output .local-data/research/rq3-$(date +%Y%m%d-%H%M%S)
python -m f1_intelligence_lab.research.tcn --output .local-data/research/rq4-$(date +%Y%m%d-%H%M%S)
```

The current commands intentionally stop rather than silently substituting fixtures when `--fixture` is omitted. Do not implement an adapter by reading the previously examined 2026 labels during model selection.

When at least three newly verified races start after 2026-11-02, open the forward set exactly once:

```bash
python -m f1_intelligence_lab.research.forward_holdout \
  --dataset "$F1_FORWARD_DATASET" \
  --output ".local-data/research/forward-$(date +%Y%m%d-%H%M%S)"
```

If fewer than three races are present, the script writes `forward holdout pending` and does not calculate model metrics.
