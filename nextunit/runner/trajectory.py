"""One trajectory: an agent develops a predictor for one fold, which is then sealed and evaluated on hidden units.

Layout under the output root:
  trajectories/<id>/   manifest.json, result.json, OpenCode logs, compute events and logs, smoke checks,
                       sealed_artifact.json, deployment/ (holds hidden labels: never expose it to an agent)
  stages/run-<random>/ the sandbox mount sources (random names, so mount paths reveal nothing about the task)

Phases follow the paper's protocol: development (two hours of active wall time, compute queueing excluded),
submission check and smoke check on the first development unit (failures go back to the agent in the same
session while budget remains), sealing, offline deployment on the hidden units. Interrupted trajectories resume
in the same stage and OpenCode session."""
from __future__ import annotations

import json
import os
import secrets
import shutil
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .. import definition
from ..artifact import seal as sealing
from ..artifact import spec as artifact_spec
from ..eval.evaluator import evaluate, record_ids
from ..eval.fold import FoldView, fold_view
from ..eval.score import score_fold
from ..sandbox import bwrap
from ..sandbox.files import place, place_tree, symbolic_links
from . import opencode
from .broker import Broker, cgroup_command

PROMPT = definition.ROOT / 'prompts' / 'initial_prompt.txt'
REPAIR = ('\n\nContinue in this same OpenCode session. Fix only this development validation or file I/O issue; do not '
          'seek or infer hidden evaluation results. After fixing it, rerun the required development checks and finish.\n')
GiB = 1 << 30


class InfraPause(RuntimeError):
    """Not the agent's fault: the trajectory pauses and resumes later."""


@dataclass
class Settings:
    out: Path
    prepared: Path
    runtime: bwrap.Runtime
    backend: opencode.Backend
    budget_seconds: float = 7200.0
    label: str = 'none'
    pause_below_gib: float = 10.0
    start_below_gib: float = 25.0
    extra: dict = field(default_factory=dict)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    tmp.replace(path)


def free_gib(path: Path) -> float:
    return shutil.disk_usage(path).free / GiB


def trajectory_id(dataset: str, fold: int, label: str, replicate: int = 1) -> str:
    return f'{dataset}_f{fold}_{label}_r{replicate}'


def _development(stage: Path, view: FoldView) -> None:
    root = stage / 'readonly/development'
    for public in view.inputs:
        (root / public).mkdir(parents=True)
        place_tree(view.inputs[public], root / public / 'inputs')
        place(view.labels[public], root / public / 'labels.csv')
    if view.auxiliary is not None:
        place_tree(view.auxiliary, root / 'auxiliary')
    if links := symbolic_links(root):                 # the agent must see regular files only
        raise RuntimeError(f'symbolic link in the development view: {links[0].relative_to(root)}')


def _smoke_view(view: FoldView, destination: Path) -> FoldView:
    """The first development unit (stream tasks: its first chunk only), as in the paper's runs."""
    import pandas as pd
    entity = next(iter(view.inputs))
    source, target = view.inputs[entity], destination / entity / 'inputs'
    target.parent.mkdir(parents=True)
    if view.mode == 'stream':
        chunk = json.loads((source / 'stream.json').read_text())[0]
        target.mkdir()
        place_tree(source / chunk, target / 'chunk_000000')
        (target / 'stream.json').write_text(json.dumps(['chunk_000000']))
        ids = record_ids(target / 'chunk_000000')
    else:
        place_tree(source, target)
        ids = record_ids(target)
    truth = pd.read_csv(view.labels[entity], dtype={'record_id': str})
    truth[truth.record_id.isin(ids)].to_csv(destination / entity / 'labels.csv', index=False)
    return FoldView(view.dataset, view.fold, 'smoke', view.mode, view.metric, view.aggregation, view.class_values,
                    view.stream_layout, {entity: target}, {entity: destination / entity / 'labels.csv'}, {entity: entity}, None)


def _submission(stage: Path, destination: Path) -> None:
    """Copy the workspace (minus the inputs mounted into it), make links relative, check, add info.md."""
    workspace = stage / 'workspace'
    ignore = lambda d, names: list(artifact_spec.WORKSPACE_INPUTS.intersection(names)) if Path(d) == workspace else []
    shutil.copytree(workspace, destination, symlinks=True, copy_function=os.link, ignore=ignore)
    for path in [p for p in destination.rglob('*') if p.is_symlink()]:
        link = path.readlink()
        if link.is_absolute() and link.is_relative_to('/workspace'):
            path.unlink()
            path.symlink_to(os.path.relpath(destination / link.relative_to('/workspace'), path.parent))
    sealing.validate(destination)
    shutil.copy2(stage / 'readonly/info.md', destination / 'info.md')


class Trajectory:
    def __init__(self, settings: Settings, broker: Broker, dataset: str, fold: int, replicate: int = 1):
        self.s, self.broker, self.dataset, self.fold = settings, broker, dataset, fold
        self.id = trajectory_id(dataset, fold, settings.label, replicate)
        self.dir = settings.out / 'trajectories' / self.id
        self.manifest_path, self.result_path = self.dir / 'manifest.json', self.dir / 'result.json'
        self.spec = {'trajectory_id': self.id, 'dataset': dataset, 'fold': fold, 'condition': settings.label,
                     'replicate': replicate, 'model': settings.backend.model, 'reasoning_effort': settings.backend.reasoning_effort}

    # --- bookkeeping -----------------------------------------------------------------------------------------------
    def _finish(self, manifest: dict, status: str, category: str | None, phase: str, extra: dict | None = None) -> dict:
        manifest.update(status=status, phase=phase, failure_category=category, finished_at_utc=utc_now())
        save(self.manifest_path, manifest)
        result = {**self.spec, 'status': status, 'failure_category': category, 'phase': phase,
                  'development_active_wall_seconds': manifest.get('development_active_wall_seconds'),
                  'compute_queue_wait_seconds': manifest.get('compute_queue_wait_seconds'),
                  'tokens': manifest.get('token_stats'), 'finished_at_utc': utc_now(), **(extra or {})}
        save(self.result_path, result)
        return result

    def _mounts(self, stage: Path):
        def mounts():
            readonly = [(stage / 'readonly/development', '/workspace/development'), (stage / 'readonly/task.md', '/workspace/task.md'),
                        (stage / 'readonly/info.md', '/workspace/info.md'), (stage / 'readonly/skills', '/skills')]
            return readonly, [(stage / 'workspace', '/workspace'), (stage / 'tmp', '/tmp')]
        return mounts

    def _new_stage(self) -> Path:
        stage = self.s.out / 'stages' / ('run-' + secrets.token_hex(4))
        for name in ('readonly/development', 'readonly/skills', 'workspace', 'opencode', 'tmp/home'):
            (stage / name).mkdir(parents=True, exist_ok=True)
        stage.chmod(0o700)
        shutil.copyfile(definition.task_md(self.dataset), stage / 'readonly/task.md')
        shutil.copyfile(definition.info_md(self.dataset), stage / 'readonly/info.md')
        _development(stage, fold_view(self.dataset, self.fold, 'development', self.s.prepared))
        return stage

    def _guard(self) -> None:
        if free_gib(self.s.out) < self.s.pause_below_gib:
            raise InfraPause(f'free disk below {self.s.pause_below_gib} GiB')

    def _eval_wrap(self, command):
        slot = self.broker.pool.evaluation_slot()
        return cgroup_command(command, cpu_percent=100 * slot['cpus'], memory=f"{slot['memory_gb']}G", oom_omit=True)

    def _eval_gpu(self):
        return None if self.broker.pool.gpus > 0 else False      # None: the GPU if the machine has one

    # --- the run ---------------------------------------------------------------------------------------------------
    def run(self) -> dict:
        previous = json.loads(self.result_path.read_text()) if self.result_path.exists() else None
        if previous and previous['status'] in ('completed', 'failed'):
            return previous
        manifest = json.loads(self.manifest_path.read_text()) if self.manifest_path.exists() else None
        resumable = bool(manifest and manifest.get('session_id') and Path(manifest.get('stage', '/nonexistent')).is_dir())
        if not resumable:
            if manifest and Path(manifest.get('stage', '/nonexistent')).is_dir():
                shutil.rmtree(manifest['stage'])          # nothing to resume without a session: start over
            manifest = {'schema': 1, 'spec': self.spec, 'status': 'running', 'phase': 'development', 'started_at_utc': utc_now(),
                        'harness': 'OpenCode', 'model': self.s.backend.model, 'budget_seconds': self.s.budget_seconds,
                        'stage': str(self._new_stage()), 'attempts': 0, 'development_active_wall_seconds': 0.0}
        stage = Path(manifest['stage'])
        backend, runtime = self.s.backend, self.s.runtime
        (stage / 'readonly/opencode.json').write_text(json.dumps(backend.config(runtime), indent=2))
        manifest['credentials'] = backend.stage_credentials(stage)
        handle = self.broker.register(self.id, stage, self.dir, runtime, self._mounts(stage), gpu_default=True)
        manifest.update(status='running', resumed_at_utc=utc_now() if resumable else None,
                        pool={**asdict(self.broker.pool), 'evaluation_slot': self.broker.pool.evaluation_slot()})
        save(self.manifest_path, manifest)
        try:
            return self._loop(manifest, stage, handle)
        except InfraPause as error:
            manifest.update(infra_detail=str(error))
            return self._finish(manifest, 'infra_paused', 'INFRA_STORAGE' if 'disk' in str(error) else 'INFRA', manifest.get('phase'))
        finally:
            try:
                handle.close()
            finally:
                backend.remove_credentials(stage)

    def _loop(self, manifest: dict, stage: Path, handle) -> dict:
        s, backend, runtime = self.s, self.s.backend, self.s.runtime
        prior = float(manifest.get('development_active_wall_seconds') or 0.0)
        origin, queue_origin = time.monotonic(), handle.wait_seconds()
        excluded = [0.0]
        active = lambda: prior + max(0.0, time.monotonic() - origin - excluded[0] - max(0.0, handle.wait_seconds() - queue_origin))
        view = fold_view(self.dataset, self.fold, 'development', s.prepared)
        smoke_dir = self.dir / 'smoke_inputs'
        shutil.rmtree(smoke_dir, ignore_errors=True)
        smoke = _smoke_view(view, smoke_dir)
        scratch = s.out / 'scratch'
        scratch.mkdir(parents=True, exist_ok=True)
        repair = manifest.get('repair_prompt')
        while manifest.get('phase') != 'sealed' and active() < s.budget_seconds:
            manifest['attempts'] += 1
            prompt = PROMPT.read_text() + ((REPAIR + repair + '\n') if repair else '')

            def checkpoint(session, _):
                manifest.update(session_id=session, development_active_wall_seconds=active(),
                                compute_queue_wait_seconds=handle.wait_seconds())
                save(self.manifest_path, manifest)
            record = opencode.run(backend, stage, runtime, handle, prompt, self.dir, session_id=manifest.get('session_id'),
                                  attempt=manifest['attempts'], budget_seconds=max(0.0, s.budget_seconds - active()),
                                  on_progress=checkpoint, guard=self._guard)
            excluded[0] += record['stall_seconds']          # a provider stall is not development time
            manifest['stall_seconds_excluded'] = (manifest.get('stall_seconds_excluded') or 0.0) + record['stall_seconds']
            manifest.update(process=record, session_id=record['session_id'] or manifest.get('session_id'),
                            development_active_wall_seconds=active(), compute_queue_wait_seconds=handle.wait_seconds())
            manifest['token_stats'] = _add(manifest.get('token_stats'), record['token_stats'])
            handle.cancel_jobs()
            save(self.manifest_path, manifest)
            if record['failure_category'] == 'INFRA_PROVIDER_STALL':
                manifest.setdefault('stalls', []).append({'attempt': manifest['attempts'], 'seconds': record['stall_seconds']})
                if len(manifest['stalls']) <= opencode.STALL_RETRIES:
                    continue
            if record['timed_out']:
                return self._finish(manifest, 'failed', 'DEVELOPMENT_WALL_TIMEOUT', 'development')
            if record['returncode'] != 0 or record['failure_category']:
                raise InfraPause(record['failure_category'] or 'OPENCODE_PROCESS_ERROR')
            if manifest.get('session_id'):
                manifest['session_export'] = opencode.export_session(backend, stage, runtime, handle, manifest['session_id'], self.dir)
            submission = stage / f"submission_{manifest['attempts']:03d}"
            try:
                _submission(stage, submission)
            except (OSError, ValueError, json.JSONDecodeError) as error:
                shutil.rmtree(submission, ignore_errors=True)
                repair = manifest['repair_prompt'] = f'Artifact submission validation failed: {type(error).__name__}: {error}'
                manifest['phase'] = 'repair'
                save(self.manifest_path, manifest)
                continue
            remaining = s.budget_seconds - active()
            if remaining <= 0:
                shutil.rmtree(submission, ignore_errors=True)
                break
            with self.broker.slot(handle, **self.broker.pool.evaluation_slot()):
                result = evaluate(submission, smoke, self.dir / f"smoke_attempt_{manifest['attempts']:03d}", runtime,
                                  scratch=scratch, validation_only=True, observation_seconds=remaining, wrap=self._eval_wrap,
                                  gpu=self._eval_gpu())
            if result['status'] != 'completed':
                shutil.rmtree(submission, ignore_errors=True)
                detail = result.get('error') or result['status']
                repair = manifest['repair_prompt'] = 'Development-only inference validation failed: ' + str(detail)[:3000]
                manifest.update(phase='repair', smoke_status=result['status'])
                save(self.manifest_path, manifest)
                continue
            if active() >= s.budget_seconds:
                shutil.rmtree(submission, ignore_errors=True)
                break
            handle.cancel_jobs()
            sealed = stage / 'sealed'
            submission.rename(sealed)
            record = {'created_at_utc': utc_now(), 'files': sealing.file_manifest(sealed)}
            save(self.dir / 'sealed_artifact.json', record)
            for name in ('workspace', 'tmp'):
                shutil.rmtree(stage / name, ignore_errors=True)
            for path in sealed.rglob('*'):
                if path.is_file() and not path.is_symlink():
                    path.chmod(path.stat().st_mode & ~0o222)
            manifest.update(phase='sealed', status='sealed', smoke_status='completed', development_active_wall_seconds=active(),
                            sealed_at_utc=utc_now(), repair_prompt=None)
            save(self.manifest_path, manifest)
        if manifest.get('phase') != 'sealed':
            return self._finish(manifest, 'failed', 'DEVELOPMENT_WALL_TIMEOUT', 'development')
        # Deployment: only now is the hidden role of the fold loaded.
        hidden = fold_view(self.dataset, self.fold, 'hidden', s.prepared)
        shutil.rmtree(self.dir / 'deployment', ignore_errors=True)
        with self.broker.slot(handle, **self.broker.pool.evaluation_slot()):
            result = evaluate(stage / 'sealed', hidden, self.dir / 'deployment', runtime, scratch=scratch,
                              sealed_record=self.dir / 'sealed_artifact.json', wrap=self._eval_wrap,
                              gpu=self._eval_gpu())
        if result['status'] != 'completed':
            return self._finish(manifest, 'failed', 'DEPLOYMENT_EVALUATION_FAILED', 'deployment',
                                {'deployment_error': result.get('error'), **score_fold(self.dataset, self.fold, None, 'failed')})
        scores = score_fold(self.dataset, self.fold, result['E'], 'completed')
        return self._finish(manifest, 'completed', None, 'deployment', {'quality_score': result['primary_score'], **scores})


def _add(total: dict | None, part: dict | None) -> dict | None:
    if part is None:
        return total
    if total is None:
        return dict(part)
    return {k: (total.get(k) or 0) + (part.get(k) or 0) for k in part}
