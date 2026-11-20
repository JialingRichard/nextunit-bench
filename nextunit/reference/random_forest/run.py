"""Retrain the reference forest of every fold and score its hidden predictions with the fixed scoring code.

Two phases, each on a pool of ``jobs`` single-threaded processes: training caches (one task per dataset), then folds
(train, predict every hidden unit, score). Results do not depend on ``jobs``.
"""
from __future__ import annotations

import json
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import get_context
from pathlib import Path

import numpy as np
import pandas as pd

from ... import definition
from ...eval.evaluator import finish
from ...eval.fold import fold_view
from ...eval.scoring import FoldScorer
from . import cache, mimii, readers
from .model import Units, fit

PREDICT_ROWS, PREDICT_BYTES = 8192, 2 ** 28
NEEDS_RAW = ('PUBD16',)
COST = {'TEP': 9, 'SCANIA': 8, 'THREEW': 7, 'MATWI': 6, 'BACKBLAZE': 5, 'CMAPSS': 4, 'NB14': 3, 'XJTU-SY': 3,
        'PHM10': 3, 'CALCE': 2, 'CARE': 2, 'PUBD16': 2}       # rough order of running time: long tasks start first


def _predict_unit(forest, dataset, inputs, unit, raw) -> pd.DataFrame:
    ids, values, pending, limit = [], [], [], None

    def flush():
        arrays = {k: np.stack([s[k] for s in pending]) if pending[0].get(k) is not None else None
                  for k in ('sequence', 'tabular', 'image')}
        values.append(forest.predict(arrays))
        ids.extend(s['record_id'] for s in pending)
        pending.clear()

    for item in readers.iter_samples(dataset, inputs, unit, raw):
        if limit is None:
            width = sum(np.asarray(item[k]).size for k in ('sequence', 'tabular', 'image') if item.get(k) is not None)
            limit = max(1, min(PREDICT_ROWS, PREDICT_BYTES // max(1, 4 * width)))
        pending.append(item)
        if len(pending) == limit:
            flush()
    if pending:
        flush()
    return pd.DataFrame({'record_id': ids, 'prediction': np.concatenate(values) if values else np.empty(0)})


def run_fold(dataset: str, fold: int, prepared: Path | str, cache_root: Path | str, raw=None) -> dict:
    """Train, predict and score one fold; returns E and timings."""
    started = time.monotonic()
    view = fold_view(dataset, fold, 'hidden', prepared)
    if dataset == 'MIMII_DUE':
        models = mimii.fit(prepared, fold)
        trained = time.monotonic()
        predict = lambda public: pd.DataFrame(dict(zip(('record_id', 'prediction'), mimii.predict(models, view.inputs[public]))))
        record = {'models': len(models)}
    else:
        task = definition.task(dataset)
        classes = cache.cache_classes(dataset)          # None for regression
        forest, record = fit(Units(cache.load(dataset, fold, prepared, cache_root)), task['metric'], task['aggregation'],
                             None if classes is None else sorted(classes))
        trained = time.monotonic()
        predict = lambda public: _predict_unit(forest, dataset, view.inputs[public], view.entity_mapping[public], raw)
    scorer = FoldScorer(view.metric, view.aggregation, view.class_values)
    for public in sorted(view.inputs):
        scorer.add(public, predict(public), view.labels[public])
    result = finish(scorer.result(), view)
    return {'dataset': dataset, 'fold': fold, 'E': result['E'], 'train_seconds': trained - started,
            'predict_seconds': time.monotonic() - trained, **record}


def _build(dataset, prepared, cache_root, raw):
    started = time.monotonic()
    cache.build(dataset, prepared, cache_root, raw)
    return {'dataset': dataset, 'cache_seconds': time.monotonic() - started}


def run(prepared: Path | str, datasets, cache_root: Path | str, raw=None, jobs: int = 2, log=print) -> list[dict]:
    """All folds of ``datasets``; returns one row per fold (dataset, fold, E, timings), in definition order."""
    missing = [d for d in datasets if d in NEEDS_RAW and raw is None]
    if missing:
        raise ValueError(f'{missing}: the reference reader needs the raw root (--raw)')
    order = sorted(datasets, key=lambda d: -COST.get(d, 0))
    folds = [(d, f) for d in order for f in definition.folds(d)]
    rows = []
    with ProcessPoolExecutor(max_workers=jobs, mp_context=get_context('spawn')) as pool:
        for done in as_completed([pool.submit(_build, d, prepared, cache_root, raw) for d in order if d != 'MIMII_DUE']):
            log(json.dumps(done.result()))
        for done in as_completed([pool.submit(run_fold, d, f, prepared, cache_root, raw) for d, f in folds]):
            rows.append(done.result())
            log(json.dumps(rows[-1]))
    position = {key: i for i, key in enumerate(definition.all_folds())}
    return sorted(rows, key=lambda r: position[(r['dataset'], r['fold'])])
