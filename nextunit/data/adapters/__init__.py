"""One converter per dataset: ``build(raw, out)`` reads the extracted raw files under ``raw`` and writes the
prepared units under ``out`` (``out/<unit_id>/inputs/...`` and ``out/<unit_id>/labels.csv``).

Converters are fixed code: their output must match ``nextunit/benchmark/checksums/prepared/<DATASET>.sha256``.
"""
from __future__ import annotations

import importlib

MODULES = {
    'AHU21': 'ahu21', 'BACKBLAZE': 'backblaze', 'CALCE': 'calce', 'CARE': 'care', 'CFRP': 'cfrp',
    'CMAPSS': 'cmapss', 'CWRU': 'cwru', 'HSF15': 'hsf15', 'IMS': 'ims', 'MATR': 'matr', 'MATWI': 'matwi',
    'MIMII_DUE': 'mimii_due', 'NB1': 'nb1', 'NB14': 'nb14', 'NCMAPSS': 'ncmapss', 'PHM10': 'phm10',
    'PHME20': 'phme20', 'PRONOSTIA': 'pronostia', 'PUBD16': 'pubd16', 'SCANIA': 'scania', 'SEU': 'seu',
    'TEP': 'tep', 'THREEW': 'threew', 'XJTU-SY': 'xjtu_sy',
}


def adapter(dataset: str):
    return importlib.import_module(f'{__name__}.{MODULES[dataset]}')
