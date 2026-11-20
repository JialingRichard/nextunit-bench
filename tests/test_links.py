"""Prepared roots may contain symbolic links (to raw files, or to data kept elsewhere). Sandboxed processes see
only what is mounted, so every view the runner and the evaluator build must hold regular files.

Run: python -m unittest discover -s tests"""
import shutil
import tempfile
import unittest
from pathlib import Path

from nextunit.artifact import seal
from nextunit.eval.evaluator import evaluate
from nextunit.runner.trajectory import _development, _smoke_view
from nextunit.sandbox.bwrap import Runtime
from nextunit.sandbox.files import place_tree, symbolic_links

from test_eval import HAS_BWRAP, make_artifact, make_units, view


def link_out(root: Path, elsewhere: Path) -> None:
    """Move every labels.csv and input file of the units elsewhere and leave absolute symbolic links behind."""
    for path in sorted(p for p in root.rglob('*') if p.is_file()):
        moved = elsewhere / path.relative_to(root)
        moved.parent.mkdir(parents=True, exist_ok=True)
        path.rename(moved)
        path.symlink_to(moved.resolve())


class LinkedPreparedRoot(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='nextunit-links-'))
        make_units(self.root / 'data')
        link_out(self.root / 'data', self.root / 'elsewhere')

    def tearDown(self):
        for p in self.root.rglob('*'):
            if not p.is_symlink():
                p.chmod(0o755 if p.is_dir() else 0o644)
        shutil.rmtree(self.root)

    def test_development_view_has_regular_files(self):
        stage = self.root / 'stage'
        _development(stage, view(self.root / 'data'))
        development = stage / 'readonly/development'
        self.assertEqual(symbolic_links(development), [])
        for public in ('entity_0001', 'entity_0002'):
            self.assertTrue((development / public / 'labels.csv').is_file())
            self.assertTrue((development / public / 'inputs/records.csv').is_file())

    def test_smoke_view_has_regular_files(self):
        smoke = _smoke_view(view(self.root / 'data'), self.root / 'smoke')
        self.assertEqual(symbolic_links(self.root / 'smoke'), [])
        self.assertTrue(next(iter(smoke.inputs.values())).joinpath('records.csv').is_file())

    def test_place_tree_resolves_links(self):
        place_tree(self.root / 'data/u1', self.root / 'copy')
        self.assertEqual(symbolic_links(self.root / 'copy'), [])
        self.assertEqual((self.root / 'copy/labels.csv').stat().st_ino, (self.root / 'elsewhere/u1/labels.csv').stat().st_ino)

    @unittest.skipUnless(HAS_BWRAP, 'bubblewrap not available')
    def test_evaluator_reads_linked_inputs(self):
        for link_inputs in (True, False):
            with self.subTest(link_inputs=link_inputs):
                sealed = self.root / f'sealed_{link_inputs}' / 'artifact'; sealed.parent.mkdir()
                record = seal.seal(make_artifact(self._fresh(f'a_{link_inputs}'), 0.0), sealed)
                r = evaluate(sealed, view(self.root / 'data'), self.root / f'out_{link_inputs}', Runtime.host(),
                             scratch=self.root / 'scratch', sealed_record=record, gpu=False, link_inputs=link_inputs)
                self.assertEqual(r['status'], 'completed', r.get('error'))
                self.assertEqual(r['E'], 0.0)

    def _fresh(self, name):
        d = self.root / name; d.mkdir(); return d


if __name__ == '__main__':
    unittest.main()
