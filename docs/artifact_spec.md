# Artifact specification

An artifact is what a method (or an agent) delivers for one fold. The
evaluator in `nextunit/eval/evaluator.py` runs it; this document states the
rules it applies. The task description each agent receives (`task.md`, in
Chinese) states the same rules.

## Contents

A directory with, at its root:

| File | Rule |
|---|---|
| `artifact.py` | Defines `predict(input_directory, output_file)`. |
| `resources.json` | A JSON object describing dependencies, expected run time and GPU needs. Required, but not read by the evaluator. |
| anything else | Model files, code, bundled packages. Symbolic links must point inside the directory. |

Nothing outside the directory is available at deployment, and there is no
network. The predictor runs in the pinned runtime environment (`runtime/`);
packages it needs beyond that must be bundled.

## How it is called

- Each hidden unit runs in a fresh process, in a sandbox that sees the
  artifact (read-only, as the working directory `/artifact`), the runtime, and
  that unit's inputs at `/input/entity_XXXX/inputs` (read-only). Writable:
  `/tmp` and the output directory. State does not carry over between units.
- `artifact.py` is imported once per unit; `predict` is then called once
  (batch tasks) or once per chunk (stream tasks), each time with the same
  `input_directory` and a new `output_file`.
- **Batch tasks**: the input directory holds the unit's whole input.
- **Stream tasks**: before each call the input directory holds only the
  current chunk. Module-level state persists across the chunks of one unit.
  Layout per task (`stream_layout` in `task.json`): `flat` (the chunk's files
  directly in the input directory), `manifest` (the chunk as a subdirectory
  plus `stream.json` naming it), or `manifest_with_flat_alias` (both).
- Stdout of the predictor is redirected to stderr; anything it prints is only
  logged.

## Output

`output_file` must be a UTF-8 CSV with exactly the columns
`record_id,prediction`, in this order.

- Every requested record ID of the unit appears exactly once, no other IDs.
  Requested IDs are listed in the input's request index (`query.csv`,
  `requests.csv`, `records.csv`, `signals.csv`, `features.csv` or
  `records.json`, depending on the task).
- Predictions are finite numbers. In classification tasks they must be among
  the task's `prediction_values`.
- In stream tasks this holds for every call: the output of a call contains
  exactly the IDs requested by the current chunk (KNOWN_ISSUES.md, C3).

## Failure

The fold fails, and scores `S = 0`, if any unit's process exits with an
error, returns without writing its output, writes a file with other columns,
an empty file, duplicate or missing IDs, non-finite values, or class values
outside the allowed set. Deployment has no time limit; the smoke check during
development runs within the remaining development budget.

## Sealing

Before deployment the artifact is sealed: copied, every file's SHA-256 is
recorded in `sealed_artifact.json`, and write permission is removed. The
evaluator re-checks the files against that record before running them.
