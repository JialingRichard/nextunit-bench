"""Where prepared data lives under a prepared-data root (see nextunit/benchmark/README.md)."""
from __future__ import annotations

from pathlib import Path


def unit_dir(root: Path | str, dataset: str, entity_id: str) -> Path:
    return Path(root) / dataset / entity_id


def inputs_dir(root: Path | str, dataset: str, entity_id: str) -> Path:
    return unit_dir(root, dataset, entity_id) / 'inputs'


def labels_path(root: Path | str, dataset: str, entity_id: str) -> Path:
    return unit_dir(root, dataset, entity_id) / 'labels.csv'


def auxiliary_dir(root: Path | str, dataset: str) -> Path:
    return Path(root) / dataset / 'auxiliary'
