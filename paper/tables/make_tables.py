"""Recompute the numbers of the paper's run-based tables from paper/data/ and write them to tables/out/tables.md.

Table II  (agent scores under alternative choices)  - from trajectories.csv
Table III (score by plan author, data seen, implementer) - from trajectories.csv
Table IV  (toolkit trials)          - same computation as Fig. 5a, by figures/fig6_levers.py (figures/out/fig6_series.csv)
Table V   (alternative baselines)   - written by figures/figA_alt_baselines.py to figures/out/figA_table.tex
Table VI  (published methods)       - from trajectories.csv and published_methods.csv
Bootstrap intervals: 4000 resamples of the datasets (sorted), numpy default_rng(20261004).integers(0, n, (4000, n)).
"""
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / 'data'
OUT = HERE / 'out'
OUT.mkdir(exist_ok=True)
T = pd.read_csv(DATA / 'trajectories.csv')
SHORTCUT = {'AHU21', 'THREEW', 'CARE'}          # collection or preparation left a shortcut
NO_UNITS = {'CWRU', 'SEU', 'HSF15'}             # no independent units; operating conditions held out


def run(cond, rep=1):
    return T[(T.condition == cond) & (T.replicate == rep)].set_index(['dataset', 'fold'])


def boot(v):
    v = np.asarray(v, float); n = len(v)
    idx = np.random.default_rng(20261004).integers(0, n, size=(4000, n))
    lo, hi = np.quantile(v[idx].mean(axis=1), [0.025, 0.975])
    return v.mean(), lo, hi


def per_dataset(fold_s, keep=None):
    d = fold_s.groupby(level='dataset').mean().sort_index()
    return d if keep is None else d[[x for x in d.index if keep(x)]]


lines = ['# Tables recomputed from paper/data/', '']

# ---------------------------------------------------------------- Table II
lines += ['## Table II: agent scores under alternative choices', '',
          '| Agent | S (24) | S, floor -100 | S, without shortcut sets | S, 21 unit sets | Fail (%) | Worse (%) |',
          '|---|---|---|---|---|---|---|']
AG = ['Astra', 'Kimi', 'DeepSeek', 'Luna', 'Qwen3.6', 'Gemma 4']
res = {}
for a in AG:
    r = run(a)
    done = r.status == 'completed'
    floor = pd.Series(np.where(done, 100 * np.maximum(-1, 1 - r.E / r.B), 0.0), index=r.index)
    res[a] = [boot(per_dataset(r.S)), boot(per_dataset(floor)), boot(per_dataset(r.S, lambda x: x not in SHORTCUT)),
              boot(per_dataset(r.S, lambda x: x not in NO_UNITS)),
              100 * (~done).mean(), 100 * (done & (r.E > r.B)).mean()]
ranks = [{a: i + 1 for i, a in enumerate(sorted(AG[:4], key=lambda a: -res[a][c][0]))} for c in range(4)]
for a in AG:
    cells = []
    for c in range(4):
        m, lo, hi = res[a][c]
        rk = f' ({ranks[c][a]})' if a in ranks[c] else ''
        cells.append(f'{m:.1f}{rk} [{lo:.1f}, {hi:.1f}]')
    lines.append(f'| {a} | ' + ' | '.join(cells) + f' | {res[a][4]:.1f} | {res[a][5]:.1f} |')

# ---------------------------------------------------------------- Table III
def S24(cond, rep=1, drop_unresolved=False):
    r = run(cond, rep)
    if drop_unresolved:            # the registered analysis of this condition leaves unresolved runs out
        r = r[r.status != 'unresolved']
    return per_dataset(r.S).mean()


def cell(c):
    s = f'{S24(c, 1):.1f}'
    if ((T.condition == c) & (T.replicate == 2)).any():
        s += f' ({S24(c, 2):.1f})'
    return s


LUNA_ASTRA, ASTRA_LUNA = "Luna implements Astra's plans", "Astra implements Luna's plans"
LUNA_ASTRA_ND, ASTRA_ASTRA_ND = "Luna implements Astra's no-data plans", "Astra implements Astra's no-data plans"
LUNA_LUNA_ND, ASTRA_LUNA_ND = "Luna implements Luna's no-data plans", "Astra implements Luna's no-data plans"
ADVICE, LIGHT = "Luna, Astra's no-data plans as advice", "Astra implements Astra's lightened plans"
lines += ['', '## Table III: score by plan author, data seen, implementer (S over 24 datasets; second run in parentheses)', '',
          '| Plan by | Data seen | Carried out by Luna | Carried out by Astra |', '|---|---|---|---|',
          f"| Astra | yes | {cell(LUNA_ASTRA)} | {S24('Astra (OpenCode)'):.1f} (own run, no plan) |",
          f"| Luna | yes | {S24('Luna (OpenCode)'):.1f} (own run, no plan) | {cell(ASTRA_LUNA)} |",
          f"| Astra | no | {S24(LUNA_ASTRA_ND, drop_unresolved=True):.1f} | {cell(ASTRA_ASTRA_ND)} |",
          f"| Luna | no | {cell(LUNA_LUNA_ND)} | {cell(ASTRA_LUNA_ND)} |",
          '', f"Also used in the text: Luna given Astra's no-data plans as advice {S24(ADVICE):.1f}; "
          f"Astra following its own lightened plans {S24(LIGHT):.1f}."]

# ---------------------------------------------------------------- Table VI
lit = T[T.condition == 'Astra implements a published method']
own = run('Astra (OpenCode), alongside the literature runs').S
pm = pd.read_csv(DATA / 'published_methods.csv')
lines += ['', "## Table VI: published methods implemented by Astra (S of the method; S of Astra's own design on the same folds)", '',
          '| Dataset | Method | Year | S (method) | S (Astra) | Beat |', '|---|---|---|---|---|---|']
for p in pm.itertuples():
    r = lit[lit.published_method == p.method]
    o = own[[(d, f) for d, f in zip(r.dataset, r.fold)]].to_numpy()
    beat = int((r.S.to_numpy() > o + 1e-9).sum())
    lines.append(f'| {p.dataset} | {p.method} | {p.year} | {r.S.mean():.1f} | {o.mean():.1f} | {beat}/{len(r)} |')

(OUT / 'tables.md').write_text('\n'.join(lines) + '\n')
print('\n'.join(lines))
