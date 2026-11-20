"""Checking, sealing and re-checking artifacts.

``validate`` applies the delivery rules; ``seal`` copies an artifact, records
the SHA-256 of every file and removes write permission; ``verify`` re-checks a
sealed artifact against its record before every deployment.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from . import spec

RECORD = 'sealed_artifact.json'


class ArtifactError(ValueError):
    """The delivery does not satisfy the artifact specification."""


def validate(directory: Path) -> None:
    directory = Path(directory)
    for path in [p for p in directory.rglob('*') if p.is_symlink()]:
        resolved = path.resolve()
        if not resolved.is_relative_to(directory.resolve()) or not resolved.exists():
            raise ArtifactError(f'交付文件 {path.relative_to(directory)} 的链接指向交付目录之外或不存在的文件。')
    if not (directory / spec.ENTRY).is_file():
        raise ArtifactError('交付根目录缺少 artifact.py。')
    if not (directory / spec.RESOURCES).is_file():
        raise ArtifactError('交付根目录缺少 resources.json。')
    if not isinstance(json.loads((directory / spec.RESOURCES).read_text()), dict):
        raise ArtifactError('resources.json 必须是 JSON 对象。')


def file_manifest(directory: Path) -> list[dict]:
    out = []
    for path in sorted(Path(directory).rglob('*')):
        if path.is_symlink():
            out.append({'path': str(path.relative_to(directory)), 'link': str(path.readlink())})
        elif path.is_file():
            with path.open('rb') as handle:
                out.append({'path': str(path.relative_to(directory)), 'sha256': hashlib.file_digest(handle, 'sha256').hexdigest()})
    return out


def seal(source: Path, destination: Path, *, exclude=spec.WORKSPACE_INPUTS) -> dict:
    """Copy ``source`` to ``destination`` (top-level names in ``exclude`` are left out), check, record, freeze."""
    source, destination = Path(source), Path(destination)
    ignore = lambda d, names: list(exclude.intersection(names)) if Path(d) == source else ['__pycache__']
    shutil.copytree(source, destination, symlinks=True, ignore=ignore)
    validate(destination)
    record = {'created_at_utc': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
              'files': file_manifest(destination)}
    for path in destination.rglob('*'):
        if path.is_file() and not path.is_symlink():
            path.chmod(path.stat().st_mode & ~0o222)
    (destination.parent / RECORD).write_text(json.dumps(record, indent=2) + '\n')
    return record


def verify(directory: Path, record: dict | Path) -> None:
    """Raise unless ``directory`` holds exactly the files recorded at sealing."""
    if not isinstance(record, dict):
        record = json.loads(Path(record).read_text())
    current = [row for row in file_manifest(directory) if '__pycache__' not in Path(row['path']).parts]
    recorded = [row for row in record['files'] if '__pycache__' not in Path(row['path']).parts]
    if current != recorded:
        changed = sorted({r['path'] for r in current} ^ {r['path'] for r in recorded}
                         | {a['path'] for a, b in zip(current, recorded) if a != b})
        raise ArtifactError(f'sealed artifact changed since sealing: {changed[:5]}')
