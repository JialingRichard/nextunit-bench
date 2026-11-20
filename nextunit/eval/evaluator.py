"""The fixed evaluator: run a sealed artifact on hidden units offline and score it.

Each unit runs in a fresh sandboxed process that sees only the artifact, the
runtime and that unit's inputs (in stream tasks one chunk at a time). Labels
are joined outside the sandbox. ``score_stored`` re-scores predictions that an
earlier evaluation wrote, through the same scoring code.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .fold import FoldView
from .metrics import loss
from .scoring import FoldScorer, PredictionError

OUTPUT_COLUMNS = ['record_id', 'prediction']


def check_part(frame: pd.DataFrame) -> None:
    if list(frame.columns) != OUTPUT_COLUMNS:
        raise PredictionError('predict CSV must have record_id,prediction columns')


def check_prediction(frame: pd.DataFrame) -> None:
    if frame.empty:
        raise PredictionError('输出 CSV 为 0 行；未返回请求记录。')
    if frame.record_id.duplicated().any() or not np.isfinite(frame.prediction).all():
        raise PredictionError('prediction record IDs must be unique; values must be finite')


def read_prediction(path: Path | str) -> pd.DataFrame:
    return pd.read_csv(path, dtype={'record_id': str})


def finish(result: dict, view: FoldView) -> dict:
    result.update(dataset=view.dataset, fold=view.fold, role=view.role)
    if result['status'] == 'completed' and result.get('primary_score') is not None:
        result['E'] = loss(view.metric, result['primary_score'])
    return result


def score_stored(view: FoldView, prediction_files: dict[str, Path], scored_csv: Path | None = None) -> dict:
    """Score per-unit prediction files (public ID -> predictions.csv) of one fold."""
    if sorted(prediction_files) != sorted(view.inputs):
        raise PredictionError(f'units {sorted(prediction_files)} given, {sorted(view.inputs)} expected')
    scorer = FoldScorer(view.metric, view.aggregation, view.class_values, scored_csv=scored_csv)
    for entity in sorted(view.inputs):
        prediction = read_prediction(prediction_files[entity])
        check_part(prediction)
        check_prediction(prediction)
        scorer.add(entity, prediction, view.labels[entity])
    return finish(scorer.result(), view)


# ---------------------------------------------------------------------------
# Running a sealed artifact

import json
import os
import re
import select
import shutil
import subprocess
import tempfile
import time

from ..artifact import seal as sealing
from ..sandbox import bwrap
from ..sandbox.files import place
from ..sandbox.process import stop

WORKER = Path(__file__).resolve().parents[1] / 'artifact' / 'predict_worker.py'
REQUEST_INDEXES = ('query.csv', 'requests.csv', 'records.csv', 'signals.csv', 'features.csv')
FAILURES = (PredictionError, RuntimeError, ValueError)


class MissingOutput(RuntimeError):
    """The predictor returned without writing its output file."""


def record_ids(directory: Path) -> list[str]:
    """Requested record IDs of one input directory (one chunk in stream tasks)."""
    directory = Path(directory)
    for name in REQUEST_INDEXES:
        path = directory / name
        if path.is_file():
            if 'record_id' in pd.read_csv(path, nrows=0).columns:
                return pd.read_csv(path, usecols=['record_id'], dtype={'record_id': str}).record_id.tolist()
    path = directory / 'records.json'
    if path.exists():
        return [str(row['record_id']) for row in json.loads(path.read_text())]
    raise ValueError(f'No request index in {directory}')


def run_unit(runtime_dir: Path, runtime: bwrap.Runtime, source: Path, destination: Path, mode: str, *,
             stream_layout: str | None, input_path: str, scratch: Path, deadline: float | None = None,
             gpu: bool = False, strict_stream: bool = True, link_inputs: bool = True,
             wrap=None) -> tuple[pd.DataFrame | None, dict]:
    """Run one unit in a fresh sandboxed process. In stream tasks one chunk is mounted at a time and the
    predictor module persists across chunks. Returns (predictions, usage); predictions is None if the
    deadline passed first."""
    destination.mkdir(parents=True, exist_ok=True)
    chunks = json.loads((source / 'stream.json').read_text()) if mode == 'stream' else ['.']
    layout = stream_layout or 'flat'
    # Mount sources appear in /proc/self/mountinfo, so they live under neutral scratch names.
    with tempfile.TemporaryDirectory(prefix='phm-input-', dir=scratch) as temp, \
            tempfile.TemporaryDirectory(prefix='phm-output-', dir=scratch) as output_temp:
        view, work_output = Path(temp), Path(output_temp)
        copy_input = place if link_inputs else shutil.copy2
        argv = [runtime.python, '/runtime/predict_worker.py', input_path]
        command = bwrap.command(runtime, argv, readonly=[(runtime_dir, '/runtime'), (runtime_dir / 'artifact', '/artifact'),
                                                         (view, input_path)],
                                writable=[(work_output, '/output')], cwd='/artifact', env={'PYTHONPATH': '/runtime'}, gpu=gpu)
        if wrap is not None:
            command = wrap(command)
        start = time.monotonic()
        frames, usages, censored, failure = [], [], False, None
        with (destination / 'stderr.log').open('w') as stderr:
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr,
                                       text=True, start_new_session=True)
            try:
                for index, chunk in enumerate(chunks):
                    for item in view.iterdir():
                        shutil.rmtree(item) if item.is_dir() else item.unlink()
                    if mode == 'stream' and layout != 'flat':
                        shutil.copytree(source / chunk, view / chunk, copy_function=copy_input)
                        (view / 'stream.json').write_text(json.dumps([chunk]) + '\n')
                    if mode != 'stream' or layout in ('flat', 'manifest_with_flat_alias'):
                        shutil.copytree(source / chunk, view, dirs_exist_ok=True, copy_function=copy_input)
                    output_name = f'part_{index:06d}.csv'
                    (work_output / output_name).unlink(missing_ok=True)
                    process.stdin.write(json.dumps({'output_file': '/output/' + output_name}) + '\n')
                    process.stdin.flush()
                    if deadline is not None:
                        ready, _, _ = select.select([process.stdout], [], [], max(0, deadline - time.monotonic()))
                        if not ready:
                            censored = True
                            break
                    line = process.stdout.readline()
                    if not line:
                        raise RuntimeError(f"predict failed: {(destination / 'stderr.log').read_text()}")
                    usages.append(json.loads(line))
                    if not (work_output / output_name).is_file():
                        raise MissingOutput(f'predict returned without writing {output_name}')
                    frame = read_prediction(work_output / output_name)
                    check_part(frame)
                    if strict_stream and mode == 'stream':
                        requested = record_ids(source / chunk)
                        if sorted(frame.record_id) != sorted(requested):
                            raise PredictionError(f'chunk {index}: output IDs differ from the requested IDs of this chunk')
                    frames.append(frame)
                process.stdin.close()
                if not censored:
                    remaining = max(0, deadline - time.monotonic()) if deadline is not None else None
                    try:
                        returncode = process.wait(timeout=remaining)
                    except subprocess.TimeoutExpired:
                        censored = True
                    else:
                        if returncode != 0:
                            raise RuntimeError(f'predict failed; see {destination / "stderr.log"}')
            except Exception as error:  # recorded below, then re-raised
                failure = error
            finally:
                if process.poll() is None:
                    stop(process)
                    process.wait()
        usage = {'wall_seconds': time.monotonic() - start,
                 'cpu_seconds': usages[-1]['cpu_seconds'] if usages else None,
                 'peak_worker_rss_bytes': max((u['max_rss_bytes'] for u in usages), default=None),
                 'predict_calls': len(usages),
                 'status': 'failed' if failure else ('censored' if censored else 'completed')}
    (destination / 'resources.json').write_text(json.dumps(usage, indent=2) + '\n')
    if failure is not None:
        raise failure
    if censored:
        return None, usage
    prediction = pd.concat(frames, ignore_index=True)
    check_prediction(prediction)
    prediction.to_csv(destination / 'predictions.csv', index=False)
    return prediction, usage


def evaluate(artifact: Path, view: FoldView, output: Path, runtime: bwrap.Runtime, *, scratch: Path,
             sealed_record: dict | Path | None = None, observation_seconds: float | None = None,
             validation_only: bool = False, gpu: bool | None = None, strict_stream: bool = True,
             link_inputs: bool = True, wrap=None) -> dict:
    """Run ``artifact`` on every unit of ``view`` and score it. Returns a result with ``status``
    ``completed`` (with ``primary_score`` and ``E``), ``censored`` (deadline) or ``failed`` (with ``error``).

    ``strict_stream``: in stream tasks, each call's output must hold exactly the IDs requested by the current
    chunk (v1.0 default; ``False`` reproduces the paper's check, which compared IDs per unit only; no paper
    score depends on the difference, see KNOWN_ISSUES.md C3).
    ``wrap``: optional function applied to each sandbox command line (e.g. to add cgroup resource limits).
    ``link_inputs``: hard-link input files into the sandbox view when on the same file system (fast);
    otherwise they are copied with their timestamps."""
    artifact, output, scratch = Path(artifact).resolve(), Path(output).resolve(), Path(scratch).resolve()
    output.mkdir(parents=True, exist_ok=True)
    scratch.mkdir(parents=True, exist_ok=True)
    if sealed_record is not None:
        sealing.verify(artifact, sealed_record)
    gpu = bool(bwrap.gpu_devices()) if gpu is None else gpu
    deadline = time.monotonic() + observation_seconds if observation_seconds is not None else None
    scorer = FoldScorer(view.metric, view.aggregation, view.class_values, validation_only=validation_only,
                        scored_csv=None if validation_only else output / 'scored_predictions.csv')
    start = time.monotonic()
    try:
        with tempfile.TemporaryDirectory(prefix='phm-runtime-', dir=scratch) as temp:
            runtime_dir = Path(temp)
            shutil.copytree(artifact, runtime_dir / 'artifact', ignore=shutil.ignore_patterns('__pycache__'))
            shutil.copy2(WORKER, runtime_dir / 'predict_worker.py')
            for entity in sorted(view.inputs):
                assert re.fullmatch(r'entity_\d+', entity), entity  # predictors only ever see anonymous names
                if deadline is not None and time.monotonic() >= deadline:
                    scorer.add_unfinished(entity, 'not_started_at_window')
                    continue
                prediction, usage = run_unit(runtime_dir, runtime, view.inputs[entity].resolve(), output / entity, view.mode,
                                             stream_layout=view.stream_layout, input_path=f'/input/{entity}/inputs',
                                             scratch=scratch, deadline=deadline, gpu=gpu, strict_stream=strict_stream,
                                             link_inputs=link_inputs, wrap=wrap)
                if prediction is None:
                    scorer.add_unfinished(entity, 'censored', {'resources': usage})
                    continue
                scorer.add(entity, prediction, view.labels[entity], {'resources': usage})
                del prediction
        result = scorer.result()
    except FAILURES as error:
        result = {'status': 'failed', 'error': f'{type(error).__name__}: {error}'}
    result['wall_seconds'] = time.monotonic() - start
    result['observation_seconds'] = observation_seconds
    result = finish(result, view)
    (output / 'metrics.json').write_text(json.dumps(result, indent=2, default=int) + '\n')
    return result
