# Full-scope verification evidence

This records executed checks, not a final release certification.

Final workspace suite: **205 passed**, zero failed, 20 legacy NWB warnings,
66.11 seconds; this includes the subject diagnostic. Nine assets and eight
experiments are indexed, with 283 numerical/checkpoint entries.

- Existing Conda `cerebro`: Python 3.11.16; no additional environment created.
- Isolated source-snapshot full suite: **201 passed**, zero failed, 20 legacy
  NWB manufacturer warnings, 50.08 seconds. Recorded coverage, cross-subject
  masks, restoration and clock guards were included. A later identity diagnostic
  passed four focused tests and independently reproduced exact results.
- The exact documented `python -m pip install -e '.[dev,classical,deep]'`
  command succeeded, including build isolation. Declared dependencies passed
  `pip check`. Fresh dependency resolution was
  executed as a dry run; it is not a fresh environment installation.
- An isolated source snapshot was installed with the documented editable extras
  using the existing Conda environment; installation succeeded. The working
  checkout's editable installation was restored. Fresh public acquisition and all major workflows passed: nine assets verified.
  Seven experiments reproduced their scientific arrays, metrics and controls
  exactly. See `isolated_verification.json`. This is a source snapshot procedure;
  no published clean-clone success is inferred.
- Regular package wheel built, includes MIT license, excludes recordings and
  numerical/checkpoint data. Compilation and whitespace checks passed earlier.
- Interactive explorer tested with actual stored Maze and LINK results: trial,
  decoder, PCA, calibration and ablation controls worked without console errors.
- Targeted scanning of 114 source/document/config files found no credential patterns; no unignored file exceeded 10 MB. Configuration scanning found no executable
  machine-specific paths. This was not a comprehensive security audit.
- Read-only scientific review found two report/protocol guards, now corrected:
  README historical scope and dynamics validation of native 20 ms clocks.

Two initial verification attempts failed because an extra source-path override
shadowed installed metadata, including one concurrent install/test overlap.
Sequential installation and the documented test command without that override
passed; no tests were weakened.

Committed local clone `3767295c5fd7abe0ca8ad295b6481982e01e6162` passed
all 38 verification commands and **205 tests** (20 warnings, 48.60 seconds).
It began clean, with no processed data beyond `.gitkeep`. Maze Small downloaded
fresh; eight assets from prior fresh public downloads were explicitly reused
after checksum verification. No derived arrays/checkpoints/splits were copied.
All eight experiments matched numerical results and source hashes. Installation,
imports, dependency checks and restoration passed. See `committed_verification.json`.
The final wheel includes all models and MIT license, with no recordings/checkpoints.

Public branch `codex/research-platform` and draft PR #1 were verified at
`64d4d30e7e308d673ecfbe5056bd5366b27d823e`; all 157 remote blob hashes matched.
Anonymous public cloning, documented installation, four installation tests and
`pip check` passed. Both push/PR CI runs succeeded: fresh Linux dependencies,
**193 tests passed, 12 data-dependent tests skipped**. CI did not download
recordings or reproduce scientific results. See `publication_verification.json`.
Main and v0.1.0 remain unchanged. No merge or final release tag was performed.
The temporary verification server was stopped; the HTML explorer is offline. No GPU, standalone type-checker or coverage run has
been claimed. Preserve v0.1.0; a final release tag requires all delivery gates.
