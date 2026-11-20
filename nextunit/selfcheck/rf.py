"""Self-check layer: retrain the random-forest reference and compare every fold's loss with the shipped values.

The reference predicts single-threaded, so its losses are deterministic; they must equal the ``random_forest`` rows
of ``nextunit/benchmark/reference_scores.csv`` (relative tolerance 1e-12). PUBD16 needs the raw root; without it,
PUBD16 is listed as skipped."""
from __future__ import annotations

import math
import sys
import tempfile
import time
from pathlib import Path

from .. import definition
from ..reference.random_forest.run import NEEDS_RAW, run
from .run import reference

TOLERANCE = 1e-12


def random_forest(prepared, datasets, jobs, raw=None, scratch=None) -> dict:
    expected = reference('random_forest')
    chosen = [d for d in datasets if raw is not None or d not in NEEDS_RAW]
    started = time.monotonic()
    with tempfile.TemporaryDirectory(dir=scratch) as temp:
        rows = run(prepared, chosen, Path(temp), raw, jobs, log=lambda line: print(line, file=sys.stderr, flush=True))
    wrong, worst = [], 0.0
    for r in rows:
        want = float(expected[(r['dataset'], r['fold'])]['E'])
        rel = abs(r['E'] - want) / max(abs(want), 1e-300) if r['E'] != want else 0.0
        worst = max(worst, rel)
        if not math.isclose(r['E'], want, rel_tol=TOLERANCE, abs_tol=0.0):
            wrong.append((r['dataset'], r['fold'], r['E'], want))
    expected_folds = sum(len(definition.folds(d)) for d in chosen)
    return {'layer': 'random-forest reference', 'ok': not wrong and len(rows) == expected_folds, 'folds': len(rows),
            'max_rel_diff': worst, 'wrong': wrong[:5], 'skipped': sorted(set(datasets) - set(chosen)),
            'minutes': round((time.monotonic() - started) / 60, 1)}
