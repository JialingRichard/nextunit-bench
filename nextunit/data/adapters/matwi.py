"""MATWI tool wear, Sets 1-17 (raw: MATWI/Set*/{images,sensordata}/ from the official Set*.zip archives, and
MATWI/labels.csv, the official label table)."""
import csv
import io
from pathlib import Path

import pandas as pd

from ..write import same_file

RAW_DIRS = ('MATWI',)


def build(raw: Path, out: Path) -> None:
    rows = {}
    with (raw / 'MATWI/labels.csv').open() as handle:
        for row in csv.DictReader(handle):
            if row['wear'] and row['ImageFile'] and row['SensorFile']:
                rows.setdefault(f"Set{row['Set']}", []).append(row)
    for name in sorted(rows):
        unit = out / name
        records, labels = [], []
        for i, row in enumerate(rows[name]):
            record_id = f'm{i + 1:06d}'
            record = {'record_id': record_id, 'image_path': f'image/{record_id}.jpg', 'sensor_path': f'sensor/{record_id}.csv'}
            for field, target in (('ImageFile', record['image_path']), ('SensorFile', record['sensor_path'])):
                same_file(raw / row[field], unit / 'inputs' / target)     # ImageFile/SensorFile start with "MATWI/"
            records.append(record)
            labels.append({'record_id': record_id, 'target': float(row['wear'])})
        pd.DataFrame(records).to_csv(unit / 'inputs/records.csv', index=False)
        staged = pd.read_csv(io.StringIO(pd.DataFrame(labels).to_csv(index=False)), dtype={'record_id': str}, float_precision='round_trip')
        staged.to_csv(unit / 'labels.csv', index=False)
