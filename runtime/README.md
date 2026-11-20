# Runtime and tool environments

| File | Content |
|---|---|
| `requirements.lock` | The predictors' runtime: the 208 Python packages of the paper's runs (CPython 3.12.13; PyTorch 2.11.0 with CUDA 12.6 from the PyTorch index; transformers from a pinned git commit). |
| `tools.lock` | Added for the tool environment: readers used by the converters (h5py, pyreadr, pyarrow). |
| `Containerfile` | Builds both environments in a container (`/opt/runtime`, `/opt/tools`). |

The paper ran predictors in a snapshot of its host system, which is not
distributed. These files pin the same Python packages; system libraries
differ (KNOWN_ISSUES.md, E2). The converters' output bytes depend on numpy,
pandas, scipy, h5py, openpyxl, pyreadr and pyarrow; keep the pinned versions.

**Sandbox runtime file.** The evaluator runs predictors with bubblewrap on a
read-only file system described by a JSON file:

```
python -m nextunit.sandbox runtime --venv local/runtime --out local/runtime.json
python -m nextunit.sandbox check --runtime local/runtime.json
```

For a container image exported to a directory, write the file by hand:
`{"bundle": "<dir>", "python": "/opt/runtime/bin/python", "mounts": [{"source": "usr", "target": "/usr"}, {"source": "opt/runtime", "target": "/opt/runtime"}, {"source": "opt/python", "target": "/opt/python"}]}`.

**GPU.** Optional. Device nodes `/dev/nvidia*` are passed into the sandbox
when present; the driver libraries must be visible inside it as well (for a
venv on the host they are under the mounted `/usr`).
