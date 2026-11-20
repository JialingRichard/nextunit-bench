"""File writers shared by the converters. Each reproduces the exact bytes of the paper's prepared data:
do not change line endings, float formatting or JSON options."""
from __future__ import annotations

import csv
import json
import os
import shutil
from pathlib import Path


def json_file(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def csv_crlf(path: Path, columns, rows) -> None:
    """csv.writer defaults: CRLF line ends, values through str()."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        writer.writerows(rows)


LINK_RAW = True   # set False to copy raw files instead of hard-linking them (prepare.build(link_raw=False))


def same_file(source: Path, target: Path) -> None:
    """Place a raw file unchanged: hard link if allowed and possible, else copy."""
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        return
    if LINK_RAW:
        try:
            os.link(source, target)
            return
        except OSError:
            pass
    shutil.copyfile(source, target)
