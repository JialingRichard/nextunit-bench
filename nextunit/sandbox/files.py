"""Placing data files where a sandboxed process will read them."""
from __future__ import annotations

import os
import shutil
from pathlib import Path


def place(source, target):
    """Hard-link the file that ``source`` names, following symbolic links; copy it if linking is impossible.

    A sandbox sees only the target. A symbolic link must never be reproduced there: its target may lie outside
    every mount (an unreadable file) and it would show a host path."""
    real = os.path.realpath(source)
    try:
        os.link(real, target)
    except OSError:
        shutil.copy2(real, target)
    return target


def place_tree(source, target, **kwargs):
    """``shutil.copytree`` with :func:`place`: symbolic links to files and directories are resolved."""
    return shutil.copytree(source, target, copy_function=place, **kwargs)


def symbolic_links(root) -> list[Path]:
    return [p for p in Path(root).rglob('*') if p.is_symlink()]
