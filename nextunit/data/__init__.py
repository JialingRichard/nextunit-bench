"""Data acquisition and conversion (filled at M4).

- ``sources``: per dataset, the official URL, any documented mirror (PHMD for
  PHME20 and PHM2010, marked as a third-party mirror without a licence
  statement), expected SHA-256 of every raw file, and the licence.
- ``download``: fetches raw files and refuses any file whose hash differs.
- ``adapters``: one converter per dataset, ``build(raw_dir, out_dir)``, which
  writes the prepared layout (one directory per unit with ``inputs/`` and
  ``labels.csv``). Release fix applied here: MIMII_DUE files are written in
  file-name order with one fixed modification time.

Converters are fixed code. The agent that builds the benchmark runs them; it
does not edit them.
"""
