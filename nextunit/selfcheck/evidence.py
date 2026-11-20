"""Recompute the evidence quoted in KNOWN_ISSUES.md (A1-A3) from prepared data. Descriptive only; no model is fitted.

python -m nextunit.selfcheck.evidence --prepared PREPARED_ROOT"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from .. import definition
from ..data import layout
from ..eval.fold import fold_view
from ..eval.score import fold_scores
from ..eval.scoring import FoldScorer


def ahu21(prepared: Path) -> dict:
    """A1: faults share one schedule. Time-only predictor: fault iff the timestamp is a development fault time."""
    frames = {}
    for unit in definition.public_ids('AHU21'):
        signals = pd.read_csv(layout.inputs_dir(prepared, 'AHU21', unit) / 'signals.csv', usecols=['record_id', 'Time'], dtype={'record_id': str})
        labels = pd.read_csv(layout.labels_path(prepared, 'AHU21', unit), dtype={'record_id': str})
        frames[unit] = signals.merge(labels, on='record_id')
    out = {}
    for fold in definition.folds('AHU21'):
        fault_times = set().union(*(set(frames[u].Time[frames[u].target == 1]) for u in definition.units('AHU21', fold, 'development')))
        view = fold_view('AHU21', fold, 'hidden', prepared)
        scorer = FoldScorer(view.metric, view.aggregation, view.class_values)
        for public, unit in sorted(view.entity_mapping.items()):
            f = frames[unit]
            scorer.add(public, pd.DataFrame({'record_id': f.record_id, 'prediction': f.Time.isin(fault_times).astype(int)}),
                       f[['record_id', 'target']])
        E = 1 - scorer.result()['primary_score']
        out[f'fold_{fold}'] = {'S_time_only': round(fold_scores(E, definition.baseline('AHU21', fold), 'completed')[0], 1)}
    return out


def threew(prepared: Path) -> dict:
    """A2: per instance, length and relative position of the first requested row, by event class."""
    rows = []
    for unit in definition.public_ids('THREEW'):
        inputs = layout.inputs_dir(prepared, 'THREEW', unit)
        requests = pd.read_csv(inputs / 'records.csv', dtype={'record_id': str})
        labels = pd.read_csv(layout.labels_path(prepared, 'THREEW', unit), dtype={'record_id': str})
        joined = requests.merge(labels, on='record_id')
        for sequence, group in joined.groupby('sequence_id'):
            with np.load(inputs / f'{sequence}.npz') as arrays:
                length = len(arrays['elapsed_seconds'])
            event = int(max(t % 100 for t in group.target))
            rows.append({'class': event, 'rows': length, 'first_request': group.row_index.min() / length})
    table = pd.DataFrame(rows)
    out = {}
    for event, group in table.groupby('class'):
        q = group.first_request.quantile([0.25, 0.5, 0.75])
        out[str(event)] = {'instances': len(group), 'rows_min': int(group.rows.min()), 'rows_max': int(group.rows.max()),
                           'rows_median': int(group.rows.median()), 'first_request_median': round(q[0.5], 3),
                           'first_request_iqr': round(q[0.75] - q[0.25], 3)}
    return out


def care(prepared: Path) -> dict:
    """A3: within each wind farm, single-variable ROC-AUC of the observation-window length against the label."""
    rows = []
    for unit in definition.public_ids('CARE'):
        inputs = layout.inputs_dir(prepared, 'CARE', unit)
        labels = pd.read_csv(layout.labels_path(prepared, 'CARE', unit), dtype={'record_id': str})
        for record, target in zip(labels.record_id, labels.target):
            with np.load(inputs / f'{record}.npz') as arrays:
                t = arrays['observation_time_seconds']
                days = (t[-1] - t[0]) / 86400
                rows.append({'site': str(arrays['site_id']), 'days': days, 'off_whole_day': abs(days - round(days)), 'target': target})
    table = pd.DataFrame(rows)
    out = {}
    for site, group in table.groupby('site'):
        out[site] = {'events': len(group), 'auc_window_days': round(roc_auc_score(group.target, group.days), 2),
                     'auc_distance_from_whole_day': round(roc_auc_score(group.target, group.off_whole_day), 2),
                     'median_days_anomaly': round(group.days[group.target == 1].median(), 1),
                     'median_days_normal': round(group.days[group.target == 0].median(), 1)}
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog='python -m nextunit.selfcheck.evidence')
    parser.add_argument('--prepared', type=Path, required=True)
    args = parser.parse_args(argv)
    print(json.dumps({'A1_AHU21': ahu21(args.prepared), 'A2_THREEW': threew(args.prepared), 'A3_CARE': care(args.prepared)}, indent=1))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
