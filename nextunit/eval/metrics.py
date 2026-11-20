"""The six task metrics, computed exactly as in the paper's evaluator."""
from __future__ import annotations

import numpy as np
import pandas as pd

METRICS = ('accuracy', 'balanced_accuracy', 'mae', 'rmse', 'roc_auc', 'average_precision')
CLASSIFICATION = frozenset({'accuracy', 'balanced_accuracy'})
RANKING = frozenset({'roc_auc', 'average_precision'})
LOSSES = frozenset({'mae', 'rmse'})


def score(frame: pd.DataFrame, metric: str, weights=None) -> float:
    """Raw metric value of a frame with columns ``target`` and ``prediction``."""
    if metric == 'accuracy':
        return float(np.average(frame.target == frame.prediction, weights=weights))
    if metric == 'balanced_accuracy':
        return float((frame.target == frame.prediction).groupby(frame.target).mean().mean())
    if metric == 'mae':
        return float(np.average(np.abs(frame.target - frame.prediction), weights=weights))
    if metric == 'rmse':
        return float(np.sqrt(np.average((frame.target - frame.prediction) ** 2, weights=weights)))
    if metric in RANKING:
        from sklearn.metrics import average_precision_score, roc_auc_score
        scorer = roc_auc_score if metric == 'roc_auc' else average_precision_score
        return float(scorer(frame.target, frame.prediction, sample_weight=weights))
    raise ValueError(metric)


def loss(metric: str, value: float) -> float:
    """The loss E: the metric itself for MAE and RMSE, one minus it otherwise."""
    if metric not in METRICS:
        raise ValueError(metric)
    return value if metric in LOSSES else 1.0 - value


class ClassificationCounts:
    """Exact pooled classification metrics from a confusion table."""

    def __init__(self) -> None:
        self.confusion: dict[tuple[float, float], int] = {}
        self.records = 0

    def update(self, frame: pd.DataFrame) -> None:
        table = pd.crosstab(frame.target, frame.prediction)
        for target in table.index:
            for prediction in table.columns:
                count = int(table.loc[target, prediction])
                if count:
                    key = (float(target), float(prediction))
                    self.confusion[key] = self.confusion.get(key, 0) + count
                    self.records += count

    def score(self, metric: str) -> float:
        totals: dict[float, int] = {}
        correct: dict[float, int] = {}
        for (target, prediction), count in self.confusion.items():
            totals[target] = totals.get(target, 0) + count
            correct[target] = correct.get(target, 0) + (count if target == prediction else 0)
        if metric == 'accuracy':
            return float(sum(correct.values()) / self.records)
        if metric == 'balanced_accuracy':
            return float(np.mean([correct[target] / count for target, count in sorted(totals.items())]))
        raise ValueError(metric)
