"""The development view of one fold: what a method developer (or an agent under test) may see.

Layout, as in the paper's runs:
  <out>/task.md, <out>/info.md
  <out>/development/entity_XXXX/inputs/...   and   .../labels.csv
  <out>/development/auxiliary/...            (SCANIA only)
Hidden units, their labels and the benchmark definition are never part of it.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from .. import definition
from ..sandbox.files import place
from .fold import fold_view


def export(dataset: str, fold: int, prepared_root: Path | str, out: Path | str, *, link: bool = False) -> Path:
    """Write the development view. ``link`` hard-links data files (for read-only mounts only); default copies.
    Symbolic links in the prepared root are resolved either way."""
    out = Path(out)
    if out.exists():
        raise FileExistsError(out)
    view = fold_view(dataset, fold, 'development', prepared_root)
    copy = place if link else shutil.copy2
    development = out / 'development'
    development.mkdir(parents=True)
    for public_id in sorted(view.inputs):
        target = development / public_id
        target.mkdir()
        shutil.copytree(view.inputs[public_id], target / 'inputs', copy_function=copy)
        copy(view.labels[public_id], target / 'labels.csv')
    if view.auxiliary is not None:
        shutil.copytree(view.auxiliary, development / 'auxiliary', copy_function=copy)
    shutil.copyfile(definition.task_md(dataset), out / 'task.md')
    shutil.copyfile(definition.info_md(dataset), out / 'info.md')
    return out
