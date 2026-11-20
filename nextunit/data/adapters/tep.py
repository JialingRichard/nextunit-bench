"""Tennessee Eastman process, Rieth et al. 2017 (raw: TEP/TEP_{FaultFree,Faulty}_{Training,Testing}.RData, the four
official Harvard Dataverse files doi:10.7910/DVN/6C3JR1). Needs pyreadr; peak memory about 15 GiB."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ._hashid import SEED, rid

RAW_DIRS = ('TEP',)
SIZES = {'TEP_FaultFree_Testing.RData': 47327663, 'TEP_FaultFree_Training.RData': 24678017,
         'TEP_Faulty_Testing.RData': 836882037, 'TEP_Faulty_Training.RData': 494063194}


def _json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def build(raw: Path, out: Path) -> None:
    import pyreadr
    source = raw / 'TEP'
    selected_runs = sorted(np.random.default_rng(SEED).choice(np.arange(1, 501), size=50, replace=False).tolist())
    for partition in ('Training', 'Testing'):
        for state in ('FaultFree', 'Faulty'):
            path = next(source.rglob(f'TEP_{state}_{partition}.RData'))
            assert path.stat().st_size == SIZES[path.name]
            frames = pyreadr.read_r(str(path))
            frame = next(iter(frames.values()))
            frame = frame.loc[frame.simulationRun.isin(selected_runs)].copy()
            del frames
            signals = [column for column in frame if column.startswith(('xmeas_', 'xmv_'))]
            assert len(signals) == 52
            for (fault, run), values in frame.groupby(['faultNumber', 'simulationRun'], sort=True):
                values = values.sort_values('sample')
                assert np.array_equal(values['sample'].to_numpy(), np.arange(1, (500 if partition == 'Training' else 960) + 1))
                fault, run = int(fault), int(run)
                unit = out / f'{partition.lower()}_f{fault:02d}_r{run:03d}'
                (unit / 'inputs').mkdir(parents=True)
                records = [rid(f'tep:{partition}:{fault}:{run}:{sample}') for sample in values['sample']]
                np.savez_compressed(unit / 'inputs/measurements.npz', values=values[signals].to_numpy(dtype=np.float64),
                                    columns=np.asarray(signals), elapsed_minutes=values['sample'].to_numpy() * 3,
                                    record_ids=np.asarray(records))
                _json(unit / 'inputs/records.json', [{'record_id': record, 'signal_file': 'measurements.npz', 'row': i}
                                                     for i, record in enumerate(records)])
                onset = 20 if partition == 'Training' else 160    # fault introduced after this sample
                targets = np.where(values['sample'].to_numpy() > onset, fault, 0)
                pd.DataFrame(list(zip(records, targets.tolist())), columns=['record_id', 'target']).to_csv(unit / 'labels.csv', index=False)
            del frame
