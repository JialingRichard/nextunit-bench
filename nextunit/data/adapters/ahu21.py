"""AHU fault detection, six air-handling units (raw: AHU21/data/AHU*.xlsx from the PHMD archive AHU21.zip, the
official Mendeley Data files)."""
import csv
import io
from pathlib import Path

import numpy as np
import pandas as pd

RAW_DIRS = ('AHU21',)


def build(raw: Path, out: Path) -> None:
    for path in sorted((raw / 'AHU21/data').glob('AHU*.xlsx')):
        frame = pd.read_excel(path)
        ids = np.arange(len(frame)).astype(str)
        signals = frame.drop(columns=['fault', 'equipment'])
        signals.insert(0, 'record_id', ids)
        # Two passes, as in the paper's pipeline: pandas writes the readings, csv.writer renames the records (CRLF).
        staged = signals.to_csv(index=False)
        unit = out / path.stem
        (unit / 'inputs').mkdir(parents=True)
        mapping = {}
        with (unit / 'inputs/signals.csv').open('w', newline='') as handle:
            reader, writer = csv.reader(io.StringIO(staged, newline='')), csv.writer(handle)
            columns = next(reader)
            key = columns.index('record_id')
            writer.writerow(columns)
            for i, row in enumerate(reader):
                mapping[row[key]] = f'm{i + 1:06d}'
                row[key] = mapping[row[key]]
                writer.writerow(row)
        labels = pd.DataFrame({'record_id': ids, 'target': (frame['fault'] != 'no fault').astype(int)}).to_csv(index=False)
        labels = pd.read_csv(io.StringIO(labels), dtype={'record_id': str}, float_precision='round_trip')
        labels.record_id = labels.record_id.map(mapping)
        labels.to_csv(unit / 'labels.csv', index=False)
