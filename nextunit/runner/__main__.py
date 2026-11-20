"""Run agents on the benchmark.

  python -m nextunit.runner run    --config RUN.json (--dataset DS --fold K | --all) [--jobs N]
  python -m nextunit.runner status --config RUN.json
  python -m nextunit.runner score  --config RUN.json

RUN.json: {"out": dir, "prepared": PREPARED_ROOT, "runtime": runtime file, "opencode": OpenCode binary,
           "model": "gpt-6-luna", "reasoning_effort": "max", "label": "none", "budget_seconds": 7200,
           "pool": {"cpus": 8, "memory_gb": 16, "gpus": 1}}
Credentials come from the environment only (NEXTUNIT_OPENCODE_AUTH, or NEXTUNIT_API_KEY [+ NEXTUNIT_API_BASE]).
Stopping `run` (SIGTERM or Ctrl-C) kills its agents and jobs; running the same command again resumes.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .. import definition
from ..eval.score import summarize
from ..sandbox.bwrap import Runtime
from . import opencode
from .broker import UNIT_PREFIX, Broker, Pool, stop_all_units
from .trajectory import Settings, Trajectory, free_gib, trajectory_id


def load(path: Path) -> tuple[Settings, Broker, dict]:
    config = json.loads(Path(path).read_text())
    backend = opencode.Backend.from_environment(config['opencode'], config['model'], config.get('reasoning_effort', 'max'))
    settings = Settings(out=Path(config['out']), prepared=Path(config['prepared']), runtime=Runtime.load(config['runtime']),
                        backend=backend, budget_seconds=float(config.get('budget_seconds', 7200)), label=config.get('label', 'none'))
    settings.out.mkdir(parents=True, exist_ok=True)
    return settings, Broker(Pool(**config.get('pool', {}))), config


def results(settings: Settings) -> dict:
    out = {}
    for dataset, fold in definition.all_folds():
        path = settings.out / 'trajectories' / trajectory_id(dataset, fold, settings.label) / 'result.json'
        out[(dataset, fold)] = json.loads(path.read_text()) if path.exists() else None
    return out


def stop_on_signal(signum, _frame) -> None:
    """Agents and jobs run in their own systemd scopes and would outlive the runner: kill them, remove the run-local
    credential copies, and exit. Trajectories stay resumable (manifest with session ID)."""
    stop_all_units()
    for stage in list(opencode.STAGED):
        opencode.Backend.remove_credentials(stage)
    print(json.dumps({'stopped_by_signal': signal.Signals(signum).name}), flush=True)
    os._exit(128 + signum)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog='python -m nextunit.runner')
    parser.add_argument('command', choices=['run', 'status', 'score'])
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--dataset', choices=definition.datasets())
    parser.add_argument('--fold', type=int)
    parser.add_argument('--all', action='store_true')
    parser.add_argument('--jobs', type=int, default=1)
    args = parser.parse_args(argv)
    settings, broker, _ = load(args.config)
    if args.command == 'run':
        signal.signal(signal.SIGTERM, stop_on_signal)
        signal.signal(signal.SIGINT, stop_on_signal)
        todo = [(args.dataset, args.fold)] if not args.all else [k for k, v in results(settings).items()
                                                                 if v is None or v['status'] not in ('completed', 'failed')]
        print(json.dumps({'folds': len(todo), 'jobs': args.jobs, 'systemd_scopes': UNIT_PREFIX + '*'}), flush=True)
        lock = threading.Lock()

        def one(key):
            while free_gib(settings.out) < settings.start_below_gib:   # disk guard: do not start new trajectories
                time.sleep(60)
            trajectory = Trajectory(settings, broker, *key)
            with lock:
                print(json.dumps({'trajectory_id': trajectory.id, 'status': 'started'}), flush=True)
            try:
                result = trajectory.run()
            except Exception as error:                    # a runner fault: record it, keep the others going
                result = {**trajectory.spec, 'status': 'infra_paused', 'failure_category': 'INFRA_RUNNER_ERROR',
                          'error': f'{type(error).__name__}: {error}'[:2000]}
                trajectory.result_path.parent.mkdir(parents=True, exist_ok=True)
                trajectory.result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
            with lock:
                print(json.dumps({k: result.get(k) for k in ('trajectory_id', 'status', 'failure_category', 'E', 'S')}), flush=True)
            return result
        with ThreadPoolExecutor(max(1, args.jobs)) as pool:
            list(pool.map(one, todo))
        return 0
    found = results(settings)
    if args.command == 'status':
        counts = {}
        for (dataset, fold), value in found.items():
            manifest = settings.out / 'trajectories' / trajectory_id(dataset, fold, settings.label) / 'manifest.json'
            if value:
                status = value['status']
            elif manifest.exists():                   # in progress, or stopped before it finished: resumable
                status = 'started: ' + json.loads(manifest.read_text()).get('phase', 'development')
            else:
                status = 'not started'
            counts[status] = counts.get(status, 0) + 1
        print(json.dumps(counts))
        return 0
    done = {k: v for k, v in found.items() if v and v['status'] in ('completed', 'failed')}
    report = {'folds_finished': len(done), 'delivered': sum(v['status'] == 'completed' for v in done.values())}
    if len(done) == 58:
        summary = summarize({k: v['S'] for k, v in done.items()})
        report.update({name: {x: summary[name][x] for x in ('S', 'ci_low', 'ci_high')} for name in summary})
    print(json.dumps(report, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
