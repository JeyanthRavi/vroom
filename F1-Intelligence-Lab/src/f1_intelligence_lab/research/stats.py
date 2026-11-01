"""Small statistical helpers with race-level resampling."""
from __future__ import annotations

import math
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np


def paired_race_bootstrap(
    differences: Sequence[float], resamples: int = 10000, seed: int = 20261102
) -> Dict[str, object]:
    values = np.asarray(differences, dtype=float)
    if values.size == 0 or not np.isfinite(values).all():
        raise ValueError('finite per-race differences are required')
    rng = np.random.default_rng(seed)
    draws = rng.choice(values, size=(resamples, values.size), replace=True).mean(axis=1)
    return {
        'mean_difference': float(values.mean()),
        'ci95': [float(v) for v in np.quantile(draws, [0.025, 0.975])],
        'races': int(values.size),
        'wins': int((values < 0).sum()),
        'resampling_unit': 'race',
    }


def wilson(successes: int, total: int, z: float = 1.959963984540054) -> Tuple[float, float]:
    if total <= 0 or successes < 0 or successes > total:
        raise ValueError('valid successes and positive total required')
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    radius = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return center - radius, center + radius


def reliability_bins(
    labels: Sequence[int], probabilities: Sequence[float], bins: int = 10
) -> List[Dict[str, float]]:
    y = np.asarray(labels, dtype=int)
    p = np.asarray(probabilities, dtype=float)
    if y.shape != p.shape or not np.isin(y, [0, 1]).all() or not ((0 <= p) & (p <= 1)).all():
        raise ValueError('binary labels and aligned probabilities in [0,1] required')
    result = []
    edges = np.linspace(0, 1, bins + 1)
    for index in range(bins):
        mask = (p >= edges[index]) & (p < edges[index + 1] if index < bins - 1 else p <= 1)
        if mask.any():
            result.append({
                'lower': float(edges[index]), 'upper': float(edges[index + 1]),
                'count': int(mask.sum()), 'mean_probability': float(p[mask].mean()),
                'observed_rate': float(y[mask].mean()),
            })
    return result


def expected_calibration_error(labels: Sequence[int], probabilities: Sequence[float]) -> float:
    rows = reliability_bins(labels, probabilities, 10)
    total = sum(int(row['count']) for row in rows)
    return sum(
        int(row['count']) / total * abs(row['mean_probability'] - row['observed_rate'])
        for row in rows
    )


def interval_score(
    actual: Iterable[float], lower: Iterable[float], upper: Iterable[float], alpha: float
) -> float:
    y, lo, hi = (np.asarray(list(values), dtype=float) for values in (actual, lower, upper))
    if y.shape != lo.shape or y.shape != hi.shape or (lo > hi).any() or not 0 < alpha < 1:
        raise ValueError('aligned valid intervals and alpha required')
    score = hi - lo + 2 / alpha * (lo - y) * (y < lo) + 2 / alpha * (y - hi) * (y > hi)
    return float(score.mean())

