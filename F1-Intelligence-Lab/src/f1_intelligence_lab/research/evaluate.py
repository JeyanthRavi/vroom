"""Deterministic synthetic race fixture and common evaluation helpers."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def fixture_rows(seed: int = 20261102) -> List[Dict[str, Any]]:
    rng = np.random.default_rng(seed)
    rows = []
    for race_index in range(8):
        circuit = 'Fixture A' if race_index % 2 == 0 else 'Fixture B'
        split = 'train' if race_index < 4 else 'validation' if race_index < 6 else 'test'
        for lap in range(12, 52):
            variance = float(0.15 + 0.02 * (lap % 7))
            hazard = int((lap + race_index * 3) % 31 in {0, 1})
            state = 'GREEN' if not hazard else ('SC' if lap % 2 else 'VSC')
            pit = int(lap in {24 + race_index % 3, 39})
            pace = 88 + race_index * 0.25 + 0.035 * lap + rng.normal(0, 0.22)
            target = pace + pit * 18 + hazard * 25
            rows.append({
                'race_id': 'fixture-%02d' % race_index, 'race_index': race_index,
                'split': split, 'circuit': circuit, 'lap': lap,
                'cutoff_order': lap - 1, 'feature_latest_order': lap - 1,
                'pace_variance': variance, 'local_yellows': int((lap + 2) % 19 == 0),
                'cars_in_pit_window': pit, 'tyre_age_gap': abs(28 - (lap % 30)),
                'state': state, 'hazard_h1': hazard,
                'hazard_h3': int(any((future + race_index * 3) % 31 in {0, 1} for future in range(lap, lap + 3))),
                'green_target': state == 'GREEN' and not pit,
                'rolling_median_3': pace + rng.normal(0, 0.45),
                'rolling_median_5': pace + rng.normal(0, 0.35),
                'rolling_mean': pace + rng.normal(0, 0.4),
                'last_lap': pace + rng.normal(0, 0.55),
                'target_s': float(target), 'pace_target_s': float(pace),
            })
    return rows


def assert_no_leakage(rows: List[Dict[str, Any]]) -> None:
    if any(row['feature_latest_order'] > row['cutoff_order'] for row in rows):
        raise ValueError('feature timestamp exceeds cutoff')
    race_splits: Dict[str, set] = {}
    for row in rows:
        race_splits.setdefault(row['race_id'], set()).add(row['split'])
    if any(len(splits) != 1 for splits in race_splits.values()):
        raise ValueError('race crosses partitions')


def regression_scores(actual: np.ndarray, predicted: np.ndarray, races: List[str]) -> Dict[str, Any]:
    per_race = {}
    for race in sorted(set(races)):
        mask = np.asarray([value == race for value in races])
        per_race[race] = {'rows': int(mask.sum()), 'mae_s': float(mean_absolute_error(actual[mask], predicted[mask]))}
    return {
        'rows': int(actual.size), 'mae_s': float(mean_absolute_error(actual, predicted)),
        'race_macro_mae_s': float(np.mean([row['mae_s'] for row in per_race.values()])),
        'rmse_s': float(mean_squared_error(actual, predicted) ** 0.5),
        'r2': float(r2_score(actual, predicted)), 'per_race': per_race,
    }


def write_predictions(path: Path, rows: List[Dict[str, Any]], columns: List[str]) -> None:
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows({column: row[column] for column in columns} for row in rows)
