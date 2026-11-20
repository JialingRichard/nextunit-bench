"""Host-side compute broker: runs the agent's commands in sandboxed jobs with hard resource limits.

Pool (paper defaults): 8 logical CPUs, 16 GiB and one GPU shared by all trajectories; one trajectory's
heavy commands at most 4 CPUs and 8 GiB; light commands 1 CPU, 512 MiB, 10 s. A trajectory's commands run in
submission order. Time a trajectory spends with commands queued and none running is excluded from its budget."""
from __future__ import annotations

import json
import math
import os
import select
import signal
import socket
import socketserver
import subprocess
import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from ..sandbox import bwrap

LIGHT_CPU_PERCENT, LIGHT_MEMORY, LIGHT_TIMEOUT_SECONDS = 100, '512M', 10
MCP_SCRIPT = Path(__file__).resolve().parent / 'compute_mcp.py'
UNIT_PREFIX = 'nextunit-' + os.urandom(3).hex() + '-'     # every scope this runner process starts carries it


@dataclass(frozen=True)
class Pool:
    cpus: int = 8
    memory_gb: int = 16
    gpus: int = 1
    trajectory_cpus: int = 4
    trajectory_memory_gb: int = 8
    light_commands: int = 3

    def __post_init__(self):
        values = {k: getattr(self, k) for k in self.__dataclass_fields__}
        if any(type(v) is not int for v in values.values()) or min(values.values()) < 0 or \
                min(self.cpus, self.memory_gb, self.trajectory_cpus, self.trajectory_memory_gb, self.light_commands) < 1:
            raise ValueError(f'pool: positive integers required (gpus may be 0): {values}')
        if self.trajectory_cpus > self.cpus or self.trajectory_memory_gb > self.memory_gb:
            raise ValueError('pool: trajectory_cpus/trajectory_memory_gb cannot exceed cpus/memory_gb')

    def evaluation_slot(self) -> dict:
        """The broker slot an evaluation (smoke check, deployment) holds: 4 CPUs, 8 GiB and the GPU in the paper."""
        return {'cpus': min(4, self.trajectory_cpus), 'memory_gb': min(8, self.trajectory_memory_gb), 'gpu': self.gpus > 0}


def stop_unit(unit: str) -> None:
    subprocess.run(['systemctl', '--user', 'kill', '--signal=SIGKILL', unit], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def stop_all_units() -> None:
    """Kill every agent, compute and evaluation scope started by this process (they outlive it otherwise)."""
    stop_unit(UNIT_PREFIX + '*')


def stop_process(process: subprocess.Popen, unit: str) -> None:
    for _ in range(20):            # cancellation can precede systemd's registration of the scope
        stop_unit(unit)
        try:
            process.wait(timeout=0.1)
            return
        except subprocess.TimeoutExpired:
            pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait()
    stop_unit(unit)


def cgroup_command(command: list[str], *, cpu_percent: int, memory: str, unit: str | None = None,
                   oom_omit: bool = False) -> list[str]:
    """``oom_omit`` asks systemd-oomd not to pick this scope under host memory pressure (evaluations, as in the
    paper's runs); the scope's own MemoryMax still applies."""
    unit = unit or UNIT_PREFIX + uuid.uuid4().hex + '.scope'
    return ['systemd-run', '--user', '--scope', '--quiet', '--unit=' + unit, '-p', f'CPUQuota={cpu_percent}%',
            '-p', f'MemoryMax={memory}', '-p', 'MemorySwapMax=0', '-p', 'TasksMax=512',
            *(['-p', 'ManagedOOMPreference=omit'] if oom_omit else []), '--', *command]


def validate_request(request: dict, pool: Pool, gpu_default: bool) -> dict:
    if not isinstance(request, dict) or set(request) != {'tool', 'arguments'}:
        raise ValueError('Expected tool and arguments fields')
    tool, arguments = request['tool'], request['arguments']
    if tool not in ('run_command', 'run_light_command') or not isinstance(arguments, dict):
        raise ValueError('Unknown tool or invalid arguments')
    heavy = tool == 'run_command'
    allowed = {'command', 'max_output_chars'} | ({'cpus', 'memory_gb', 'gpu', 'timeout_seconds'} if heavy else set())
    if set(arguments) - allowed:
        raise ValueError('Unsupported arguments: ' + ', '.join(sorted(set(arguments) - allowed)))
    if not isinstance(arguments.get('command'), str) or not arguments['command'].strip():
        raise ValueError('command must be a nonempty string')
    limit = arguments.get('max_output_chars', 16000)
    if type(limit) is not int or not 1 <= limit <= 100000:
        raise ValueError('max_output_chars must be an integer between 1 and 100000')
    out = {'lane': 'heavy' if heavy else 'light', 'command': arguments['command'], 'max_output_chars': limit,
           'cpus': 0, 'memory_gb': 0, 'gpu': False, 'timeout_seconds': LIGHT_TIMEOUT_SECONDS}
    if heavy:
        cpus, memory, gpu = arguments.get('cpus', 1), arguments.get('memory_gb', 2), arguments.get('gpu', gpu_default)
        if type(cpus) is not int or not 1 <= cpus <= pool.trajectory_cpus:
            raise ValueError(f'cpus must be an integer between 1 and {pool.trajectory_cpus}')
        if type(memory) is not int or not 1 <= memory <= pool.trajectory_memory_gb:
            raise ValueError(f'memory_gb must be an integer between 1 and {pool.trajectory_memory_gb}')
        if type(gpu) is not bool:
            raise ValueError('gpu must be a boolean')
        gpu = gpu and pool.gpus > 0                  # a pool without GPU runs every job on CPU
        timeout = arguments.get('timeout_seconds', 7200)
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 7200:
            raise ValueError('timeout_seconds must be a finite number greater than 0 and at most 7200')
        out.update(cpus=cpus, memory_gb=memory, gpu=gpu, timeout_seconds=timeout)
    return out


class Handle:
    """One trajectory's connection to the broker: its socket, queue clock and running jobs."""

    def __init__(self, broker: 'Broker', ident: str, stage: Path, directory: Path, runtime: bwrap.Runtime,
                 mounts, gpu_default: bool = True):
        self.broker, self.ident, self.stage, self.directory, self.runtime = broker, ident, Path(stage), Path(directory), runtime
        self.mounts = mounts                         # callable -> (readonly, writable) for compute jobs
        self.gpu_default = gpu_default
        self.directory.mkdir(parents=True, exist_ok=True)
        self.clock_path = self.directory / 'compute_queue.json'
        previous = json.loads(self.clock_path.read_text()) if self.clock_path.exists() else {}
        self.wait_total, self.wait_started = previous.get('compute_queue_wait_seconds', 0.0), None
        self.queued = self.active = self.used_cpus = self.used_memory_gb = self.used_gpus = 0
        self.closed, self.cancel_epoch, self.units = False, 0, set()
        self.socket_path = self.stage / 'broker.sock'
        self.socket_path.unlink(missing_ok=True)
        self.server = _Server(str(self.socket_path), _Request)
        self.server.handle = self
        threading.Thread(target=self.server.serve_forever, kwargs={'poll_interval': 0.05}, daemon=True).start()

    def agent_mounts(self):
        return [(self.socket_path, '/broker.sock'), (MCP_SCRIPT, '/compute_mcp.py')]

    def wait_seconds(self) -> float:
        with self.broker.condition:
            return self.wait_total + (time.monotonic() - self.wait_started if self.wait_started is not None else 0)

    def update_clock(self) -> None:
        waiting = self.queued > 0 and self.active == 0
        if waiting and self.wait_started is None:
            self.wait_started = time.monotonic()
        elif not waiting and self.wait_started is not None:
            self.wait_total += time.monotonic() - self.wait_started
            self.wait_started = None
        tmp = self.clock_path.with_suffix('.tmp')
        tmp.write_text(json.dumps({'compute_queue_wait_seconds': self.wait_seconds(), 'queued': self.queued, 'active': self.active}) + '\n')
        tmp.replace(self.clock_path)

    def cancel_jobs(self) -> None:
        with self.broker.condition:
            self.cancel_epoch += 1
            self.broker.condition.notify_all()
            units = list(self.units)
        for unit in units:
            stop_unit(unit)
        with self.broker.condition:
            self.broker.condition.wait_for(lambda: self.queued == 0 and self.active == 0)

    def close(self) -> None:
        with self.broker.condition:
            self.closed = True
            self.broker.condition.notify_all()
        self.cancel_jobs()
        self.server.shutdown()
        self.server.server_close()
        self.socket_path.unlink(missing_ok=True)
        with self.broker.condition:
            self.update_clock()


class _Server(socketserver.ThreadingUnixStreamServer):
    daemon_threads = True


class _Request(socketserver.StreamRequestHandler):
    def handle(self):
        handle = self.server.handle

        def disconnected():
            ready, _, _ = select.select([self.connection], [], [], 0)
            return bool(ready) and not self.connection.recv(1, socket.MSG_PEEK)
        try:
            try:
                request = json.loads(self.rfile.readline())
            except ValueError as error:
                result = {'status': 'invalid_request', 'error': str(error)}
            else:
                result = handle.broker.execute(handle, request, disconnected)
            self.wfile.write((json.dumps(result, ensure_ascii=False) + '\n').encode())
        except (BrokenPipeError, ConnectionResetError):
            pass


class Broker:
    def __init__(self, pool: Pool = Pool()):
        self.pool = pool
        self.condition = threading.Condition(threading.RLock())
        self.queue, self.handles = [], {}
        self.used_cpus = self.used_memory_gb = self.gpu_active = self.light_active = 0
        self.events_lock = threading.Lock()

    def register(self, ident, stage, directory, runtime, mounts, gpu_default=True) -> Handle:
        with self.condition:
            existing = self.handles.get(ident)
            if existing is not None and not existing.closed:
                raise ValueError('Trajectory already registered: ' + ident)
            handle = Handle(self, ident, stage, directory, runtime, mounts, gpu_default)
            self.handles[ident] = handle
            return handle

    def event(self, handle, kind, **fields):
        row = {'event': kind, 'at_unix': time.time(), 'trajectory_id': handle.ident, **fields}
        with self.events_lock, (handle.directory / 'compute_events.jsonl').open('a') as out:
            out.write(json.dumps(row, ensure_ascii=False) + '\n')

    def _fits(self, ticket) -> bool:
        handle, p = ticket['handle'], self.pool
        if handle.closed or handle.cancel_epoch != ticket['epoch'] or handle.active:
            return False
        if next((t for t in self.queue if t['handle'] is handle), ticket) is not ticket:
            return False                            # a trajectory's commands run in order
        if self.gpu_active + int(ticket['gpu']) > p.gpus:
            return False
        if ticket['lane'] == 'light':
            return self.light_active < p.light_commands
        return (self.used_cpus + ticket['cpus'] <= p.cpus and self.used_memory_gb + ticket['memory_gb'] <= p.memory_gb
                and handle.used_cpus + ticket['cpus'] <= p.trajectory_cpus
                and handle.used_memory_gb + ticket['memory_gb'] <= p.trajectory_memory_gb
                and handle.used_gpus + int(ticket['gpu']) <= p.gpus)

    def _allocate(self, ticket, sign) -> None:
        handle = ticket['handle']
        handle.active += sign
        self.gpu_active += sign * int(ticket['gpu'])
        handle.used_gpus += sign * int(ticket['gpu'])
        if ticket['lane'] == 'light':
            self.light_active += sign
        else:
            self.used_cpus += sign * ticket['cpus']
            self.used_memory_gb += sign * ticket['memory_gb']
            handle.used_cpus += sign * ticket['cpus']
            handle.used_memory_gb += sign * ticket['memory_gb']

    @contextmanager
    def slot(self, handle, *, lane='heavy', cpus=1, memory_gb=2, gpu=False, cancelled=lambda: False, epoch=None):
        ticket = {'handle': handle, 'lane': lane, 'cpus': cpus if lane == 'heavy' else 0,
                  'memory_gb': memory_gb if lane == 'heavy' else 0, 'gpu': gpu if lane == 'heavy' else False,
                  'id': uuid.uuid4().hex}
        fields = {k: ticket[k] for k in ('lane', 'cpus', 'memory_gb', 'gpu')}
        with self.condition:
            ticket['epoch'] = handle.cancel_epoch if epoch is None else epoch
            self.queue.append(ticket)
            handle.queued += 1
            handle.update_clock()
            acquired = False
            self.event(handle, 'queued', job_id=ticket['id'], **fields)
            try:
                while True:
                    if handle.closed or handle.cancel_epoch != ticket['epoch'] or cancelled():
                        raise InterruptedError('Execution cancelled')
                    if next((t for t in self.queue if self._fits(t)), None) is ticket:
                        self.queue.remove(ticket)
                        self._allocate(ticket, 1)
                        handle.queued -= 1
                        handle.update_clock()
                        acquired = True
                        self.event(handle, 'acquired', job_id=ticket['id'], **fields)
                        self.condition.notify_all()
                        break
                    self.condition.wait(0.1)
            finally:
                if not acquired:
                    self.queue.remove(ticket)
                    handle.queued -= 1
                    handle.update_clock()
                    self.condition.notify_all()
        try:
            yield ticket['id']
        finally:
            with self.condition:
                self._allocate(ticket, -1)
                handle.update_clock()
                self.event(handle, 'released', job_id=ticket['id'], **fields)
                self.condition.notify_all()

    def execute(self, handle: Handle, request: dict, disconnected) -> dict:
        try:
            request = validate_request(request, self.pool, handle.gpu_default)
        except ValueError as error:
            return {'status': 'invalid_request', 'returncode': None, 'error': str(error), 'output': str(error)}
        lane, cpus, memory, gpu = (request[k] for k in ('lane', 'cpus', 'memory_gb', 'gpu'))
        fields = {'lane': lane, 'cpus': cpus, 'memory_gb': memory, 'gpu': gpu}
        queued_at = time.monotonic()
        with self.condition:
            epoch = handle.cancel_epoch
        try:
            with self.slot(handle, lane=lane, cpus=cpus, memory_gb=memory, gpu=gpu, cancelled=disconnected, epoch=epoch) as job_id:
                start = time.monotonic()
                readonly, writable = handle.mounts()
                threads = str(cpus if lane == 'heavy' else 1)
                argv = bwrap.command(handle.runtime, ['/bin/bash', '-c', request['command']], readonly=readonly,
                                     writable=writable, network=True, gpu=gpu, cwd='/workspace',
                                     env={k: threads for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS')})
                unit = UNIT_PREFIX + 'compute-' + job_id + '.scope'
                with self.condition:
                    if handle.closed or handle.cancel_epoch != epoch:
                        raise InterruptedError('Execution cancelled')
                    handle.units.add(unit)
                logs = handle.directory / 'compute'
                logs.mkdir(exist_ok=True)
                path = logs / (job_id + '.log')
                self.event(handle, 'command', job_id=job_id, command=request['command'], **fields)
                cpu_percent, memory_limit = (cpus * 100, f'{memory}G') if lane == 'heavy' else (LIGHT_CPU_PERCENT, LIGHT_MEMORY)
                timeout, limit = request['timeout_seconds'], request['max_output_chars']
                with path.open('wb') as output:
                    process = subprocess.Popen(cgroup_command(argv, cpu_percent=cpu_percent, memory=memory_limit, unit=unit),
                                               stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
                    reason = None
                    try:
                        while process.poll() is None:
                            if handle.closed or handle.cancel_epoch != epoch or disconnected():
                                reason = 'cancelled'
                            elif time.monotonic() - start >= timeout:
                                reason = 'command_timeout'
                            if reason:
                                stop_process(process, unit)
                                break
                            time.sleep(0.1)
                    finally:
                        if reason is None and (handle.closed or handle.cancel_epoch != epoch or disconnected()):
                            reason = 'cancelled'
                        stop_process(process, unit)
                        with self.condition:
                            handle.units.discard(unit)
                with path.open('rb') as output:
                    output.seek(max(0, path.stat().st_size - limit * 4))
                    content = output.read().decode(errors='replace')[-limit:]
                result = {'returncode': process.returncode,
                          'status': reason or ('completed' if process.returncode == 0 else 'failed'),
                          'output': content, 'output_truncated': path.stat().st_size > len(content.encode()),
                          'queue_seconds': start - queued_at, 'execution_seconds': time.monotonic() - start,
                          **fields, 'job_id': job_id}
                if lane == 'light' and result['status'] in ('command_timeout', 'failed'):
                    result['limits'] = {'cpu_percent': LIGHT_CPU_PERCENT, 'memory_mib': 512,
                                        'timeout_seconds': LIGHT_TIMEOUT_SECONDS, 'gpu': gpu}
                    result['retry_automatically'] = False
                    if result['status'] == 'command_timeout':
                        result['error'] = ('轻量命令达到 10 秒执行上限，已终止；本次执行时间计入开发预算。'
                                           '命令可能已修改部分文件，请检查输出后按需通过 run_command 申请资源继续；不会自动重跑。')
                        result['suggested_tool'] = 'run_command'
                    else:
                        result['error'] = (f'轻量命令以退出码 {process.returncode} 失败。请检查输出；'
                                           '若需要更多资源，使用 run_command。不会自动重跑。')
                self.event(handle, 'completed', **{k: v for k, v in result.items() if k != 'output'})
                return result
        except InterruptedError:
            return {'status': 'cancelled', 'returncode': None, 'output': 'Execution cancelled'}
