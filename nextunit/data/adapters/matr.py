"""Severson et al. 2019 battery cycle life (raw: FCLB19/data/ from the PHMD archive FCLB19.zip)."""
from pathlib import Path

import numpy as np
import pandas as pd

from ..write import json_file

RAW_DIRS = ('FCLB19',)
FILES = ['2017-05-12_batchdata_updated_struct_errorcorrect.mat', '2017-06-30_batchdata_updated_struct_errorcorrect.mat',
         '2018-04-12_batchdata_updated_struct_errorcorrect.mat']
# As in the authors' "Load Data.ipynb": cells dropped per batch, and batch-2 continuations of batch-1 cells.
EXCLUDED = {1: {8, 10, 12, 13, 22}, 2: {7, 8, 9, 15, 16}, 3: {2, 23, 32, 37, 42, 43}}
CONTINUATIONS = {0: (7, 662), 1: (8, 981), 2: (9, 1060), 3: (15, 208), 4: (16, 482)}


def build(raw: Path, out: Path) -> None:
    import h5py
    count = 0
    for batch_number, filename in enumerate(FILES, start=1):
        with h5py.File(raw / 'FCLB19/data' / filename, 'r') as source:
            batch = source['batch']
            for index in range(batch['summary'].shape[0]):
                if index in EXCLUDED[batch_number]:
                    continue
                unit = out / f'b{batch_number}c{index}'
                inputs = unit / 'inputs'
                inputs.mkdir(parents=True, exist_ok=True)
                lifetime = float(source[batch['cycle_life'][index, 0]][()].item())
                if batch_number == 1 and index in CONTINUATIONS:
                    lifetime += CONTINUATIONS[index][1]
                summary = source[batch['summary'][index, 0]]
                prefix = {name: summary[name][()].reshape(-1)[:100] for name in summary}
                assert len(prefix['cycle']) == 100 and lifetime > 100
                pd.DataFrame(prefix).to_csv(inputs / 'summary.csv', index=False)
                policy = source[batch['policy_readable'][index, 0]][()].tobytes()[::2].decode().replace('-newstructure', '')
                json_file(inputs / 'conditions.json', {'charge_policy': policy, 'nominal_capacity_Ah': 1.1,
                                                       'chamber_temperature_C': 30, 'discharge_rate_C': 4})
                cycles = source[batch['cycles'][index, 0]]
                arrays = {}
                for cycle in range(100):
                    for channel in cycles:
                        arrays[f'cycle_{cycle + 1:03d}_{channel}'] = source[cycles[channel][cycle, 0]][()].reshape(-1).astype(np.float32)
                np.savez_compressed(inputs / 'cycles.npz', **arrays)
                pd.DataFrame([{'record_id': 'r0001', 'observed_cycles': 100}]).to_csv(inputs / 'query.csv', index=False)
                pd.DataFrame([{'record_id': 'r0001', 'target': lifetime}]).to_csv(unit / 'labels.csv', index=False)
                count += 1
    assert count == 124
