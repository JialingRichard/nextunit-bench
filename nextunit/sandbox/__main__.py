"""python -m nextunit.sandbox runtime --venv PATH --out RUNTIME.json   # describe a runtime venv for the sandbox
   python -m nextunit.sandbox check --runtime RUNTIME.json             # run a probe inside the offline sandbox"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from .bwrap import Runtime, command, gpu_devices

PROBE = r'''
import json, socket, sys, importlib
out = {"python": sys.version.split()[0]}
for name in ("numpy", "pandas", "scipy", "sklearn", "torch"):
    try:
        out[name] = importlib.import_module(name).__version__
    except Exception as error:
        out[name] = "missing: " + type(error).__name__
try:
    socket.create_connection(("1.1.1.1", 53), timeout=2); out["network"] = True
except OSError:
    out["network"] = False
print(json.dumps(out))
'''


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog='python -m nextunit.sandbox')
    sub = parser.add_subparsers(dest='command', required=True)
    r = sub.add_parser('runtime')
    r.add_argument('--venv', type=Path, required=True)
    r.add_argument('--out', type=Path, required=True)
    c = sub.add_parser('check')
    c.add_argument('--runtime', type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == 'runtime':
        Runtime.venv(args.venv).save(args.out)
        print(args.out)
        return 0
    runtime = Runtime.load(args.runtime)
    result = subprocess.run(command(runtime, [runtime.python, '-c', PROBE]), capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        print(result.stderr[-2000:])
        return 1
    report = json.loads(result.stdout.strip().splitlines()[-1])
    report['gpu_devices'] = len(gpu_devices())
    print(json.dumps(report))
    return 0 if not report['network'] else 1


if __name__ == '__main__':
    sys.exit(main())
