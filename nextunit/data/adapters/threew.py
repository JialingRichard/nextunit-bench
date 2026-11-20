"""Petrobras 3W v2.0.0, real wells only (raw: THREEW/3w_dataset_2.0.0.zip, the official figshare archive
doi:10.6084/m9.figshare.29205836.v1, read in place). Needs pyarrow.

v1.0 keeps the paper's request construction: requests exist only for rows with a class label, which leaves the
shortcut documented in KNOWN_ISSUES A2. v1.1 will change this function."""
import csv
import hashlib
import re
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

RAW_DIRS = ('THREEW',)
SEED = 20261002


def build(raw: Path, out: Path) -> None:
    archive = zipfile.ZipFile(raw / 'THREEW/3w_dataset_2.0.0.zip')
    members = [n for n in archive.namelist() if n.endswith('.parquet')]
    groups = defaultdict(list)
    for name in members:
        match = re.search(r'(WELL-\d+)_', Path(name).name)
        if match:
            groups[match.group(1)].append(name)
    assert len(members) == 2228 and sum(map(len, groups.values())) == 1119
    for well in sorted(groups):
        unit = out / well
        inputs = unit / 'inputs'
        inputs.mkdir(parents=True)
        columns = None
        # Sequence numbers follow a fixed hash, not the source class or time order.
        ordered = sorted(groups[well], key=lambda n: hashlib.sha256(f'{SEED}|{n}'.encode()).digest())
        with (inputs / 'records.csv').open('w', newline='') as rq, (unit / 'labels.csv').open('w', newline='') as lb:
            requests, labels = csv.writer(rq), csv.writer(lb)
            requests.writerow(['record_id', 'sequence_id', 'row_index'])
            labels.writerow(['record_id', 'target'])
            for index, name in enumerate(ordered):
                with archive.open(name) as data:
                    frame = pd.read_parquet(data)
                assert frame.index.is_monotonic_increasing
                features = [c for c in frame.columns if c not in ('class', 'state')]
                assert len(features) == 27
                columns = columns or features
                assert features == columns
                sequence = f'sequence_{index:05d}'
                elapsed = np.asarray((frame.index - frame.index[0]).total_seconds(), dtype=np.float64)
                np.savez_compressed(inputs / f'{sequence}.npz', values=frame[features].to_numpy(dtype=np.float64),
                                    elapsed_seconds=elapsed, columns=np.asarray(features, dtype='U32'))
                mask = frame['class'].notna().to_numpy()       # the v1.0 shortcut: only labelled rows are requested
                for row, label in zip(np.flatnonzero(mask), frame.loc[mask, 'class'].to_numpy(dtype=np.int16)):
                    record = f'{sequence}_r{row:08d}'
                    requests.writerow([record, sequence, int(row)])
                    labels.writerow([record, int(label)])
