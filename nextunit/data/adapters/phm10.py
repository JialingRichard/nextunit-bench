"""PHM Society 2010 milling, cutters c1, c4, c6 (raw: PHM10/data/train/ from the PHMD archive PHM10_train.zip)."""
from pathlib import Path

import numpy as np
import pandas as pd

from ..write import json_file, same_file

RAW_DIRS = ('PHM10',)


def build(raw: Path, out: Path) -> None:
    for cutter in ('c1', 'c4', 'c6'):
        source = raw / 'PHM10/data/train' / cutter
        wear = pd.read_csv(source / f'{cutter}_wear.csv')
        assert len(wear) == 315 and wear['cut'].is_unique
        inputs = out / cutter / 'inputs'
        inputs.mkdir(parents=True, exist_ok=True)
        blocks, labels = [], []
        for row in wear.itertuples(index=False):
            cut = int(row.cut)
            record_id = f'r{cut:04d}'
            block = inputs / record_id
            block.mkdir(exist_ok=True)
            same_file(source / cutter / f'c_{cutter[1:]}_{cut:03d}.csv', block / 'signals.csv')
            pd.DataFrame([{'record_id': record_id, 'cut_index': cut}]).to_csv(block / 'query.csv', index=False)
            labels.append({'record_id': record_id, 'target': float(np.mean([row.flute_1, row.flute_2, row.flute_3]))})
            blocks.append(record_id)
        json_file(inputs / 'stream.json', blocks)
        pd.DataFrame(labels).to_csv(out / cutter / 'labels.csv', index=False)
