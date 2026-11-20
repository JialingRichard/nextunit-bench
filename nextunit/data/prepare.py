"""Build one dataset's prepared data from its raw files, and verify prepared data against the shipped checksums."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from .. import definition
from . import write
from .adapters import adapter

CHECKSUMS = definition.ROOT / 'checksums' / 'prepared'


def array_digests(path: Path) -> list[list]:
    """Per array of an .npz file, in member order: name, dtype, shape, SHA-256 of its C-order bytes."""
    import numpy as np
    out = []
    with np.load(path, allow_pickle=False) as arrays:
        for name in arrays.files:
            value = np.ascontiguousarray(arrays[name])
            out.append([name, value.dtype.str, list(value.shape), hashlib.sha256(value.tobytes()).hexdigest()])
    return out


def expected_arrays(dataset: str) -> dict[str, list]:
    """Files verified by array content instead of bytes (CARE only): relative path -> array digests."""
    path = CHECKSUMS / f'{dataset}.arrays.json'
    return json.loads(path.read_text()) if path.exists() else {}


def expected(dataset: str) -> dict[str, str]:
    """Relative path -> SHA-256 for every prepared file of a dataset."""
    out = {}
    for line in (CHECKSUMS / f'{dataset}.sha256').read_text().splitlines():
        digest, path = line.split('  ', 1)
        out[path] = digest
    return out


def build(dataset: str, raw_root: Path | str, prepared_root: Path | str, *, link_raw: bool = True) -> Path:
    """Write ``prepared_root/<dataset>``; the directory appears only once the converter has finished.
    ``link_raw``: files that are passed through unchanged are hard-linked to the raw copy (saves disk)."""
    prepared_root = Path(prepared_root)
    target = prepared_root / dataset
    if target.exists():
        raise FileExistsError(target)
    partial = prepared_root / f'.{dataset}.partial'
    if partial.exists():
        shutil.rmtree(partial)
    partial.mkdir(parents=True)
    write.LINK_RAW = link_raw
    adapter(dataset).build(Path(raw_root), partial)
    partial.rename(target)
    return target


def _files(base: Path) -> list[str]:
    """Relative paths of all files under base, following symbolic links (a prepared root may link to data elsewhere)."""
    out = []
    for directory, _, files in os.walk(base, followlinks=True):
        out += [(Path(directory) / f).relative_to(base).as_posix() for f in files]
    return out


def _sha256(path: Path) -> str:
    with open(path, 'rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def verify(dataset: str, prepared_root: Path | str, workers: int = 4) -> dict:
    """Compare ``prepared_root/<dataset>`` with the checksum list: missing, unexpected and differing files."""
    base = Path(prepared_root) / dataset
    want = expected(dataset)
    arrays = expected_arrays(dataset)
    have = sorted(_files(base))
    missing = sorted((set(want) | set(arrays)) - set(have))
    unexpected = sorted(set(have) - set(want) - set(arrays))
    common = sorted(set(want) & set(have))
    by_array = sorted(set(arrays) & set(have))
    with ProcessPoolExecutor(workers) as pool:
        digests = list(pool.map(_sha256, [base / p for p in common], chunksize=64))
        content = list(pool.map(array_digests, [base / p for p in by_array], chunksize=4))
    differing = [p for p, d in zip(common, digests) if d != want[p]]
    differing += [p for p, d in zip(by_array, content) if d != arrays[p]]
    return {'dataset': dataset, 'expected': len(want) + len(arrays), 'found': len(have), 'missing': missing,
            'unexpected': unexpected, 'differing': differing,
            'ok': not (missing or unexpected or differing)}


def metadata_check(dataset: str, prepared_root: Path | str) -> dict:
    """Do file timestamps or creation order (inode numbers) separate the classes within a unit?

    Reports, per unit with two classes, the ROC-AUC of the label against modification time and against inode
    number of each record's input file; 0.5 means no information, 0 or 1 a perfect separation. Used for
    MIMII_DUE (KNOWN_ISSUES C1), whose release fix makes every timestamp equal."""
    import pandas as pd
    from sklearn.metrics import roc_auc_score
    base = Path(prepared_root) / dataset
    units = []
    for unit in sorted(p for p in base.iterdir() if p.is_dir()):
        labels = pd.read_csv(unit / 'labels.csv', dtype={'record_id': str})
        if labels.target.nunique() < 2:
            continue
        records = {r['record_id']: r for r in json.loads((unit / 'inputs/records.json').read_text())}
        stats = [(unit / 'inputs' / records[rid]['signal_file']).stat() for rid in labels.record_id]
        mtimes = [s.st_mtime_ns for s in stats]
        units.append({'unit': unit.name, 'distinct_mtimes': len(set(mtimes)),
                      'auc_mtime': float(roc_auc_score(labels.target, mtimes)) if len(set(mtimes)) > 1 else 0.5,
                      'auc_inode': float(roc_auc_score(labels.target, [s.st_ino for s in stats]))})
    worst = max((abs(u['auc_inode'] - 0.5) for u in units), default=0.0)
    return {'dataset': dataset, 'units': len(units), 'all_mtimes_equal': all(u['distinct_mtimes'] == 1 for u in units),
            'max_inode_auc_distance_from_half': worst, 'per_unit': units}
