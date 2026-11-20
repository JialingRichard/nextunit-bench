"""Training cache of the reference forest: the reader's arrays for a fixed subset of every development unit.

Per unit at most ``limit = min(60000, max(64, ceil(120000 / n)))`` records, n the number of units that are
development units in any fold: the records at evenly spaced positions of ``labels.csv``, plus every record of a class
that has at most ``limit / n_classes`` records in the unit (AUC/AP tasks: classes 0 and 1). The selection depends on
labels only through those class counts; the forest draws its training rows from this cache (model.Units.select).
SCANIA adds its official training set (``<prepared>/SCANIA/auxiliary``) as batches of 256 readouts.

Layout: ``<cache>/<DATASET>/<unit>/{sequence,tabular[,image]}.npy`` and ``records.csv``; ``complete.json`` marks a
finished dataset. The cache is derived data and can be deleted at any time.
"""
from __future__ import annotations

import json
import math
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from ... import definition
from ...data import layout
from . import readers
from .model import RANKING, ARRAYS

RECORDS_PER_DATASET, MIN_PER_UNIT, MAX_PER_UNIT = 120000, 64, 60000
SCANIA_AUXILIARY_CAP, SCANIA_BATCH = 114954, 256


def development_units(dataset: str) -> list[str]:
    units = set().union(*(definition.units(dataset, fold, 'development') for fold in definition.folds(dataset)))
    return [e['id'] for e in definition.task(dataset)['entities'] if e['id'] in units]


def cache_classes(dataset: str):
    task = definition.task(dataset)
    return [0, 1] if task['metric'] in RANKING else task['prediction_values']


def _write_unit(dataset, unit, prepared, raw, destination: Path, limit: int) -> dict:
    labels = pd.read_csv(layout.labels_path(prepared, dataset, unit), dtype={'record_id': str})
    ids = labels.record_id.to_numpy()
    positions = np.unique(np.linspace(0, len(ids) - 1, min(limit, len(ids)), dtype=np.int64))
    selected = {str(ids[i]) for i in positions}
    classes = cache_classes(dataset)
    if classes is not None:
        for value in classes:
            members = labels.loc[labels.target == value, 'record_id']
            if len(members) <= limit / len(classes):
                selected.update(members)
    destination.mkdir(parents=True)
    arrays, out_ids, shapes = {}, [], {}
    for item in readers.iter_samples(dataset, layout.inputs_dir(prepared, dataset, unit), unit, raw,
                                     selected=selected if dataset == 'THREEW' else None):
        if item['record_id'] not in selected:
            continue
        if not arrays:
            for name in ARRAYS:
                if item.get(name) is not None:
                    shapes[name] = np.asarray(item[name]).shape
                    arrays[name] = np.lib.format.open_memmap(destination / f'{name}.npy', mode='w+', dtype='float32',
                                                             shape=(len(selected), *shapes[name]))
        for name, array in arrays.items():
            value = np.asarray(item[name], dtype=np.float32)
            assert value.shape == shapes[name], (dataset, unit, name, value.shape)
            array[len(out_ids)] = value
        out_ids.append(item['record_id'])
    assert len(out_ids) == len(set(out_ids)) and set(out_ids) == selected, (dataset, unit, len(out_ids), len(selected))
    for array in arrays.values():
        array.flush()
    pd.DataFrame({'record_id': out_ids}).to_csv(destination / 'records.csv', index=False)
    return {'unit': unit, 'records': len(out_ids), 'of': len(ids)}


def _scania_auxiliary(prepared, destination: Path) -> list[str]:
    """SCANIA's official training readouts with interval labels from repair and censoring times (no validation or
    test outcomes): 60,000 evenly spaced valid readouts plus every class with at most cap/5 readouts."""
    source = layout.auxiliary_dir(prepared, 'SCANIA')
    z = np.load(source / 'history.npz')
    vehicles, offsets, times, values = z['vehicle_id'], z['offsets'], z['time_step'], z['values']
    specs = pd.read_csv(source / 'specifications.csv').set_index('vehicle_id')
    outcomes = pd.read_csv(source / 'outcomes.csv').set_index('vehicle_id')
    vindex = np.repeat(np.arange(len(vehicles)), np.diff(offsets))
    ends = outcomes.loc[vehicles, 'observation_end_time'].to_numpy()[vindex]
    events = outcomes.loc[vehicles, 'repair_observed'].to_numpy()[vindex]
    delta = ends - times
    valid = (delta >= 0) & ((events == 1) | (delta > 48))
    candidates = np.flatnonzero(valid)
    target = np.zeros(len(times), dtype=np.int8)
    for cutoff, label in [(48, 1), (24, 2), (12, 3), (6, 4)]:
        target[(events == 1) & (delta <= cutoff) & (delta >= 0)] = label
    uniform = candidates[np.unique(np.linspace(0, len(candidates) - 1, min(60000, len(candidates)), dtype=np.int64))]
    rare = []
    for label in range(5):
        positions = candidates[target[candidates] == label]
        if len(positions) <= SCANIA_AUXILIARY_CAP // 5:
            rare.extend(positions)
    rare = np.array(sorted(set(rare)), dtype=np.int64)
    rest = np.setdiff1d(uniform, rare)
    remaining = SCANIA_AUXILIARY_CAP - len(rare)
    if len(rest) > remaining:
        rest = rest[np.unique(np.linspace(0, len(rest) - 1, remaining, dtype=np.int64))]
    chosen = np.sort(np.r_[rare, rest])
    spec = {str(v): specs.loc[v].to_numpy() for v in vehicles}
    names = []
    for batch_start in range(0, len(chosen), SCANIA_BATCH):
        selected = chosen[batch_start:batch_start + SCANIA_BATCH]
        name = f'auxiliary_train_{batch_start // SCANIA_BATCH:04d}'
        batch = destination / name
        batch.mkdir(parents=True)
        sequence = np.zeros((len(selected), 105, 32), dtype=np.float32)
        table = np.zeros((len(selected), 257), dtype=np.float32)
        ids = []
        for n, pos in enumerate(selected):
            vi = vindex[pos]
            vehicle, start, end = str(vehicles[vi]), int(offsets[vi]), int(pos) + 1
            sequence[n] = readers.scania_rows(values[max(start, end - 32):end])
            table[n] = readers.scania_tabular(spec[vehicle], times[pos])
            ids.append(f'{vehicle}_readout_{pos - start:06d}')
        np.save(batch / 'sequence.npy', sequence)
        np.save(batch / 'tabular.npy', table)
        pd.DataFrame({'record_id': ids, 'target': target[selected]}).to_csv(batch / 'records.csv', index=False)
        names.append(name)
    return names


def build(dataset: str, prepared: Path | str, cache: Path | str, raw: Path | str | None = None) -> dict:
    """Write the dataset's training cache (skipped if complete); returns its summary."""
    root = Path(cache) / dataset
    if (root / 'complete.json').exists():
        return json.loads((root / 'complete.json').read_text())
    if root.exists():
        shutil.rmtree(root)
    units = development_units(dataset)
    limit = min(MAX_PER_UNIT, max(MIN_PER_UNIT, math.ceil(RECORDS_PER_DATASET / len(units))))
    summary = {'dataset': dataset, 'limit': limit, 'units': [_write_unit(dataset, u, prepared, raw, root / u, limit) for u in units]}
    if definition.task(dataset)['development_auxiliary']:
        summary['auxiliary'] = _scania_auxiliary(prepared, root / 'auxiliary')
    (root / 'complete.json').write_text(json.dumps(summary) + '\n')
    return summary


def load(dataset: str, fold: int, prepared: Path | str, cache: Path | str) -> list[dict]:
    """The fold's training units in order (development units, then auxiliary batches): id, arrays, target."""
    root = Path(cache) / dataset
    summary = json.loads((root / 'complete.json').read_text())
    out = []
    for unit in definition.units(dataset, fold, 'development'):
        records = pd.read_csv(root / unit / 'records.csv', dtype={'record_id': str})
        labels = pd.read_csv(layout.labels_path(prepared, dataset, unit), dtype={'record_id': str}).set_index('record_id')
        out.append({'id': unit, 'arrays': _arrays(root / unit), 'target': labels.loc[records.record_id, 'target'].to_numpy()})
    for name in summary.get('auxiliary', []):
        records = pd.read_csv(root / 'auxiliary' / name / 'records.csv', dtype={'record_id': str})
        out.append({'id': name, 'arrays': _arrays(root / 'auxiliary' / name), 'target': records.target.to_numpy()})
    return out


def _arrays(directory: Path) -> dict:
    return {name: np.load(directory / f'{name}.npy', mmap_mode='r') if (directory / f'{name}.npy').exists() else None
            for name in ARRAYS}
