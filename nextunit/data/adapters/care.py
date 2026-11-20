"""CARE to Compare wind-turbine events (raw: CARE/CARE_To_Compare.zip, the official Zenodo 15846963 archive, read in place).

One unit per wind-turbine asset; one record per event (an observation window and its preceding history).
v1.0 note (KNOWN_ISSUES C4): the files differ byte-wise from the paper's, whose zip headers carried the
writing history; every array is identical, and CARE is verified per array (checksums/prepared/CARE.arrays.json)."""
import csv
import hashlib
import io
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

RAW_DIRS = ('CARE',)
FEATURES = {'A': 81, 'B': 252, 'C': 952}
EXCLUDED = {'time_stamp', 'asset_id', 'id', 'train_test', 'status_type_id'}


def build(raw: Path, out: Path) -> None:
    with zipfile.ZipFile(raw / 'CARE/CARE_To_Compare.zip') as z:
        events = []
        for farm in 'ABC':
            with z.open(f'CARE_To_Compare/Wind Farm {farm}/event_info.csv') as handle:
                for row in csv.DictReader(io.TextIOWrapper(handle, encoding='utf-8'), delimiter=';'):
                    row['farm'] = farm
                    row['entity'] = farm + '_' + row.get('asset_id', row.get('asset'))
                    events.append(row)
        ordered = sorted(events, key=lambda r: hashlib.sha256(f"20261002|CARE|event|{r['farm']}|{r['event_id']}".encode()).digest())
        for i, row in enumerate(ordered):
            row['record_id'] = f'r{i + 1:04d}'
        for row in events:
            inputs = out / row['entity'] / 'inputs'
            inputs.mkdir(parents=True, exist_ok=True)
            with z.open(f"CARE_To_Compare/Wind Farm {row['farm']}/datasets/{row['event_id']}.csv") as handle:
                frame = pd.read_csv(handle, sep=';', float_precision='round_trip')
            history = (frame.train_test == 'train').to_numpy()
            observation = ~history
            stamps = pd.to_datetime(frame.time_stamp)
            assert stamps.is_monotonic_increasing and stamps.is_unique and stamps[history].max() < stamps[observation].min()
            seconds = (stamps - stamps.iloc[0]).dt.total_seconds().to_numpy(dtype='float64')
            features = [c for c in frame if c not in EXCLUDED]
            assert len(features) == FEATURES[row['farm']]
            values = frame[features].to_numpy(dtype='float64')
            payload = {'history_values': values[history], 'observation_values': values[observation],
                       'history_time_seconds': seconds[history], 'observation_time_seconds': seconds[observation],
                       'feature_names': np.array(features), 'site_id': np.array('site_' + str('ABC'.index(row['farm']) + 1))}
            # Day of year of every reading; the anonymised years are not passed on.
            start = pd.Timestamp(str(frame.time_stamp.iloc[0]))
            for part in ('history', 'observation'):
                times = start + pd.to_timedelta(payload[part + '_time_seconds'], unit='s')
                payload[part + '_day_of_year'] = times.dayofyear.to_numpy(dtype=np.int16)
            np.savez_compressed(inputs / f"{row['record_id']}.npz", **payload)
        for entity in sorted({r['entity'] for r in events}):
            rows = [r for r in events if r['entity'] == entity]
            pd.DataFrame([{'record_id': r['record_id'], 'file': r['record_id'] + '.npz'} for r in rows]) \
                .to_csv(out / entity / 'inputs/records.csv', index=False)
            pd.DataFrame([{'record_id': r['record_id'], 'target': int(r['event_label'] == 'anomaly')} for r in rows]) \
                .to_csv(out / entity / 'labels.csv', index=False)
    assert len(events) == 95
