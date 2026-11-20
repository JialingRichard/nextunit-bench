"""One fold and role of the frozen definition, resolved against a prepared-data root."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .. import definition
from ..data import layout


@dataclass(frozen=True)
class FoldView:
    dataset: str
    fold: int
    role: str
    mode: str
    metric: str
    aggregation: str
    class_values: tuple | None
    stream_layout: str | None
    inputs: dict[str, Path]          # public ID -> inputs directory
    labels: dict[str, Path]          # public ID -> labels.csv (never mounted into a sandbox)
    entity_mapping: dict[str, str]   # public ID -> unit ID
    auxiliary: Path | None           # shared development data, development role only


def fold_view(dataset: str, fold: int, role: str, prepared_root: Path | str) -> FoldView:
    task = definition.task(dataset)
    public = definition.public_ids(dataset)
    selected = definition.units(dataset, fold, role)
    root = Path(prepared_root)
    values = task['prediction_values']
    return FoldView(
        dataset=dataset, fold=fold, role=role, mode=task['mode'], metric=task['metric'],
        aggregation=task['aggregation'], class_values=tuple(values) if values is not None else None,
        stream_layout=task['stream_layout'],
        inputs={public[i]: layout.inputs_dir(root, dataset, i) for i in selected},
        labels={public[i]: layout.labels_path(root, dataset, i) for i in selected},
        entity_mapping={public[i]: i for i in selected},
        auxiliary=layout.auxiliary_dir(root, dataset) if task['development_auxiliary'] and role == 'development' else None)
