"""OpenCode as the agent harness: configuration, sandboxed invocation, budget clock, stall watchdog, session export.

The agent's own tools are all denied; it works only through the broker's MCP tools run_command and
run_light_command. Credentials: NEXTUNIT_OPENCODE_AUTH (path to an OpenCode auth.json, copied into the run's
private OpenCode data directory and removed afterwards) or NEXTUNIT_API_KEY with NEXTUNIT_API_BASE for an
OpenAI-compatible endpoint (passed as environment variables, never written to disk)."""
from __future__ import annotations

import json
import os
import selectors
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

from ..sandbox import bwrap
from .broker import UNIT_PREFIX, cgroup_command, stop_unit

STALL_SECONDS = 900.0          # no output and no compute job for this long: a provider stall, not charged
STALL_RETRIES = 2
STAGED: set[Path] = set()      # stages holding a copy of the credentials
PROVIDER_MARKERS = ('unauthorized', 'authentication', 'invalid token', 'rate limit', 'too many requests',
                    'connection reset', 'connection refused', 'service unavailable', 'upstream error',
                    'network error', 'failed to fetch', 'econnreset', 'etimedout')
ENVIRONMENT = {'XDG_CONFIG_HOME': '/opencode/config', 'XDG_DATA_HOME': '/opencode/data', 'XDG_CACHE_HOME': '/opencode/cache',
               'XDG_STATE_HOME': '/opencode/state', 'OPENCODE_CONFIG': '/opencode-config.json', 'OPENCODE_PURE': 'true',
               'OPENCODE_DISABLE_PROJECT_CONFIG': 'true', 'OPENCODE_DISABLE_AUTOUPDATE': 'true',
               'OPENCODE_DISABLE_DEFAULT_PLUGINS': 'false', 'OPENCODE_DISABLE_CLAUDE_CODE': 'true',
               'OPENCODE_DISABLE_LSP_DOWNLOAD': 'true', 'OPENCODE_DISABLE_MODELS_FETCH': 'true',
               'OPENCODE_EXPERIMENTAL_DISABLE_FILEWATCHER': 'true', 'OPENCODE_EXPERIMENTAL_WEBSOCKETS': 'false',
               'OPENCODE_ENABLE_QUESTION_TOOL': 'false', 'NO_COLOR': '1'}


@dataclass(frozen=True)
class Backend:
    binary: Path                      # the OpenCode executable (version 1.19.0 in the paper)
    model: str                        # e.g. gpt-6-luna
    reasoning_effort: str = 'max'
    provider: str = 'openai'          # 'openai' (OpenCode's native provider) or 'compatible'
    context: int = 272000
    output: int = 128000
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_environment(cls, binary, model, reasoning_effort='max') -> 'Backend':
        provider = 'compatible' if os.environ.get('NEXTUNIT_API_BASE') else 'openai'
        return cls(Path(binary), model, reasoning_effort, provider)

    def model_id(self) -> str:
        return ('openai/' if self.provider == 'openai' else 'compatible/') + self.model

    def config(self, runtime: bwrap.Runtime) -> dict:
        model = {'id': self.model, 'name': self.model, 'reasoning': True,
                 'limit': {'context': self.context, 'output': self.output},
                 'options': {'reasoningEffort': self.reasoning_effort, 'serviceTier': 'default', 'store': False},
                 'variants': {'max': {'reasoningEffort': self.reasoning_effort, 'serviceTier': 'default'}}}
        if self.provider == 'openai':
            providers = {'openai': {'whitelist': [self.model], 'models': {self.model: model}}}
            if os.environ.get('NEXTUNIT_API_KEY'):
                providers['openai']['options'] = {'apiKey': '{env:NEXTUNIT_API_KEY}'}
        else:
            providers = {'compatible': {'npm': '@ai-sdk/openai-compatible', 'name': 'OpenAI-compatible',
                                        'options': {'baseURL': os.environ['NEXTUNIT_API_BASE'], 'apiKey': '{env:NEXTUNIT_API_KEY}'},
                                        'models': {self.model: model}}}
        return {'$schema': 'https://opencode.ai/config.json', 'model': self.model_id(), 'small_model': self.model_id(),
                'default_agent': 'build', 'autoupdate': False, 'share': 'disabled', 'snapshot': False, 'plugin': [],
                'instructions': [], 'enabled_providers': list(providers), 'lsp': False, 'formatter': False,
                'provider': providers,
                'permission': {'*': 'deny', 'skill': {'*': 'deny'}, 'compute_*': 'allow'},
                'mcp': {'compute': {'type': 'local', 'command': [runtime.python, '/compute_mcp.py', '/broker.sock', 'B'],
                                    'enabled': True, 'timeout': 172800000}}}

    def stage_credentials(self, stage: Path) -> dict:
        source = os.environ.get('NEXTUNIT_OPENCODE_AUTH')
        if source:
            target = stage / 'opencode/data/opencode/auth.json'
            target.parent.mkdir(parents=True, exist_ok=True)
            STAGED.add(stage)
            with open(target, 'wb', opener=lambda p, f: os.open(p, f, 0o600)) as out, open(source, 'rb') as src:
                shutil.copyfileobj(src, out)
            return {'method': 'OpenCode auth file (NEXTUNIT_OPENCODE_AUTH), run-local copy'}
        if os.environ.get('NEXTUNIT_API_KEY'):
            return {'method': 'API key from NEXTUNIT_API_KEY', 'base_url': os.environ.get('NEXTUNIT_API_BASE', 'OpenAI')}
        raise RuntimeError('No credentials: set NEXTUNIT_OPENCODE_AUTH or NEXTUNIT_API_KEY')

    @staticmethod
    def remove_credentials(stage: Path) -> None:
        (stage / 'opencode/data/opencode/auth.json').unlink(missing_ok=True)
        STAGED.discard(stage)

    def command(self, stage: Path, runtime: bwrap.Runtime, handle, args: list[str]) -> list[str]:
        readonly = [(self.binary, '/opt/opencode'), (stage / 'readonly/opencode.json', '/opencode-config.json'),
                    (stage / 'readonly/development', '/workspace/development'), (stage / 'readonly/task.md', '/workspace/task.md'),
                    (stage / 'readonly/info.md', '/workspace/info.md'), (stage / 'readonly/skills', '/skills'),
                    *handle.agent_mounts()]
        writable = [(stage / 'workspace', '/workspace'), (stage / 'opencode', '/opencode'), (stage / 'tmp', '/tmp')]
        env = dict(ENVIRONMENT)
        for name in ('NEXTUNIT_API_KEY',):
            if os.environ.get(name):
                env[name] = os.environ[name]
        return bwrap.command(runtime, ['/opt/opencode', *args], readonly=readonly, writable=writable,
                             network=True, gpu=False, cwd='/workspace', env=env)


def in_scope(argv: list[str]):
    """The OpenCode process itself: 25% of a CPU and 2 GiB (orchestration only; computation goes to the broker)."""
    unit = UNIT_PREFIX + 'agent-' + os.urandom(8).hex() + '.scope'
    return cgroup_command(argv, cpu_percent=25, memory='2G', unit=unit), lambda: stop_unit(unit)


def session_id_of(event: dict):
    for container in (event, event.get('properties')):
        if isinstance(container, dict):
            for key in ('sessionID', 'sessionId', 'session_id'):
                if isinstance(container.get(key), str) and container[key]:
                    return container[key]
    return None


def token_row(event: dict):
    if event.get('type') not in {'step_finish', 'message.updated', 'message_update', 'turn.completed'}:
        return None
    for container in (event, event.get('part'), event.get('message'), event.get('properties')):
        if not isinstance(container, dict):
            continue
        for key in ('tokens', 'usage', 'tokenUsage', 'token_usage'):
            value = container.get(key)
            if not isinstance(value, dict):
                continue
            def number(*names):
                for name in names:
                    found = value.get(name)
                    if isinstance(found, (int, float)) and not isinstance(found, bool):
                        return int(found)
                return None
            cache = value.get('cache') or value.get('input_tokens_details') or {}
            cache = cache if isinstance(cache, dict) else {}
            raw_input, raw_output = number('input', 'inputTokens', 'input_tokens'), number('output', 'outputTokens', 'output_tokens')
            reasoning = number('reasoning', 'reasoningTokens', 'reasoning_tokens') or 0
            read = cache.get('read', cache.get('cached_tokens', value.get('cachedInputTokens')))
            write = cache.get('write', value.get('cacheWriteInputTokens'))
            read = read if isinstance(read, (int, float)) else 0
            write = write if isinstance(write, (int, float)) else 0
            total = number('total', 'totalTokens', 'total_tokens')
            if total is None and raw_input is not None and raw_output is not None:
                total = raw_input + raw_output + reasoning + read + write
            if total is not None:
                return {'input_tokens': (raw_input + read + write) if raw_input is not None else None,
                        'output_tokens': (raw_output + reasoning) if raw_output is not None else None,
                        'reasoning_output_tokens': reasoning, 'cached_input_tokens': read, 'total_tokens': total}
    return None


def run(backend: Backend, stage: Path, runtime: bwrap.Runtime, handle, prompt: str, directory: Path, *, session_id=None,
        attempt=1, budget_seconds: float, on_progress=None, guard=None) -> dict:
    """One OpenCode turn. Stops at the active-wall budget (wall time minus compute-queue time) or a provider stall."""
    args = ['run', '--model', backend.model_id(), '--variant', 'max', '--format', 'json']
    args += ['--session', session_id] if session_id else ['--title', 'PHM workflow']
    argv, cancel = in_scope(backend.command(stage, runtime, handle, args))
    stdout_path = directory / f'opencode.attempt_{attempt:03d}.stdout.jsonl'
    stderr_path = directory / f'opencode.attempt_{attempt:03d}.stderr.log'
    started, wait_origin = time.monotonic(), handle.wait_seconds()
    timed_out, stalled, errors, tail, tokens, emitted = False, 0.0, 0, '', [], session_id
    selector = selectors.DefaultSelector()
    process = None
    try:
        with stdout_path.open('wb') as stdout, stderr_path.open('wb') as stderr:
            process = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       start_new_session=True, bufsize=0)
            try:
                process.stdin.write(prompt.encode())
                process.stdin.close()
            except BrokenPipeError:
                pass
            selector.register(process.stdout, selectors.EVENT_READ, ('stdout', stdout))
            selector.register(process.stderr, selectors.EVENT_READ, ('stderr', stderr))
            pending, last_checkpoint = b'', 0.0
            last_output = last_compute = time.monotonic()
            while selector.get_map() or process.poll() is None:
                if guard is not None:
                    guard()
                active = time.monotonic() - started - max(0.0, handle.wait_seconds() - wait_origin)
                if active >= budget_seconds and process.poll() is None:
                    timed_out = True
                    cancel()
                    break
                for key, _ in selector.select(timeout=0.1):
                    name, sink = key.data
                    chunk = os.read(key.fileobj.fileno(), 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    sink.write(chunk)
                    sink.flush()
                    last_output = time.monotonic()
                    tail = (tail + chunk.decode('utf-8', errors='replace'))[-8000:]
                    if name == 'stderr':
                        continue
                    pending += chunk
                    while b'\n' in pending:
                        line, pending = pending.split(b'\n', 1)
                        try:
                            event = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if not isinstance(event, dict):
                            continue
                        emitted = emitted or session_id_of(event)
                        errors += event.get('type') == 'error'
                        row = token_row(event)
                        if row:
                            tokens.append(row)
                now = time.monotonic()
                if handle.queued or handle.active:
                    last_compute = now
                if now - max(last_output, last_compute) >= STALL_SECONDS and process.poll() is None:
                    stalled = now - max(last_output, last_compute)
                    cancel()
                    break
                if on_progress and emitted and now - last_checkpoint >= 1.0:
                    on_progress(emitted, max(0.0, now - started - max(0.0, handle.wait_seconds() - wait_origin)))
                    last_checkpoint = now
            if timed_out or stalled:
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    cancel()
            returncode = process.wait()
    finally:
        try:
            if process is not None and process.poll() is None:
                cancel()
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
        finally:
            selector.close()
    elapsed = time.monotonic() - started
    queue_wait = max(0.0, handle.wait_seconds() - wait_origin)
    stderr_text = stderr_path.read_text(errors='replace')
    if timed_out:
        category = 'DEVELOPMENT_WALL_TIMEOUT'
    elif stalled:
        category = 'INFRA_PROVIDER_STALL'
    elif returncode != 0 and any(m in (stderr_text + tail).lower() for m in PROVIDER_MARKERS):
        category = 'INFRA_PROVIDER_OR_AUTH'
    elif returncode != 0:
        category = 'OPENCODE_PROCESS_ERROR'
    else:
        category = 'INFRA_OPENCODE_ERROR_EVENT' if errors else None
    total = {k: sum(r[k] or 0 for r in tokens) for k in ('input_tokens', 'output_tokens', 'reasoning_output_tokens',
                                                        'cached_input_tokens', 'total_tokens')} if tokens else None
    return {'returncode': returncode, 'session_id': emitted, 'elapsed_wall_seconds': elapsed, 'queue_wait_seconds': queue_wait,
            'active_wall_seconds': max(0.0, elapsed - queue_wait), 'budget_seconds': budget_seconds, 'timed_out': timed_out,
            'stall_seconds': stalled, 'failure_category': category, 'error_events': errors, 'token_stats': total,
            'stdout_path': stdout_path.name, 'stderr_path': stderr_path.name}


def export_session(backend: Backend, stage: Path, runtime: bwrap.Runtime, handle, session_id: str, directory: Path) -> dict:
    argv, cancel = in_scope(backend.command(stage, runtime, handle, ['export', session_id]))
    fd, temporary = tempfile.mkstemp(prefix='session_export.', suffix='.tmp', dir=directory)
    try:
        with os.fdopen(fd, 'wb') as stream:
            proc = subprocess.run(argv, stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.PIPE, timeout=120, check=False)
    except subprocess.TimeoutExpired:
        cancel()
        os.unlink(temporary)
        return {'status': 'timeout'}
    if proc.returncode:
        os.unlink(temporary)
        return {'status': 'failed', 'returncode': proc.returncode, 'stderr': proc.stderr.decode(errors='replace')[-2000:]}
    try:
        json.loads(Path(temporary).read_text(encoding='utf-8'))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        os.replace(temporary, directory / 'session_export.invalid.json')
        return {'status': 'invalid', 'error': f'{type(error).__name__}: {error}'}
    os.replace(temporary, directory / 'session_export.json')
    return {'status': 'exported', 'path': 'session_export.json'}
