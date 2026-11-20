"""python -m nextunit.reference.random_forest --prepared PREPARED_ROOT [--raw RAW_ROOT] [--datasets DS ...]
       [--jobs N] [--cache DIR] [--out FILE]

Retrains the reference forest of each fold, predicts the hidden units single-threaded and prints one JSON line per
fold with its loss E and its score S against B. --raw is needed for PUBD16. --cache keeps the training caches (default:
a temporary directory, deleted at the end). --out writes the rows as CSV (predictor, dataset, fold, E, S)."""
from __future__ import annotations

import argparse
import csv
import sys
import tempfile
from pathlib import Path

from ... import definition
from ...eval.score import fold_scores
from .run import run


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog='python -m nextunit.reference.random_forest')
    parser.add_argument('--prepared', type=Path, required=True)
    parser.add_argument('--raw', type=Path)
    parser.add_argument('--datasets', nargs='+', choices=definition.datasets(), default=list(definition.datasets()))
    parser.add_argument('--jobs', type=int, default=2)
    parser.add_argument('--cache', type=Path)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args(argv)
    with tempfile.TemporaryDirectory() as temp:
        rows = run(args.prepared, args.datasets, args.cache or Path(temp), args.raw, args.jobs)
    if args.out:
        with open(args.out, 'w', newline='') as handle:
            writer = csv.writer(handle, lineterminator='\n')
            writer.writerow(['predictor', 'dataset', 'fold', 'E', 'S'])
            for r in rows:
                writer.writerow(['random_forest', r['dataset'], r['fold'], repr(r['E']),
                                 repr(fold_scores(r['E'], definition.baseline(r['dataset'], r['fold']), 'completed')[0])])
    return 0


if __name__ == '__main__':
    sys.exit(main())
