"""SEU gearbox, gearset part (raw: SEUGB17/gearset/ from the PHMD archive SEUGB17.zip)."""
from pathlib import Path

import numpy as np
import pandas as pd

from ..write import csv_crlf

RAW_DIRS = ('SEUGB17',)


def build(raw: Path, out: Path) -> None:
    for condition in ['20_0', '30_2']:
        for label, fault in enumerate(['Health', 'Chipped', 'Root', 'Miss', 'Surface']):
            x = pd.read_csv(raw / f'SEUGB17/gearset/{fault}_{condition}.csv', sep='\t', skiprows=16, header=None,
                            usecols=range(8), dtype='float32').to_numpy()
            n = len(x) // 4096
            unit = out / f'condition_{condition}_record_{label:02d}'
            (unit / 'inputs').mkdir(parents=True, exist_ok=True)
            np.save(unit / 'inputs/signals.npy', x[:n * 4096].reshape(n, 4096, 8))
            csv_crlf(unit / 'inputs/records.csv', ['record_id', 'start_sample'], ((f'r{i:05d}', i * 4096) for i in range(n)))
            csv_crlf(unit / 'labels.csv', ['record_id', 'target'], ((f'r{i:05d}', label) for i in range(n)))
