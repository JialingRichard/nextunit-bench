# NextUnit-Bench Field Manual

> Version 1.0 (the benchmark of the paper). Chapter 1 was tested end to end
> by an agent that had not seen this repository, on a subset of datasets.

You are a coding agent. A person asked you to set up this benchmark, and
perhaps to evaluate a method or another agent with it. This manual is written
for you. Work through it in order, running every command from the
repository's root directory. Every step ends with a check you can run.
When a check fails, **stop and report to your human**; do not work around it,
and do not edit the benchmark's code or data files to make a check pass.

## Step 0. Get the repository (if you are reading this from a URL)

If your current directory is not a clone of this repository (there is no
`nextunit/benchmark/` next to this file), get it first:

1. Ask your human where to put it, if they did not say. The repository is
   small; the data built later is not (Chapter 1.1), and its location is
   chosen separately.
2. Clone the version that matches this manual (the tag in the URL you read,
   `v1.0` here):
   ```
   git clone --branch v1.0 --depth 1 https://github.com/JialingRichard/nextunit-bench.git
   cd nextunit-bench
   ```
3. Check: `git describe --tags` prints `v1.0`.
4. From now on read the local `FIELD_MANUAL.md`, not the URL: it is the same
   text, and its links and commands refer to files of this clone.

Before any large download, tell your human what Chapter 1.1 requires (disk,
memory, time) and wait for their go-ahead.

---

## Rule 0. You are the builder, not the subject

> **Building this benchmark exposes you to the hidden units and their labels.
> Therefore you must never be evaluated on it.**
>
> - Do not develop, tune, or select a method that will be scored on this
>   benchmark. Do not write plans, hints, or prompts for an agent that will be.
> - The agent under evaluation runs **only** inside the runner's sandbox
>   (Chapter 3), which mounts the development units of one fold and nothing
>   else. Never give it, or anyone developing a method, a path outside the
>   development view.
> - Do not copy prepared data, labels, or evaluation outputs anywhere an agent
>   under evaluation can read them, and do not paste them into its prompt.
> - If your human asks you to be both builder and subject, refuse and explain
>   this rule.

## Rule 1. Scoring is fixed code; you only call it

The splits, hidden-unit lists, baseline table `B`, metrics, scoring, evaluator
and data converters are provided by this repository. Call them; never
reimplement, patch, or "fix" them. If something looks wrong, stop and report,
and check [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) first. Your own work is limited
to the dirty jobs: downloading, unpacking, installing the environment, and
running the provided commands.

---

## Chapter 1. Build: download, convert, verify

### 1.0 What you are building
- 24 public PHM datasets and 58 folds that hold out units or operating
  conditions (CWRU, SEU and HSF15 hold out operating conditions; all others
  hold out units). The folds, the hidden-unit lists and everything that
  decides a score are fixed in `nextunit/benchmark/`.
- You produce the prepared data on this machine and prove, with the
  self-check, that it is the data the benchmark defines.

### 1.1 Check the machine
- Linux x86_64; unprivileged user namespaces enabled (`bwrap` must work).
- Disk: about 90 GB of downloads (official routes first; sizes per file in
  `nextunit/data/sources.json`), about 85 GB of unpacked raw files
  (downloaded archives can be deleted once `verify-raw` passes, except those
  read in place), and 89 GB of prepared data.
- Memory: at least 20 GB available (the `available` column of `free`). Converting TEP reads whole R data files and
  peaks at 15.4 GiB (measured); every other dataset needs far less.
- Python 3.12 or the provided container; GPU optional.
- Check: after 1.2, `python -m nextunit.sandbox check --runtime local/runtime.json`
  must print the package versions and `"network": false`; `systemd-run --user
  --scope true` must succeed if you will run agents (Chapter 3).

### 1.2 Install the environments
Two virtual environments, both CPython 3.12.13, created with `uv`
(https://docs.astral.sh/uv/); details in `runtime/README.md`:
```
export UV_INDEX_STRATEGY=unsafe-best-match UV_HTTP_TIMEOUT=300 UV_CONCURRENT_DOWNLOADS=4
uv venv --python 3.12.13 local/runtime && VIRTUAL_ENV=local/runtime uv pip sync runtime/requirements.lock
uv venv --python 3.12.13 local/tools && VIRTUAL_ENV=local/tools uv pip sync runtime/requirements.lock runtime/tools.lock
VIRTUAL_ENV=local/tools uv pip install --no-deps -e .
local/tools/bin/python -m nextunit.sandbox runtime --venv local/runtime --out local/runtime.json
local/tools/bin/python -m nextunit.sandbox check --runtime local/runtime.json
```
- Use `uv pip sync`, not `uv pip install`: the lock is the exact package
  list of the paper's environment, which `install` would re-resolve and
  reject (one package declares an older numpy than the one installed).
  `unsafe-best-match` lets uv take packages from both PyPI and the PyTorch
  index. On a slow link, retry `sync` after a download timeout; it resumes.
- `local/runtime` is what predictors run in (the paper's 208 packages,
  including CUDA builds of PyTorch, about 7 GB); `local/tools` adds the
  readers the converters need. `local/runtime.json` refers to the Python
  installation uv manages (by default under `~/.local/share/uv/python`, or
  `UV_PYTHON_INSTALL_DIR`): removing it breaks the sandbox. Run every `python -m nextunit...` command
  with `local/tools/bin/python`.
- Check: `sandbox check` prints the package versions seen inside the
  sandbox and must report `"network": false`.
- `runtime/Containerfile` builds the same two environments in a container.

### 1.3 Choose a local data root
- One directory holding raw downloads, prepared data and runs; the default is
  `local/` in the repository, ignored by git: `local/downloads/` (archives),
  `local/raw/` (unpacked raw files, `RAW_ROOT`), `local/prepared/`
  (`PREPARED_ROOT`).
- Everything under it is a dataset derivative and contains hidden labels.
- Prepared data: 156,606 files, 88.8 GB in total (per dataset:
  `nextunit/benchmark/checksums/prepared_sizes.csv`). Layout:
  `<root>/<DATASET>/<entity_id>/inputs/...` and `.../labels.csv`, plus
  `<root>/SCANIA/auxiliary/`.

### 1.4 Download raw data
```
python -m nextunit.data fetch DS --raw RAW_ROOT --downloads DOWNLOADS
python -m nextunit.data verify-raw DS --raw RAW_ROOT
```
- Routes per dataset are in `nextunit/data/sources.json`, official source
  first. `fetch` runs the first automatic route that works, checks each
  download against its recorded size and, where one is recorded, its hash
  (SHA-256; MD5 for some mirror archives), lays the files out under
  `RAW_ROOT`, then checks every raw file the converter will read (SHA-256).
- `fetch` prints the size and rate of a running download every 30 seconds.
  Some official servers are slow: in a test, HSF15 from UCI ran at about
  10 kB/s (90 minutes for 77 MB). Slow is not failed; if it is too slow for
  you, treat the route as failed (below) and report that.
- Routes marked `manual` (official downloads of PUBD16, XJTU-SY and IMS)
  need a browser or archive tools (unrar, 7z): follow their instructions, or
  run `fetch DS --route mirror` to use the mirror instead.
- The mirror is the PHMD mirror: **third-party cloud storage with no
  licence statement**, maintained by the PHMD project
  (https://github.com/dasolma/phmd). It is the only route for PHME20 and
  PHM2010 (official downloads defunct) and CALCE (the mirror's CSV
  conversion is what the converter reads). The SHA-256 checks are what make
  it acceptable.
- If you use the mirror, tell your human to cite both the original data
  publisher (`docs/datasets.md`) and PHMD: D. Solís-Martín, J. Galán-Páez,
  J. Borrego-Díaz, "PHMD: An easy data access tool for prognosis and health
  management datasets", SoftwareX 29 (2025) 102039,
  doi:10.1016/j.softx.2025.102039. Download each dataset once and keep the
  archives; do not fetch from the mirror repeatedly.
- Check: `verify-raw` must report `ok`. A missing or differing file means
  stop; do not edit raw files to make it pass (except the PUBD16 pruning its
  manual route describes).
- If a route fails (download refused, hash differs, `verify-raw` or `build`
  fails on its files, or it is too slow), you may try the next route of the same dataset: first
  delete that dataset's directories under `RAW_ROOT` (the `RAW_DIRS` named in
  its converter, `nextunit/data/adapters/<ds>.py`), then `fetch DS --route
  mirror`. Report which route you used. If no route passes, stop.
- Ask your human before downloads that exceed your disk budget (sizes in
  `sources.json`).

### 1.5 Convert
```
python -m nextunit.data build DS --raw RAW_ROOT --prepared PREPARED_ROOT
python -m nextunit.data verify DS --prepared PREPARED_ROOT
```
- `build` runs the dataset's fixed converter (`nextunit/data/adapters/`) on
  the raw files and writes `PREPARED_ROOT/DS/` (one directory per unit:
  `inputs/` and `labels.csv`). The directory appears only when the converter
  has finished. Files passed through unchanged are hard-linked to the raw
  copy when possible; `--copy-raw` copies them instead.
- `verify` compares every file with the shipped SHA-256 list and reports
  missing, unexpected and differing files. CARE is compared per array
  (KNOWN_ISSUES.md, C4); all other datasets byte for byte.
- The converters also apply the release fix listed in KNOWN_ISSUES.md (C1:
  MIMII file order and timestamps). Do not apply any other change.
- Check: every prepared file matches the shipped checksum list
  (`nextunit/benchmark/checksums/prepared/<DATASET>.sha256`; plain
  `sha256sum -c --strict` works from `<root>/<DATASET>`).

### 1.6 Run the self-check
```
python -m nextunit.selfcheck --prepared PREPARED_ROOT --runtime local/runtime.json --raw RAW_ROOT
```
Run it from the repository root: `--scratch DIR` (working space for the
evaluator and the random-forest caches) defaults to `local/scratch`
relative to the current directory.

Layers, each printed as one JSON line with `"ok"`:
1. **definition files**: every file of `nextunit/benchmark/` matches
   `MANIFEST.sha256`. A failure means the benchmark itself was modified.
2. **raw files** (with `--raw`): what each converter reads matches its list.
3. **prepared files**: every prepared file (CARE: every array) matches; no
   missing or extra files; MIMII_DUE timestamps are all equal.
4. **constant predictor**: its fold losses equal the shipped reference
   exactly; with all 58 folds it also prints S24 (3.94) and S_noshortcut.
5. **sandboxed evaluator**: the constant predictor, sealed as an artifact,
   run offline through the evaluator on HSF15 and NCMAPSS (or, when those
   were not built, fold 1 of the alphabetically first batch dataset and the
   alphabetically first stream dataset you built), gives the same losses.
6. **random-forest reference** (only with `--rf`; `--jobs N` processes of one
   core each, default 2): retrains the fixed random forest of every fold
   from code (57 models, plus the IsolationForest anchor of MIMII_DUE),
   predicts the hidden units single-threaded and requires each fold's loss
   to equal the shipped value (`reference_scores.csv`, rows `random_forest`).
   No model files are distributed. It needs scikit-learn 1.8.0 (the pinned
   version), about 30 minutes on 4 cores and 8 GB of scratch space for its
   training caches; PUBD16 also needs `--raw` (its reader uses the channel
   time axes stored only in the original MAT files) and is listed as
   skipped without it.
- `--datasets DS ...` restricts the check to the datasets you built.
- The last line reads `"selfcheck": "passed"`. Report the output to your
  human before going further; on any failure, stop.

### 1.7 Licences
- The datasets keep their original licences; Paderborn and MIMII DUE are
  non-commercial. Tell your human about [`docs/datasets.md`](docs/datasets.md)
  before they use the data.

---

## Chapter 2. Evaluate a method

Commands below run from the repository root in the tool environment. `ROOT`
is the prepared-data root of Chapter 1; `RUNTIME` is the runtime file written
in 1.2 (`local/runtime.json`).

### 2.1 The artifact
- A directory with `artifact.py` defining `predict(input_directory,
  output_file)`, a `resources.json` (a JSON object), and any model files.
- Output: UTF-8 CSV with columns `record_id,prediction`; every requested ID
  exactly once; finite values; class labels from the task's allowed values.
- Batch and stream tasks; in stream tasks one process per unit keeps state
  across chunks and is reset between units.
- Full specification: [`docs/artifact_spec.md`](docs/artifact_spec.md).

### 2.2 Give the developer the development view only
```
python -m nextunit.eval export-dev --dataset DS --fold K --prepared ROOT --out DEVDIR
```
- Writes `task.md`, `info.md` and `development/entity_XXXX/{inputs,labels.csv}`
  for the development units of one fold (copies, not links).
- Whoever develops the method (a person, a script, another agent) gets that
  directory and nothing else. Rule 0 applies: not you.

### 2.3 Seal and evaluate
```
python -m nextunit.eval seal ARTIFACT_DIR SEALED/artifact
python -m nextunit.eval evaluate --artifact SEALED/artifact --sealed-record SEALED/sealed_artifact.json \
    --dataset DS --fold K --prepared ROOT --runtime RUNTIME --out OUTDIR
```
- `seal` checks the artifact, copies it, records the SHA-256 of every file and
  removes write permission. `evaluate` re-checks those hashes, runs one
  offline sandboxed process per hidden unit, joins labels outside the
  sandbox, and prints the fold's `E`, `B`, `S`, `D`.
- A predictor that fails to run or writes invalid output fails the fold:
  `S = 0`, `D = 100`.
- `OUTDIR` then holds `metrics.json`, per-unit predictions and logs, and
  `scored_predictions.csv`. These contain hidden labels: keep them away from
  anything under evaluation.

### 2.4 Scores
```
python -m nextunit.eval score RESULTS.csv      # columns: dataset,fold,status,E (status: completed|failed)
```
- Per fold: `E` (loss; one minus the metric for accuracy, balanced accuracy,
  ROC-AUC, average precision), `B` (frozen table), `S = 100*max(0, 1-E/B)`,
  `D = 100*max(0, 1-B/E)` (auxiliary).
- Aggregate: mean over folds within a dataset, then equal weight over
  datasets, with a 95% bootstrap interval over datasets. Reported for
  **S24** (24 datasets) and **S_noshortcut** (21 datasets: without AHU21,
  THREEW, CARE). Do not confuse S_noshortcut with the paper's "21 unit sets".
  An aggregate needs all 58 folds; a fold without a result is a failure.
- Paired comparison of two methods on common folds: `nextunit.eval.score.paired`
  (bootstrap over datasets).

## Chapter 3. Evaluate an agent

Rule 0 applies with full force here: you run the runner; the agent under
test runs inside it and never sees anything else.

### 3.1 What the runner does
For each fold the runner
- builds a private stage (random directory name) holding the fold's
  development view, `task.md`, `info.md`, an empty workspace and the agent's
  harness state;
- starts the agent (OpenCode) in a `bwrap` sandbox with network access, the
  workspace writable and everything else read-only. The agent's built-in
  tools are disabled; it works only through two MCP tools served by the
  host's compute broker: `run_command` (up to 4 CPUs, 8 GiB, the GPU) and
  `run_light_command` (1 CPU, 512 MiB, 10 s). Every command runs in its own
  sandbox with hard limits; the pool (8 CPUs, 16 GiB, 1 GPU) is shared by all
  trajectories running at once;
- gives the agent two hours of **active** wall time: elapsed time minus the
  time its commands wait for resources. A provider stall (900 s without any
  output or running command) is not charged, and the turn is resumed (at
  most twice);
- when a turn ends, copies the workspace as the submission, checks it
  (Chapter 2.1), and runs a smoke check on the first development unit (the
  first chunk in stream tasks) offline; a failure is sent back to the agent
  in the same session while budget remains;
- seals the first submission that passes, retires the workspace, and only
  then evaluates the sealed artifact on the hidden units (Chapter 2.3).

### 3.2 Install the harness and credentials
- OpenCode 1.19.0 (the paper's version): install the npm package
  `opencode-ai@1.19.0` (e.g. `npm install --prefix local/opencode
  opencode-ai@1.19.0`) and set `"opencode"` to
  `local/opencode/node_modules/.bin/opencode`. That is a link to the native
  executable (`opencode-ai/bin/opencode.exe`, despite the name a Linux
  program; `opencode-linux-x64/bin/opencode` is the same file). Its SHA-256
  starts with `135ac3f8`, as in the paper's runs.
- Credentials only through environment variables, never in files of this
  repository: `NEXTUNIT_OPENCODE_AUTH` (path to an OpenCode `auth.json`,
  e.g. from `opencode auth login`; copied into each run's private directory
  and deleted when the run ends), or `NEXTUNIT_API_KEY` for the OpenAI API,
  plus `NEXTUNIT_API_BASE` for any OpenAI-compatible endpoint.
- Requirements: `systemd-run --user` (resource limits), `bwrap`.

### 3.3 Run one fold, or all 58
```
python -m nextunit.runner run    --config RUN.json --dataset DS --fold K
python -m nextunit.runner run    --config RUN.json --all --jobs 6
python -m nextunit.runner status --config RUN.json
python -m nextunit.runner score  --config RUN.json
```
`RUN.json`:
```
{"out": "local/runs/luna", "prepared": "PREPARED_ROOT", "runtime": "local/runtime.json",
 "opencode": "/path/to/opencode", "model": "gpt-6-luna", "reasoning_effort": "max",
 "label": "none", "budget_seconds": 7200,
 "pool": {"cpus": 8, "memory_gb": 16, "gpus": 1}}
```
- Paths in `RUN.json` are absolute or relative to the directory you run
  the runner from.
- `pool` is the compute shared by all trajectories of one `run` command; the
  values above are the paper's. A trajectory's commands never get more than
  `trajectory_cpus` (default 4) CPUs and `trajectory_memory_gb` (default 8)
  GiB; its smoke check and deployment run with the same limits. Lower the
  pool only if the machine is shared or smaller, and report it: queueing is
  not charged to the agent, but a smaller pool changes how runs interleave,
  and smaller per-trajectory limits change the protocol. `"gpus": 0` runs
  every command on CPU (the tool description still offers a GPU, as in the
  paper); report that too. Each trajectory's `manifest.json` records the
  pool it ran with.
- Results: `OUT/trajectories/<DS>_f<K>_<label>_r1/` holds `result.json`
  (status, E, B, S, D), `manifest.json`, the agent's event log, every
  compute command and its output, smoke checks, `sealed_artifact.json`, and
  `deployment/`. **`deployment/` contains hidden labels**: keep it away from
  any agent.
- Progress: `run` prints one JSON line when it starts (number of folds and
  the name pattern of its systemd scopes), and one when each fold starts and
  ends. `status` counts the folds by state. For a running fold, its
  `manifest.json` shows `phase` (development, repair, sealed, deployment),
  `attempts`, `development_active_wall_seconds`,
  `compute_queue_wait_seconds` and `smoke_status`.
- Scopes: each `run` process names its systemd scopes
  `nextunit-<6 hex>-agent-…` (the agent), `nextunit-<6 hex>-compute-…`
  (its commands) and `nextunit-<6 hex>-<hex>` (evaluations), with one prefix
  per process. On a shared machine, stop or inspect only your own prefix.
- Stop: SIGTERM or Ctrl-C (or `systemctl --user stop` if you started the
  runner as a service). The runner kills its agent, job and evaluation
  scopes, which would otherwise outlive it, and removes its credential
  copies. Do not kill it with SIGKILL.
- Resume: run the same command again. Finished folds are skipped; paused
  or stopped ones continue in the same stage and agent session.
- Disk guard: no new fold starts below 25 GiB free; a running fold pauses
  below 10 GiB.

### 3.4 Network
- Development has internet access, by design: the protocol allows general
  documentation, tools, packages and pretrained models. It forbids obtaining
  additional samples of the dataset, the evaluation data, labels, existing
  predictions or ready-made answers, and this repository counts as such. The
  boundary is a rule stated in `task.md` and recorded in the logs; it is not
  technically filtered.
- Smoke checks and deployment are offline.

### 3.5 Failure classes
- `DEVELOPMENT_WALL_TIMEOUT` (no sealed artifact within budget) and
  `DEPLOYMENT_EVALUATION_FAILED` are the agent's failures: `S = 0`, and they
  stay in every average.
- `infra_paused` (provider errors, disk guard) is not a result: resume it.

### 3.6 Reserved: skills and tool libraries (not in v1.0)
- Read-only skill files mounted at `/skills`, tool libraries installed in
  the runtime, and one paragraph added to the initial prompt. Independent of
  any harness's own skill system.

## Chapter 4. Rules and known issues

### 4.1 Protocol rules for the agent under test
The agent sees exactly what the paper's agents saw: the initial prompt
(`nextunit/benchmark/prompts/initial_prompt.txt`), `task.md` (task, inputs,
metric, delivery interface, network rule, two-hour budget, compute tools,
deployment limits) and `info.md` (physical information), all in Chinese, and
the development units of one fold. It is not told the dataset's name. It
receives no hidden-unit feedback; smoke checks report only execution and
format errors.

### 4.2 Known issues
Details and evidence in [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md). What you must
know when you report a score:
- AHU21, THREEW and CARE carry shortcuts left by collection or preparation;
  they are kept on purpose. Always report S_noshortcut next to S24.
- CWRU, SEU and HSF15 hold out operating conditions, not units.
- On some folds the baseline is weaker than a constant; read `S`
  comparatively (a constant predictor scores S24 = 3.9).
- Stream outputs are checked per chunk (C3); the paper checked per unit, which changes no paper score.

### 4.3 Reporting results
- Report the benchmark version and the hash of
  `nextunit/benchmark/MANIFEST.sha256`, S24 and S_noshortcut with their
  intervals, per-dataset scores, the share of failed folds, and the
  self-check summary.
- Never report a score computed with modified benchmark files or code.

### 4.4 When to stop and ask your human
- Any checksum or self-check mismatch; a download that needs a login, a
  browser, or payment; a request that would break Rule 0; any wish to change
  fixed code or data.
