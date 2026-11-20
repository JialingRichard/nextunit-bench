"""Fig. 7 of the paper (appendix) and the body of Table V: S over 23 datasets (all but MIMII_DUE) under five choices of the fixed baseline.

Only the denominator changes: S_fold = 100 max(0, 1 - E/B') with E from each method's own run.
B' = the original B; the random forest alone; the 1D CNN alone; the better of the two on each fold; AutoGluon with
the feature bank (folds where that fit failed are not counted). A failed run of the scored method counts 0; a method
is not scored against itself. Fold scores are averaged within a dataset, then over the 23 datasets.
Writes out/figA_alt_baselines.pdf, out/figA_series.csv and out/figA_table.tex (body of the appendix table).
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

import common as C
import style

style.apply()
T = C.trajectories()
R = pd.read_csv(C.DATA / 'reference_methods.csv')
AGENTS = [('Astra', 'Astra'), ('Kimi', 'Kimi'), ('DeepSeek', 'DeepSeek'), ('Luna', 'Luna'), ('Qwen3.6', 'Qwen3.6'), ('Gemma 4', 'Gemma 4')]
REFS = ['AutoGluon', 'FLAML', 'AutoGluon + features', 'FLAML + features', 'MOMENT-1-base', 'Chronos-2', 'Constant prediction']
E, ok = {}, {}   # method -> per-fold loss, delivered flag (index dataset, fold)
for lab, cond in AGENTS:
    r = C.runs(T, cond, 1)
    E[lab], ok[lab] = r.E, r.status == 'completed'
for m in REFS + ['Random forest (baseline component)', '1D CNN (baseline component)']:
    r = R[R.method == m].set_index(['dataset', 'fold'])
    E[m], ok[m] = r.E, r.status == 'completed'
B0 = C.runs(T, 'Astra', 1).B
idx = B0.index
rf, cnn = E['Random forest (baseline component)'].reindex(idx), E['1D CNN (baseline component)'].reindex(idx)
BASES = [('Original', 'Original\n(RF+CNN)/2', B0), ('Random forest', 'Random\nforest', rf), ('1D CNN', '1D CNN', cnn),
         ('Better of the two', 'Better of\nthe two\n(hindsight)', np.minimum(rf, cnn)),
         ('AutoGluon + features', 'AutoGluon\n+ features', E['AutoGluon + features'].where(ok['AutoGluon + features']).reindex(idx))]
DS23 = sorted(d for d in set(idx.get_level_values(0)) if d != 'MIMII_DUE')
S = {}
for bname, _, Bp in BASES:
    for m in [a for a, _ in AGENTS] + REFS:
        if m == bname:
            continue
        e, d = E[m].reindex(idx), ok[m].reindex(idx).fillna(False).astype(bool)
        s = pd.Series(np.where(d, 100 * np.maximum(0, 1 - e / Bp), 0.0), index=idx)
        s = s[Bp.notna() & (Bp > 0) & (idx.get_level_values(0) != 'MIMII_DUE')]
        S[(bname, m)] = s.groupby(level='dataset').mean().reindex(DS23).mean()
METHODS = [('Astra', 'Astra', 'Astra', 'o'), ('Kimi', 'Kimi', 'Kimi', 'o'), ('DeepSeek', 'DeepSeek', 'DeepSeek', 'o'),
           ('Luna', 'Luna', 'Luna', 'o'), ('Gemma 4', 'Gemma 4', 'Gemma', 's'), ('Qwen3.6', 'Qwen3.6', 'Qwen', 's'),
           ('AutoGluon + features', 'AutoGluon + features', 'AutoML', 'D'), ('FLAML + features', 'FLAML + features', 'AutoML', '^'),
           ('AutoGluon', 'AutoGluon', 'AutoML', 'v'), ('FLAML', 'FLAML', 'AutoML', 'x'),
           ('MOMENT-1-base', 'MOMENT', 'TSFM', 'D'), ('Chronos-2', 'Chronos-2', 'TSFM', '^')]

fig, ax = plt.subplots(figsize=(style.SINGLE, 2.9))
for key, lab, ck, mk in reversed(METHODS):
    col = style.COLORS[ck]
    big = key in ('Astra', 'Kimi', 'DeepSeek', 'Luna')
    pts = [(i, S[(b, key)]) for i, (b, _, _) in enumerate(BASES) if (b, key) in S]
    segs, cur = [], [pts[0]]
    for p in pts[1:]:
        if p[0] == cur[-1][0] + 1:
            cur.append(p)
        else:
            segs.append(cur); cur = [p]
    segs.append(cur)
    for sg in segs:
        ax.plot(*zip(*sg), color=col, lw=1.4 if big else 0.8, marker=mk, ms=3.2 if big else 2.6,
                mfc=col if mk != 'x' else 'none', alpha=1 if big else 0.85)
    if big:
        ax.text(len(BASES) - 1 + 0.12, S[(BASES[-1][0], key)], lab, va='center', fontsize=6.5)
ax.set_xticks(range(len(BASES))); ax.set_xticklabels([l for _, l, _ in BASES], fontsize=6.3)
ax.set_xlim(-0.2, len(BASES) - 0.2); ax.set_ylim(0, 46)
ax.set_ylabel(r'$S$ over 23 datasets'); ax.set_xlabel('Fixed baseline used to compute $S$')
ax.grid(axis='y', color='0.9', lw=0.5); ax.set_axisbelow(True)
handles = [Line2D([], [], color=style.COLORS[c], marker=m, lw=0.8, ms=2.6, mfc=style.COLORS[c] if m != 'x' else 'none', label=l)
           for _, l, c, m in METHODS[4:]]
ax.legend(handles=handles, loc='upper center', bbox_to_anchor=(0.5, -0.31), ncol=3, frameon=False, fontsize=5.8,
          handlelength=1.6, columnspacing=1.0)
style.save(fig, C.OUT / 'figA_alt_baselines.pdf')

rows = [a for a, _ in AGENTS] + REFS
rank = {}
for b, _, _ in BASES:   # rank among the twelve methods (constant prediction and the baseline's own method excluded)
    ks = [k for k in rows[:-1] if (b, k) in S]
    for i, k in enumerate(sorted(ks, key=lambda k: -S[(b, k)])):
        rank[(b, k)] = i + 1
with open(C.OUT / 'figA_series.csv', 'w') as f, open(C.OUT / 'figA_table.tex', 'w') as t:
    f.write('method,' + ','.join(b for b, _, _ in BASES) + '\n')
    for k in rows:
        f.write(k + ',' + ','.join(f'{S[(b, k)]:.2f}' if (b, k) in S else '' for b, _, _ in BASES) + '\n')
        if k in ('Qwen3.6', 'AutoGluon', 'MOMENT-1-base', 'Constant prediction'):
            t.write('\\midrule\n')
        cells = []
        for b, _, _ in BASES:
            if (b, k) not in S:
                cells.append('---')
            elif k != 'Constant prediction' and rank[(b, k)] <= 4:
                cells.append(f'{S[(b, k)]:.1f} ({rank[(b, k)]})')
            else:
                cells.append(f'{S[(b, k)]:.1f}')
        t.write(k + ' & ' + ' & '.join(cells) + ' \\\\\n')
print(open(C.OUT / 'figA_series.csv').read())
