"""C-MAPSS FD004 (raw: CMAPSS/{train,test}/ from the PHMD archives CMAPSS_train.zip, CMAPSS_test.zip)."""
from pathlib import Path

import numpy as np

from ..write import csv_crlf

RAW_DIRS = ('CMAPSS',)


def build(raw: Path, out: Path) -> None:
    endpoint = np.loadtxt(raw / 'CMAPSS/test/RUL_FD004.txt')
    counts = {}
    for split in ['train', 'test']:
        data = np.loadtxt(raw / f'CMAPSS/{split}/{split}_FD004.txt')
        units = np.unique(data[:, 0]).astype(int)
        counts[split] = len(units)
        for number in units:
            x = data[data[:, 0] == number, 1:]
            unit = out / f'{split}_{number:03d}'
            csv_crlf(unit / 'inputs/observations.csv', ['cycle'] + [f'setting_{i}' for i in range(1, 4)] +
                     [f'sensor_{i}' for i in range(1, 22)], x)
            indices = range(len(x)) if split == 'train' else [len(x) - 1]
            csv_crlf(unit / 'inputs/requests.csv', ['record_id', 'cycle'], ((f'r{i:05d}', int(x[i, 0])) for i in indices))
            offset = 0 if split == 'train' else float(endpoint[number - 1])
            csv_crlf(unit / 'labels.csv', ['record_id', 'target'],
                     ((f'r{i:05d}', float(x[-1, 0] - x[i, 0] + offset)) for i in indices))
    assert (counts['train'], counts['test'], len(endpoint)) == (249, 248, 248)
