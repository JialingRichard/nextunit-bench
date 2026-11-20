"""FEMTO/PRONOSTIA bearings (raw: PRONOSTIA/{train,test}/ from the PHMD archives PRONOSTIA_train.zip, PRONOSTIA_test.zip)."""
from pathlib import Path

import numpy as np

from ..write import csv_crlf

RAW_DIRS = ('PRONOSTIA',)

# Remaining life (s) of each test bearing at its last record, from the IEEE PHM 2012 Prognostic Challenge
# description (FEMTO-ST); the test files end before failure.
PRONOSTIA_RUL = {'Bearing1_3': 5730, 'Bearing1_4': 339, 'Bearing1_5': 1610,
                 'Bearing1_6': 1460, 'Bearing1_7': 7570, 'Bearing2_3': 7530,
                 'Bearing2_4': 1390, 'Bearing2_5': 3090, 'Bearing2_6': 1290,
                 'Bearing2_7': 580, 'Bearing3_3': 820}


def build(raw: Path, out: Path) -> None:
    groups = {}
    for split in ['train', 'test']:
        groups[split] = []
        for folder in sorted((raw / f'PRONOSTIA/{split}').iterdir()):
            unit = out / folder.name
            (unit / 'inputs').mkdir(parents=True, exist_ok=True)
            files = sorted(folder.glob('acc_*.csv'))
            n = len(files)
            signals = np.lib.format.open_memmap(unit / 'inputs/signals.npy', mode='w+', dtype='float32', shape=(n, 2560, 2))
            for i, path in enumerate(files):
                signals[i] = np.loadtxt(path, delimiter=',', usecols=(4, 5), dtype='float32')
            signals.flush()
            del signals
            csv_crlf(unit / 'inputs/observations.csv', ['sample_index', 'elapsed_seconds'], ((i, i * 10) for i in range(n)))
            indices = range(n) if split == 'train' else [n - 1]
            csv_crlf(unit / 'inputs/requests.csv', ['record_id', 'sample_index'], ((f'r{i:05d}', i) for i in indices))
            offset = 0 if split == 'train' else PRONOSTIA_RUL[folder.name]
            csv_crlf(unit / 'labels.csv', ['record_id', 'target'], ((f'r{i:05d}', (n - 1 - i) * 10 + offset) for i in indices))
            groups[split].append(folder.name)
    assert len(groups['train']) == 6 and set(groups['test']) == set(PRONOSTIA_RUL)
