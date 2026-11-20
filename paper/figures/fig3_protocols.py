"""Fig. 3: faithful implementations of published methods under the papers' protocols and under ours.

(a) C-MAPSS FD004, RMSE in cycles: x = paper reported; open circle = our implementation under the paper protocol
    (test labels and predictions capped at 125; data/fig3_protocols.csv); filled circle = the benchmark's own task
    (true remaining life, last cycle of each test engine): E of the published-method run in trajectories.csv.
(b) Paderborn fold 1 (one bearing per class held out), accuracy: x = paper reported, dot = ours.
Writes out/fig3_protocols.pdf and out/fig3_series.csv.
"""
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

import common as C
import style

style.apply()
T = C.trajectories()
P = pd.read_csv(C.DATA / 'fig3_protocols.csv')
lit = T[(T.condition == 'Astra implements a published method') & (T.dataset == 'CMAPSS')].set_index('published_method').E
cm = P[P.dataset == 'CMAPSS'].copy()
cm['ours_deployment'] = [lit[m] for m in cm.method]
pb = P[P.dataset == 'PUBD16']
pd.concat([cm, pb]).to_csv(C.OUT / 'fig3_series.csv', index=False)

A = style.COLORS['Astra']; K = style.COLORS['Paper']
fig, (a, b) = plt.subplots(2, 1, figsize=(style.SINGLE, 3.7), height_ratios=[4.2, 3], gridspec_kw={'hspace': 0.75})
ys, labels = [], []
for y, r in enumerate(cm.itertuples()):
    p, c, t = r.paper_reported, r.ours_paper_protocol, r.ours_deployment
    dy = 0.13 if abs(c - t) < 1 else 0   # DA-TCN: the two protocols nearly coincide, nudge the circles apart
    a.plot([c, t], [y - dy, y + dy], color=A, lw=1.2, zorder=1)
    a.plot(p, y, 'x', color=K, ms=5, mew=1.1, zorder=3)
    a.plot(c, y - dy, 'o', mfc='white', mec=A, mew=1.1, ms=5, zorder=4)
    a.plot(t, y + dy, 'o', color=A, ms=5, zorder=2)
    ys.append(y); labels.append(r.method)
a.set_yticks(ys); a.set_yticklabels(labels); a.set_ylim(3.5, -0.5)
a.set_xlim(0, 42); a.set_xlabel('RMSE (cycles), C-MAPSS FD004'); a.set_axisbelow(True); a.grid(axis='x', lw=.3, color='#ddd')
a.text(-0.02, 1.04, '(a)', transform=a.transAxes, fontsize=9, weight='bold', ha='right')
h = [Line2D([], [], marker='x', ls='', color=K, mew=1.1, label='Paper reported'),
     Line2D([], [], marker='o', ls='', mfc='white', mec=A, mew=1.1, label='Ours, paper protocol (capped at 125)'),
     Line2D([], [], marker='o', ls='', color=A, label='Ours, deployment protocol (true remaining life)')]
a.legend(handles=h, loc='upper center', bbox_to_anchor=(0.45, 1.42), ncol=1, frameon=False, handletextpad=.3, labelspacing=.25)
for i, r in enumerate(pb.itertuples()):
    b.plot([r.ours_paper_protocol, r.paper_reported], [i, i], color='#999', lw=1.0, zorder=1)
    b.plot(r.paper_reported, i, 'x', color=K, ms=5, mew=1.1, zorder=3)
    b.plot(r.ours_paper_protocol, i, 'o', color=A, ms=5, zorder=2)
b.set_yticks(range(len(pb))); b.set_yticklabels(list(pb.method)); b.set_ylim(2.5, -0.5)
b.set_xlim(0.4, 1.02); b.set_xlabel('Accuracy (Paderborn, fold 1, held-out bearings)')
b.grid(axis='x', lw=.3, color='#ddd'); b.set_axisbelow(True)
b.text(-0.02, 1.30, '(b)', transform=b.transAxes, fontsize=9, weight='bold', ha='right')
hb = [Line2D([], [], marker='x', ls='', color=K, mew=1.1, label='Paper reported'),
      Line2D([], [], marker='o', ls='', color=A, label='Ours (one bearing per class held out, as the papers describe)')]
b.legend(handles=hb, loc='upper left', bbox_to_anchor=(0.0, 1.38), ncol=1, frameon=False, handletextpad=.3, labelspacing=.25)
style.save(fig, C.OUT / 'fig3_protocols.pdf')
print(pd.concat([cm, pb]).to_string(index=False))
