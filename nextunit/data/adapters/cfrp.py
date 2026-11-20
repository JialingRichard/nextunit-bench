"""NASA CFRP composites, Stanford fatigue tests (raw: CFRP/Layup{1,2,3}.zip, the inner archives of the official
NASA PCoE "2. Composites.zip"). Only coupons with measured stiffness degradation are kept (three)."""
import collections
import hashlib
import io
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

RAW_DIRS = ('CFRP',)
METADATA = ['actuator', 'sensor', 'amplitude', 'frequency', 'gain', 'sampling_rate']


def _members(z):
    return [n for n in z.namelist() if n.lower().endswith('.mat') and '/._' not in n and not n.startswith('__MACOSX')]


def build(raw: Path, out: Path) -> None:
    from scipy.io import loadmat
    kept = 0
    for layup in (1, 2, 3):
        with zipfile.ZipFile(raw / f'CFRP/Layup{layup}.zip') as z:
            specimens = collections.defaultdict(list)
            for name in _members(z):
                specimens[name.split('/')[0]].append(name)
            for specimen, names in specimens.items():
                summary = []
                for name in names:
                    data = loadmat(io.BytesIO(z.read(name)), simplify_cells=True)
                    if 'coupon' not in data:
                        continue
                    c = data['coupon']
                    y = np.asarray(c.get('straingage_data', {}).get('stiffness_degradation', [])).ravel()
                    summary.append({'name': name, 'cycle': float(c['cycles']),
                                    'target': float(y[0]) if y.size == 1 and np.isfinite(y[0]) else None})
                valid = [r for r in summary if r['target'] is not None]
                # The source encodes absent stiffness with zeros; an all-zero coupon has no measured progression.
                if not valid or not any(r['target'] != 0 for r in valid):
                    continue
                groups = collections.defaultdict(list)
                for r in summary:
                    groups[r['cycle']].append(r)
                targets = {}
                for cycle, rows in groups.items():
                    values = {r['target'] for r in rows if r['target'] is not None}
                    assert len(values) <= 1, (specimen, cycle, values)
                    if values:
                        targets[cycle] = next(iter(values))
                unit = out / f'coupon_{hashlib.sha256(specimen.encode()).hexdigest()[:10]}'
                inputs = unit / 'inputs'
                inputs.mkdir(parents=True)
                labels, chunks, last = [], [], -np.inf
                for index, (cycle, target) in enumerate(sorted(targets.items())):
                    chunk = f'chunk_{index:06d}'
                    folder = inputs / chunk
                    folder.mkdir()
                    observations = []
                    available = sorted((r for r in summary if last < r['cycle'] <= cycle), key=lambda r: (r['cycle'], r['name']))
                    for j, row in enumerate(available):
                        c = loadmat(io.BytesIO(z.read(row['name'])), simplify_cells=True)['coupon']
                        paths = c['path_data']
                        paths = [paths] if isinstance(paths, dict) else list(paths)
                        sensor = [np.asarray(p['signal_sensor']).ravel() for p in paths]
                        actuator = [np.asarray(p['signal_actuator']).ravel() for p in paths]
                        assert len({len(a) for a in sensor + actuator}) == 1, (specimen, row['name'])
                        metadata = np.asarray([[p[k] for k in METADATA] for p in paths], dtype=np.float64)
                        filename = f'measurement_{j:04d}.npz'
                        np.savez_compressed(folder / filename, signal_sensor=np.stack(sensor), signal_actuator=np.stack(actuator),
                                            path_metadata=metadata, metadata_columns=np.array(METADATA))
                        observations.append({'file': filename, 'cycles': float(c['cycles']), 'load_kips': float(c['load']),
                                             'condition': str(c['condition'])})
                    pd.DataFrame(observations).to_csv(folder / 'measurements.csv', index=False)
                    record = f'r{index:06d}'
                    pd.DataFrame([{'record_id': record, 'cycles': cycle, 'layup': layup}]).to_csv(folder / 'requests.csv', index=False)
                    labels.append({'record_id': record, 'target': target})
                    chunks.append(chunk)
                    last = cycle
                (inputs / 'stream.json').write_text(json.dumps(chunks))
                pd.DataFrame(labels).to_csv(unit / 'labels.csv', index=False)
                kept += 1
    assert kept == 3, kept
