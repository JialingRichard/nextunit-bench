"""XJTU-SY bearings (raw: XJTU-SY/train/<bearing>/<minute>.csv from the PHMD archive XJTU-SY.zip)."""
import json
from pathlib import Path

import pandas as pd

from ..write import same_file

RAW_DIRS = ('XJTU-SY',)


def _json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2) + '\n')


def build(raw: Path, out: Path) -> None:
    for folder in sorted(p for p in (raw / 'XJTU-SY/train').iterdir() if p.is_dir()):
        unit = out / folder.name
        paths = sorted(folder.glob('*.csv'), key=lambda p: int(p.stem))
        last = max(int(p.stem) for p in paths)
        chunks = [f'chunk_{i:06d}' for i in range(len(paths))]
        for i, path in enumerate(paths):
            chunk = unit / 'inputs' / chunks[i]
            chunk.mkdir(parents=True)
            same_file(path, chunk / 'measurement.csv')
            _json(chunk / 'records.json', [{'record_id': f'm{i + 1:06d}', 'signal_file': 'measurement.csv',
                                            'elapsed_minutes': int(path.stem) - 1}])
        _json(unit / 'inputs/stream.json', chunks)
        pd.DataFrame([{'record_id': f'm{i + 1:06d}', 'target': last - int(p.stem)} for i, p in enumerate(paths)]) \
            .to_csv(unit / 'labels.csv', index=False)
