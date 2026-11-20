"""Command line for the fixed evaluator and scoring.

  python -m nextunit.eval evaluate --artifact DIR --dataset DS --fold K --prepared ROOT --runtime FILE --out DIR
                                   [--sealed-record FILE] [--no-gpu] [--scratch DIR]
  python -m nextunit.eval score RESULTS.csv     # columns dataset,fold,status,E  ->  S per fold, S24, S_noshortcut
  python -m nextunit.eval export-dev --dataset DS --fold K --prepared ROOT --out DIR   # development view only
  python -m nextunit.eval seal SOURCE DESTINATION   # check, copy, record hashes, remove write permission
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from .. import definition
from ..sandbox.bwrap import Runtime
from ..artifact import seal as sealing
from . import devview
from .evaluator import evaluate
from .fold import fold_view
from .score import score_fold, summarize


def _evaluate(args) -> int:
    view = fold_view(args.dataset, args.fold, 'hidden', args.prepared)
    runtime = Runtime.host() if args.runtime == 'host' else Runtime.load(args.runtime)
    result = evaluate(args.artifact, view, args.out, runtime, scratch=args.scratch or Path(args.out) / '.scratch',
                      sealed_record=args.sealed_record, gpu=False if args.no_gpu else None)
    status = result['status']
    fold = score_fold(args.dataset, args.fold, result.get('E'), 'completed' if status == 'completed' else 'failed')
    print(json.dumps({**fold, 'error': result.get('error')}))
    return 0


def _score(args) -> int:
    folds = {}
    with open(args.results, newline='') as handle:
        for row in csv.DictReader(handle):
            status = row['status']
            error = float(row['E']) if status == 'completed' else None
            folds[row['dataset'], int(row['fold'])] = score_fold(row['dataset'], int(row['fold']), error, status)
    missing = sorted(set(definition.all_folds()) - set(folds))
    summary = summarize({key: value['S'] for key, value in folds.items()}) if not missing else None
    print(json.dumps({'folds': list(folds.values()), 'missing_folds': missing,
                      'summary': {k: {x: v[x] for x in ('S', 'ci_low', 'ci_high', 'datasets')} for k, v in summary.items()} if summary else None},
                     indent=1))
    return 0


def _export(args) -> int:
    print(devview.export(args.dataset, args.fold, args.prepared, args.out))
    return 0


def _seal(args) -> int:
    record = sealing.seal(args.source, args.destination)
    print(json.dumps({'sealed': str(args.destination), 'record': str(Path(args.destination).parent / sealing.RECORD),
                      'files': len(record['files'])}))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog='python -m nextunit.eval')
    sub = parser.add_subparsers(dest='command', required=True)
    e = sub.add_parser('evaluate', help='run a sealed artifact on the hidden units of one fold')
    e.add_argument('--artifact', type=Path, required=True)
    e.add_argument('--dataset', required=True, choices=definition.datasets())
    e.add_argument('--fold', type=int, required=True)
    e.add_argument('--prepared', type=Path, required=True)
    e.add_argument('--runtime', required=True, help="runtime file, or 'host' for tests")
    e.add_argument('--out', type=Path, required=True)
    e.add_argument('--sealed-record', type=Path)
    e.add_argument('--scratch', type=Path)
    e.add_argument('--no-gpu', action='store_true')
    s = sub.add_parser('score', help='S per fold and the aggregates from a table of fold losses')
    s.add_argument('results', type=Path)
    x = sub.add_parser('export-dev', help='write the development view of one fold')
    x.add_argument('--dataset', required=True, choices=definition.datasets())
    x.add_argument('--fold', type=int, required=True)
    x.add_argument('--prepared', type=Path, required=True)
    x.add_argument('--out', type=Path, required=True)
    z = sub.add_parser('seal', help='seal an artifact directory')
    z.add_argument('source', type=Path)
    z.add_argument('destination', type=Path)
    args = parser.parse_args(argv)
    return {'evaluate': _evaluate, 'score': _score, 'export-dev': _export, 'seal': _seal}[args.command](args)


if __name__ == '__main__':
    sys.exit(main())
