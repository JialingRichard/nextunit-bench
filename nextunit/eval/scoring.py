"""Fold quality from per-unit predictions and labels: the scoring half of the evaluator.

The evaluator feeds each hidden unit's predictions in here as soon as they are
produced; re-scoring stored predictions goes through the same code.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .metrics import CLASSIFICATION, RANKING, ClassificationCounts, score


class PredictionError(ValueError):
    """The predictor's output violates the artifact specification."""


class FoldScorer:
    """Accumulates units of one fold and returns its primary score.

    ``class_values``: allowed predictions of a classification task.
    ``validation_only``: check IDs and values but compute no score (smoke check).
    ``scored_csv``: optional path; every scored row is appended there.
    """

    def __init__(self, metric: str, aggregation: str, class_values=None, *, validation_only: bool = False,
                 scored_csv: Path | None = None) -> None:
        if aggregation not in ('entity_equal', 'pooled', 'entity_weighted_pooled'):
            raise ValueError(aggregation)
        self.metric, self.aggregation, self.class_values = metric, aggregation, class_values
        self.validation_only = validation_only
        self.classification = metric in CLASSIFICATION
        self.counts = ClassificationCounts() if self.classification else None
        self.rows: list[pd.DataFrame] = []
        self.entities: list[dict] = []
        self.scored_csv = scored_csv
        self._csv_started = False

    def add(self, entity: str, prediction: pd.DataFrame, labels: Path | str | pd.DataFrame, extra: dict | None = None) -> dict:
        truth = labels if isinstance(labels, pd.DataFrame) else pd.read_csv(labels, dtype={'record_id': str})
        if self.class_values is not None and not set(prediction.prediction).issubset(set(self.class_values)):
            raise PredictionError('prediction must contain state codes from the task contract')
        joined = truth.merge(prediction, on='record_id', how='outer', validate='one_to_one', indicator=True)
        if not (joined['_merge'] == 'both').all():
            raise PredictionError(f'{entity}: prediction IDs do not exactly match scoring IDs')
        joined = joined.drop(columns='_merge')
        joined.insert(0, 'entity', entity)
        scored = joined[joined['score'].astype(bool)] if 'score' in joined else joined
        if not self.validation_only:
            if self.classification:
                self._append_csv(scored)
                self.counts.update(scored)
            else:
                self.rows.append(scored)
        # A single-class unit has no standalone AUC/AP; pooled scoring still includes it.
        scoreable = not self.validation_only and not (self.metric in RANKING and scored.target.nunique() < 2)
        row = {'entity': entity, 'records': len(joined), 'scored_records': len(scored),
               'score': score(scored, self.metric) if scoreable else None, 'status': 'completed', **(extra or {})}
        if not self.validation_only and self.classification:
            row['confusion'] = pd.crosstab(joined.target, joined.prediction).to_dict()
            row['target_counts'] = joined.target.value_counts().to_dict()
            row['accuracy'] = score(joined, 'accuracy')
        self.entities.append(row)
        return row

    def add_unfinished(self, entity: str, status: str, extra: dict | None = None) -> None:
        self.entities.append({'entity': entity, 'score': None, 'status': status, **(extra or {})})

    def _append_csv(self, frame: pd.DataFrame) -> None:
        if self.scored_csv is not None:
            frame.to_csv(self.scored_csv, index=False, mode='a' if self._csv_started else 'w', header=not self._csv_started)
            self._csv_started = True

    def result(self) -> dict:
        entities = self.entities
        if any(row['status'] != 'completed' for row in entities):
            return {'metric': self.metric, 'score': None, 'primary_score': None, 'status': 'censored',
                    'entities': len(entities), 'entity_metrics': entities,
                    'completion_fraction': sum(row['status'] == 'completed' for row in entities) / len(entities)}
        if self.validation_only:
            return {'status': 'completed', 'validation_only': True, 'metric': self.metric, 'score': None,
                    'primary_score': None, 'entities': len(entities), 'entity_metrics': entities, 'completion_fraction': 1.0}
        if self.classification:
            all_rows = None
            pooled = self.counts.score(self.metric)
            records = self.counts.records
        else:
            all_rows = pd.concat(self.rows, ignore_index=True)
            if self.scored_csv is not None:
                all_rows.to_csv(self.scored_csv, index=False)
            pooled = score(all_rows, self.metric)
            records = len(all_rows)
        entity_mean = (float(np.mean([row['score'] for row in entities]))
                       if all(row['score'] is not None for row in entities) else None)
        if self.aggregation == 'entity_equal':
            if entity_mean is None:
                raise PredictionError('Entity-equal metric is undefined for a single-class group')
            primary = entity_mean
        elif self.aggregation == 'pooled':
            primary = pooled
        elif self.classification:
            # Matches the paper's scorer: accuracy uses entity weights; balanced accuracy is pooled.
            primary = entity_mean if self.metric == 'accuracy' else pooled
        else:
            weights = 1 / all_rows.groupby('entity').entity.transform('size')
            primary = score(all_rows, self.metric, weights)
        result = {'metric': self.metric, 'aggregation': self.aggregation, 'score': pooled, 'entity_mean_score': entity_mean,
                  'primary_score': primary, 'status': 'completed', 'completion_fraction': 1.0,
                  'records': records, 'entities': len(entities), 'entity_metrics': entities}
        if self.metric == 'roc_auc' and all_rows is not None:
            from sklearn.metrics import roc_auc_score
            result['diagnostics'] = {'pooled_partial_auc_0_1': float(roc_auc_score(all_rows.target, all_rows.prediction, max_fpr=0.1))}
        if self.metric == 'balanced_accuracy':
            result['diagnostics'] = {'accuracy': self.counts.score('accuracy')}
        return result
