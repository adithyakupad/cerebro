# CEREBRO-1: inspect one public MC_Maze recording

Status: implemented under Mission 002's explicit authorization, using MC_Maze
Small instead of standard as requested. See `docs/datasets/mc_maze_small.md`
and `reports/sense_01.json` for observed results and remaining human decisions.
The specification below retains the original planned scope for comparison.

## Objective and inputs

Load one real public intracortical recording and produce an auditable inventory
of neural signals, behavior, events, and timing. Do not train a model or make
decoding/adaptation claims in this milestone.

The [official NLB dataset description](https://neurallatents.github.io/datasets.html)
describes MC_Maze as macaque M1/PMd activity during delayed reaching around
barriers, with cursor, gaze, and hand kinematics. It also documents an M1
electrode-index conversion error; inspect unit IDs and record any correction
explicitly rather than trusting electrode indices.

Select the standard MC_Maze release through the official page's DANDI link.
Record a fixed Dandiset version, chosen NWB asset identifier, checksum, license,
session/subject identifiers, and retrieval date. Inspect the
[official NLB codepack](https://github.com/neurallatents/nlb_tools) and its loading
examples before choosing an NWB reader. Select dependencies only then and check
Python 3.11 compatibility. Never silently substitute a scaled MC_Maze variant.

## Expected structure and synchronization

- Raw unit spike trains: one variable-length timestamp sequence per unit.
  If binned, neural counts have shape `(time_bins, units)`; trial-aligned arrays
  may have shape `(trials, bins, units)` with explicit padding/masks.
- Behavioral streams: `(behavior_samples, coordinates)` with their own timestamps
  or sampling-rate/start-time metadata. Determine coordinate count, units, and
  sampling rate from the file; do not hard-code them.
- Trial metadata: trial boundaries, available task events and conditions, and
  split membership where supplied. Unit metadata: IDs, area/electrode mapping,
  and any quality annotations. Preserve missing fields as missing.
- Discover and report exact unit, trial, sample, and session counts from the
  selected asset. Source descriptions are expectations, not observed results.
- Establish the common clock, time origin, timestamp units, and coverage for
  spikes, behavior, and events. Quantify offsets, gaps, duplicates, and irregular
  sampling. Define bin edges, endpoint rules, event alignment, and any resampling
  policy before conversion. Do not assume equal sampling rates or invent timing
  corrections. Never interpolate across invalid intervals silently.

## Validation and human decisions

Validate readable NWB structure, checksum, monotonic finite timestamps, trial
bounds, unique unit IDs, consistent stream shapes, behavioral units, missing
values, and overlapping recording coverage. Flag empty units/trials and unusual
counts instead of deleting them silently. If counts are generated, test spike
conservation over the selected interval and alignment with a tiny synthetic
fixture clearly labeled as a software test. Respect benchmark withheld-unit and
time masks; absence of released values is not zero activity.

Required background: spike trains versus rates, population matrix axes, NWB
tables/time series, sampling and binning, trial alignment, motor-task metadata,
and leakage-free evaluation. Use PREDICT → LEARN → IMPLEMENT → INTERROGATE →
VALIDATE. Before substantial implementation, the human chooses the exact asset,
inspection interval, bin width if needed, event reference, missing-data policy,
and which behavioral stream to inspect. Cross-session design and models belong
to later milestones.

## Acceptance criteria

1. A reproducible local loading command reads the approved asset without changing
   raw data and records provenance and environment versions.
2. An inspection report gives actual shapes, counts, units, clocks, coverage,
   trial/event inventory, masks, and validation findings, including absent fields.
3. One labeled neural/behavior timing visualization demonstrates inspected
   alignment and exposes gaps; no inferred synchronization is presented as fact.
4. Automated tests cover malformed inputs and temporal boundaries, plus an
   explicit local real-asset check (not a mandatory network download in tests).
5. A human reviews timing assumptions and data limitations. No model performance,
   cross-session result, or unsupported neuroscience conclusion is reported.
