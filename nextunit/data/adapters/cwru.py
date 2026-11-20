"""CWRU 12k drive-end bearing data (raw: CWRU/data/ from the PHMD archive CWRU.zip)."""
from pathlib import Path

import numpy as np
from scipy.io import loadmat
from scipy.signal import resample_poly

from ..write import csv_crlf

RAW_DIRS = ('CWRU',)


def build(raw: Path, out: Path) -> None:
    base = raw / 'CWRU/data'
    for load, rpm in enumerate([1797, 1772, 1750, 1730]):
        files = [(base / f'NormalBaseline/{rpm}/Normal.mat', 0)]
        for size in ['0.007', '0.014', '0.021']:
            for fault, label in [('InnerRace', 1), ('Ball', 2), ('OuterRace6', 3)]:
                files.append((base / f'12DriveEndFault/{rpm}/{size}-{fault}.mat', label))
        for recording, (path, target) in enumerate(files):
            data = loadmat(path)
            # Normal files: the variable of this load explicitly (the 1750 rpm file also holds X098).
            key = f'X{97 + load:03d}_DE_time' if target == 0 else next(k for k in data if k.endswith('_DE_time'))
            signal = data[key].reshape(-1)
            if target == 0:
                signal = resample_poly(signal, 1, 4)  # 48 kHz -> 12 kHz
            n = len(signal) // 4096
            windows = signal[:n * 4096].reshape(n, 4096, 1).astype('float32')
            unit = out / f'condition_{load}_record_{recording:02d}'
            (unit / 'inputs').mkdir(parents=True, exist_ok=True)
            np.save(unit / 'inputs/signals.npy', windows)
            csv_crlf(unit / 'inputs/records.csv', ['record_id', 'start_sample'], ((f'r{i:05d}', i * 4096) for i in range(n)))
            csv_crlf(unit / 'labels.csv', ['record_id', 'target'], ((f'r{i:05d}', target) for i in range(n)))
