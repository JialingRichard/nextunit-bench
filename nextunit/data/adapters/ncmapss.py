"""N-CMAPSS DS02-006 (raw: NCMAPSS/data/N-CMAPSS_DS02-006.h5 from the PHMD archive NCMAPSS.zip)."""
from pathlib import Path

import numpy as np

from ..write import csv_crlf, json_file

RAW_DIRS = ('NCMAPSS',)


def build(raw: Path, out: Path) -> None:
    import h5py
    counts = {}
    with h5py.File(raw / 'NCMAPSS/data/N-CMAPSS_DS02-006.h5') as h:
        columns = [v.decode() for key in ['W_var', 'X_s_var'] for v in h[key][:]]
        for split in ['dev', 'test']:
            # Only identifiers, cycle and flight class are read from A; health-state truth never.
            aux = h[f'A_{split}'][:, :3]
            units = np.unique(aux[:, 0]).astype(int)
            counts[split] = len(units)
            for number in units:
                unit = out / f'engine_{number:02d}'
                positions = np.flatnonzero(aux[:, 0] == number)
                a = aux[positions]
                blocks, labels = [], []
                for cycle in np.unique(a[:, 1]).astype(int):
                    pos = positions[a[:, 1] == cycle]
                    assert np.all(np.diff(pos) == 1)
                    start, stop = int(pos[0]), int(pos[-1] + 1)
                    name = f'blocks/{cycle:05d}'
                    block = unit / 'inputs' / name
                    block.mkdir(parents=True, exist_ok=True)
                    x = np.concatenate([h[f'W_{split}'][start:stop], h[f'X_s_{split}'][start:stop]], axis=1).astype('float32')
                    np.save(block / 'observations.npy', x)
                    json_file(block / 'columns.json', columns)
                    csv_crlf(block / 'records.csv', ['record_id', 'cycle', 'flight_class'], [(f'r{cycle:05d}', cycle, int(aux[start, 2]))])
                    y = h[f'Y_{split}'][start:stop, 0]
                    assert np.all(y == y[0]) and np.isfinite(x).all()
                    blocks.append(name)
                    labels.append((f'r{cycle:05d}', int(y[-1])))
                json_file(unit / 'inputs/stream.json', blocks)
                csv_crlf(unit / 'labels.csv', ['record_id', 'target'], labels)
    assert counts == {'dev': 6, 'test': 3}
