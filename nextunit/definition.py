"""Read-only access to the frozen benchmark definition in ``nextunit/benchmark``.

Everything that decides a score (datasets, splits, public unit IDs, metrics,
aggregation, the baseline table, the aggregate sets) is read from these files;
nothing here is computed from data.
"""
from __future__ import annotations

import csv
import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent / 'benchmark'
ROLES = ('development', 'hidden')


@lru_cache(maxsize=None)
def datasets() -> tuple[str, ...]:
    return tuple(sorted(p.name for p in (ROOT / 'tasks').iterdir() if p.is_dir()))


@lru_cache(maxsize=None)
def task(dataset: str) -> dict:
    return json.loads((ROOT / 'tasks' / dataset / 'task.json').read_text(encoding='utf-8'))


def task_md(dataset: str) -> Path:
    return ROOT / 'tasks' / dataset / 'task.md'


def info_md(dataset: str) -> Path:
    return ROOT / 'tasks' / dataset / 'info.md'


@lru_cache(maxsize=None)
def _splits() -> dict[tuple[str, int, str], tuple[str, ...]]:
    out: dict[tuple[str, int, str], list[str]] = {}
    with open(ROOT / 'splits.csv', newline='') as handle:
        for row in csv.DictReader(handle):
            out.setdefault((row['dataset'], int(row['fold']), row['role']), []).append(row['entity_id'])
    return {key: tuple(value) for key, value in out.items()}


def folds(dataset: str) -> list[int]:
    return list(range(1, task(dataset)['n_folds'] + 1))


def all_folds() -> list[tuple[str, int]]:
    return [(dataset, fold) for dataset in datasets() for fold in folds(dataset)]


def units(dataset: str, fold: int, role: str) -> tuple[str, ...]:
    """Unit IDs of one fold and role, in the order the evaluator uses."""
    if role not in ROLES:
        raise ValueError(role)
    return _splits()[(dataset, fold, role)]


@lru_cache(maxsize=None)
def public_ids(dataset: str) -> dict[str, str]:
    """Unit ID -> anonymous directory name shown to agents and predictors."""
    return {entity['id']: entity['public_id'] for entity in task(dataset)['entities']}


@lru_cache(maxsize=None)
def _baseline() -> dict[tuple[str, int], dict]:
    with open(ROOT / 'baseline_B.csv', newline='') as handle:
        return {(row['dataset'], int(row['fold'])): row for row in csv.DictReader(handle)}


def baseline(dataset: str, fold: int) -> float:
    """The frozen baseline loss B of one fold."""
    return float(_baseline()[(dataset, fold)]['B'])


@lru_cache(maxsize=None)
def aggregate_sets() -> dict[str, tuple[str, ...]]:
    """Named dataset sets over which S is averaged: S24 and S_noshortcut."""
    data = json.loads((ROOT / 'aggregates.json').read_text())
    return {name: tuple(names) for name, names in data.items()}
