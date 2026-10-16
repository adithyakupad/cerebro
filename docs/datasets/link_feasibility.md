# LINK sampled longitudinal feasibility

## Authentic pair and provenance

The [LINK release](https://dandiarchive.org/dandiset/001201/0.251023.2336)
is pinned to DANDI 001201 version `0.251023.2336`, CC-BY-4.0. Attribute
Temmar and colleagues, *Long-term Intracortical Neural activity and Kinematics
(LINK)*, and DOI `10.48324/dandi.001201/0.251023.2336`; see the
[authors' dataset documentation](https://chesteklab.github.io/LINK_dataset/).
The two chronological center-out (CO) sessions were selected from public
asset metadata before acquisition. Both passed published byte-size and SHA256
verification and remain in Git-ignored `data/raw/link/`.

| Field | 2020-01-27 | 2020-01-30 |
|---|---|---|
| Asset ID | c002a9a1-664d-4a69-af02-ba810046c4fb | 9d1820f1-7583-4faf-bbd0-7e9fb7001ca4 |
| Bytes | 45,005,026 | 43,863,496 |
| Source identifier | 2020-01-27_CO_nwb | 2020-01-30_CO_nwb |
| Threshold-crossing and SBP shape | 27,649 × 96 | 26,944 × 96 |
| Trials | 375 | 375 |
| Native timestamp span, seconds | 8.410–561.370 | 15.465–554.325 |
| Referenced trial samples | 27,274 | 26,569 |

Exact checksums and acquisition URLs are in `configs/link_20200127.json` and
`configs/link_20200130.json`. Measured source fields, channel coordinates and
data checks are in `reports/link_native_audit.json`.

## Native representation and supported coverage

The subject is Monkey N. Both files have a null `session_id`; retain the unique
source NWB identifier as the session key rather than inventing a source field.
Both native reference clocks are midnight UTC on their recording dates.
There is no sorted-units table or individual spike timestamp list.

Six source time series are reachable through trial `timeseries` references and
NWB children, despite empty acquisition and processing collections:
`ThresholdCrossings`, `SpikingBandPower`, `index_position`, `mrs_position`,
`index_velocity`, and `mrs_velocity`. All six have exactly identical timestamps
within each session. All observed data values are finite. Timestamps are strictly
increasing with median 20 ms spacing; maximum spacing is 21 ms. There are 36 and
44 intervals above 20.001 ms respectively. Preserve this clock jitter; do not
replace timestamps with an idealized clock or fill missing samples.

Threshold-crossing arrays are nonnegative integer-valued, with observed range
0–8. Source descriptions specify crossings at −4.5 RMS summed in 20 ms bins.
The ElectricalSeries `unit` field nevertheless says **volts**, with conversion 1.
This is a metadata inconsistency: preserve it and label any interpretation as
threshold-crossing counts justified by source description, values and authors'
documentation. SBP is labeled volts with conversion 1e−6 despite a power label;
avoid claiming calibrated physical power until that convention is resolved.

Position arrays are samples × 1, in normalized flexion units (0 full extension,
1 full flexion). Velocity arrays are samples × 1 in **flexion units per time
bin**, not meters/second or hand velocity. Preserve this native target convention.
Do not silently convert velocity without a stated timing interpretation.

Electrode row references explicitly identify all 96 feature columns. Array name,
bank, pin, row and column coordinates and source electrode IDs are identical
between these files. This supports a documented channel-coordinate mapping,
not persistent neuron correspondence: threshold crossings can reflect changing
neurons and multiunit mixtures on the same contact.

The sampled arrays establish observed neural and behavioral samples, unlike the
Perich files' missing observation intervals. They do not certify unobserved
between-sample activity or uninterrupted raw recording. No explicit per-sample
quality mask was present among the six referenced series. Finite samples alone
do not prove electrode quality or absence of preprocessing artifacts.

## Trial and evaluation policy

All 375 trials in each file have target style CO and run ID 3. Trials include
source trial number/count, index and MRS target positions, trial timeout, and
explicit references into each series. No go cue or movement-onset marker is
available. All modalities share each trial's reference start/count. References
leave one sample per trial unassigned: 375 per session. Preserve these exclusions
and use source reference slices; do not include endpoint samples by interpreting
start/stop as inclusive bounds. Splits must preserve original trial numbers and
keep returns to center distinct from reaches away from center.

This pair supports a limited same-subject, same-task, three-day longitudinal
channel-level workflow. Use a source-session training split, early chronological
target-session calibration trials, and later untouched evaluation trials.
Keep sampled clocks, target units and channel coordinates explicit. Model or
adaptation conclusions require actual held-out evaluation and cannot establish
3.5-year stability from these two sessions. No modeling was performed in this
feasibility audit.

Reproduce acquisition using the existing environment:

```bash
python -m cerebro.dataset configs/link_20200127.json
python -m cerebro.dataset configs/link_20200130.json
```

The native audit was executed using established PyNWB and source trial
references. The generic `nwb_audit` command currently audits units and behavior
processing modules; it does not yet reproduce this LINK-specific reference audit.
`cerebro.link.load_link(manifest)` materializes neural counts, finger positions,
velocities and native timestamps using those explicit references. Its channel
mapping helper requires identical unique source contact-coordinate sets; no
implicit column or neuron identity is assumed. Source quality masks are absent,
so returned finite-value masks describe available numbers rather than certified
recording quality.

## Mission 014 additional native session

The [additional acquisition audit](mission_014_acquisition.md#link-2020-02-05)
records the checksum-verified 2020-02-05 CO session, its exact contact mapping,
375 native trial references and observed sampled-count coverage. The
[machine inventory](mission_014_inventory.json) preserves its full native audit.
The acquisition evidence is distinct from subsequent model experiments.
