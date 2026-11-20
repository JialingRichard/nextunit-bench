"""Offline tests of the compute broker's pool: no agent, no credentials.

Run: python -m unittest discover -s tests"""
import shutil
import tempfile
import threading
import unittest
from pathlib import Path

from nextunit.runner.broker import Broker, Pool, validate_request


class PoolTests(unittest.TestCase):
    def test_defaults_are_the_paper_pool(self):
        self.assertEqual(Pool().evaluation_slot(), {'cpus': 4, 'memory_gb': 8, 'gpu': True})

    def test_invalid_pools_are_refused(self):
        for bad in ({'cpus': 2}, {'memory_gb': 4}, {'gpus': -1}, {'cpus': 0}, {'cpus': 8.0}):
            with self.subTest(pool=bad), self.assertRaises(ValueError):
                Pool(**bad)

    def test_pool_without_gpu_runs_on_cpu(self):
        pool = Pool(gpus=0)
        request = {'tool': 'run_command', 'arguments': {'command': 'true', 'gpu': True}}
        self.assertFalse(validate_request(request, pool, gpu_default=True)['gpu'])
        self.assertFalse(validate_request({'tool': 'run_command', 'arguments': {'command': 'true'}}, pool, True)['gpu'])
        self.assertEqual(pool.evaluation_slot(), {'cpus': 4, 'memory_gb': 8, 'gpu': False})

    def test_small_pool_evaluation_slot_is_granted(self):
        pool = Pool(cpus=2, memory_gb=4, gpus=0, trajectory_cpus=2, trajectory_memory_gb=4)
        broker, root = Broker(pool), Path(tempfile.mkdtemp(prefix='nextunit-pool-'))
        try:
            (root / 'stage').mkdir()
            handle = broker.register('t', root / 'stage', root / 'out', None, lambda: ([], []))
            granted = threading.Event()

            def take():
                with broker.slot(handle, **pool.evaluation_slot()):
                    granted.set()
            worker = threading.Thread(target=take, daemon=True); worker.start(); worker.join(5)
            self.assertTrue(granted.is_set(), 'evaluation slot never granted')
            handle.close()
        finally:
            shutil.rmtree(root)


if __name__ == '__main__':
    unittest.main()
