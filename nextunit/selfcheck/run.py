"""The self-check, layer by layer. Each layer returns {'layer', 'ok', ...}; nothing is repaired."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
import tempfile
from pathlib import Path

from .. import definition
from ..artifact import seal
from ..data import download, prepare
from ..eval.evaluator import evaluate
from ..eval.fold import fold_view
from ..eval.score import summarize
from ..sandbox.bwrap import Runtime
from .constant import constant, score_fold

ARTIFACT = Path(__file__).resolve().parent / 'constant_artifact'
SMOKE_FOLDS = [('HSF15', 1), ('NCMAPSS', 1)]       # one batch task, one stream task with the manifest layout


def smoke_folds(datasets) -> list[tuple[str, int]]:
    """The default smoke folds if built; otherwise fold 1 of the first batch and the first stream dataset built."""
    chosen = [f for f in SMOKE_FOLDS if f[0] in datasets]
    for mode in ('batch', 'stream'):
        if not any(definition.task(d)['mode'] == mode for d, _ in chosen):
            first = next((d for d in sorted(datasets) if definition.task(d)['mode'] == mode), None)
            if first:
                chosen.append((first, 1))
    return chosen


def reference(predictor: str) -> dict[tuple[str, int], dict]:
    with open(definition.ROOT / 'reference_scores.csv', newline='') as handle:
        return {(r['dataset'], int(r['fold'])): r for r in csv.DictReader(handle) if r['predictor'] == predictor}


def definition_files() -> dict:
    bad = []
    for line in (definition.ROOT / 'MANIFEST.sha256').read_text().splitlines():
        digest, rel = line.split('  ', 1)
        path = definition.ROOT / rel
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            bad.append(rel)
    return {'layer': 'definition files', 'ok': not bad, 'changed': bad}


def raw_files(raw: Path, datasets) -> dict:
    results = [download.verify_raw(d, raw) for d in datasets]
    return {'layer': 'raw files', 'ok': all(r['ok'] for r in results),
            'failed': {r['dataset']: (r['missing'][:3], r['differing'][:3]) for r in results if not r['ok']}}


def prepared_files(prepared: Path, datasets) -> dict:
    results = [prepare.verify(d, prepared) for d in datasets]
    meta = prepare.metadata_check('MIMII_DUE', prepared) if 'MIMII_DUE' in datasets else None
    ok = all(r['ok'] for r in results) and (meta is None or meta['all_mtimes_equal'])
    return {'layer': 'prepared files', 'ok': ok,
            'failed': {r['dataset']: {k: r[k][:3] for k in ('missing', 'unexpected', 'differing')} for r in results if not r['ok']},
            'mimii_metadata': None if meta is None else {k: meta[k] for k in ('units', 'all_mtimes_equal', 'max_inode_auc_distance_from_half')}}


def constant_scores(prepared: Path, datasets) -> dict:
    expected = reference('constant')
    rows, wrong = {}, []
    for dataset, fold in definition.all_folds():
        if dataset not in datasets:
            continue
        E = score_fold(dataset, fold, prepared)['E']
        rows[(dataset, fold)] = E
        want = float(expected[(dataset, fold)]['E'])
        if not math.isclose(E, want, rel_tol=1e-12, abs_tol=1e-15):
            wrong.append((dataset, fold, E, want))
    out = {'layer': 'constant predictor', 'ok': not wrong, 'folds': len(rows), 'wrong': wrong[:5]}
    if len(rows) == 58:
        s = summarize({k: float(expected[k]['S']) for k in rows})
        out['S24'], out['S_noshortcut'] = round(s['S24']['S'], 4), round(s['S_noshortcut']['S'], 4)
    return out


def evaluator_smoke(prepared: Path, runtime: Path, scratch: Path, folds=SMOKE_FOLDS) -> dict:
    """The constant predictor as a sealed artifact through the sandboxed evaluator; E must equal the direct score."""
    results = []
    run = Runtime.load(runtime)
    with tempfile.TemporaryDirectory(dir=scratch) as temp:
        temp = Path(temp)
        for dataset, fold in folds:
            source = temp / f'{dataset}_{fold}/artifact'
            shutil.copytree(ARTIFACT, source)
            (source / 'resources.json').write_text(json.dumps({'constant': constant(dataset, fold, prepared)}))
            sealed = temp / f'{dataset}_{fold}/sealed/artifact'
            sealed.parent.mkdir()
            record = seal.seal(source, sealed)
            result = evaluate(sealed, fold_view(dataset, fold, 'hidden', prepared), temp / f'{dataset}_{fold}/out', run,
                              scratch=temp / 'scratch', sealed_record=record, gpu=False)
            want = score_fold(dataset, fold, prepared)['E']
            results.append({'dataset': dataset, 'fold': fold, 'status': result['status'], 'error': result.get('error'),
                            'E': result.get('E'), 'match': result.get('E') is not None and math.isclose(result['E'], want, rel_tol=1e-12)})
    return {'layer': 'sandboxed evaluator', 'ok': all(r['match'] for r in results), 'folds': results}
