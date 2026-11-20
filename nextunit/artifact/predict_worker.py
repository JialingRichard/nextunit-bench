"""Small isolated predict loader; one process per entity, many stream calls."""
import contextlib
import importlib
import json
import os
import resource
import sys


def main():
    # Keep the harness protocol separate from artifact and subprocess output.
    protocol_output = os.fdopen(os.dup(1), 'w', buffering=1)
    os.set_inheritable(protocol_output.fileno(), False)
    os.dup2(2, 1)

    sys.path.insert(0, '/runtime')
    sys.path.insert(0, '/artifact')
    with contextlib.redirect_stdout(sys.stderr):
        module = importlib.import_module('artifact')

    for line in sys.stdin:
        request = json.loads(line)
        with contextlib.redirect_stdout(sys.stderr):
            module.predict(sys.argv[1] if len(sys.argv) > 1 else '/input', request['output_file'])
        usage = resource.getrusage(resource.RUSAGE_SELF)
        children = resource.getrusage(resource.RUSAGE_CHILDREN)
        print(json.dumps({'cpu_seconds': usage.ru_utime + usage.ru_stime + children.ru_utime + children.ru_stime,
                          'max_rss_bytes': max(usage.ru_maxrss, children.ru_maxrss) * 1024}), file=protocol_output, flush=True)


if __name__ == '__main__':
    main()
