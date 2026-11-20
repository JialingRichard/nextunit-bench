"""bubblewrap sandboxes.

A ``Runtime`` is the read-only file system a sandbox runs on: a Python
interpreter and the directories it needs, mounted from a runtime bundle (for
example a container image exported to a directory) or from the host.
Predictors always run offline; only the runner's development sandbox may share
the network.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

OPTIONS = ['--die-with-parent', '--unshare-all', '--new-session', '--as-pid-1', '--clearenv']
ENVIRONMENT = {'HOME': '/tmp/home', 'USER': 'phm', 'LANG': 'C.UTF-8',
               'OMP_NUM_THREADS': '2', 'OPENBLAS_NUM_THREADS': '2', 'MKL_NUM_THREADS': '2',
               'PYTHONDONTWRITEBYTECODE': '1', 'TORCHINDUCTOR_CACHE_DIR': '/tmp/torchinductor'}


@dataclass(frozen=True)
class Runtime:
    python: str                                   # interpreter path inside the sandbox
    mounts: tuple[tuple[str, str], ...]           # (host source, sandbox target), read-only
    merged_usr: bool = True                       # /bin, /sbin, /lib, /lib64 are links into /usr
    name: str = field(default='runtime', compare=False)

    @classmethod
    def load(cls, path: Path | str) -> 'Runtime':
        """Read a runtime file: {"bundle": dir, "python": path, "mounts": [{"source", "target"}], "merged_usr": bool}.

        Relative ``bundle`` is resolved against the file's directory, relative sources against ``bundle``."""
        path = Path(path).resolve()
        spec = json.loads(path.read_text())
        bundle = (path.parent / spec.get('bundle', '.')).resolve()
        mounts = tuple((str((bundle / m['source']).resolve()), m['target']) for m in spec['mounts'])
        return cls(python=spec['python'], mounts=mounts, merged_usr=spec.get('merged_usr', True), name=path.stem)

    @classmethod
    def venv(cls, path: Path | str) -> 'Runtime':
        """A virtual environment on this host plus the host's /usr: the runtime of the predictors."""
        path = Path(os.path.abspath(path))
        python = path / 'bin' / 'python'
        mounts = [('/usr', '/usr'), (str(path.resolve()), str(path))]
        merged = Path('/lib').is_symlink()
        if not merged:
            mounts += [(p, p) for p in ('/lib', '/lib64') if Path(p).exists()]
        link = python
        while link.is_symlink():          # the base interpreter and every alias on the way to it
            target = link.readlink()
            target = target if target.is_absolute() else link.parent / target
            prefix = target.parent.parent
            if not str(prefix).startswith('/usr/') and str(prefix) not in {t for _, t in mounts}:
                mounts.append((str(prefix.resolve()), str(prefix)))
            link = target
        for etc in ('/etc/ld.so.cache', '/etc/localtime', '/etc/ssl/certs', '/etc/resolv.conf', '/etc/nsswitch.conf'):
            if Path(etc).exists():
                mounts.append((str(Path(etc).resolve()), etc))
        return cls(python=str(python), mounts=tuple(mounts), merged_usr=merged, name=path.name)

    def save(self, path: Path | str) -> None:
        Path(path).write_text(json.dumps({'bundle': '/', 'python': self.python, 'merged_usr': self.merged_usr,
                                          'mounts': [{'source': s, 'target': t} for s, t in self.mounts]}, indent=1) + '\n')

    @classmethod
    def host(cls) -> 'Runtime':
        """The current interpreter and the host's /usr (development and tests only)."""
        mounts = [('/usr', '/usr')]
        merged = Path('/lib').is_symlink()
        if not merged:
            mounts += [(p, p) for p in ('/lib', '/lib64') if Path(p).exists()]
        for prefix in dict.fromkeys([sys.prefix, sys.base_prefix]):
            if not prefix.startswith('/usr/'):
                mounts.append((prefix, prefix))
        # Follow the interpreter's symlink chain; every prefix on it must exist inside the sandbox.
        link = Path(sys.executable)
        while link.is_symlink():
            target = link.readlink()
            target = target if target.is_absolute() else link.parent / target
            prefix = target.parent.parent
            if not str(prefix).startswith('/usr/') and str(prefix) not in {t for _, t in mounts}:
                mounts.append((str(prefix.resolve()), str(prefix)))
            link = target
        for etc in ('/etc/ld.so.cache', '/etc/localtime', '/etc/ssl/certs', '/etc/resolv.conf', '/etc/nsswitch.conf'):
            if Path(etc).exists():
                mounts.append((str(Path(etc).resolve()), etc))
        return cls(python=sys.executable, mounts=tuple(mounts), merged_usr=merged, name='host')


def gpu_devices() -> list[Path]:
    return sorted(Path('/dev').glob('nvidia*'))


def command(runtime: Runtime, argv: list[str], *, readonly=(), writable=(), network: bool = False,
            gpu: bool = False, cwd: str = '/', env: dict | None = None) -> list[str]:
    """The bwrap command line; ``readonly`` and ``writable`` are (host, sandbox) pairs."""
    bwrap = shutil.which('bwrap')
    if bwrap is None:
        raise FileNotFoundError('bwrap (bubblewrap) is not installed')
    out = [bwrap, *OPTIONS]
    if network:
        out.append('--share-net')
    environment = {'PATH': f'{Path(runtime.python).parent}:/usr/bin:/bin', **ENVIRONMENT, **(env or {})}
    for key, value in environment.items():
        out += ['--setenv', key, str(value)]
    for source, target in runtime.mounts:
        out += ['--ro-bind', source, target]
    if runtime.merged_usr:
        for name in ('bin', 'sbin', 'lib', 'lib64'):
            out += ['--symlink', 'usr/' + name, '/' + name]
    out += ['--proc', '/proc', '--dev', '/dev', '--tmpfs', '/tmp', '--dir', '/tmp/home']
    for device in gpu_devices() if gpu else ():
        out += ['--dev-bind', str(device), str(device)]
    for source, target in writable:
        out += ['--bind', str(Path(source).resolve()), target]
    for source, target in readonly:
        out += ['--ro-bind', str(Path(source).resolve()), target]
    return out + ['--chdir', cwd, *map(str, argv)]
