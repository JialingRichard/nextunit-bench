"""Constant predictor as an artifact: predicts VALUE (from resources.json) for every requested record.
Used by the self-check to exercise the sandboxed evaluator end to end."""
import csv
import json
from pathlib import Path

VALUE = json.loads((Path(__file__).parent / 'resources.json').read_text())['constant']
INDEXES = ('query.csv', 'requests.csv', 'records.csv', 'signals.csv', 'features.csv')


def _ids(directory: Path) -> list[str]:
    for name in INDEXES:
        path = directory / name
        if path.is_file():
            with path.open(newline='') as handle:
                reader = csv.DictReader(handle)
                if 'record_id' in (reader.fieldnames or []):
                    return [row['record_id'] for row in reader]
    path = directory / 'records.json'
    return [str(row['record_id']) for row in json.loads(path.read_text())]


def predict(input_directory, output_file):
    directory = Path(input_directory)
    manifest = directory / 'stream.json'
    if manifest.is_file() and not any((directory / n).is_file() for n in INDEXES + ('records.json',)):
        directory = directory / json.loads(manifest.read_text())[0]
    with open(output_file, 'w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['record_id', 'prediction'])
        writer.writerows([rid, VALUE] for rid in _ids(directory))
