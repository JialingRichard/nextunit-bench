"""From fold losses to S, D and the aggregates S24 and S_noshortcut, as in the paper.

Per fold: S = 100*max(0, 1 - E/B), D = 100*max(0, 1 - B/E); a failed fold scores
S = 0 and D = 100. Per dataset: the mean over its folds. Aggregate: the
equal-weight mean over the datasets of a named set, with a percentile bootstrap
over datasets.
"""
from __future__ import annotations

import math
import random
import statistics
from collections import defaultdict

import numpy as np

from .. import definition

BOOTSTRAP_SEED, BOOTSTRAP_RESAMPLES = 20261004, 4000      # intervals of S24 and S_noshortcut
PAIRED_SEED, PAIRED_RESAMPLES = 20261030, 10000           # paired differences between two methods


def fold_scores(error: float | None, baseline: float, status: str) -> tuple[float, float]:
    """(S, D) of one fold; ``status`` is ``completed`` or ``failed``."""
    if status == 'failed':
        return 0.0, 100.0
    if status != 'completed':
        raise ValueError(f'Unfinished record: {status}')
    if error is None or not math.isfinite(error) or error < 0:
        raise ValueError(f'Invalid completed loss: {error}')
    if not math.isfinite(baseline) or baseline < 0:
        raise ValueError(f'Invalid reference loss: {baseline}')
    # Comparisons before division define the zero-reference and perfect-result cases.
    gain = 100 * (1 - error / baseline) if error < baseline else 0.0
    penalty = 100 * (1 - baseline / error) if error > baseline else 0.0
    return gain, penalty


def score_fold(dataset: str, fold: int, error: float | None, status: str) -> dict:
    B = definition.baseline(dataset, fold)
    S, D = fold_scores(error, B, status)
    return {'dataset': dataset, 'fold': fold, 'status': status, 'E': error, 'B': B, 'S': S, 'D': D}


def dataset_means(fold_S: dict[tuple[str, int], float]) -> dict[str, float]:
    """Mean S over the folds of each dataset. Every fold of a dataset must be present."""
    by = defaultdict(dict)
    for (dataset, fold), value in fold_S.items():
        by[dataset][fold] = value
    out = {}
    for dataset, values in by.items():
        expected = definition.folds(dataset)
        if sorted(values) != expected:
            raise ValueError(f'{dataset}: folds {sorted(values)} given, {expected} required')
        out[dataset] = float(np.mean([values[fold] for fold in expected]))
    return out


def aggregate(fold_S: dict[tuple[str, int], float], name: str = 'S24') -> dict:
    """Mean of dataset means over a named set, with a 95% bootstrap interval over datasets."""
    names = sorted(definition.aggregate_sets()[name])
    means = dataset_means({key: value for key, value in fold_S.items() if key[0] in names})
    missing = sorted(set(names) - set(means))
    if missing:
        raise ValueError(f'{name}: no scores for {missing}')
    vector = np.array([means[dataset] for dataset in names])
    index = np.random.default_rng(BOOTSTRAP_SEED).integers(0, len(names), size=(BOOTSTRAP_RESAMPLES, len(names)))
    low, high = np.quantile(vector[index].mean(axis=1), [0.025, 0.975])
    return {'name': name, 'datasets': len(names), 'S': float(vector.mean()), 'ci_low': float(low), 'ci_high': float(high),
            'per_dataset': means}


def summarize(fold_S: dict[tuple[str, int], float]) -> dict:
    """S24 and S_noshortcut of one method."""
    return {name: aggregate(fold_S, name) for name in definition.aggregate_sets()}


def paired(a: dict[tuple[str, int], float], b: dict[tuple[str, int], float], keep=lambda key: True) -> dict | None:
    """Difference a - b on common folds: per-dataset means, equal weight, bootstrap over datasets."""
    by = defaultdict(list)
    for key in sorted(a.keys() & b.keys()):
        if keep(key):
            by[key[0]].append(a[key] - b[key])
    if not by:
        return None
    mean = {dataset: statistics.mean(values) for dataset, values in by.items()}
    names = sorted(by)
    agg = lambda sample: statistics.mean(mean[dataset] for dataset in sample)
    rng = random.Random(PAIRED_SEED)
    boot = sorted(agg([rng.choice(names) for _ in names]) for _ in range(PAIRED_RESAMPLES))
    return {'dS': agg(names), 'ci_low': boot[int(0.025 * PAIRED_RESAMPLES)], 'ci_high': boot[int(0.975 * PAIRED_RESAMPLES) - 1],
            'datasets': len(names), 'folds': sum(len(v) for v in by.values()),
            'up': sum(v > 0 for v in mean.values()), 'down': sum(v < 0 for v in mean.values())}
