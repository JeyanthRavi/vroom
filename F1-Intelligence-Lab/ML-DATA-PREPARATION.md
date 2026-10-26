# Race pace ML — task 1: audit and features

This task builds the dataset foundation only. No model is trained, no accuracy claim is made, and the running website/source library is unchanged.

## Run

From `F1-Intelligence-Lab`:

```sh
.venv/bin/python -m pip install -e '.[audit]'
PYTHONPATH=src .venv/bin/python -m f1_intelligence_lab.ml_prep \
  --data-root .local-data --fetch-fia \
  --output .local-data/ml-prep/my-new-run
```

Omit `--fetch-fia` for an offline replay using downloaded evidence. Every output directory must be new; existing runs are never overwritten. Missing evidence causes quarantine, not an automatic pass. The source SQLite connection is read-only. Evidence PDFs are cached separately under `.local-data/ml-evidence/`; datasets remain local and git-ignored.

## Prediction contract

Predict a driver's **lap t duration in seconds at its recorded start time**. Require the immediately preceding three numbered laps to have valid durations and calculated completion times no later than that cutoff. This is a conditional model for completed laps with sufficient history, not a predictor of whether a driver will retire.

The explicit 13-feature allowlist contains circuit, target lap number, three prior lap durations, their mean and population standard deviation, recent time change, previous-lap tyre compound/estimated age/stint lap, previous-lap pit-out indicator, and conservatively reconstructed race-control state at the cutoff.

Tyre age counts completed laps including the previous lap. Compound and tyre age come from the **previous** stint context; the target lap might use different tyres, which are deliberately not leaked into inputs. The last known stint start is used; final stint end is never used as a feature. Future race-control messages are ignored.

No target-lap sectors, target-lap compound, target-lap flags, final standings, race-wide medians, future stints, fastest-lap summaries or future weather are model inputs. Driver/session identifiers, timestamps, partition labels and verification status are metadata only. There are no weather features yet: verified as-of weather joins would be a separate addition.

### Important availability limitation

Historical data provides event timestamps, **not verified feed-arrival timestamps**. This pipeline prevents future-event leakage, but cannot prove that retrospectively corrected timing/stint information had already been published live. A genuinely live backtest requires captured arrival-time snapshots. Do not describe this dataset as a certified live-trading-style replay.

Start timestamps and published durations show sub-second boundary jitter. No timestamps are silently corrected or rounded. A historical lap ending after the target cutoff is excluded even by a millisecond. Earlier boundary disagreements are reported as observations; they do not imply access to information after the prediction cutoff.

## Quality policy

| Dimension | Check / action |
|---|---|
| Completeness | Required lap timing, start time, driver and pit-out fields; gaps break contiguous history. No imputation. |
| Accuracy | Independent FIA final-classification PDF: event/year, driver identities, classified positions, completed laps where published, and at least 10 published fastest-lap time anchors. |
| Consistency | Session/meeting references, cached versus dossier driver/results, sector sum within 0.020 seconds when all sectors exist; no lap beyond classified completed count except DSQ records whose counts may be suppressed. |
| Freshness | Source hashes, cache modification timestamps, import age and race age recorded. Old historical records do not fail merely due to age. Future session/timing/import dates fail. |
| Validity | Finite 1–3600 second durations, integer laps 1–300, timezone-aware start time, known driver; previous tyre context and compound checks. |
| Uniqueness | Quarantine every member of a duplicate driver/lap key; never arbitrarily keep one. Unique prediction IDs include session, car and target lap. |

Classification verification is **bounded evidence**, not proof of every lap, tyre record or live arrival time. Missing/unreadable PDFs and parser limitations are distinguished from numeric disagreements in the report. DSQ rows can lack completed-lap counts. One explicit name alias handles `Andrea Kimi Antonelli` / `Kimi Antonelli`; no fuzzy identity matching is used. Long valid laps (including neutralised/pit laps) are reported, not discarded simply to improve future model scores.

All target laps meeting the validity contract remain eligible regardless of their eventual flag or pit outcome. There is no hindsight "clean-laps only" target selection. This means future evaluation must report performance during disruptions, not just average pace.

## Frozen chronological partitions

| Partition | Race start, UTC | Purpose |
|---|---|---|
| Train | Before 1 September 2025 | Fit model and preprocessing |
| Validation | 1 September–31 October 2025 | Choose settings |
| Test | 1 November–31 December 2025 | Untouched final evaluation |
| Future holdout | 2026 onward | Separate cross-season evaluation; not tuning data |

These boundaries are fixed rules, not chosen to maximize scores. Whole races stay together across every driver. No preprocessing or feature selection has been fitted. Fit any future encoders/scalers/imputers on **train only**. Never random-split the lap rows.

## Artifacts

- `REPORT.md`: readable session-by-session decisions.
- `audit.json`: schema/null profiles, failure counts, source provenance, timing discrepancies and verification evidence.
- `train.csv`, `validation.csv`, `test.csv`, `future_holdout.csv`: verified-session feature rows.
- `candidates_NOT_FOR_TRAINING.csv`: diagnostic rows, including unverified sessions. Not a fallback training set.
- `quarantined_laps.jsonl`: original rejected records with reasons; source records are preserved.
- `feature_contract.json`: feature allowlist, target, availability and split policies.
- `manifest.json`: hashes of pipeline outputs. Separately generated `dq-*.json` reports are supplemental.

The conservative loader verifies hashes, the gate, partition/session membership, row counts, feature columns and prediction cutoffs. It returns only allowed model features separately from labels and metadata:

```python
from f1_intelligence_lab.ml_dataset import load_split
X, y, metadata = load_split('.local-data/ml-prep/audit-2026-10-27-final', 'train')
```

## Initial audit: 27 October 2026

50 saved sessions / 55,606 raw lap records audited. 38 sessions passed the bounded FIA checks; 12 were excluded from model datasets. 238 raw lap records were quarantined. There are 25,791 diagnostic candidate rows, including rows from excluded sessions.

Verified partitions: **7,884 train**, **2,632 validation**, **1,655 test**, **8,343 future holdout**. These are feature examples, not independent races or independent observations.

The next task is baseline/model training and held-out evaluation. A dataset gate passing does not imply a useful trained model or deployment readiness.

Reference sources: [OpenF1 API documentation](https://openf1.org/docs/) and [FIA decision documents](https://www.fia.com/documents). Downloaded evidence is for local research; public redistribution/licensing is not established by this audit.
