"""The constant predictor: the zero-information reference whose scores are exact.

Classification: the most frequent development label (smallest on ties); regression: the median development
label; ranking metrics: a constant score. Development labels are pooled over the fold's development units
(scored records only). Scored with the fixed scoring code, without a sandbox."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .. import definition
from ..eval.evaluator import finish
from ..eval.fold import fold_view
from ..eval.metrics import CLASSIFICATION, LOSSES
from ..eval.scoring import FoldScorer


def _labels(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype={'record_id': str})
    return frame[frame['score'].astype(bool)] if 'score' in frame else frame


def constant(dataset: str, fold: int, prepared_root: Path | str) -> float:
    metric = definition.task(dataset)['metric']
    development = fold_view(dataset, fold, 'development', prepared_root)
    pooled = pd.concat([_labels(p) for p in development.labels.values()], ignore_index=True).target
    if metric in CLASSIFICATION:
        return float(pooled.mode().iloc[0])
    if metric in LOSSES:
        return float(pooled.median())
    return 0.0


def score_fold(dataset: str, fold: int, prepared_root: Path | str) -> dict:
    value = constant(dataset, fold, prepared_root)
    view = fold_view(dataset, fold, 'hidden', prepared_root)
    scorer = FoldScorer(view.metric, view.aggregation, view.class_values)
    for entity in sorted(view.inputs):
        labels = pd.read_csv(view.labels[entity], dtype={'record_id': str})
        scorer.add(entity, pd.DataFrame({'record_id': labels.record_id, 'prediction': np.full(len(labels), value)}), labels)
    result = finish(scorer.result(), view)
    return {'dataset': dataset, 'fold': fold, 'constant': value, 'E': result['E']}
