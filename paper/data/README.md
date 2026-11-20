# Data behind the paper's figures and tables

All files are CSV with a header row. Licence: CC BY 4.0 (see the repository README).
Dataset codes and fold numbers are those of `nextunit/benchmark/` (e.g. `PUBD16` = Paderborn,
`HSF15` = UCI hydraulic, `NB1`/`NB14` = NASA battery / randomized battery). No file here contains
hidden labels, predictions or run artefacts; only losses and scores.

## `trajectories.csv`: one row per agent run on one fold

2959 rows, 56 runs (a run = one `condition` and `replicate` over its folds). `conditions.csv` lists them.

| Column | Meaning |
|---|---|
| `condition` | Public name of the configuration, as in the paper (e.g. `Astra`, `Luna (OpenCode)`, `Astra + tsfresh`, `Luna implements Astra's plans`, `Qwen3.6, 4 h`) |
| `replicate` | 1 = the run the paper calls the main or first run; 2, 3, ... = further runs of the same condition. For `Qwen3.6`, replicates 1-4 are the four standard runs of Fig. 5b (1 = main run on a workstation CPU; see `setting`) |
| `agent` | GPT-6 Astra, GPT-6 Luna, Kimi K3, DeepSeek V4.1-Flash, Qwen3.6-35B-A3B, Gemma 4 (short names) |
| `harness` | `Codex` (Codex CLI 0.156.1) or `OpenCode` (OpenCode 1.19.0) |
| `setting` | Local models only: weight precision and hardware the model ran on |
| `budget_h` | Development budget in hours (2, except `Qwen3.6, 4 h`) |
| `toolkit` | Toolkit or skill given to the agent (`none` otherwise) |
| `plan_source` | Whose plan the agent followed: `none`, `astra`, `luna`, or `paper` (a published method) |
| `plan_kind` | `none`; `delivered` (plan written from the method the author delivered on that fold); `lightened` (the same plan with heavy machinery removed under written rules); `without data` (plan written from the task description and a data-layout card only); `without data, as advice` (such a plan given as advice rather than instructions); `published method` |
| `published_method` | For `plan_source = paper`: the method name used in the paper's Table VI |
| `dataset`, `fold` | Benchmark fold |
| `metric` | Fold metric |
| `status` | `completed` (a predictor was delivered and evaluated), `failed` (no working predictor within the budget, or evaluation of the delivered predictor failed), `unresolved` (an infrastructure failure outside the agent's control; 4 rows) |
| `attempt` | 2 for the 5 folds of `Qwen3.6 implements Astra's lightened plans`, replicate 2, that were re-run after a connection failure of the model server, as that experiment's rules provided; 1 otherwise |
| `E` | Loss of the delivered predictor (one minus the metric for accuracy, balanced accuracy, ROC-AUC and average precision; MAE or RMSE otherwise); empty if not completed |
| `B` | Loss of the fixed baseline on the fold (`nextunit/benchmark/baseline_B.csv`) |
| `S` | `100 * max(0, 1 - E/B)`; 0 if failed or unresolved |
| `D` | `100 * max(0, 1 - B/E)`, how far a delivered predictor falls short of the baseline; 100 if failed; empty if unresolved. Not used in the paper |
| `development_minutes` | Active development wall-clock time in minutes (queue waits excluded); empty for 12 Codex runs whose record lacks it |

How the paper treats `unresolved`: as a failure (S = 0, not delivered) everywhere, except Table III's
`Luna implements Astra's no-data plans`, whose registered analysis leaves its one unresolved fold out
(27.6 instead of 27.2). The delivery rate of 31% quoted for `Qwen3.6 implements Astra's lightened plans`
is 35 of the 114 resolved runs.

Plans: Astra's plans describe the methods of `Astra`, replicate 2; Luna's plans those of `Luna (OpenCode)`.
The no-data plans were written by a fresh session of the named agent.

## `conditions.csv`: one row per run

`condition`, `replicate` and the descriptive columns of `trajectories.csv`, plus `trajectories`, `datasets`,
`delivered`, `unresolved`, `S` (mean over datasets of the fold mean; failures and unresolved as 0; empty for
the published methods, which cover 4 datasets) and `used_in` (figures, tables or sections of the paper).

## `reference_methods.csv`: non-agent references, per fold

`method, dataset, fold, status, E, B`. Methods: `AutoGluon`, `FLAML`, `AutoGluon + features`, `FLAML + features`
(the AutoML baselines; not run on MIMII_DUE, so 57 folds), `MOMENT-1-base`, `Chronos-2` (fine-tuned per fold),
`Random forest (baseline component)` and `1D CNN (baseline component)` (the two models whose mean loss is `B`),
`Constant prediction` (median or majority of the development labels). `E` is empty when `status = failed`
(a failed AutoML fit scores 0).

## `fig3_protocols.csv`: Fig. 3

`dataset, method, metric, paper_reported, ours_paper_protocol`: the value a paper reports, and our
implementation's value under the paper's own protocol (C-MAPSS FD004: RMSE with test labels and
predictions capped at 125 cycles; Paderborn fold 1: accuracy, one bearing per class held out). The
deployment-protocol RMSE plotted in Fig. 3a is `E` of the same method in `trajectories.csv`.

## `published_methods.csv`: Table VI

`dataset, method, year, doi` of the 20 published methods (year of the journal issue).

## `fig5_plan_load.csv`: Fig. 6a

One row per plan (`plan_source, dataset, fold`), five features of the plan author's own implementation:
`n_models` (models in the final predictor), `external_dependency` (1 if a package that is not preinstalled
was used), `neural_network` (1 if any), `heavy_compute_seconds` (time of compute-heavy commands during
development), `python_lines` (lines of Python delivered). The load index is computed from them in
`figures/fig5_execution.py`.

## `fig5_landing_reference.csv`: Fig. 6b

`plan_source, dataset, fold, v_a_qwen, v_a_frontier`: the implementer's reference score on the fold without
a plan (mean S over its delivered runs without a plan, with fixed fallbacks), for Qwen3.6 and for the frontier
implementer of that plan source (Luna for Astra's plans, Astra for Luna's). Fixed before the landing analysis.

## `ahu_timeshift.csv`: Section VII-B (text, not a figure)

The sealed AHU21 predictors of 12 runs, re-evaluated on the same hidden units: `S_recorded` (as in
`trajectories.csv`), `S_rerun` (re-run unchanged), `S_shift_182_days` (all timestamps +182 days; hour and
weekday kept), `S_shift_random` (each unit's clock shifted by its own random offset of 1 to 5 years).
