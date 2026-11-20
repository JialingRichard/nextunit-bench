# Tests

Offline tests that need no credentials, no GPU and no dataset (synthetic
tasks):

- `test_eval.py`: metrics and scoring, the evaluator end to end (batch and
  stream layouts, per-chunk check, failures, tampered seals, no network).
- `test_data.py`: raw-data tools (unpacking, nested extraction, hash checks)
  and prepared-data verification.
- `test_links.py`: prepared roots containing symbolic links; every view the
  runner and the evaluator build must hold regular files.

Run from the repository root:

    python -m unittest discover -s tests

The end-to-end cases need `bwrap` and unprivileged user namespaces; they use
the host interpreter.
