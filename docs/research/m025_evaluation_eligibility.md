# M025 prospective-recording eligibility

2026-10-19. **PASS for the bounded performance-unscored recipe-replication claim**
in the [frozen protocol](m025_protocol.md), commit `7f756c2`. Execution still
requires the development-promotion gate. No model was fitted, prediction scored,
or reserved spike/velocity value read during this audit. Exact evidence hashes,
metadata, timing masks and eligible original IDs are in the
[machine record](m025_evaluation_eligibility.json).

## Recording, targets and identities

The sole approved recording is MC_Maze standard, DANDI `000128`, version
`0.220113.0400`, asset `26e85f09-39b7-480f-b337-278a8f034007`,
`sub-Jenkins/sub-Jenkins_ses-full_desc-train_behavior+ecephys.nwb`.
Its local 690,612,247 bytes reproduce SHA256
`a27f84f9c31f077011062fd99a6ced199fdf19e656151f056c3c6244a408a3c4`.
The [manifest](../../configs/mc_maze.json) records CC-BY-4.0 attribution,
Churchland/Kaufman and the [versioned public source](https://dandiarchive.org/dandiset/000128/0.220113.0400).

Direct native structural inspection confirms Jenkins, session `full`, NWB
identifier `ac9fe3ee-0ba6-11ec-93c2-ab1d5afd05f0`, reference clock
`2009-09-25T00:00:00-07:00`. Sorted-unit IDs are session-local: 137 held-in
units are eligible inputs; 45 held-out units are excluded. Native per-unit
observation intervals establish coverage; spike extrema were not used.

The hand-velocity dataset has shape `6,809,920 × 2`, dtype `float64`, physical
unit `m/s` and conversion `0.001`; NWB's default offset is zero, agreeing with
the prior native audit. Velocity values were not read. Timestamps are finite,
strictly increasing seconds on the recording reference clock. The go-cue field
is described as "Time of go cue delivery, as detected by the photobox".

## Structural and timing eligibility

| Criterion | Status | Evidence or limitation |
| --- | --- | --- |
| Authentic pinned asset and permitted research reuse | PASS | Complete local size/checksum match; CC-BY-4.0 manifest |
| Separate recording from Small development | PASS | Standard Sep25 versus Small Sep28, distinct NWB identifiers and disjoint absolute-clock trial intervals |
| Authentic neural coverage | PASS | Every proposed bin is contained in a native observation interval for every held-in unit |
| Target units and clock compatibility | PASS | Native velocity metadata and timestamp-only checks agree with the frozen recipe |
| Trial identity and source split integrity | PASS | Unique IDs; 1,721 train / 574 val; disjoint split IDs; ordered, nonoverlapping trial bounds |
| Documented absence of previous standard-validation decoder fits/scores/selection | PASS, bounded | Maintained command records and source paths below contain no such computation; private/unlogged activity cannot be certified |
| Raw standard validation never opened | FAIL | Historical eager loading materialized the whole recording; this stronger claim is explicitly not made |
| Proof that no unrecorded prior use exists | INCONCLUSIVE | A repository audit cannot prove absence of private or unlogged operations |
| Finite target values and actual spike-count conservation | INCONCLUSIVE | Mandatory execution-time guards; this metadata audit deliberately did not access those arrays |
| Independent subjects or matched neurons | FAIL | Same animal, different session-local unit populations; neither inference is claimed |

The frozen timing rule is go cue `−0.4:+1.0 s`, 70 half-open 20-ms bins,
20-ms count observations and maximum behavioral sample gap 2 ms. Each window
must stay within its own original trial. Derived edges are rounded to 12 decimal
places, matching existing bin construction. The screen tests every held-in
unit's observation intervals and every bin's timestamp endpoints/internal gaps.
No extrapolation or interpolation is assumed.

| Original split | Trials | Timing/coverage eligible | Window / neural / timestamp exclusions |
| --- | ---: | ---: | --- |
| Train | 1,721 | 1,721 | 0 / 0 / 0 |
| Validation | 574 | 574 | 0 / 0 / 0 |

These are **timing/coverage counts**, not proof that every target sample is
finite or that counted spikes conserve original events. Those checks remain
required after the promotion gate and before reporting model outcomes. The
machine record freezes timing-eligible IDs and little-endian-int64 ID digests:
train `2b0a106cd159eb9516ed0080847acc341787bbf3caff0a14d2a9db33457aedff`;
validation `cd0d266479d094ca8e16d3c45b7f2baa1bdb810347b0dda38cdbe928dbc1619e`.
Any later value-integrity exclusion must be recorded explicitly.

## Prior exposure and the meaning of prospective

[Recorded Mission 014 commands](../development/mission_014_workflows.json)
acquired standard Maze, ran `cerebro.nwb_audit`, and ran
`cerebro.maze_feasibility`. The standard
[native audit](../../reports/mc_maze_native_audit.json) reports metadata,
all-unit spike sanity summaries and whole-stream timestamp summaries. The
[event feasibility report](../../reports/mc_maze_event_feasibility.json)
reports training-only event, coverage and repetition summaries, labeling all
574 validation trials unused. Its stored hashes for `maze_feasibility.py`,
`event_audit.py` and `sense.py` exactly match the audited source.

Importantly, `maze_feasibility.run` calls `sense.load_recording` before
`event_audit.audit` filters original training rows. The loader eagerly
materializes spikes and behavior across the complete file. Historical raw
validation values therefore entered memory, although the reported feasibility
calculations were training-only. `nwb_audit` additionally checked all-unit
spike timestamps and full behavior clocks. No fit, normalization-statistic
estimation, model selection, decoder prediction or decoder error on these
574 trials appears in those source paths or the maintained experiment records.

The integrated technical report explicitly distinguishes standard-Maze native/
feasibility use from **Small** decoder experiments. Repository-wide references
to the standard manifest and report identities, recorded commands and tracked
source/report history were inspected. This supports the operational claim
**performance-unscored under a prospectively frozen recipe**, not a universal
claim of never-seen data. Full private shell history and off-repository analyses
were unavailable; absence of such work is not asserted.

## Overlap and independent units

Native absolute trial bounds are Sep25 `00:00:00–01:55:52.301 −07:00` for
standard, versus Sep28 `00:00:00–00:04:53.666 −07:00` for Small. No absolute
recording interval overlaps. All 100 Small numeric trial IDs also occur as
integers in standard; these are **not duplicate biological trials** because
trial IDs are recording-local. Every identity must include its asset/session.
No cross-session unit-ID correspondence is assumed. Sample-level duplicate
fingerprinting was not performed because it would read reserved arrays; native
session/clock identity establishes the bounded recording distinction.

The evaluation unit is a held-out trial conditional on a single recording.
This is one additional session of **the same animal**, not independent-subject
validation or transfer of one neuron-matched decoder. Session-specific fits
must use only standard training trials for scaling, internal tuning and refits.
The 574 original validation trials remain unavailable for outcome-dependent
changes. A failed Small development gate still forbids their scoring; eligibility
is not permission to bypass that stopping rule or substitute another dataset.

No historical report, model, source or result was modified for this audit.
