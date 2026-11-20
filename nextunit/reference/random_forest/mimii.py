"""MIMII_DUE: the RF half of B is an IsolationForest per machine type and product group (development data are normal
recordings only). Input: three unchanged 256-sample pieces (beginning, middle, end) of each mono PCM file; one model
per development unit (200 trees, max_samples=256, max_features=1.0, random_state=20260925); a hidden unit is scored
by the model of its group; prediction = -score_samples (larger = more anomalous)."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sklearn.ensemble import IsolationForest

from ... import definition
from ...data import layout
from .model import SEED

SEGMENT = 256


def waveforms(inputs: Path) -> tuple[list[str], tuple[str, str], np.ndarray]:
    import soundfile as sf
    records = json.loads((inputs / 'records.json').read_text())
    values = np.zeros((len(records), 3 * SEGMENT), dtype=np.float32)
    for i, row in enumerate(records):
        with sf.SoundFile(inputs / row['signal_file']) as f:
            assert f.channels == 1
            for slot, start in enumerate((0, max(0, (len(f) - SEGMENT) // 2), max(0, len(f) - SEGMENT))):
                f.seek(start)
                part = f.read(SEGMENT, dtype='float32')
                values[i, slot * SEGMENT:slot * SEGMENT + len(part)] = part
    groups = {(r['machine_type'], r['product_group']) for r in records}
    assert len(groups) == 1
    return [r['record_id'] for r in records], groups.pop(), values


def fit(prepared: Path | str, fold: int, jobs: int = 1) -> dict:
    models = {}
    for unit in definition.units('MIMII_DUE', fold, 'development'):
        _, group, x = waveforms(layout.inputs_dir(prepared, 'MIMII_DUE', unit))
        assert group not in models
        models[group] = IsolationForest(n_estimators=200, max_samples=256, max_features=1.0, contamination='auto',
                                         n_jobs=jobs, random_state=SEED).fit(x).set_params(n_jobs=1)
    return models


def predict(models: dict, inputs: Path) -> tuple[list[str], np.ndarray]:
    ids, group, x = waveforms(inputs)
    return ids, -models[group].score_samples(x)
