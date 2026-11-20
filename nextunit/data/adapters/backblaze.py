"""Backblaze drive stats, 2024 Q4 (raw: BACKBLAZE/data_Q4_2024/2024-*.csv from the official data_Q4_2024.zip).

About 10% of disks, chosen by a hash of the serial number before any failure is seen; development days 0-45
(1 Oct - 15 Nov), hidden days 61-84 (1-24 Dec); target: failure flagged within the next seven days."""
import hashlib
import json
from pathlib import Path

import pandas as pd

from ._hashid import SEED, rid

RAW_DIRS = ('BACKBLAZE',)


def _json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def build(raw: Path, out: Path) -> None:
    files = sorted(path for path in (raw / 'BACKBLAZE').rglob('2024-*.csv') if '__MACOSX' not in str(path))
    assert len(files) == 92
    buckets, selected, observed_last, failure_day = {}, {}, {}, {}
    origin = pd.Timestamp('2024-10-01')
    for path in files:
        frame = pd.read_csv(path, usecols=['serial_number', 'failure'])
        for serial in set(frame.serial_number) - buckets.keys():
            number = int(hashlib.sha256(f'{SEED}:disk:{serial}'.encode()).hexdigest(), 16)
            buckets[serial] = (number // 10) % 3 if number % 10 == 0 else -1
        frame = frame.loc[frame.serial_number.map(buckets) >= 0]
        day = int((pd.Timestamp(path.stem) - origin).days)
        for serial, failed in frame[['serial_number', 'failure']].itertuples(index=False, name=None):
            selected[serial] = buckets[serial]
            observed_last[serial] = day
            if int(failed) == 1:
                failure_day.setdefault(serial, day)
    disk_ids = {serial: rid(f'disk:{serial}') for serial in selected}
    labels, chunks = {}, {}
    for partition in ('development', 'hidden'):
        for bucket in range(3):
            unit = f'{partition}_cohort_{bucket}'
            (out / unit / 'inputs').mkdir(parents=True)
            labels[unit], chunks[unit] = [], []
    for path in files:
        day = int((pd.Timestamp(path.stem) - origin).days)
        partition = 'development' if day <= 45 else 'hidden' if 61 <= day <= 84 else None
        if partition is None:
            continue
        frame = pd.read_csv(path, dtype=str, keep_default_na=False)
        frame = frame.loc[frame.serial_number.map(buckets) >= 0].copy()
        labels_by_serial, eligible = {}, []
        for serial, failure in zip(frame.serial_number, frame.failure):
            if failure == '1' or failure_day.get(serial, 10**9) <= day:
                continue                                   # failure day or later
            event = failure_day.get(serial, 10**9)
            positive = day < event <= day + 7
            if positive or observed_last[serial] >= day + 7:
                eligible.append(serial)
                labels_by_serial[serial] = int(positive)   # otherwise censored: followed up for less than 7 days
        frame = frame.loc[frame.serial_number.isin(eligible)].copy()
        for bucket in range(3):
            unit = f'{partition}_cohort_{bucket}'
            current = frame.loc[frame.serial_number.map(buckets) == bucket].copy()
            current = current.sort_values('serial_number', key=lambda values: values.map(disk_ids))
            if current.empty:
                continue
            serials = current.serial_number.tolist()
            records = [rid(f'backblaze:{serial}:{day}') for serial in serials]
            current = current.drop(columns=['date', 'serial_number', 'failure'])
            current.insert(0, 'elapsed_day', day)
            current.insert(0, 'disk_id', [disk_ids[serial] for serial in serials])
            current.insert(0, 'record_id', records)
            for column in ('datacenter', 'cluster_id', 'vault_id', 'pod_id'):
                if column in current:
                    current[column] = current[column].map(lambda value: rid(f'{column}:{value}') if value else '')
            chunk = f'chunk_{len(chunks[unit]):06d}'
            target = out / unit / 'inputs' / chunk
            target.mkdir()
            current.to_csv(target / 'measurements.csv', index=False)
            _json(target / 'records.json', [{'record_id': record, 'signal_file': 'measurements.csv', 'row': i}
                                            for i, record in enumerate(records)])
            labels[unit].extend(zip(records, [labels_by_serial[s] for s in serials]))
            chunks[unit].append(chunk)
    for unit in labels:
        _json(out / unit / 'inputs/stream.json', chunks[unit])
        assert {value for _, value in labels[unit]} == {0, 1}
        pd.DataFrame(labels[unit], columns=['record_id', 'target']).to_csv(out / unit / 'labels.csv', index=False)
