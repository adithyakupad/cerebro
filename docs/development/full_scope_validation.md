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

CI, committed clean-clone checks and publication remain pending. No GPU, standalone type-checker or coverage run has
been claimed. Preserve v0.1.0; a final release tag requires all delivery gates.
