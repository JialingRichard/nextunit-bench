"""Fig. 6 of the paper (file name fig5_execution as in the paper sources): plans reach only implementers that can execute them.

(a) Share of Qwen3.6 runs that deliver a predictor in time: no plan (Qwen3.6 replicates 2 and 4, the two cluster-CPU
    runs), Luna's plans and Astra's plans (two runs each); Wilson 95% intervals. Thin bars: within thirds of plan load.
    Plan load (data/fig5_plan_load.csv): five features of the plan author's own implementation - log number of models,
    external dependency, neural network, log1p heavy-compute seconds, log1p Python lines - each turned into normal
    scores over the 116 plans (rank average, (rank - 0.375) / (n + 0.25)), averaged and standardized. Thirds are cut
    at the 1/3 and 2/3 percentiles of the load over the 232 pooled Qwen plan runs.
(b) One square per Qwen run and fold (116 per plan source). Landing: delivered and
      |x| >= 5: z = (S - v_a) / x within [0.8672, 1.126];  |x| < 5: |S - v_p| <= max(1, 0.2 |x|),
    with x = v_p - v_a, v_p the plan author's own S on the fold, and v_a the implementer's reference S without a plan
    (data/fig5_landing_reference.csv). Plan authors: 'Astra' replicate 2 for Astra's plans, 'Luna (OpenCode)' for
    Luna's. Frontier implementers: "Luna implements Astra's plans" and "Astra implements Luna's plans" (replicate 1).
    Not compared: both S 100, both S 0, or v_p = 0.
Writes out/fig5_execution.pdf and out/fig5_series.csv.
"""
from statistics import NormalDist

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
from matplotlib.patches import Rectangle

import common as C
import style

style.apply()
T = C.trajectories()
BAND = (0.8672, 1.126)


def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def delivered(cond, reps):
    r = pd.concat([C.runs(T, cond, k).assign(rep=k) for k in reps]).reset_index()
    r['delivered'] = (r.status == 'completed').astype(int)
    return r


PLAN = {'Astra': "Qwen3.6 implements Astra's plans", 'Luna': "Qwen3.6 implements Luna's plans"}
rows = []
for lab, (cond, reps) in (('No plan', ('Qwen3.6', (2, 4))), ("Luna's plans", (PLAN['Luna'], (1, 2))),
                          ("Astra's plans", (PLAN['Astra'], (1, 2)))):
    g = delivered(cond, reps)
    k, n = int(g.delivered.sum()), len(g); lo, hi = wilson(k, n)
    rows.append(dict(panel='a', group=lab, cell='delivered', k=k, n=n, rate=k / n, lo=lo, hi=hi))

# plan load index
pl = pd.read_csv(C.DATA / 'fig5_plan_load.csv')
feats = [np.log(pl.n_models.astype(float)), pl.external_dependency.astype(float), pl.neural_network.astype(float),
         np.log1p(pl.heavy_compute_seconds), np.log1p(pl.python_lines.astype(float))]
nd = NormalDist()
ns = [np.array([nd.inv_cdf((r - 0.375) / (len(pl) + 0.25)) for r in pd.Series(v).rank(method='average')]) for v in feats]
Lraw = np.mean(ns, axis=0)
pl['L'] = (Lraw - Lraw.mean()) / Lraw.std()
Lmap = {(s, d, int(f)): v for s, d, f, v in zip(pl.plan_source, pl.dataset, pl.fold, pl.L)}
q = pd.concat([delivered(PLAN[s], (1, 2)).assign(src=s) for s in ('Astra', 'Luna')], ignore_index=True)
q['L'] = [Lmap[(s.lower(), d, int(f))] for s, d, f in zip(q.src, q.dataset, q.fold)]
cut = np.percentile(q.L, [100 / 3, 200 / 3]); q['T'] = np.searchsorted(cut, q.L)
for s in ('Astra', 'Luna'):
    for k in range(3):
        g = q[(q.src == s) & (q['T'] == k)]
        rows.append(dict(panel='load', group=s, cell=f'tercile{k + 1}', k=len(g), n=int((q.src == s).sum()), rate=len(g) / (q.src == s).sum()))
        kd = int(g.delivered.sum()); lo, hi = wilson(kd, len(g))
        rows.append(dict(panel='a_load', group=s, cell=f'tercile{k + 1}', k=kd, n=len(g), rate=kd / len(g), lo=lo, hi=hi))


# (b) landing
def land(S, va, vp, dl):
    x = vp - va; big = np.abs(x) >= 5
    with np.errstate(divide='ignore', invalid='ignore'):
        z = (S - va) / x
    return (dl & np.where(big, (z >= BAND[0]) & (z <= BAND[1]), np.abs(S - vp) <= np.maximum(1.0, 0.2 * np.abs(x)))).astype(int)


ref = pd.read_csv(C.DATA / 'fig5_landing_reference.csv')
cells_b = {}
for src, lab, author, frontier in (('astra', "Astra's plans", ('Astra', 2), "Luna implements Astra's plans"),
                                   ('luna', "Luna's plans", ('Luna (OpenCode)', 1), "Astra implements Luna's plans")):
    p = delivered(PLAN[src.capitalize()], (1, 2)).merge(ref[ref.plan_source == src], on=['dataset', 'fold'])
    assert len(p) == 116
    key = list(zip(p.dataset, p.fold))
    vp = C.fold_S(T, *author).reindex(key).to_numpy()
    fr = C.runs(T, frontier, 1).reindex(key)
    Sf, df_ = fr.S.to_numpy(), (fr.status == 'completed').to_numpy()
    lq = land(p.S.to_numpy(), p.v_a_qwen.to_numpy(), vp, p.delivered.to_numpy() == 1)
    lf = land(Sf, p.v_a_frontier.to_numpy(), vp, df_)
    triv = ((p.S < .01) & (Sf < .01)) | ((p.S > 99.99) & (Sf > 99.99)) | (vp < .01)
    keep = ~triv.to_numpy()
    c = dict(frontier_landed=int((lf[keep] == 1).sum()), qwen_on_landed=int(((lf == 1) & (lq == 1) & keep).sum()),
             frontier_not=int((lf[keep] == 0).sum()), qwen_on_not=int(((lf == 0) & (lq == 1) & keep).sum()),
             not_compared=int(triv.sum()))
    cells_b[lab] = c
    for kk, v in c.items():
        rows.append(dict(panel='b', group=lab, cell=kk, k=v, n=116))
df = pd.DataFrame(rows)
df.to_csv(C.OUT / 'fig5_series.csv', index=False)
print(df.to_string())

# ---- figure
CL = style.COLORS
fig = plt.figure(figsize=(style.SINGLE, 5.0))
a = fig.add_axes([0.22, 0.555, 0.73, 0.43]); b = fig.add_axes([0.02, 0.0, 0.96, 0.45])
light = lambda c, k=0.45: tuple(x + (1 - x) * k for x in to_rgb(c))  # noqa: E731
cols = {'No plan': '#9e9e9e', "Luna's plans": CL['Luna'], "Astra's plans": CL['Astra']}
src_of = {"Luna's plans": 'Luna', "Astra's plans": 'Astra'}
noplan = df[(df.panel == 'a') & (df.group == 'No plan')].rate.iloc[0]
a.axvline(noplan, color='#9e9e9e', lw=0.6, ls=(0, (3, 2)), zorder=0)
y = 0; ticks, labs, bold = [], [], []


def bar(y, r, col, h, fs):
    a.barh(y, r.rate, color=col, height=h)
    a.errorbar(r.rate, y, xerr=[[r.rate - r.lo], [r.hi - r.rate]], color='#8a8a8a', lw=0.5, capsize=1.5, capthick=0.5)
    x = r.hi + 0.02
    if x <= noplan <= x + 0.13:   # keep the count off the dashed line
        x = noplan + 0.025
    a.text(x, y, f'{r.k}/{r.n}', va='center', fontsize=fs)


for g in ['No plan', "Luna's plans", "Astra's plans"]:
    r = df[(df.panel == 'a') & (df.group == g)].iloc[0]
    bar(y, r, cols[g], 0.8, 6.5); ticks.append(y); labs.append(g); bold.append(True); y += 0.95
    if g in src_of:
        for t, nm in zip(range(1, 4), ['light', 'middle', 'heavy']):
            rr = df[(df.panel == 'a_load') & (df.group == src_of[g]) & (df.cell == f'tercile{t}')].iloc[0]
            bar(y, rr, light(cols[g]), 0.5, 5.5); ticks.append(y); labs.append(f'{nm} load'); bold.append(False); y += 0.62
    y += 0.45
a.set_yticks(ticks); a.set_yticklabels(labs)
for tl, bb in zip(a.get_yticklabels(), bold):
    tl.set_fontweight('bold' if bb else 'normal'); tl.set_fontsize(7 if bb else 6)
a.invert_yaxis(); a.set_ylim(y - 0.3, -0.6)
a.set_xlim(0, 1); a.set_xlabel('Qwen3.6 delivers a predictor in time')
a.tick_params(axis='y', length=0)
for s_ in ('top', 'right'):
    a.spines[s_].set_visible(False)
a.set_title('(a)', loc='left', fontweight='bold', x=-0.24)

COLS, step, sz = 12, 1.0, 0.8
b.set_aspect('equal'); b.axis('off')
for gi, src in enumerate(["Astra's plans", "Luna's plans"]):
    c = cells_b[src]; x0 = gi * (COLS + 1.6)
    b.text(x0, 0.6, src, fontsize=8, fontweight='bold')
    cells = ([('L', j < c['qwen_on_landed']) for j in range(c['frontier_landed'])]
             + [('N', j < c['qwen_on_not']) for j in range(c['frontier_not'])] + [('X', False)] * c['not_compared'])
    assert len(cells) == 116
    for idx, (kind, ql) in enumerate(cells):
        r, cc = divmod(idx, COLS); x, yy = x0 + cc * step, -(r + 1) * step
        if kind == 'X':
            b.add_patch(Rectangle((x, yy), sz, sz, facecolor='none', edgecolor='#b5b5b5', lw=0.5))
        else:
            b.add_patch(Rectangle((x, yy), sz, sz, facecolor='#4d4d4d' if kind == 'L' else '#dcdcdc', edgecolor='none'))
        if ql:
            b.add_patch(Rectangle((x + 0.15, yy + 0.15), sz - 0.3, sz - 0.3, facecolor=CL['Qwen'], edgecolor='white', lw=0.5))
    nq = c['qwen_on_landed'] + c['qwen_on_not']
    b.text(x0, -11.1, f"Qwen landed {nq}: {c['qwen_on_landed']} on dark, {c['qwen_on_not']} on light", fontsize=7, va='top')
b.text(-0.2, 1.9, '(b)', fontweight='bold')
for x, (fc, ec, lab) in zip([0, 6.2, 13.2, 19.0], [('#4d4d4d', 'none', 'frontier landed'), ('#dcdcdc', 'none', 'frontier did not'),
                                                   (CL['Qwen'], 'none', 'Qwen landed'), ('none', '#b5b5b5', 'not compared')]):
    b.add_patch(Rectangle((x, -13.4), sz, sz, facecolor=fc, edgecolor=ec, lw=0.5)); b.text(x + 1.1, -13.0, lab, fontsize=7, va='center')
b.set_xlim(-0.5, 2 * COLS + 1.8); b.set_ylim(-14, 2.6)
style.save(fig, C.OUT / 'fig5_execution.pdf')
