# Mission 004 execution and verification

## Preservation gate

Mission 003 was inspected on `research/signal-characterization`. Its full suite
passed **46 tests**, no failures or skips, with six legacy NWB manufacturer-field
warnings. Source hashes, report hashes, the pinned asset checksum, numerical
summaries, and all five figures were checked before committing.

Local Mission 003 commit: `4fe2bd0f605c90fc0928511d511bd1a39bcb1f92`
(`research: characterize MC_Maze spike counts across bin widths`). It was neither
merged nor pushed. Published `v0.1.0` remains at
`8f9ffd91e4342713cb5a571e63d9931484caa143`; the tag was not changed.

Mission 004 uses local branch `codex/event-aligned-activity`, based on that
Mission 003 commit. All 23 previously tracked source/test/report/figure/manifest
files checked against the commit remained byte-identical. New artifacts have
separate event_04 names. Raw data and derived NPZ tensors remain Git-ignored.

## Scientific gates and protocol

The real-file feasibility audit preceded the final protocol. Its 75 training
trials have 27 geometry-compatible conditions: 21 with three repetitions and
six with two. Maze-only grouping would inflate repetitions by mixing variants.
All target, go and source-onset markers are finite and have complete coverage
for the candidate window. Go cue was selected explicitly by the human researcher.

`configs/event_04.json` declares the event/window, 20 ms bins, condition threshold,
behavioral coverage policy, comparison epochs, fixed covariance bin, and whole-
trial bootstrap settings. No validation trials enter means, uncertainty or
covariance. Reliable residual correlations are withheld because no condition
has sufficient replication under the declared screening policy. Descriptive
residuals and mean-response/total covariance outputs are labeled accordingly.

## Executed validation

- Initial new-module suite: **13 passed**, no failures, four legacy-device warnings.
- Complete final suite: **59 passed**, **0 failed**, **0 skipped**, ten legacy-device
  warnings, using Python 3.11.16 in existing Conda `cerebro`.
- Tests exercise event/bin units and boundaries, source identities, variant/
  geometry grouping, missing markers, coverage gaps, silent units, rate conversion,
  condition-time residuals, constant/missing correlation inputs, validation-trial
  exclusion, whole-trial resampling, and real-report/tensor reproducibility.
- Real-data JSON was regenerated twice in the automated test with identical
  bytes. Tensor values and their per-array hashes agree. Archive byte identity
  is not asserted; numerical content is the reproducibility target.
- The final experiment retained **53,670** primary-window spikes and **52,175**
  secondary-window spikes with per-unit/trial conservation checks. All 75 windows
  passed for both events. Residual zero-sum error was below 1e-12.
- Seven figures were rendered and visually inspected for source labels, units,
  event/time axes, uncertainty wording and explicit unsupported residual inference.
- Asset/source/tensor integrity, prior-artifact preservation, `pip check`,
  `git diff --check`, and final Git status checks passed. No dependency was added.

Manual review used established bounded ECC/Ponytail conventions. No agent fan-out,
Graphify graph, standalone lint/type checker, coverage tool, new environment,
or infrastructure was needed. The scientific report and learning notes contain
the uncertainty assumptions and the case for a larger recording feasibility audit.

Mission 004 changes remain local and uncommitted. No push, merge, tag update,
PCA, decoder, learned representation, or subsequent mission was performed.

## Full-scope preservation review

The later full-scope directive authorizes consolidation and subsequent research.
Independent review identified two robustness issues for nondefault protocols:
fixed scientific labels with configurable parameters, and positional pairing of
independently accepted event subsets. Fixed publication protocol validation now
rejects unsupported settings, and timing joins use original trial IDs. Default
empirical values are unchanged; source hashes and figures were regenerated.
The focused event suite passed 20 tests (four legacy-device warnings), including
seven additional protocol/identity checks. This addendum supersedes the prior
statement that this mission must remain uncommitted indefinitely; the historical
execution record above is retained.
