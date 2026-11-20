"""The reference random forest: training rows, weights, input matrix, model and prediction.

Training rows: at most 60,000 (fewer if the float32 matrix would exceed 1 GiB), dealt equally over the development
units (``select``), drawn with ``numpy.random.default_rng(20260925)``; in classification, classes with few records in
a unit are kept whole. Weights (``training_weights``): every unit counts equally (entity-weighted tasks); balanced
accuracy: classes equal within each unit; AUC/AP: classes equal globally. Inputs: the reader's arrays, tabular columns
constant over the training rows dropped, missing values replaced by their training mean, no scaling, flattened.
Model: scikit-learn RandomForestRegressor / RandomForestClassifier, 200 trees, max_features='sqrt',
min_samples_leaf=2, random_state=20260925. Training is deterministic for any number of threads. Prediction runs
single-threaded: with several threads scikit-learn adds the trees' outputs in completion order, which changes the
last bits of the average.
"""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

SEED = 20260925
SAMPLE_CAP = 60000
MATRIX_LIMIT_BYTES = 1024 ** 3
FOREST = {'n_estimators': 200, 'max_features': 'sqrt', 'min_samples_leaf': 2}
RANKING = ('average_precision', 'roc_auc')
ARRAYS = ('sequence', 'tabular', 'image')


class Units:
    """Cached arrays of the training units (cache.load), indexed by (unit position, row)."""

    def __init__(self, units: list[dict]):
        self.ids = [u['id'] for u in units]
        self.arrays = [u['arrays'] for u in units]
        self.targets = [u['target'] for u in units]
        self.lengths = [len(t) for t in self.targets]
        self.raw_width = sum(int(np.prod(v.shape[1:])) for v in self.arrays[0].values() if v is not None)

    def select(self, cap, seed, class_values=None):
        rng = np.random.default_rng(seed)
        lengths = np.asarray(self.lengths, dtype=int)
        allocation = np.zeros(len(lengths), dtype=int)
        left = min(int(cap), int(lengths.sum()))
        while left:
            available = np.flatnonzero(allocation < lengths)
            each = max(1, left // len(available))
            for unit in available:
                take = min(each, int(lengths[unit] - allocation[unit]), left)
                allocation[unit] += take
                left -= take
                if not left:
                    break
        rows = []
        for unit, count in enumerate(allocation):
            pool = np.arange(lengths[unit])
            retained = np.empty(0, dtype=int)
            if class_values is not None:
                minority = [pool[self.targets[unit][pool] == label] for label in class_values]
                minority = [indices for indices in minority if len(indices) <= count / len(class_values)]
                if minority:
                    retained = np.concatenate(minority)
            remaining = np.setdiff1d(pool, retained, assume_unique=True)
            index = np.sort(np.concatenate([retained, rng.choice(remaining, count - len(retained), replace=False)]))
            rows.extend((unit, int(row)) for row in index)
        return np.asarray(rows, dtype=np.int64).reshape(-1, 2)

    def read_targets(self, rows):
        target = np.empty(len(rows), dtype=np.float64)
        for unit in np.unique(rows[:, 0]):
            positions = np.flatnonzero(rows[:, 0] == unit)
            target[positions] = self.targets[unit][rows[positions, 1]]
        return target

    def read(self, rows):
        values = {}
        for name, exemplar in self.arrays[0].items():
            if exemplar is None:
                values[name] = None
                continue
            out = np.empty((len(rows), *exemplar.shape[1:]), dtype=np.float32)
            for unit in np.unique(rows[:, 0]):
                positions = np.flatnonzero(rows[:, 0] == unit)
                out[positions] = self.arrays[unit][name][rows[positions, 1]]
            values[name] = out
        return values

    def batches(self, rows, size=512):
        for start in range(0, len(rows), size):
            yield self.read(rows[start:start + size])


def training_weights(rows, target, metric, aggregation):
    """Effective sample weights with mean exactly one."""
    weights = np.ones(len(rows), dtype=np.float64)
    entity_equal = aggregation in ('entity_equal', 'entity_weighted_pooled')
    if entity_equal:
        for unit in np.unique(rows[:, 0]):
            take = rows[:, 0] == unit
            weights[take] = 1 / take.sum()
    if metric == 'balanced_accuracy':
        scopes = [rows[:, 0] == u for u in np.unique(rows[:, 0])] if entity_equal else [np.ones(len(rows), dtype=bool)]
        for take in scopes:
            classes = np.unique(target[take])
            for label in classes:
                members = take & (target == label)
                weights[members] = 1 / (len(classes) * members.sum())
    elif metric in RANKING:
        classes = np.unique(target)
        for label in classes:
            take = target == label
            weights[take] = 1 / (len(classes) * take.sum())
        if entity_equal:
            for unit in np.unique(rows[:, 0]):
                take = rows[:, 0] == unit
                weights[take] /= weights[take].sum()
    return weights / weights.mean()


class Normalizer:
    """Training means (missing values are replaced by them) and the mask of non-constant tabular columns."""

    def __init__(self, statistics, tabular_mask):
        self.statistics = statistics
        self.tabular_mask = np.asarray(tabular_mask, dtype=bool)

    @classmethod
    def fit(cls, batches):
        moments, tabular_min, tabular_max = {}, None, None
        for batch in batches:
            tabular = np.asarray(batch['tabular'], dtype=np.float64)
            finite = np.isfinite(tabular)
            low = np.where(finite, tabular, np.inf).min(axis=0)
            high = np.where(finite, tabular, -np.inf).max(axis=0)
            tabular_min = low if tabular_min is None else np.minimum(tabular_min, low)
            tabular_max = high if tabular_max is None else np.maximum(tabular_max, high)
            for name, array in batch.items():
                if array is None or array.shape[1] == 0:
                    continue
                value = np.asarray(array, dtype=np.float64)
                axes = (0,) + tuple(range(2, value.ndim))
                valid = np.isfinite(value)
                value = np.where(valid, value, 0)
                current = (valid.sum(axis=axes), value.sum(axis=axes), np.square(value).sum(axis=axes))
                moments[name] = current if name not in moments else tuple(a + b for a, b in zip(moments[name], current))
        statistics = {}
        for name, (count, total, square) in moments.items():
            mean = total / np.maximum(count, 1)
            scale = np.sqrt(np.maximum(square / np.maximum(count, 1) - mean ** 2, 0))
            scale[scale < 1e-8] = 1
            statistics[name] = {'mean': mean.astype(np.float32), 'scale': scale.astype(np.float32)}
        mask = tabular_max > tabular_min
        if 'tabular' in statistics:
            statistics['tabular'] = {key: value[mask] for key, value in statistics['tabular'].items()}
        return cls(statistics, mask)

    def flat(self, arrays):
        """Mask, fill missing values with the mean (no scaling), flatten and concatenate sequence, tabular, image."""
        parts = []
        for name in ARRAYS:
            array = arrays.get(name)
            if name == 'tabular':
                array = array[:, self.tabular_mask]
            if array is None or array.shape[1] == 0:
                continue
            mean = self.statistics[name]['mean'].reshape((1, -1) + (1,) * (array.ndim - 2))
            parts.append(np.where(np.isfinite(array), array, mean).astype(np.float32).reshape(len(array), -1))
        return np.concatenate(parts, axis=1)


class Forest:
    """A fitted reference forest of one fold; ``predict`` returns the values the task expects."""

    def __init__(self, model, normalizer, metric):
        self.model, self.normalizer, self.metric = model, normalizer, metric

    def predict(self, arrays, batch_size=512):
        out = []
        for start in range(0, len(arrays['sequence']), batch_size):
            flat = self.normalizer.flat({k: None if v is None else v[start:start + batch_size] for k, v in arrays.items()})
            if self.metric in RANKING:
                classes = list(self.model.classes_)
                out.append(self.model.predict_proba(flat)[:, classes.index(1)] if 1 in classes else np.zeros(len(flat)))
            else:
                out.append(self.model.predict(flat))
        return np.concatenate(out).astype(float) if out else np.empty(0)


def fit(units: Units, metric: str, aggregation: str, class_values, jobs: int = 1) -> tuple[Forest, dict]:
    """Train the reference forest on cached development units; returns the forest and a training record."""
    limit = min(SAMPLE_CAP, MATRIX_LIMIT_BYTES // max(4 * units.raw_width, 1))
    rows = units.select(limit, SEED, class_values=class_values)
    target = units.read_targets(rows)
    weights = training_weights(rows, target, metric, aggregation)
    normalizer = Normalizer.fit(units.batches(rows))
    width = units.raw_width - len(normalizer.tabular_mask) + int(normalizer.tabular_mask.sum())
    flat = np.empty((len(rows), width), dtype=np.float32)
    start = 0
    for arrays in units.batches(rows):
        stop = start + len(arrays['sequence'])
        flat[start:stop] = normalizer.flat(arrays)
        start = stop
    kind = RandomForestClassifier if class_values is not None else RandomForestRegressor
    model = kind(**FOREST, n_jobs=jobs, random_state=SEED).fit(flat, target, sample_weight=weights)
    model.set_params(n_jobs=1)
    record = {'rows': len(rows), 'features': width, 'available': int(sum(units.lengths)),
              'kept_tabular_columns': int(normalizer.tabular_mask.sum())}
    return Forest(model, normalizer, metric), record
