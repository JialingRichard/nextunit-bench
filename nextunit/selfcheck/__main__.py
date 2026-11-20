"""python -m nextunit.selfcheck --prepared PREPARED_ROOT --runtime RUNTIME.json [--raw RAW_ROOT] [--datasets DS ...]
       [--rf [--jobs N]]

Layers: definition files; raw files (with --raw); prepared files and the MIMII_DUE metadata check; constant
predictor scores (exact); the sandboxed evaluator on two folds; with --rf, the random-forest reference (retrains every
fold's forest on --jobs processes; PUBD16 needs --raw)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .. import definition
from . import rf, run


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog='python -m nextunit.selfcheck')
    parser.add_argument('--prepared', type=Path, required=True)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--raw', type=Path)
    parser.add_argument('--datasets', nargs='+', choices=definition.datasets(), default=list(definition.datasets()))
    parser.add_argument('--scratch', type=Path, default=Path('local/scratch'))
    parser.add_argument('--rf', action='store_true', help='also retrain and check the random-forest reference')
    parser.add_argument('--jobs', type=int, default=2, help='processes for --rf (one core each)')
    args = parser.parse_args(argv)
    args.scratch.mkdir(parents=True, exist_ok=True)
    layers = [run.definition_files]
    if args.raw:
        layers.append(lambda: run.raw_files(args.raw, args.datasets))
    layers += [lambda: run.prepared_files(args.prepared, args.datasets),
               lambda: run.constant_scores(args.prepared, args.datasets)]
    smoke = run.smoke_folds(args.datasets)
    layers.append(lambda: run.evaluator_smoke(args.prepared, args.runtime, args.scratch, smoke) if smoke
                  else {'layer': 'sandboxed evaluator', 'ok': False, 'skipped': 'no dataset built'})
    if args.rf:
        layers.append(lambda: rf.random_forest(args.prepared, args.datasets, args.jobs, raw=args.raw, scratch=args.scratch))
    ok = True
    for layer in layers:
        result = layer()
        ok &= result['ok']
        print(json.dumps(result, ensure_ascii=False, default=str), flush=True)
    print(json.dumps({'selfcheck': 'passed' if ok else 'FAILED', 'datasets': len(args.datasets)}))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
