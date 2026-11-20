"""IMS bearings, runs 1-3 (raw: IMS/unit {1,2,3}/ from the PHMD archive IMS.zip)."""
from datetime import datetime
from pathlib import Path

import numpy as np

from ..write import csv_crlf, json_file

RAW_DIRS = ('IMS',)
FAILED = [(1, [3, 4]), (2, [1]), (3, [3])]   # bearings that failed in each run


def build(raw: Path, out: Path) -> None:
    for run, bearings in FAILED:
        files = sorted((raw / f'IMS/unit {run}').iterdir())
        dates = [datetime.strptime(p.name, '%Y.%m.%d.%H.%M.%S') for p in files]
        seconds = np.array([(t - dates[0]).total_seconds() for t in dates])
        units = [out / f'run_{run}_bearing_{b}' for b in bearings]
        blocks = [f'blocks/{i:05d}' for i in range(len(files))]
        channels = [(b - 1) * 2 if run == 1 else b - 1 for b in bearings]
        for i, path in enumerate(files):
            x = np.loadtxt(path, usecols=channels, dtype='float32', ndmin=2)
            for j, unit in enumerate(units):
                block = unit / 'inputs' / blocks[i]
                block.mkdir(parents=True, exist_ok=True)
                np.save(block / 'signals.npy', x[:, j:j + 1])
                csv_crlf(block / 'records.csv', ['record_id', 'elapsed_hours'], [(f'r{i:05d}', seconds[i] / 3600)])
        for unit in units:
            json_file(unit / 'inputs/stream.json', blocks)
            csv_crlf(unit / 'labels.csv', ['record_id', 'target'],
                     ((f'r{i:05d}', (seconds[-1] - seconds[i]) / 3600) for i in range(len(files))))
