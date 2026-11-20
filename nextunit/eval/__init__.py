"""Fixed evaluator and scoring (filled at M3).

- Metrics: accuracy, balanced_accuracy, mae, rmse, roc_auc, average_precision.
- Aggregation within a fold: entity_equal, pooled, entity_weighted_pooled.
- Loss ``E`` (one minus the metric for score-type metrics), frozen baseline
  ``B``, ``S = 100*max(0, 1-E/B)``, auxiliary ``D = 100*max(0, 1-B/E)``.
- Aggregates: S24 (24 datasets) and S_noshortcut (without AHU21, THREEW,
  CARE); paired bootstrap over datasets.
- Deployment: sealed artifact, hash re-check, one offline sandboxed process
  per hidden unit, labels joined outside the sandbox.

Fixed code: nobody using the benchmark edits or reimplements it.
"""
