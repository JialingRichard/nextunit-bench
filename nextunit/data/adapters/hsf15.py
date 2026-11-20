"""UCI condition monitoring of hydraulic systems (raw: HSF15/data/*.txt from the PHMD archive HSF15.zip, the official UCI files)."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ._hashid import rid

RAW_DIRS = ('HSF15',)
VALVE = {100: 0, 90: 1, 80: 2, 73: 3}


def _json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def build(raw: Path, out: Path) -> None:
    source = raw / 'HSF15/data'
    profile = np.loadtxt(source / 'profile.txt', dtype=int)
    sensors = {p.stem: np.loadtxt(p, dtype=np.float32) for p in sorted(source.glob('*.txt')) if p.name != 'profile.txt'}
    assert profile.shape == (2205, 5) and all(len(v) == len(profile) for v in sensors.values())
    for cooler in sorted(set(profile[:, 0])):
        unit = out / f'cooler_{cooler}'
        (unit / 'inputs/signal').mkdir(parents=True)
        rows, labels = [], []
        for index in sorted(np.flatnonzero(profile[:, 0] == cooler), key=lambda i: rid(f'hsf:{i}')):
            record = rid(f'hsf:{index}')
            relative = f'signal/{record}.npz'
            np.savez_compressed(unit / 'inputs' / relative, **{name: values[index] for name, values in sensors.items()})
            rows.append({'record_id': record, 'signal_file': relative})
            labels.append((record, VALVE[int(profile[index, 1])]))
        _json(unit / 'inputs/records.json', rows)
        pd.DataFrame(labels, columns=['record_id', 'target']).to_csv(unit / 'labels.csv', index=False)
