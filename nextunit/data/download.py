"""Fetch raw files as listed in sources.json and lay them out under the raw root.

Each dataset lists routes in order of preference: the official source first where it was verified, then a documented
mirror. A route is a list of files; each file is downloaded (resuming, checked against its recorded size and hash
when one is recorded) and then

  place    copied to <raw>/<to> as it is;
  unpack   unpacked (zip or tar) into <raw>/<to>;
  extract  selected members copied out, following rules that may descend into archives inside the archive:
           {"from": [inner archive, ...], "member": path | "prefix": dir/ [, "pattern": glob] | "pattern": glob, "to": target}.

A route marked "manual" holds instructions for steps that need a browser or external tools. Whatever the route, the
result is accepted only if every raw file the converter reads matches checksums/raw/<DATASET>.sha256 (``verify_raw``)."""
from __future__ import annotations

import fnmatch
import hashlib
import json
import shutil
import sys
import tarfile
import time
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from .. import definition

SOURCES = Path(__file__).resolve().parent / 'sources.json'
RAW_CHECKSUMS = definition.ROOT / 'checksums' / 'raw'
USER_AGENT = 'nextunit-bench-downloader/1.0'
CHUNK = 1 << 22


class DownloadError(RuntimeError):
    pass


def sources() -> dict:
    return json.loads(SOURCES.read_text(encoding='utf-8'))


def _digests(path: Path) -> dict[str, str]:
    md5, sha = hashlib.md5(), hashlib.sha256()
    with open(path, 'rb') as handle:
        for block in iter(lambda: handle.read(CHUNK), b''):
            md5.update(block)
            sha.update(block)
    return {'md5': md5.hexdigest(), 'sha256': sha.hexdigest()}


def check(path: Path, spec: dict) -> bool:
    if not path.is_file() or ('bytes' in spec and path.stat().st_size != spec['bytes']):
        return False
    if not any(k in spec for k in ('md5', 'sha256')):
        return True
    found = _digests(path)
    return all(found[k] == spec[k] for k in ('md5', 'sha256') if k in spec)


def _copy_with_progress(source, out, name: str, total: int | None, every: float = 30.0) -> None:
    """Copy a response body, printing size and rate to stderr every ``every`` seconds (slow servers look stalled)."""
    begin = last = time.monotonic()
    start, done = out.tell(), 0
    while block := source.read(CHUNK):
        out.write(block)
        done += len(block)
        now = time.monotonic()
        if now - last >= every:
            last = now
            have = start + done
            share = f' of {total / 1e6:.1f} MB ({100 * have / total:.0f}%)' if total else ''
            print(f'{name}: {have / 1e6:.1f} MB{share}, {done / 1e3 / (now - begin):.0f} kB/s', file=sys.stderr, flush=True)


def fetch(url: str, target: Path, spec: dict, retries: int = 5) -> Path:
    """Download with resume into ``target``; refuse a file whose size or recorded hash differs."""
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and check(target, spec):
        return target
    part = target.with_name(target.name + '.part')
    for _ in range(retries):
        start = part.stat().st_size if part.exists() else 0
        headers = {'User-Agent': USER_AGENT, **({'Range': f'bytes={start}-'} if start else {})}
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=120) as response:
                with open(part, 'ab' if response.status == 206 else 'wb') as out:
                    _copy_with_progress(response, out, target.name, spec.get('bytes'))
        except OSError:
            continue
        if 'bytes' not in spec or part.stat().st_size >= spec['bytes']:
            break
    if not check(part, spec):
        raise DownloadError(f'{target.name}: size or hash differs from the recorded value; not accepted')
    part.rename(target)
    return target


def _copy_member(z: zipfile.ZipFile, member: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with z.open(member) as source, open(target, 'wb') as out:
        shutil.copyfileobj(source, out, CHUNK)


def _unpack(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as z:
            for member in z.namelist():
                if member.endswith('/'):
                    continue
                target = destination / member
                assert target.resolve().is_relative_to(destination.resolve()), member
                _copy_member(z, member, target)
        return
    if tarfile.is_tarfile(archive):
        with tarfile.open(archive) as t:
            t.extractall(destination, filter='data')
        return
    raise DownloadError(f'{archive.name}: not a zip or tar archive')


def _extract(archive: Path, raw: Path, rules: list[dict], scratch: Path) -> None:
    opened: dict[tuple, zipfile.ZipFile] = {(): zipfile.ZipFile(archive)}
    try:
        for rule in rules:
            path: tuple = ()
            for inner in rule['from']:          # descend into archives within the archive, via temporary copies
                key = path + (inner,)
                if key not in opened:
                    copy = scratch / f'inner_{len(opened)}.zip'
                    _copy_member(opened[path], inner, copy)
                    opened[key] = zipfile.ZipFile(copy)
                path = key
            z = opened[path]
            if 'member' in rule:
                _copy_member(z, rule['member'], raw / rule['to'])
                continue
            prefix, pattern = rule.get('prefix', ''), rule.get('pattern')
            hits = [m for m in z.namelist() if m.startswith(prefix) and not m.endswith('/')
                    and (pattern is None or fnmatch.fnmatch(m[len(prefix):] if prefix else m, pattern))]
            if not hits:
                raise DownloadError(f'{archive.name}: no member matches {rule}')
            for member in hits:
                target = raw / rule['to'] if (pattern and not prefix and len(hits) == 1 and not rule['to'].endswith('/')) \
                    else raw / rule['to'] / member[len(prefix):]
                _copy_member(z, member, target)
    finally:
        for z in opened.values():
            z.close()


def acquire(dataset: str, raw: Path, downloads: Path, route_name: str | None = None) -> str:
    """Run the first route that works (or the named one). Returns the route name; raises with instructions otherwise."""
    raw, downloads = Path(raw), Path(downloads)
    problems = []
    for route in sources()[dataset]['routes']:
        if route_name and route['name'] != route_name:
            continue
        if route.get('manual'):
            problems.append(f"{route['name']} (manual): {route['instructions']}")
            if route_name:
                break
            continue
        try:
            with tempfile.TemporaryDirectory(dir=downloads.parent if downloads.exists() else None) as scratch:
                for item in route['files']:
                    archive = fetch(item['url'], downloads / dataset / item['name'], item)
                    if item['action'] == 'place':
                        (raw / item['to']).parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(archive, raw / item['to'])
                    elif item['action'] == 'unpack':
                        _unpack(archive, raw / item['to'])
                    else:
                        _extract(archive, raw, item['rules'], Path(scratch))
            return route['name']
        except (DownloadError, OSError, zipfile.BadZipFile, KeyError) as error:
            problems.append(f"{route['name']}: {type(error).__name__}: {error}")
    raise DownloadError(f'{dataset}: no automatic route completed. ' + ' | '.join(problems))


def raw_expected(dataset: str) -> dict[str, str]:
    out = {}
    for line in (RAW_CHECKSUMS / f'{dataset}.sha256').read_text().splitlines():
        digest, path = line.split('  ', 1)
        out[path] = digest
    return out


def verify_raw(dataset: str, raw: Path) -> dict:
    """Check every raw file the converter reads against the shipped list."""
    want = raw_expected(dataset)
    missing = [p for p in want if not (Path(raw) / p).is_file()]
    differing = [p for p in want if p not in missing and _digests(Path(raw) / p)['sha256'] != want[p]]
    return {'dataset': dataset, 'files': len(want), 'missing': missing, 'differing': differing, 'ok': not (missing or differing)}
