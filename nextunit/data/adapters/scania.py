"""SCANIA Component X v3 (raw: SCANIA/{train,validation,test}_operational_readouts.csv, *_specifications.csv,
train_tte.csv, {validation,test}_labels.csv, the official files of doi:10.5878/bnh5-ka77).

The official training set becomes shared development data (``auxiliary/``); validation vehicles are the
development units and test vehicles the hidden units, in batches of 256 distinct vehicles."""
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

RAW_DIRS = ('SCANIA',)
HISTOGRAMS = ['167', '272', '291', '158', '459', '397']


def _alias(x) -> str:
    return 'vehicle_' + hashlib.sha256(f'20261002|SCANIA|{x}'.encode()).hexdigest()[:16]


def _history(frame: pd.DataFrame, path: Path, columns: list[str]):
    frame = frame.sort_values(['vehicle_id', 'time_step'], kind='stable')
    ids = frame.vehicle_id.to_numpy()
    starts = np.r_[0, np.flatnonzero(ids[1:] != ids[:-1]) + 1, len(ids)]
    vehicles = ids[starts[:-1]]
    np.savez_compressed(path, vehicle_id=np.array([_alias(x) for x in vehicles]), offsets=starts,
                        time_step=frame.time_step.to_numpy(dtype=np.float64),
                        values=frame[columns].to_numpy(dtype=np.float64), columns=np.array(columns))
    return vehicles


def build(raw: Path, out: Path) -> None:
    source = raw / 'SCANIA'
    column_map = None
    for split in ['train', 'validation', 'test']:
        readouts = pd.read_csv(source / f'{split}_operational_readouts.csv', float_precision='round_trip')
        spec = pd.read_csv(source / f'{split}_specifications.csv')
        raw_columns = [c for c in readouts if c not in ['vehicle_id', 'time_step']]
        if column_map is None:
            counters = [x for x in raw_columns if x.split('_')[0] not in HISTOGRAMS]
            column_map = {c: (f'hist_{HISTOGRAMS.index(c.split("_")[0]) + 1:02d}_{int(c.split("_")[1]):02d}'
                              if c.split('_')[0] in HISTOGRAMS else f'counter_{counters.index(c) + 1:02d}') for c in raw_columns}
        assert set(raw_columns) == set(column_map)
        readouts = readouts.rename(columns=column_map)
        columns = [column_map[c] for c in raw_columns]
        specs = [c for c in spec if c != 'vehicle_id']
        spec = spec.rename(columns={c: f'spec_{i + 1:02d}' for i, c in enumerate(specs)})
        vehicles = set(map(int, readouts.vehicle_id.unique()))
        assert vehicles == set(map(int, spec.vehicle_id))
        if split == 'train':
            auxiliary = out / 'auxiliary'
            auxiliary.mkdir(parents=True)
            _history(readouts, auxiliary / 'history.npz', columns)
            spec.vehicle_id = spec.vehicle_id.map(_alias)
            spec.to_csv(auxiliary / 'specifications.csv', index=False)
            outcome = pd.read_csv(source / 'train_tte.csv')
            assert set(outcome.vehicle_id) == vehicles
            outcome = outcome.rename(columns={'length_of_study_time_step': 'observation_end_time', 'in_study_repair': 'repair_observed'})
            outcome.vehicle_id = outcome.vehicle_id.map(_alias)
            outcome.to_csv(auxiliary / 'outcomes.csv', index=False)
            continue
        labels = pd.read_csv(source / f'{split}_labels.csv').set_index('vehicle_id')
        assert set(labels.index) == vehicles and labels.index.is_unique
        ordered = sorted(vehicles, key=_alias)
        for i in range(0, len(ordered), 256):
            batch = ordered[i:i + 256]
            unit = out / f'{split}_batch_{i // 256:03d}'
            inputs = unit / 'inputs'
            inputs.mkdir(parents=True)
            subset = readouts[readouts.vehicle_id.isin(batch)]
            included = _history(subset, inputs / 'history.npz', columns)
            batch_spec = spec[spec.vehicle_id.isin(batch)].copy()
            batch_spec.vehicle_id = batch_spec.vehicle_id.map(_alias)
            batch_spec.to_csv(inputs / 'specifications.csv', index=False)
            end = subset.groupby('vehicle_id').time_step.max()
            query = pd.DataFrame({'record_id': [_alias(x) for x in included], 'vehicle_id': [_alias(x) for x in included],
                                  'time_step': [end[x] for x in included]})
            query.to_csv(inputs / 'requests.csv', index=False)
            pd.DataFrame({'record_id': query.record_id, 'target': [int(labels.loc[x, 'class_label']) for x in included]}) \
                .to_csv(unit / 'labels.csv', index=False)
