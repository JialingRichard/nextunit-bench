"""Paderborn bearing data, 32 bearings (raw: PUBD16/data/<bearing>/*.mat from the PHMD archive PUBD16.zip, which
holds the official per-bearing archives unpacked)."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

RAW_DIRS = ('PUBD16',)
STATE = {'K0': 0, 'KA': 1, 'KI': 2, 'KB': 3}       # healthy, outer race, inner race, combined damage
INVALID = {'N15_M01_F10_KA08_2.mat'}               # corrupt in the source


def _json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2) + '\n')


def build(raw: Path, out: Path) -> None:
    from scipy.io import loadmat
    for folder in sorted(p for p in (raw / 'PUBD16/data').iterdir() if p.is_dir()):
        unit = out / folder.name
        (unit / 'inputs/signal').mkdir(parents=True)
        paths = sorted(p for p in folder.glob('*.mat') if p.name not in INVALID)
        records = []
        for i, path in enumerate(paths):
            record_id = f'm{i + 1:06d}'
            measurement = loadmat(path, simplify_cells=True)[path.stem]
            np.savez(unit / f'inputs/signal/{record_id}.npz', **{c['Name']: np.asarray(c['Data']) for c in measurement['Y']})
            records.append({'record_id': record_id, 'signal_file': f'signal/{record_id}.npz'})
        _json(unit / 'inputs/records.json', records)
        target = STATE[folder.name[:2]]
        pd.DataFrame([{'record_id': r['record_id'], 'target': target} for r in records]).to_csv(unit / 'labels.csv', index=False)
