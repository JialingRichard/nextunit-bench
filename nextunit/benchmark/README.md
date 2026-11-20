# Frozen benchmark definition

Nothing here is written at build time; these files define the benchmark and
are only read. Licence: CC BY 4.0 (see the repository README).
`MANIFEST.sha256` lists the SHA-256 of every file below except this README;
its own hash identifies the benchmark definition.

| Path | Content |
|---|---|
| `tasks/<DATASET>/task.json` | Dataset definition (fields below) |
| `tasks/<DATASET>/task.md` | Task description shown to the agent, byte-identical to the paper's runs (in Chinese) |
| `tasks/<DATASET>/info.md` | Physical information shown to the agent; PUBD16 is the redacted version (KNOWN_ISSUES.md, B1) |
| `splits.csv` | The 58 folds: one row per fold, role and unit (`dataset, fold, role, entity_id`); `role` is `development` or `hidden`. Row order within a fold and role is the order the evaluator uses. |
| `aggregates.json` | The dataset sets over which S is averaged: `S24` (all 24) and `S_noshortcut` (21: without AHU21, THREEW, CARE) |
| `baseline_B.csv` | 58 rows: `dataset, fold, metric, aggregation, e_rf, e_cnn, B`. `e_rf` and `e_cnn` are the losses of the two fixed baseline models; `B` is the value every score in the paper used, equal to their mean up to floating-point rounding (≤ 1e-13). |
| `checksums/prepared/<DATASET>.sha256` | SHA-256 of every prepared file, in `sha256sum` format, relative to the dataset's prepared directory |
| `checksums/prepared/CARE.arrays.json` | CARE only: its `.npz` files are verified per array, not per file (KNOWN_ISSUES.md, C4). For each file, in member order: array name, dtype, shape, SHA-256 of the array's C-order bytes |
| `checksums/raw/<DATASET>.sha256` | SHA-256 of every raw file the dataset's converter reads, relative to the raw root |
| `checksums/prepared_sizes.csv` | Number of files and bytes of prepared data per dataset |

## `task.json`

| Field | Meaning |
|---|---|
| `dataset` | Code name used everywhere in this repository |
| `family`, `domain`, `task` | Descriptive labels (as in the paper's configuration) |
| `mode` | `batch` or `stream` |
| `metric` | `accuracy`, `balanced_accuracy`, `mae`, `rmse`, `roc_auc` or `average_precision` |
| `aggregation` | `entity_equal`, `pooled` or `entity_weighted_pooled` |
| `prediction_values` | Allowed class labels for classification tasks, else `null` |
| `unit` | Unit of the target, if any |
| `split_type` | How folds were formed (unit, condition, run, official or temporal holdout) |
| `prediction_unit`, `physical_entity_counts` | BACKBLAZE only: its six "units" are pools of disks |
| `n_folds` | Number of folds |
| `stream_layout` | Stream tasks only: how each chunk is presented, `flat`, `manifest` or `manifest_with_flat_alias` (see docs/artifact_spec.md); `null` for batch tasks |
| `development_auxiliary` | `true` if shared development data is mounted at `development/auxiliary` in every fold (SCANIA's official training set) |
| `entities` | One object per unit: `id` (name in the source data), `public_id` (anonymous directory name the agent and the predictor see), `physical` (operating metadata known at deployment), and dataset-specific extras |

## Prepared layout

The checksums assume this layout under a prepared-data root:

```
<root>/<DATASET>/<entity_id>/inputs/...     inputs of one unit
<root>/<DATASET>/<entity_id>/labels.csv     record_id,target
<root>/<DATASET>/auxiliary/...              SCANIA only
```

so that `cd <root>/<DATASET> && sha256sum -c --strict <path>/<DATASET>.sha256`
verifies one dataset (for CARE, only its CSV files; its arrays are checked by
`python -m nextunit.data verify CARE`). Labels of hidden units are part of these files; which
units are hidden is given by `splits.csv`.
