"""Fig. 2: S over the 24 datasets per method, with 95% intervals from a bootstrap over datasets.

S = mean over 24 datasets of (mean over folds of 100 max(0, 1 - E/B)); a failed run scores 0.
AutoML was not run on MIMII_DUE and scores 0 there. Bootstrap: 4000 resamples of the 24 datasets in
alphabetical order, numpy default_rng(20261004).integers(0, 24, (4000, 24)), 2.5 / 97.5 % quantiles.
Writes out/fig2_scores.pdf and out/fig2_series.csv (per-dataset S, then S24, CI_lo, CI_hi rows).

--labels full: the GitHub version (out/fig2_scores_github.pdf): full model names and group headings, same
numbers, intervals, colours and order; the paper's outputs are not written.
"""
import sys

import numpy as np
import matplotlib.pyplot as plt

import common as C
import style

FULL = sys.argv[1:] == ['--labels', 'full']
assert FULL or not sys.argv[1:], 'usage: fig2_scores.py [--labels full]'
FULL_NAMES = {'Astra': 'GPT-6 Astra', 'Luna': 'GPT-6 Luna', 'Kimi': 'Kimi K3', 'DeepSeek': 'DeepSeek V4.1-Flash',
              'Qwen': 'Qwen3.6-35B-A3B', 'Gemma': 'Gemma 4 26B-A4B', 'MOMENT': 'MOMENT-1-base'}
FULL_GROUPS = {'Frontier agents': 'Frontier LLM agents', 'Local open-weight agents': 'Local open-weight agents',
               'AutoML': 'AutoML', 'Foundation models': 'Time-series foundation models'}

style.apply()
T = C.trajectories()
R = C.references()

scores = {}   # label -> (per-dataset Series, group, colour key)
for lab, cond in (('Astra', 'Astra'), ('Kimi', 'Kimi'), ('DeepSeek', 'DeepSeek'), ('Luna', 'Luna')):
    scores[lab] = (C.dataset_S(C.fold_S(T, cond, 1)), 'Frontier agents', lab)
scores['Qwen'] = (C.dataset_S(C.fold_S(T, 'Qwen3.6', 1)), 'Local open-weight agents', 'Qwen')
scores['Gemma'] = (C.dataset_S(C.fold_S(T, 'Gemma 4', 1)), 'Local open-weight agents', 'Gemma')
ds24 = sorted(scores['Astra'][0].index)
assert len(ds24) == 24


def ref(method):
    r = R[R.method == method].set_index(['dataset', 'fold']).S
    return C.dataset_S(r).reindex(ds24).fillna(0.0)   # AutoML has no MIMII_DUE run: 0


for lab, m in (('AutoGluon', 'AutoGluon'), ('FLAML', 'FLAML'), ('AutoGluon + features', 'AutoGluon + features'),
               ('FLAML + features', 'FLAML + features')):
    scores[lab] = (ref(m), 'AutoML', 'AutoML')
scores['Fixed random forest'] = (ref('Random forest (baseline component)'), 'Fixed RF', 'Baseline')
scores['MOMENT'] = (ref('MOMENT-1-base'), 'Foundation models', 'TSFM')
scores['Chronos-2'] = (ref('Chronos-2'), 'Foundation models', 'TSFM')

idx = np.random.default_rng(C.SEED).integers(0, 24, size=(C.NBOOT, 24))
res = {}
for k, (d, grp, col) in scores.items():
    v = d.reindex(ds24).to_numpy()
    assert not np.isnan(v).any(), k
    lo, hi = np.quantile(v[idx].mean(axis=1), [0.025, 0.975])
    res[k] = (v.mean(), lo, hi, grp, col)
    print(f'{k:22s} {v.mean():6.2f} [{lo:5.2f}, {hi:5.2f}]')
with open(C.OUT / 'fig2_series.csv', 'w') if not FULL else open('/dev/null', 'w') as f:
    f.write('dataset,' + ','.join(scores) + '\n')
    for x in ds24:
        f.write(x + ',' + ','.join(f'{scores[k][0][x]:.4f}' for k in scores) + '\n')
    for i, name in ((0, 'S24'), (1, 'CI_lo'), (2, 'CI_hi')):
        f.write(name + ',' + ','.join(f'{res[k][i]:.4f}' for k in scores) + '\n')

groups = ['Frontier agents', 'Local open-weight agents', 'AutoML', 'Foundation models', 'Fixed RF']
ys, labels, y = [], [], 0
fig, ax = plt.subplots(figsize=(style.SINGLE, 2.95) if not FULL else (style.SINGLE * 1.15, 3.9))
bounds, gl = [], []
for gi, gname in enumerate(groups):
    ks = sorted([k for k in res if res[k][3] == gname], key=lambda k: -res[k][0])
    if FULL and gname in FULL_GROUPS:                  # a heading row above the group
        ax.text(0.6, y, FULL_GROUPS[gname], va='center', ha='left', fontsize=6.5, fontweight='bold', color='0.3')
        y += 1
    start = y
    for k in ks:
        mu, lo, hi, _, col = res[k]
        ax.errorbar(mu, y, xerr=[[mu - lo], [hi - mu]], fmt='o', ms=4, color=style.COLORS[col],
                    elinewidth=1.2, capsize=2, capthick=0.8)
        ax.text(min(hi + 1.2, 58), y, f'{mu:.1f}', va='center', ha='left', fontsize=6.5)
        ys.append(y); labels.append(FULL_NAMES.get(k, k) if FULL else k); y += 1
    gl.append((gname, start, y - 1))
    if gi < len(groups) - 1:
        bounds.append(y - 0.5 + 0.35); y += 0.7
ax.set_yticks(ys); ax.set_yticklabels(labels); ax.invert_yaxis()
for b in bounds:
    ax.axhline(b, color='0.75', lw=0.5)
ax.set_xlim(0, 60); ax.set_ylim(y - 1 + 0.5, -0.6)
ax.set_xlabel(r'$S$ (share of baseline error removed, %)')
ax.grid(axis='x', color='0.9', lw=0.5); ax.set_axisbelow(True)
ax.tick_params(axis='y', length=0)
for n, a, b in gl:
    if n != 'Fixed RF' and not FULL:
        ax.text(59.5, (a + b) / 2, n.replace('Local open-weight agents', 'Local').replace('Frontier agents', 'Frontier')
                .replace('Foundation models', 'TSFM'), rotation=-90, va='center', ha='left', fontsize=6, color='0.35')
style.save(fig, C.OUT / ('fig2_scores_github.pdf' if FULL else 'fig2_scores.pdf'))
