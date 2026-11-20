"""Fig. 5 of the paper (file name fig6_levers as in the paper sources) and Table IV: what moves the score.

(a) Frontier agents: paired change in S against the same agent and harness without the intervention.
    Codex control = per-fold mean of the agent's two Codex runs (replicates 1 and 2); OpenCode controls =
    'Luna (OpenCode)' and 'Astra (OpenCode)'.
(b) Local open-weight agents: change in S against the per-fold mean of Qwen3.6's four standard runs (replicates 1-4).
    Two-run configurations enter as the per-fold mean of their two runs.
Fold S as in trajectories.csv (failed and unresolved = 0). Delta = per-dataset paired difference (folds both cover),
averaged over the datasets covered. 95% CI: percentile bootstrap over datasets, 4000 draws, default_rng(20261004),
a fresh generator per row. Writes out/fig6_levers.pdf and out/fig6_series.csv.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import common as C
import style

style.apply()
T = C.trajectories()
fs = lambda c, r=1: C.fold_S(T, c, r)  # noqa: E731


def ci(v):
    n = len(v)
    idx = np.random.default_rng(C.SEED).integers(0, n, size=(C.NBOOT, n))
    return tuple(np.quantile(v[idx].mean(axis=1), [0.025, 0.975]))


def paired(treated, control):
    k = treated.index.intersection(control.index)
    d = (treated[k] - control[k]).groupby(level='dataset').mean()
    tS = treated[k].groupby(level='dataset').mean().mean()
    cS = control[k].groupby(level='dataset').mean().mean()
    lo, hi = ci(d.to_numpy())
    return dict(delta=d.mean(), lo=lo, hi=hi, treated_S=tS, control_S=cS, datasets=len(d), folds=len(k))


def mean2(a, b):
    return (a + b.reindex(a.index)) / 2


codex = {ag: mean2(fs(ag, 1), fs(ag, 2)) for ag in ('Luna', 'Astra', 'Kimi')}
TOOLKITS = [  # (label, colour, treated condition, control)
    ('Luna Codex + AWS skill', 'Luna', 'Luna + AWS skill', codex['Luna']),
    ('Luna Codex + tsfresh', 'Luna', 'Luna + tsfresh', codex['Luna']),
    ('Luna Codex + LG', 'Luna', 'Luna + PdM server', codex['Luna']),
    ('Luna Codex + PyOD', 'Luna', 'Luna + PyOD', codex['Luna']),
    ('Luna Codex + ProgPy', 'Luna', 'Luna + ProgPy', codex['Luna']),
    ('Luna Codex + components', 'Luna', 'Luna + own components', codex['Luna']),
    ('Luna Codex + components + validation tools', 'Luna', 'Luna + own components and validation tools', codex['Luna']),
    ('Luna Codex + AWS skill after submission', 'Luna', 'Luna + AWS skill after first submission', codex['Luna']),
    ('Astra Codex + AWS skill', 'Astra', 'Astra + AWS skill', codex['Astra']),
    ('Astra Codex + tsfresh', 'Astra', 'Astra + tsfresh', codex['Astra']),
    ('Astra Codex + LG', 'Astra', 'Astra + PdM server', codex['Astra']),
    ('Astra Codex + PyOD', 'Astra', 'Astra + PyOD', codex['Astra']),
    ('Astra Codex + ProgPy', 'Astra', 'Astra + ProgPy', codex['Astra']),
    ('Kimi Codex + components', 'Kimi', 'Kimi + own components', codex['Kimi']),
    ('Luna OpenCode + AWS skill', 'Luna', 'Luna (OpenCode) + AWS skill', fs('Luna (OpenCode)')),
]
rows = []
for lab, ck, cond, ctrl in TOOLKITS:
    rows.append(dict(panel='a', row='Domain toolkits and skills (15)', item=lab, colour=ck, source=cond, **paired(fs(cond), ctrl)))
tk_mean = pd.DataFrame(rows).delta.mean()
rows.append(dict(panel='a', row='Domain toolkits and skills (15)', item='mean of the 15', colour='', source='mean of rows above',
                 delta=tk_mean))
for row, ck, t, c in (("Luna, given Astra's plans", 'Luna', fs("Luna implements Astra's plans"), fs('Luna (OpenCode)')),
                      ("Astra, given Luna's plans", 'Astra', fs("Astra implements Luna's plans"), fs('Astra (OpenCode)')),
                      ('Astra, without the data', 'Astra', fs("Astra implements Astra's no-data plans"), fs('Astra (OpenCode)')),
                      ('Luna, without the data', 'Luna', fs("Luna implements Luna's no-data plans"), fs('Luna (OpenCode)'))):
    rows.append(dict(panel='a', row=row, item='', colour=ck, source='', **paired(t, c)))

STD = {'CPU, local workstation': fs('Qwen3.6', 1), 'CPU, cluster': fs('Qwen3.6', 2), 'GPU': fs('Qwen3.6', 3),
       '2 h, concurrent with skill runs': fs('Qwen3.6', 4)}
ref = sum(STD.values()) / 4
ref_S24 = ref.groupby(level='dataset').mean().mean()
for lab, s in STD.items():
    rows.append(dict(panel='b', row='Four standard runs', item=lab, colour='Qwen', source='Qwen3.6', **paired(s, ref)))
std_d = [x['delta'] for x in rows if x['row'] == 'Four standard runs']
B_ROWS = [
    ('8-bit weights, CPU', 'Qwen', fs('Qwen3.6, 8-bit, CPU')),
    ('8-bit weights, GPU', 'Qwen', fs('Qwen3.6, 8-bit, GPU')),
    ('16-bit weights, 2×A100', 'Qwen', fs('Qwen3.6, 16-bit')),
    ('Four hours instead of two', 'Qwen', fs('Qwen3.6, 4 h')),
    ('Workflow skill, run 1', 'Qwen', fs('Qwen3.6 + workflow skill', 1)),
    ('Workflow skill, run 2', 'Qwen', fs('Qwen3.6 + workflow skill', 2)),
    ('Gemma 4 instead of Qwen3.6', 'Gemma', fs('Gemma 4')),
    ("Astra's plans", 'Qwen', mean2(fs("Qwen3.6 implements Astra's plans", 1), fs("Qwen3.6 implements Astra's plans", 2))),
    ("Luna's plans", 'Qwen', mean2(fs("Qwen3.6 implements Luna's plans", 1), fs("Qwen3.6 implements Luna's plans", 2))),
    ("Astra's plans, lightened", 'Qwen', mean2(fs("Qwen3.6 implements Astra's lightened plans", 1),
                                               fs("Qwen3.6 implements Astra's lightened plans", 2))),
]
for lab, ck, s in B_ROWS:
    rows.append(dict(panel='b', row=lab, item='', colour=ck, source='', **paired(s, ref)))
LUNA = C.dataset_S(fs('Luna', 1)).mean()   # weakest frontier agent, main run (Fig. 2)
gap = LUNA - ref_S24
rows.append(dict(panel='b', row='Gap to weakest frontier agent', item=f'Luna {LUNA:.2f} - four-run mean {ref_S24:.2f}',
                 colour='Luna', source='', delta=gap, treated_S=LUNA, control_S=ref_S24, datasets=24, folds=58))
rows.append(dict(panel='b', row='Workflow skill, run 1 minus run 2', item='connector annotation', colour='', source='',
                 **paired(fs('Qwen3.6 + workflow skill', 1), fs('Qwen3.6 + workflow skill', 2))))
data = pd.DataFrame(rows)
data.round(4).to_csv(C.OUT / 'fig6_series.csv', index=False)
print(data[['panel', 'row', 'item', 'delta', 'lo', 'hi', 'treated_S', 'control_S', 'datasets', 'folds']].round(2).to_string())

# ---- figure
CL = style.COLORS
get = lambda row, item='': data[(data.row == row) & (data.item == item)].iloc[0]  # noqa: E731
a_rows = ['Domain toolkits and skills (15)', "Luna, given Astra's plans", "Astra, given Luna's plans",
          'Astra, without the data', 'Luna, without the data']
NODATA = {'Astra, without the data', 'Luna, without the data'}   # square markers
b_rows = ['Four standard runs'] + [x[0] for x in B_ROWS]
na, nb = len(a_rows), len(b_rows)
fig, (axa, axb) = plt.subplots(2, 1, figsize=(style.SINGLE, 4.0), sharex=True,
                               gridspec_kw=dict(height_ratios=[na + 0.9, nb + 0.6], hspace=0.28))
XL = (-25, 22)
EB = dict(fmt='o', ms=3.5, capsize=2, elinewidth=0.8)
sg = lambda v: f'{v:+.1f}'.replace('-', '−')  # noqa: E731  (typographic minus)

ya = np.arange(na)[::-1].astype(float)
tkd = data[(data.row == a_rows[0]) & (data['item'] != 'mean of the 15')]
order = np.argsort(tkd.delta.values)
jit = np.tile([-0.2, 0.0, 0.2], 5)          # fixed small vertical offsets so close dots stay visible
for j, i in enumerate(order):
    x = tkd.iloc[i]
    axa.plot(x.delta, ya[0] + jit[j], 'o', ms=3.3, color=CL[x.colour], mec='white', mew=0.4, zorder=3)
axa.plot([tk_mean, tk_mean], [ya[0] - 0.4, ya[0] + 0.4], color='k', lw=0.9, zorder=2)
axa.text(tk_mean - 0.5, ya[0] + 0.42, f'mean {sg(tk_mean)}', ha='right', va='bottom', fontsize=6)
for y, lab in zip(ya[1:], a_rows[1:]):
    x = get(lab)
    eb = dict(EB, fmt='s', ms=3.2) if lab in NODATA else EB
    axa.errorbar(x.delta, y, xerr=[[x.delta - x.lo], [x.hi - x.delta]], color=CL[x.colour], **eb)
    axa.text(x.hi + 0.6, y, sg(x.delta), va='center', fontsize=6.5)
hs = [plt.Line2D([], [], ls='', marker='o', ms=3.3, color=CL[k], label=k) for k in ('Astra', 'Luna', 'Kimi')]
leg = axa.legend(handles=hs, loc='center right', ncol=3, frameon=False, handletextpad=0.1, columnspacing=0.6,
                 fontsize=6.5, borderaxespad=0.1)
axa.add_artist(leg)
hm = [plt.Line2D([], [], ls='', marker=m, ms=3.2, color='0.4', label=t)
      for m, t in (('o', 'plan swapped'), ('s', 'plan written without data'))]
axa.legend(handles=hm, loc='upper right', bbox_to_anchor=(1.0, 0.43), ncol=1, frameon=False, handletextpad=0.1, fontsize=6.5,
           borderaxespad=0.1, labelspacing=0.2)
axa.set_yticks(ya)
axa.set_yticklabels(a_rows, fontsize=6.5)
axa.set_ylim(-0.6, na - 0.1)
axa.set_title('(a) Frontier agents', loc='left', fontsize=8)

yb = np.arange(nb)[::-1].astype(float)
axb.axvspan(min(std_d), max(std_d), color=CL['Qwen'], alpha=0.10, lw=0, zorder=0)
for d in std_d:
    axb.plot(d, yb[0], 'o', ms=3.3, color=CL['Qwen'], mec='white', mew=0.4, zorder=3)
for y, lab in zip(yb[1:], b_rows[1:]):
    x = get(lab)
    axb.errorbar(x.delta, y, xerr=[[x.delta - x.lo], [x.hi - x.delta]], color=CL[x.colour], **EB)
    axb.text(x.hi + 0.6, y, sg(x.delta), va='center', fontsize=6.5)
i1, i2 = b_rows.index('Workflow skill, run 1'), b_rows.index('Workflow skill, run 2')
w1, w2 = get(b_rows[i1]), get(b_rows[i2])
xb = max(w1.hi, w2.hi) + 4.6
axb.plot([xb - 0.5, xb, xb, xb - 0.5], [yb[i1], yb[i1], yb[i2], yb[i2]], color='0.35', lw=0.6)
axb.text(xb + 0.4, (yb[i1] + yb[i2]) / 2, 'same\nconfiguration', va='center', fontsize=6, color='0.25', linespacing=0.95)
axb.axvline(gap, color=CL['Luna'], ls='--', lw=0.8, zorder=0)
axb.text(gap - 0.4, yb[0] + 0.05, f'gap to weakest\nfrontier agent\n(Luna, {sg(gap)})', ha='right', va='center',
         fontsize=6, color='0.25', linespacing=0.95)
axb.set_yticks(yb)
axb.set_yticklabels(b_rows, fontsize=6.5)
axb.set_ylim(-0.6, nb - 0.3)
axb.set_title('(b) Local open-weight agents', loc='left', fontsize=8)
axb.set_xlabel('Change in S (points)')
for ax in (axa, axb):
    ax.axvline(0, color='0.3', lw=0.6, zorder=1)
    ax.set_xlim(*XL)
    ax.tick_params(axis='y', length=0)
    ax.grid(axis='x', color='0.9', lw=0.4, zorder=0)
    ax.set_axisbelow(True)
axb.set_xticks(np.arange(-25, 21, 5))
style.save(fig, C.OUT / 'fig6_levers.pdf')
