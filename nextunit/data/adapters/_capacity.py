"""Shared by NB1 and CALCE: at valid discharge k, release only observation k and score the capacity at k+10."""
from pathlib import Path

import numpy as np
import pandas as pd

from ..write import json_file

HORIZON = 10


def forecast_unit(out: Path, unit_id: str, observations: list[dict]) -> None:
    inputs = out / unit_id / 'inputs'
    inputs.mkdir(parents=True, exist_ok=True)
    blocks, labels = [], []
    for index, observation in enumerate(observations[:-HORIZON]):
        record_id = f'r{index + 1:04d}'
        block = inputs / record_id
        block.mkdir(exist_ok=True)
        np.savez_compressed(block / 'signals.npz', **observation['signals'])
        pd.DataFrame([{'record_id': record_id, 'observed_cycle': index + 1, 'forecast_horizon': HORIZON}]).to_csv(block / 'query.csv', index=False)
        pd.DataFrame([{'observed_cycle': index + 1, 'measured_capacity_Ah': observation['capacity'],
                       **observation['measurements']}]).to_csv(block / 'observation.csv', index=False)
        labels.append({'record_id': record_id, 'target': observations[index + HORIZON]['capacity']})
        blocks.append(record_id)
    assert blocks
    json_file(inputs / 'stream.json', blocks)
    pd.DataFrame(labels).to_csv(out / unit_id / 'labels.csv', index=False)
