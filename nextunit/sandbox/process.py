"""Stopping a sandboxed process tree."""
from __future__ import annotations

import os
import signal
import subprocess


def stop(process: subprocess.Popen) -> None:
    """Kill the launcher's process group. bwrap runs with --die-with-parent and
    --as-pid-1, so the sandbox's PID namespace, and every process in it, goes too."""
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
