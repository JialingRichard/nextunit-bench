# Paper data and figures

Data and scripts behind the figures and run-based tables of *Moving Generality from Model to Modeler:
LLM Agents for PHM on a Deployment-Style Benchmark*. The scripts read only `paper/data/`.

```
paper/
  data/               CSV data; column descriptions in data/README.md
  figures/            one script per figure, style.py, common.py, fig1_protocol.tex (TikZ source of Fig. 1)
  figures/out/        generated: figN_*.pdf and figN_series.csv (the numbers each figure plots)
  tables/make_tables.py   recomputes Tables II, III and VI -> tables/out/tables.md
  make_figures.py     runs all figure scripts
```

## Regenerate

```
pip install numpy pandas matplotlib
python paper/make_figures.py          # Figs. 2-6 and the appendix figure
python paper/make_figures.py --fig1   # also Fig. 1, if tectonic or pdflatex (with newtx, TikZ) is installed
python paper/tables/make_tables.py
```

| Paper | Script | Data |
|---|---|---|
| Fig. 1 | `figures/fig1_protocol.tex` | (diagram) |
| Fig. 2 | `figures/fig2_scores.py` (`--labels full`: the README version with full model names, `out/fig2_scores_github.pdf`) | `trajectories.csv`, `reference_methods.csv` |
| Fig. 3 | `figures/fig3_protocols.py` | `fig3_protocols.csv`, `trajectories.csv` |
| Fig. 4 | `figures/fig4_transplant.py` | `trajectories.csv` |
| Fig. 5, Table IV | `figures/fig6_levers.py` | `trajectories.csv` |
| Fig. 6 | `figures/fig5_execution.py` | `trajectories.csv`, `fig5_plan_load.csv`, `fig5_landing_reference.csv` |
| Fig. 7 (appendix), Table V | `figures/figA_alt_baselines.py` (also writes the table body) | `trajectories.csv`, `reference_methods.csv` |
| Tables II, III, VI | `tables/make_tables.py` | `trajectories.csv`, `published_methods.csv` |

The script and PDF names follow the paper's source files, whose numbering predates the final order:
`fig6_levers` is printed as Fig. 5 and `fig5_execution` as Fig. 6.

Table I (the datasets) is the benchmark definition in `nextunit/benchmark/`. Bootstrap intervals use
numpy's `default_rng(20261004)`; the figures and tables reproduce the paper's numbers exactly, including
the intervals. Rendered with matplotlib 3.10 the figures are pixel-identical to the paper's own scripts in
the same environment; the paper's PDFs were made with matplotlib 3.11, whose text layout shifts some labels
by a pixel or two. Fonts are not shipped: the style asks for Nimbus Roman (URW base35, installed with
Ghostscript on most Linux systems) and otherwise falls back to Liberation Serif, Times New Roman or DejaVu
Serif, which changes glyph shapes and label widths but nothing else.

## What `data/trajectories.csv` covers

Every agent run that a figure or table of the paper uses, plus the few runs quoted only in the text
(lightened plans followed by Astra, no-data plans given to Luna as advice): 56 runs, 2959 trajectories,
each with its loss `E`, the baseline loss `B`, the score `S`, whether it delivered, and its development
time. The four frontier agents' main runs and re-runs through Codex, the fifteen toolkit trials, the
OpenCode runs without a plan, all plan transplants (plans written on the data, lightened, and written
without the data, with their second runs), the 30 implementations of published methods, and all
configurations of the local models (Qwen3.6, Gemma 4).

## What it does not cover

- Non-agent references (AutoML, time-series foundation models, the baseline's two models, the constant
  prediction) are in `reference_methods.csv`, per fold, not in the long table.
- The reproductions of published methods under the papers' own protocols (Fig. 3, open circles and
  panel b) were scored outside the benchmark (capped labels, the papers' splits); only their final
  values are given, in `fig3_protocols.csv`.
- Derived inputs of Fig. 5 (plan-load features, implementers' reference scores) are given as data, not
  recomputed from run records.
- Runs that no figure, table or result of the paper uses (pilots, smoke tests, superseded or partial
  runs, earlier versions of the benchmark), agents' transcripts, delivered code, plans and predictions
  are not included. Token counts are not included.
- The AHU time-shift re-evaluation (Section VII-B) is in `ahu_timeshift.csv` for the 12 runs of the
  long table; two further runs from that check are not in the long table and are left out.
- Run-to-run variation is visible only where a condition was run more than once (`replicate`); the
  paper's intervals cover sampling over datasets only.
