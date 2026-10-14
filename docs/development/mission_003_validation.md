# Mission 003 execution and review

## Phase A: completed before characterization

Published repository: https://github.com/adithyakupad/cerebro

Verified `main`: `8f9ffd91e4342713cb5a571e63d9931484caa143`.
Annotated tag `v0.1.0` points to that commit. The forward push did not overwrite
remote changes; local and remote history matched before publication. No GitHub
Release, dataset attachment, or binary package was published.

After the candidate-only validation described in `publication_validation.md`,
an actual fresh clone from the public GitHub URL was installed with the documented
editable dev command in the existing Conda `cerebro` environment (Python 3.11.16).
Import resolved to that clone. It independently downloaded the exact asset from
public DANDI, matched the published checksum, ran all **33 tests** (no skips,
two legacy-device warnings), and regenerated NPZ/CSV/JSON plus four figures.
The newly generated report identified the verified published commit and repeated
the 14,342 × 142 matrix and 131,262 retained spikes. Unauthenticated raw GitHub
file reads matched published README, metadata, manifest, and SENSE source bytes.
The published tree had 27 files and no NWB/NPZ/cache binaries. Editable installation
was restored to the main workspace after verification.

This tested fresh public source and data acquisition using the existing Conda
environment. Conda creation and cross-platform behavior were not tested. A
separate dependency resolution ignored installed packages and resolved declared
requirements. No additional environment or global tool was installed.

## Phase B: local research branch

Branch: `research/signal-characterization`, based on the published foundation.
Source/data integrity: original SENSE code, source manifest, raw recording,
initial report, and four initial figures are preserved. New analysis and plotting
commands use only existing NumPy/PyNWB/Matplotlib dependencies. JSON provenance
contains source hashes, environment versions, foundation revision, and the dirty
analysis-worktree flag. Numerical reports contain no wall-clock timestamp.

Full suite: **46 passed, 6 warnings**, no skips. Warnings concern legacy NWB
device manufacturer metadata, not count-validation errors. New tests cover known
sparse counts/rates, sample variance/Fano edge cases, missing/silent units,
trial-local binning, matched coverage, per-unit conservation, unmodified
electrode links, and byte-identical real-data report regeneration. All per-unit
rates on matched exposure agree within 1e-12 Hz across widths.

Manual review includes numerical definitions, all changed source and tests,
both reports, and five rendered figures. `git diff --check` and `pip check` pass.
No independent agent, Graphify graph, lint, type-check, or coverage tool was
run; the established bounded workflow and Ponytail principles were used.

Scientific findings, uncertainties, and a proposed next experiment are in the
generated Markdown report. Temporal Fano values do not establish Poisson firing
or trial-conditioned variability. +96 metadata candidates are not applied.
Research changes remain local, uncommitted and unpushed; no merge, PCA, or decoding.
