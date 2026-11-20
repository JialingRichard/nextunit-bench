"""NASA battery ageing, B0005-B0056 (raw: NB1/data/ from the PHMD archive NB1.zip)."""
from pathlib import Path

import numpy as np

from ._capacity import HORIZON, forecast_unit

RAW_DIRS = ('NB1',)
CHANNELS = {'Time': 'time_s', 'Voltage_measured': 'voltage_V', 'Current_measured': 'current_A',
            'Temperature_measured': 'temperature_C', 'Current_load': 'load_current_A', 'Voltage_load': 'load_voltage_V'}


def build(raw: Path, out: Path) -> None:
    from scipy.io import loadmat
    for path in sorted((raw / 'NB1/data').glob('*.mat')):
        rows = loadmat(path, simplify_cells=True)[path.stem]['cycle']
        observations = []
        for row in rows:
            if row['type'] != 'discharge':
                continue
            data = row['data']
            capacity = np.asarray(data.get('Capacity', []))
            if capacity.size != 1 or not np.isfinite(capacity.item()) or capacity.item() <= 0:
                continue
            signals = {target: np.asarray(data[source], dtype=np.float32).reshape(-1) for source, target in CHANNELS.items()}
            assert len({len(v) for v in signals.values()}) == 1
            observations.append({'capacity': float(capacity.item()), 'signals': signals,
                                 'measurements': {'ambient_temperature_C': float(row['ambient_temperature'])}})
        if len(observations) <= HORIZON:   # B0052: too few valid capacity measurements
            continue
        forecast_unit(out, path.stem, observations)
