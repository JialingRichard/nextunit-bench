"""PHM Europe 2020 filter clogging, the 32 runs with labels (raw: PHME20/data/ from the PHMD archive PHME20.zip;
the official download no longer works)."""
import io
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ._hashid import rid

RAW_DIRS = ('PHME20',)


def _json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def build(raw: Path, out: Path) -> None:
    source = raw / 'PHME20/data'
    text = (source / 'operation_profiles.csv').read_text()
    # Two source rows have a decimal point where the field separator belongs.
    text = text.replace('10.49,0.45', '10,49,0.45').replace('40.66,0.425', '40,66,0.425')
    operations = pd.read_csv(io.StringIO(text)).set_index('Sample')
    for path in sorted(source.glob('Sample*.csv')):
        sample = int(path.stem.replace('Sample', ''))
        frame = pd.read_csv(path)
        difference = frame.iloc[:, 2].to_numpy() - frame.iloc[:, 3].to_numpy()
        failure = int(np.flatnonzero(difference > 20)[0])   # first pressure drop above 20 psi
        end_time = float(frame.iloc[failure, 0])
        frame = frame.iloc[:failure + 1].copy()
        frame.columns = ['elapsed_seconds', 'flow_ml_min', 'upstream_psi', 'downstream_psi']
        particle, concentration = operations.loc[sample].tolist()
        unit = out / f'run_{sample:02d}'
        (unit / 'inputs').mkdir(parents=True)
        chunks, labels = [], []
        for start in range(0, len(frame), 10):
            current = frame.iloc[start:start + 10]
            chunk = f'chunk_{len(chunks):06d}'
            target = unit / 'inputs' / chunk
            target.mkdir()
            current.to_csv(target / 'measurement.csv', index=False)
            record = rid(f'phme:{sample}:{start}')
            now = float(current.iloc[-1, 0])
            _json(target / 'records.json', [{'record_id': record, 'signal_file': 'measurement.csv', 'elapsed_seconds': now,
                                             'particle_size_micron': particle, 'solid_ratio_percent': concentration}])
            labels.append((record, round(end_time - now, 6)))
            chunks.append(chunk)
        _json(unit / 'inputs/stream.json', chunks)
        pd.DataFrame(labels, columns=['record_id', 'target']).to_csv(unit / 'labels.csv', index=False)
