# MC_Maze Small: observed inventory and reproducibility

Mission 002 selected the training NWB asset in
[DANDI 000140, version 0.220113.0408](https://dandiarchive.org/dandiset/000140/0.220113.0408),
asset `7821971e-c6a4-4568-8773-1bfa205c13f8`, under CC-BY-4.0.
Published SHA-256: `dcaf3a524e2b2f65f163ee3b07789b8474bdfc6ca66098bc542ab93dff489884`.
The downloaded size is 29,207,528 bytes. Full source identity and citation are in
`configs/mc_maze_small.json`; executed measurements are in `reports/sense_01.json`.

## Discovery decision

Version-specific DANDI listings show two assets per release:

| Release | Training behavior + ecephys asset | Test ecephys asset |
| --- | ---: | ---: |
| [000128 v0.220113.0400](https://dandiarchive.org/dandiset/000128/0.220113.0400) | 690,612,247 bytes | 3,392,688 bytes |
| 000140 v0.220113.0408 | 29,207,528 bytes | 689,312 bytes |

Small training is the smallest candidate whose asset name includes behavior.
Only the selected Small file was downloaded and inspected; the standard file's
actual fields and the test files' internal contents were not inspected. These
variants must not be assumed identical. Mission 002 explicitly authorizes this
choice, superseding the initial standard-release plan.
The [official NLB codepack](https://github.com/neurallatents/nlb_tools) reader was
inspected for trial, observation-interval, and timestamp conventions. PyNWB reads
the file directly without adding NLB's modeling or preprocessing dependencies.

## Actual file observations

- Subject Jenkins, species `Macaca mulatta`; session `small`; reference time
  `2009-09-28T00:00:00-07:00`; NWB identifier
  `76ff7eba-0b93-11ec-a90d-3da92aaa0e59`.
- 142 sorted units, 131,669 spike timestamps. Unit columns: `heldout`,
  `spike_times`, `obs_intervals`, `electrodes`. The held-out flags identify
  35 units; 107 are held-in. All are present in this training asset.
- 192 electrode entries with location, group, x/y/z, impedance, and filtering
  metadata. Coordinates include missing values; no anatomical reconstruction
  is attempted. The [NLB dataset notes](https://neurallatents.github.io/datasets.html)
  document erroneous M1 electrode indices. Stored mappings remain unchanged.
  Observed here: all 142 unit links point to PMd-labeled electrodes, although
  70 unit IDs have the documented M1 prefix (2); 72 have PMd prefix (1).
  This discrepancy is recorded, not used to relabel or repair electrode entries.
- 100 successful retained trials: 75 `train`, 25 `val`. Fields include bounds,
  trial type/version, maze ID, success, target/go/movement events, reaction time,
  delay, target/barrier geometry, active target, and split. Full source field
  descriptions and tables are retained. `delay` is documented in ms; `rt`'s
  source description omits a unit, so it is not converted or used by the pipeline.
- Empty acquisition group; four numeric time series in behavior processing.
  Each has shape **(287,710, 2)** and **(287,710,)** timestamps. Available fields:
  `hand_pos`, `hand_vel`, `cursor_pos`, `eye_pos`, with x/y columns. Each has
  conversion 0.001 and offset 0: stored mm → meters, stored mm/s → m/s.
- Behavior timestamps span 0–293.665 s. Within-trial sampling is nominally 1 ms;
  retained-trial gaps reach 110 ms. Spike timestamps span 0.012567–293.6653 s.
  Times are relative to the file's reference clock, not reconstructed elapsed
  time in an uncurated acquisition. Raw timestamps are preserved.

## Implementation and checks

Run from the repository root, using the existing Conda environment:

```sh
conda activate cerebro
python -m pip install -e '.[dev]'
python -m cerebro.dataset configs/mc_maze_small.json
python -m cerebro.sense_inspect configs/mc_maze_small.json --bin-width 0.02 --max-gap 0.002
python -m pytest
```

The pinned metadata and checksum are checked before loading. Downloads use a
partial file and never replace an existing recording with unchecked bytes.
An interrupted `.part` file is retained; inspect/remove it explicitly before
retrying. Raw recordings and large derived arrays are Git-ignored. The four
compact SENSE reference figures are preserved in Git for publication.

The human researcher selected 20 ms bins for initial inspection on 2026-10-14.
Full 20 ms bins restart at each trial start; intervals are `[left, right)`.
Derived edges have 1 ps precision; original values are untouched. Incomplete
tails total 0.870 s across trials. Counts shape is **(14,342, 142)**, retaining
131,262 spikes; 407 tail spikes remain available in the raw export. Per-unit
spike conservation passes on the retained bins, not on the omitted tails.

Each behavior stream is averaged over native samples within a bin after applying
its NWB conversion and offset, giving **(14,342, 2)**. No interpolation, smoothing,
extrapolation, fitted timing offset, or samples across bin/trial boundaries are
used. Coverage requires sample endpoints within 2 ms of each edge and no internal
sample gap exceeding 2 ms. This is a documented inspection policy.

Executed checks: checksum/size match; no NWB schema errors; finite ordered spikes
and behavior timestamps; unique IDs; ordered nonoverlapping trials; no empty
units or duplicate spike times; no spikes outside observation intervals; all
retained neural and behavior bins valid; no nonfinite behavior values. This does
not establish spike-sorting quality or independently verify sensor latency.

`data/processed/sense_01.npz` contains raw flat spike arrays and offsets, unit
IDs, held-out flags, observation intervals, trial IDs/splits/bounds, original
behavior values/timestamps, aligned physical values, and validity masks.
CSV tables preserve trial, electrode, and unit metadata, including stored
electrode links. Use the report alongside the archive for units/conversions.

Four figures under `reports/figures/sense_01_*.png` show raster, population counts,
native hand/cursor trajectory, and count/velocity alignment. The interval is
training trial ID 1, **[3.500, 5.620) s**. All include release/asset identity,
time interval, and units. Lines connect observations within this single trial;
they are visual guides, not continuous signal reconstruction. Between-trial
gaps are excluded from arrays and reported rather than filled with zero counts.

## Review and limits

The first test run had 29 passes and two failures exposing decimal boundary
arithmetic; fixing derived grid construction resolved them. Final results are
recorded in the tooling log. Manual review inspected all changed code and four
rendered figures. Library warnings about legacy device metadata do not imply
schema failure; no edits were made to the source file.

Human decisions remain: whether the selected 20 ms aggregation suits later
questions, whether the 2 ms sampling policy is appropriate, whether a neural/kinematic lag is needed,
and how to use the official splits. No PCA, FA, decoder, adaptation, or claim of
population mechanism is implemented. Suggested next experiment, after approval:
compare 5/20/50 ms count sparsity and timing summaries on training trials while
preserving the same spike-conservation and boundary checks.
