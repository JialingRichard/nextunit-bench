"""Fig. 4: fit travels, good and bad. One point per dataset (dataset S = mean over its folds, failures 0).

y = implementer following the plan - implementer's own run in the same harness (OpenCode, no plan)
x = plan author's source run - an independent run of the implementer (its main Codex run)
  Luna <- Astra: own 'Luna (OpenCode)', plan "Luna implements Astra's plans" r1, source 'Astra' r2, independent 'Luna' r1
  Astra <- Luna: own 'Astra (OpenCode)', plan "Astra implements Luna's plans" r1, source 'Luna (OpenCode)', independent 'Astra' r1
Slope through the origin sum(xy)/sum(x^2); 90% interval from 4000 resamples of the 24 datasets, one numpy
default_rng(20261004) shared across implementers (Astra first) and the sensitivity checks printed below.
Writes out/fig4_transplant.pdf and out/fig4_series.csv.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import common as C
import style

style.apply()
T = C.trajectories()
ds = lambda c, r=1: C.dataset_S(C.fold_S(T, c, r))  # noqa: E731
SPEC = {  # implementer: own, independent own, alternative own (sensitivity), source, plan
    'Luna': (ds('Luna (OpenCode)'), ds('Luna', 1), ds('Luna', 2), ds('Astra', 2), ds("Luna implements Astra's plans")),
    'Astra': (ds('Astra (OpenCode)'), ds('Astra', 1), ds('Astra', 2), ds('Luna (OpenCode)'), ds("Astra implements Luna's plans")),
}
rows = []
for name, (own, ind, alt, src, plan) in SPEC.items():
    for d in own.index:
        rows.append(dict(implementer=name, dataset=d, own=own[d], indep_own=ind[d], alt_own=alt[d], source=src[d], plan=plan[d],
                         x=src[d] - ind[d], y=plan[d] - own[d], x_shared=src[d] - own[d], x_alt=src[d] - alt[d]))
df = pd.DataFrame(rows)
df.to_csv(C.OUT / 'fig4_series.csv', index=False)
rng = np.random.default_rng(C.SEED)


def slope(x, y):
    return (x * y).sum() / (x * x).sum()


res = {}
for n, g in df.groupby('implementer'):
    x, y = g.x.values, g.y.values; k = len(x)
    bs = [slope(x[i], y[i]) for i in (rng.integers(0, k, k) for _ in range(C.NBOOT))]
    res[n] = (slope(x, y), *np.percentile(bs, [5, 95]))
    for lab, col in (('x from the shared own run', 'x_shared'), ('x from the rerun', 'x_alt')):
        xx, yy = g[col].values, g.y.values
        b2 = [slope(xx[i], yy[i]) for i in (rng.integers(0, k, k) for _ in range(C.NBOOT))]
        print('   sensitivity', n, lab, 'slope %.3f [%.3f, %.3f]' % (slope(xx, yy), *np.percentile(b2, [5, 95])))
    print(n, 'slope %.3f [%.3f, %.3f]' % res[n])

fig, ax = plt.subplots(figsize=(style.SINGLE, 3.2))
lim = 75
ax.plot([-lim, lim], [-lim, lim], ls='--', c='0.75', lw=0.8, zorder=0)
ax.axhline(0, ls='--', c='0.75', lw=0.8, zorder=0)
ax.text(46, 50, 'full transfer', color='0.45', fontsize=6.5, rotation=40, ha='center', va='bottom')
ax.text(-lim + 2, 1.5, 'no change', color='0.45', fontsize=6.5, ha='left', va='bottom')
labels = {'Luna': r'Luna$\leftarrow$Astra', 'Astra': r'Astra$\leftarrow$Luna'}
for n in ['Luna', 'Astra']:
    g = df[df.implementer == n]; c = style.COLORS[n]; s, lo, hi = res[n]
    h = g.dataset == 'AHU21'
    ax.scatter(g.x[~h], g.y[~h], s=14, color=c, alpha=0.85, lw=0, zorder=3,
               label=r'%s: slope %.2f [%.2f, %.2f]' % (labels[n], s, lo, hi))
    ax.scatter(g.x[h], g.y[h], s=22, facecolor='white', edgecolor=c, lw=1.0, zorder=4)
    xs = np.array([g.x.min(), g.x.max()]); ax.plot(xs, s * xs, color=c, lw=1.0, zorder=2)
ax.scatter([], [], s=22, facecolor='white', edgecolor='0.3', lw=1.0, label='AHU (time shortcut)')
ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim); ax.set_aspect('equal')
ax.set_xlabel("Source $-$ implementer's independent run (S)"); ax.set_ylabel("With plan $-$ implementer's own run (S)")
ax.legend(loc='upper left', frameon=False, fontsize=6.3, handletextpad=0.2, borderaxespad=0.1)
style.save(fig, C.OUT / 'fig4_transplant.pdf')
