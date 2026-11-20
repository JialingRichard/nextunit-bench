# Known issues

Every issue below is known and decided. The numbers for A1-A3 are recomputed
from prepared data by `python -m nextunit.selfcheck.evidence --prepared
PREPARED_ROOT` (descriptive statistics only, no model fitted).

v1.0 is identical to the paper. Issues that affect scores are therefore kept
and documented, not fixed; the only changes are those listed under C, which
leave every score unchanged.

| # | Dataset | Issue | v1.0 status |
|---|---|---|---|
| A1 | AHU21 | Fault schedule shared by all units (collection); absolute time predicts the label | Kept; excluded from S_noshortcut |
| A2 | THREEW | Requests only for labelled rows (preparation); request position + instance length reveal a class | Kept; excluded from S_noshortcut; fix planned for v1.1 |
| A3 | CARE | Observation-window length separates anomalies within a wind farm (collection) | Kept; excluded from S_noshortcut |
| B1 | PUBD16 | Original `info.md` listed per-unit run history | Redacted `info.md` shipped; residual noted |
| B2 | CWRU | `info.md` says normal records were downsampled, a processing trace | Kept |
| C1 | MIMII_DUE | Hidden-file timestamps and write order follow the label | Fixed; scores unchanged |
| C2 | NCMAPSS | Evaluator once omitted a promised input file | Fixed before the paper's final scores |
| C3 | stream tasks | Outputs were checked per unit, not per chunk | Fixed (per-chunk check); scores unchanged |
| C4 | CARE | Prepared files differ byte-wise from the paper's; arrays identical | Verified per array; scores unchanged |
| D1 | all | Baseline `B` is worse than a constant on some folds | Kept; documented |
| D2 | CWRU, SEU, HSF15 | Conditions, not units, are held out | Kept; documented |
| D3 | all | Development has internet access; content rules are not technically enforced | By design; documented |
| D4 | all | Public datasets; agents may recognize them | Documented |
| D5 | all | Task descriptions are in Chinese | Kept (as in the paper) |
| E1 | all | `B` is a frozen table and cannot be recomputed | By design |
| E2 | all | Runtime differs from the paper's host snapshot | Documented |

---

## A. Shortcuts kept on purpose

These are the three datasets whose collection or preparation left a shortcut:
regularities that come from how the data were made, not from the machines.
AHU21 and CARE carry them from data collection; THREEW from preparation, that
is, from how this benchmark builds its prediction requests. Held-out units
cannot expose them. They stay in the benchmark as hidden indicators of fitting the protocol
rather than the machine (paper, Sec. "Fitting the Machine, or the Protocol").
Every score is reported twice: **S24** (all datasets) and **S_noshortcut**
(without AHU21, THREEW, CARE).

### A1. AHU21: shared fault schedule (collection)
- Faults were introduced in all air-handling units on the same schedule, so
  the timestamp alone predicts the fault.
- Evidence (paper): re-running sealed predictors with each unit's clock
  shifted by a random 365–1825 days dropped scores of up to 86 to 18 or less.
- Evidence (script): a predictor that uses nothing but the timestamp
  (fault if the time is a fault time of a development unit) scores S of
  95.4, 86.1 and 74.3 on the three folds.

### A2. THREEW: request set follows label availability (preparation)
- The converter issues prediction requests only for rows with a label. Label
  gaps differ by event class, so the relative position of the first requested
  row in an instance, together with the instance length, identifies class 4
  (flow instability).
- Evidence (script; event class taken from the instance's labels): class 4
  has 343 instances of 10,568–14,138 rows, first request at relative
  position 0.335 (IQR 0.002); class 0 has median position 0.168.
- v1.1 will change request construction; v1.1 scores are not comparable with
  v1.0.

### A3. CARE: observation-window length (collection)
- Within a wind farm, anomalous and normal events have different observation
  windows. Single-variable ROC-AUC against the label (script): window length
  0.20 at site 1 (0.80 reversed; medians 11.5 against 18.3 days) and 0.89 at
  site 2 (39.5 against 19.0 days); distance of the window length from whole
  days 0.77 at site 3.

## B. Traces in the documentation

### B1. PUBD16: per-unit run history in `info.md`
- The original `info.md` contained a warm-up table listed per anonymous unit,
  which identified healthy bearings. The paper's main experiments saw that
  version; one of 81 checked deliveries used it, and removing PUBD16 changes
  method scores by −1.8 to +0.2.
- v1.0 ships the redacted version, the one used from the paper's
  plans-without-data experiments on. Removed: the per-unit table of earlier
  operating conditions, the per-unit warm-up table (radial force, speed,
  duration, temperature reached), and the remarks that described the
  accelerated-ageing rig, run-in, and warm-up end temperatures. Kept: the
  manufacturer and geometry tables.
- A documentation-only predictor (reads `info.md`, never the signals) scores
  S of 19.7 / 18.1 / 4.4 on the three folds with the original file and
  0.0 / 4.4 / 0.0 with the redacted one, the majority-class level (6.4 / 4.4 /
  0.0). Removing the manufacturer column as well gave the same result.
- Residual: the redacted file still lists the manufacturer of each unit,
  which carries a weak cue about the class; at least one delivery in the
  paper's main experiments used it as a feature.
- SHA-256: original `dae6da5612298fb903a9da279fba7f25395f2904334996b3357a2e3a3f59e3ec`
  (not distributed), redacted
  `02cdd40c5d89af67f11631a397e203ac6721cdc7777e9de3a34ddefe46daecc3`
  (`nextunit/benchmark/tasks/PUBD16/info.md`).
- Source of these numbers: the documentation audit made for the paper (not
  re-run by this repository; the original file is not distributed).

### B2. CWRU: downsampling note
- `info.md` states that normal records were anti-alias downsampled from
  48 kHz, which marks them as a processing trace. Effect is small: normal
  records are about a tenth of each hidden condition and easy to separate
  anyway.

## C. Fixed in v1.0 without changing any score

### C1. MIMII_DUE: file timestamps and write order
- In the original prepared data, hidden anomalous files were written before
  normal files, so modification time and inode order separated them
  perfectly. No sealed predictor in the paper used file metadata.
- Fixed in v1.0, with no effect on scores: the converter copies the wav files
  (instead of hard-linking the raw files) in record-ID order, which is a hash
  independent of the label, and sets every file's modification time to
  2026-01-01T00:00:00Z; contents are unchanged. The self-check confirms that neither directory order nor
  modification time depends on the label.

### C2. NCMAPSS: missing input file
- The evaluator first omitted an input file that the task promised; all
  predictors were re-run through the same interface after the fix, as stated
  in the paper. v1.0 contains the fixed evaluator.

### C3. Stream outputs checked per chunk
- The paper's evaluator compared output IDs with requested IDs once per unit,
  after the last chunk. A predictor could therefore have withheld the output
  for a chunk and written it after later chunks arrived; for CALCE and NB1
  the target (capacity ten cycles ahead) appears ten chunks later.
- No paper result used this. Stored predictions are the chunk outputs
  concatenated in order; split at each chunk's requested records, all 1,295
  stream deployments on the current data returned every chunk's IDs in that
  chunk's call. (The only exceptions are 8 superseded runs on the
  uncorrected NB14 data, whose chunks no longer exist.)
- v1.0 checks every call: its output must hold exactly the IDs requested by
  the current chunk. Re-running sealed paper artifacts on stream tasks under
  this check gives the same predictions and scores.

### C4. CARE: file bytes differ, arrays identical
- The paper's CARE files were written by an earlier version of the converter
  (a different zip compression level), then had one array removed with
  `zip -d`, which rewrote their headers, and two arrays appended, which
  stamped the time of writing into the archive. The v1.0 converter writes
  the same eight arrays in the same order in one pass, so the files differ
  byte-wise while every array is identical value for value.
- CARE is therefore verified per array (name, dtype, shape and SHA-256 of
  the C-order bytes; `checksums/prepared/CARE.arrays.json`); its CSV files
  are still verified per file. Nine sealed paper artifacts (three folds
  each from three experiments) re-run on the v1.0 CARE data give the same
  scores; eight give bit-identical predictions, and one differs in the last
  bit of a few predictions (1e-16), as it also does when re-run on the
  paper's own CARE files: that predictor is not bit-deterministic.

## D. Properties of the protocol

### D1. The baseline is weak on some folds
- On a few folds `B` is worse than predicting a constant. A constant predictor
  (training median or majority class) scores S24 = 3.9; on CFRP fold 3 it
  scores 75.9. Read `S` comparatively.

### D2. Held-out conditions
- CWRU, SEU and HSF15 have no independent units; whole operating conditions
  are held out instead.

### D3. Internet during development
- Allowed by design (documentation, packages, pretrained models); obtaining
  extra samples, evaluation data, labels or existing answers is forbidden by
  rule, recorded in logs, and not technically filtered. Development compute
  jobs share the host network and can reach services on the host.
- This repository is public like the datasets. Its splits and checksums are
  covered by the same rule: an agent under evaluation may not consult them.
- What the runner records: the agent has no tools of its own; every shell
  command it runs (downloads and package installs included) goes through
  the compute broker and is logged with its output in the trajectory's
  `compute_events.jsonl` and `compute/`. Requests made by programs those
  commands start are not logged individually.

### D4. Public datasets
- All datasets are public and may be in pretraining data; agents recognize
  most of them from the task documentation.

### D5. Language
- `task.md` and `info.md` are in Chinese, as in the paper. A translation would
  be a new benchmark version.

## E. Reproducibility limits

### E1. Frozen baseline table
- The CNN half of `B` was trained on GPU without deterministic kernels, so
  `B` is shipped as a frozen 58-row table and is never recomputed.

### E2. Runtime environment
- The paper ran predictors in a snapshot of the host system. v1.0 pins the
  same Python packages by lock file and container; system libraries differ.
  Predictors that bundle their own binaries may behave differently.
- Random-forest reference: retraining reproduces the paper's models bit for
  bit (all 57 model files identical); the paper's own predictions used
  multithreaded prediction, whose summation order varies in the last bits
  (at most 4.5e-13 for regression; reordered AP ties for BACKBLAZE, at most
  1.6e-6), so the reference predicts single-threaded and its values are the
  shipped expectations.
