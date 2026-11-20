"""Data access shared by the figure scripts. Everything is read from ../data/ relative to this file."""
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / 'data'
OUT = HERE / 'out'
OUT.mkdir(exist_ok=True)
SEED, NBOOT = 20261004, 4000


def trajectories():
    return pd.read_csv(DATA / 'trajectories.csv')


def runs(T, condition, replicate=1):
    """Rows of one run (condition, replicate), indexed by (dataset, fold)."""
    r = T[(T.condition == condition) & (T.replicate == replicate)]
    assert len(r), (condition, replicate)
    return r.set_index(['dataset', 'fold']).sort_index()


def fold_S(T, condition, replicate=1):
    """Fold S of one run; failed and unresolved runs are stored as S = 0."""
    return runs(T, condition, replicate).S


def dataset_S(fold_s):
    """Mean over the folds of each dataset."""
    return fold_s.groupby(level='dataset').mean()


def fold_score(E, B):
    return 100 * np.maximum(0.0, 1 - E / B)


def references():
    """Per-fold S of the reference methods (AutoML, foundation models, baseline components, constant)."""
    R = pd.read_csv(DATA / 'reference_methods.csv')
    R['S'] = np.where(R.status == 'completed', fold_score(R.E, R.B), 0.0)
    return R
