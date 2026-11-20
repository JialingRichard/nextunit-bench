"""NASA randomized battery usage, RW1-RW28 (raw: NB14/<group>/RW*.mat from the PHMD archive NB14.zip).

Reproduces the paper's three-stage pipeline in one pass: (1) daily random-walk usage becomes the input and each
reference discharge a request, labelled with its integrated capacity; (2) each request becomes one stream chunk
holding the usage history up to that request; (3) the corrected version removes the three reference discharges
that did not actually discharge. CSV text is re-read between stages exactly as the paper's pipeline did, because
pandas' default float parser changes some last digits."""
import io
import json
from pathlib import Path

import numpy as np
import pandas as pd

RAW_DIRS = ('NB14',)
ARRAYS = ['time', 'relative_time', 'current', 'voltage', 'temperature']
INVALID = {('RW17', 'm000003'), ('RW18', 'm000003'), ('RW19', 'm000002')}


def _valid_reference(step) -> bool:
    time = np.atleast_1d(step.relativeTime).astype(float)
    current = np.atleast_1d(step.current).astype(float)
    if len(time) != len(current) or len(time) < 2 or not (np.isfinite(time).all() and np.isfinite(current).all()):
        return False
    return bool((np.diff(time) > 0).all()) and float(np.trapezoid(abs(current), time) / 3600) > 0


def build(raw: Path, out: Path) -> None:
    from scipy.io import loadmat
    removed = set()
    for number in range(1, 29):
        name = f'RW{number}'
        data = loadmat(next((raw / 'NB14').rglob(name + '.mat')), squeeze_me=True, struct_as_record=False)['data']
        # Stage 1: usage history, requests and labels.
        arrays = {key: [] for key in ARRAYS}
        offsets, discharging, requests, labels, valid = [0], [], [], [], []
        first_time = float(np.atleast_1d(data.step[0].time)[0])
        for step in data.step:
            comment = str(step.comment)
            if comment == 'reference discharge':
                record_id = str(len(requests))
                requests.append({'record_id': record_id, 'history_stop': offsets[-1],
                                 'age_seconds': float(np.atleast_1d(step.time)[0]) - first_time})
                capacity = abs(np.trapezoid(np.atleast_1d(step.current), np.atleast_1d(step.relativeTime))) / 3600
                labels.append({'record_id': record_id, 'target': float(capacity)})
                valid.append(_valid_reference(step))
            if 'random walk' in comment:
                for key in ARRAYS:
                    field = 'relativeTime' if key == 'relative_time' else key
                    arrays[key].append(np.atleast_1d(getattr(step, field)).astype(np.float64))
                offsets.append(offsets[-1] + len(arrays['time'][-1]))
                discharging.append(str(step.type) == 'D')
        history = {key: np.concatenate(values) for key, values in arrays.items()}
        step_offsets = np.asarray(offsets, dtype=np.int64)
        step_discharging = np.asarray(discharging, dtype=bool)
        requests = pd.read_csv(io.StringIO(pd.DataFrame(requests).to_csv(index=False)), dtype={'record_id': str})
        # Stage 2: one chunk per request; record IDs m000001...
        mapping = {row.record_id: f'm{i + 1:06d}' for i, row in enumerate(requests.itertuples(index=False))}
        staged = pd.read_csv(io.StringIO(pd.DataFrame(labels).to_csv(index=False)), dtype={'record_id': str}, float_precision='round_trip')
        staged.record_id = staged.record_id.map(mapping)
        # Stage 3: drop invalid references; labels re-read with pandas' default parser, as in the paper.
        staged = pd.read_csv(io.StringIO(staged.to_csv(index=False)), dtype={'record_id': str})
        dropped = {mapping[str(i)] for i, ok in enumerate(valid) if not ok}
        removed |= {(name, record) for record in dropped}
        unit = out / name
        (unit / 'inputs').mkdir(parents=True)
        chunks = []
        for index, row in enumerate(requests.itertuples(index=False)):
            public = mapping[row.record_id]
            if public in dropped:
                continue
            chunk = f'chunk_{index:06d}'
            target = unit / 'inputs' / chunk
            target.mkdir()
            stop = int(row.history_stop)
            edge = int(np.searchsorted(step_offsets, stop, side='right'))
            assert step_offsets[edge - 1] == stop     # requests fall between usage steps
            payload = {key: history[key][:stop] for key in ARRAYS}
            payload['step_offsets'] = step_offsets[:edge]
            payload['step_discharging'] = step_discharging[:edge - 1]
            np.savez_compressed(target / 'daily.npz', **payload)
            pd.DataFrame([{'record_id': public, 'history_stop': stop, 'age_seconds': row.age_seconds}]) \
                .to_csv(target / 'requests.csv', index=False)
            chunks.append(chunk)
        staged[~staged.record_id.isin(dropped)].to_csv(unit / 'labels.csv', index=False)
        (unit / 'inputs/stream.json').write_text(json.dumps(chunks, ensure_ascii=False, indent=2) + '\n')
    assert removed == INVALID, removed
