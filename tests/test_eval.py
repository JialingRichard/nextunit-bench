"""Offline tests of the evaluator and scoring: no dataset, no credentials, no GPU.

Run: python -m unittest discover -s tests
The end-to-end cases need bubblewrap and unprivileged user namespaces; they use the host interpreter."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from nextunit import definition
from nextunit.artifact import seal
from nextunit.eval.evaluator import evaluate, score_stored
from nextunit.eval.fold import FoldView
from nextunit.eval.score import fold_scores, summarize
from nextunit.eval.scoring import FoldScorer, PredictionError
from nextunit.sandbox.bwrap import Runtime

HAS_BWRAP = shutil.which('bwrap') is not None


def view(root: Path, mode='batch', metric='mae', aggregation='entity_equal', class_values=None, layout=None):
    units = {f'entity_{i:04d}': root / f'u{i}' for i in (1, 2)}
    return FoldView(dataset='SYNTH', fold=1, role='hidden', mode=mode, metric=metric, aggregation=aggregation,
                    class_values=class_values, stream_layout=layout,
                    inputs={k: v / 'inputs' for k, v in units.items()}, labels={k: v / 'labels.csv' for k, v in units.items()},
                    entity_mapping={k: k for k in units}, auxiliary=None)


def make_units(root: Path, mode='batch'):
    for i in (1, 2):
        unit = root / f'u{i}'
        ids = [f'r{i}_{j}' for j in range(6)]
        pd.DataFrame({'record_id': ids, 'target': [float(j + i) for j in range(6)]}).to_csv(unit.mkdir(parents=True) or unit / 'labels.csv', index=False)
        inputs = unit / 'inputs'
        if mode == 'batch':
            inputs.mkdir()
            pd.DataFrame({'record_id': ids, 'x': [float(j + i) for j in range(6)]}).to_csv(inputs / 'records.csv', index=False)
        else:
            chunks = []
            for c in range(3):
                d = inputs / f'chunk_{c:03d}'; d.mkdir(parents=True); chunks.append(d.name)
                pd.DataFrame({'record_id': ids[2 * c:2 * c + 2], 'x': [float(2 * c + i), float(2 * c + 1 + i)]}).to_csv(d / 'records.csv', index=False)
            (inputs / 'stream.json').write_text(json.dumps(chunks))


ARTIFACT = '''import pandas as pd
from pathlib import Path
SEEN = []
def predict(input_directory, output_file):
    frame = pd.read_csv(Path(input_directory) / 'records.csv', dtype={'record_id': str})
    SEEN.append(len(frame))
    pd.DataFrame({'record_id': frame.record_id, 'prediction': frame.x + OFFSET}).to_csv(output_file, index=False)
'''


def make_artifact(root: Path, offset=0.0, extra=''):
    a = root / 'artifact'; a.mkdir()
    (a / 'artifact.py').write_text(ARTIFACT.replace('OFFSET', repr(offset)) + extra)
    (a / 'resources.json').write_text('{}')
    return a


class ScoreTests(unittest.TestCase):
    def test_fold_scores_edges(self):
        self.assertEqual(fold_scores(0, 0, 'completed'), (0, 0))
        self.assertEqual(fold_scores(0, 1, 'completed'), (100, 0))
        self.assertEqual(fold_scores(1, 0, 'completed'), (0, 100))
        self.assertEqual(fold_scores(None, 1, 'failed'), (0, 100))
        self.assertAlmostEqual(fold_scores(0.5, 1, 'completed')[0], 50)
        self.assertAlmostEqual(fold_scores(2, 1, 'completed')[1], 50)

    def test_summary_needs_every_fold(self):
        folds = {key: 50.0 for key in definition.all_folds()}
        s = summarize(folds)
        self.assertEqual((s['S24']['datasets'], s['S_noshortcut']['datasets']), (24, 21))
        self.assertAlmostEqual(s['S24']['S'], 50.0)
        folds.pop(definition.all_folds()[0])
        with self.assertRaises(ValueError):
            summarize(folds)

    def test_scorer_metrics(self):
        def frame(t, p):
            ids = [str(i) for i in range(len(t))]
            return pd.DataFrame({'record_id': ids, 'prediction': p}), pd.DataFrame({'record_id': ids, 'target': t})
        p, t = frame([0, 0, 1, 1], [0, 1, 1, 1])
        s = FoldScorer('balanced_accuracy', 'pooled', (0, 1)); s.add('entity_0001', p, t)
        self.assertAlmostEqual(s.result()['primary_score'], 0.75)
        s = FoldScorer('accuracy', 'entity_equal', (0, 1)); s.add('entity_0001', p, t)
        self.assertAlmostEqual(s.result()['primary_score'], 0.75)
        with self.assertRaises(PredictionError):
            FoldScorer('accuracy', 'entity_equal', (0,)).add('entity_0001', p, t)
        p2 = p.iloc[:3]
        with self.assertRaises(PredictionError):
            FoldScorer('accuracy', 'entity_equal', (0, 1)).add('entity_0001', p2, t)


@unittest.skipUnless(HAS_BWRAP, 'bubblewrap not installed')
class EvaluatorTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='nextunit-test-'))

    def tearDown(self):
        for p in self.root.rglob('*'):
            if not p.is_symlink():
                p.chmod(0o755 if p.is_dir() else 0o644)
        shutil.rmtree(self.root)

    def run_eval(self, artifact, v, **kw):
        sealed = self.root / 'sealed' / 'artifact'; sealed.parent.mkdir(exist_ok=True)
        record = seal.seal(artifact, sealed)
        return evaluate(sealed, v, self.root / 'out', Runtime.host(), scratch=self.root / 'scratch', sealed_record=record, gpu=False, **kw)

    def test_batch_perfect_and_rescore(self):
        make_units(self.root / 'data')
        v = view(self.root / 'data')
        r = self.run_eval(make_artifact(self.root, 0.0), v)
        self.assertEqual(r['status'], 'completed'); self.assertEqual(r['E'], 0.0)
        files = {e: self.root / 'out' / e / 'predictions.csv' for e in v.inputs}
        self.assertEqual(score_stored(v, files)['E'], 0.0)

    def test_batch_offset(self):
        make_units(self.root / 'data')
        r = self.run_eval(make_artifact(self.root, 0.5), view(self.root / 'data'))
        self.assertAlmostEqual(r['E'], 0.5)

    def test_stream_layouts_keep_state(self):
        for layout in ('flat', 'manifest', 'manifest_with_flat_alias'):
            with self.subTest(layout=layout):
                root = self.root / layout; make_units(root / 'data', mode='stream')
                extra = '' if layout == 'flat' else '''
_old = predict
def predict(input_directory, output_file):
    import json
    d = Path(input_directory)
    if not (d / 'records.csv').exists():
        d = d / json.loads((d / 'stream.json').read_text())[0]
    return _old(str(d), output_file)
'''
                (root / 'a').mkdir(parents=True)
                artifact = make_artifact(root / 'a', 0.0, extra)
                sealed = root / 'sealed' / 'artifact'; sealed.parent.mkdir()
                record = seal.seal(artifact, sealed)
                r = evaluate(sealed, view(root / 'data', mode='stream', layout=layout), root / 'out', Runtime.host(),
                             scratch=root / 'scratch', sealed_record=record, gpu=False, strict_stream=True)
                self.assertEqual(r['status'], 'completed', r.get('error')); self.assertEqual(r['E'], 0.0)

    def test_delayed_stream_output_fails(self):
        make_units(self.root / 'data', mode='stream')
        delay = '''
_old = predict
_held = []
def predict(input_directory, output_file):
    # hold the first chunk back and write it together with the second
    import pandas as pd
    _old(input_directory, output_file)
    frame = pd.read_csv(output_file, dtype={'record_id': str})
    if len(SEEN) == 1:
        _held.append(frame); frame.iloc[:0].to_csv(output_file, index=False)
    elif _held:
        pd.concat([_held.pop(), frame]).to_csv(output_file, index=False)
'''
        v = view(self.root / 'data', mode='stream', layout='flat')
        r = self.run_eval(make_artifact(self.root, 0.0, delay), v)
        self.assertEqual(r['status'], 'failed')
        self.assertIn('chunk', r['error'])

    def test_failures(self):
        make_units(self.root / 'data')
        broken = make_artifact(self.root, 0.0, '\nraise SystemExit(3)\n')
        r = self.run_eval(broken, view(self.root / 'data'))
        self.assertEqual(r['status'], 'failed')

    def test_tampered_seal_is_refused(self):
        make_units(self.root / 'data')
        sealed = self.root / 'sealed' / 'artifact'; sealed.parent.mkdir()
        record = seal.seal(make_artifact(self.root, 0.0), sealed)
        target = sealed / 'artifact.py'; target.chmod(0o644); target.write_text(target.read_text() + '\n# changed\n')
        with self.assertRaises(seal.ArtifactError):
            evaluate(sealed, view(self.root / 'data'), self.root / 'out', Runtime.host(), scratch=self.root / 'scratch',
                     sealed_record=record, gpu=False)

    def test_no_network_in_sandbox(self):
        make_units(self.root / 'data')
        probe = '''
import socket
try:
    socket.create_connection(('1.1.1.1', 53), timeout=2); NET = True
except OSError:
    NET = False
assert not NET, 'network reachable'
'''
        r = self.run_eval(make_artifact(self.root, 0.0, probe), view(self.root / 'data'))
        self.assertEqual(r['status'], 'completed', r.get('error'))


if __name__ == '__main__':
    unittest.main()
