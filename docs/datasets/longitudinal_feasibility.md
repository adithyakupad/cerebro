# Longitudinal recording feasibility

## Verified acquisition

The public [Perich–Miller release](https://dandiarchive.org/dandiset/000688/0.250122.1735)
is pinned to DANDI 000688 version `0.250122.1735`, CC-BY-4.0. Attribute
Perich, Matthew G.; Miller, Lee E.; Azabou, Mehdi; and Dyer, Eva L.,
*Long-term recordings of motor and premotor cortical spiking activity during
reaching in monkeys*, DOI `10.48324/dandi.000688/0.250122.1735`.
Published metadata identifies 111 NWB assets across four subject directories;
its prose inconsistently says three and four subjects. The two acquired files
are authentic subject J center-out sessions, not simulated or resampled sessions.

| Measurement | 2016-04-06 | 2016-04-07 |
|---|---:|---:|
| File bytes | 23,988,300 | 22,119,020 |
| Units | 18 | 19 |
| Spikes | 152,389 | 130,191 |
| Trials | 296 | 331 |
| Rewarded trials | 195 | 199 |
| Abort / incomplete / fail | 76 / 23 / 2 | 94 / 27 / 11 |
| Finite go cues | 220 | 236 |
| Rewarded trials covering go −400 to +1000 ms | 173 | 186 |
| Behavioral samples × dimensions | 100,516 × 2 | 107,796 × 2 |

Exact identities and published SHA256 hashes are in
`configs/perich_j_20160406.json`, `configs/perich_j_20160407.json` and
`docs/research/dataset_inventory.json`. The assets were downloaded separately
and matched both published size and SHA256. Raw files remain Git ignored.

## Native schema and constraints

Both sessions contain `spike_times`, `electrodes` and `waveforms`, with electrode
locations labeled Primary Motor Cortex. These native columns do not independently
specify sorting quality or persistent neuron identity. Unit IDs restart at zero;
electrode associations differ between days and multiple units share electrodes.
Use `(session_id, unit_id)` as the local unit key. Do not match neurons by ID,
electrode number or similar firing profiles.

Neither file provides `obs_intervals`. Neural observation coverage is **unknown**:
the earliest and latest observed spikes do not establish continuous recording
between them. Do not manufacture observation intervals from spike extrema,
behavior timestamps or trial boundaries. Trial-window coverage reported above
means behavioral/trial-window support, not certified continuous neural coverage.

Cursor position, velocity and acceleration have native timestamps in seconds,
100 Hz sampling and units cm, cm/s and cm/s² respectively (conversion 1, offset 0).
These are cursor variables, not the Maze `hand_vel` field. Day 06 behavior spans
0.30–1005.45 s; day 07 spans 0.31–1078.26 s. Native reference clocks are the
source session starts: 2016-04-06 17:33:16.642 −04:00 and
2016-04-07 17:10:37.240 −04:00. Preserve these clocks; do not concatenate days
into a fictitious continuous recording.

Trials provide start/stop, target onset, go cue, target ID/direction/corners and
outcome. There is no movement-onset annotation or predefined train/calibration/
test split. Outcome R denotes reward, A abort, F fail and I incomplete.
Eight target IDs map consistently to eight directions across both recordings.
For complete rewarded go windows, counts by target ID 0–7 are
`[25,21,21,25,17,19,20,25]` and `[28,18,29,26,17,20,26,22]`.
Target corners nevertheless vary within most IDs despite constant direction.
Preserve the raw geometry discrepancy; target-direction comparability does not
prove identical physical target geometry.

## Minimal next analysis and decisions

First audit separate session populations and compatible target directions with
explicit chronology and trial identities. Fit any preprocessing on designated
training trials only; reserve later trials for target-session calibration and
evaluation. A longitudinal decoder comparison needs an explicit strategy for
18 versus 19 independently identified units; silently treating columns as the
same neurons is invalid. The human selected documented neural coverage as a
requirement; these assets remain audit-only until authoritative coverage evidence
is available. Target-geometry limitations also require explicit review.
Two adjacent days support a limited cross-session experiment, not a claim about
long-term stability or broad adaptation.

Reproduce acquisition and inspection from the repository root:

```bash
python -m cerebro.dataset configs/perich_j_20160406.json
python -m cerebro.dataset configs/perich_j_20160407.json
python -m cerebro.nwb_audit configs/perich_j_20160406.json --output reports/perich_j_20160406_audit.json
python -m cerebro.nwb_audit configs/perich_j_20160407.json --output reports/perich_j_20160407_audit.json
```

## Other public choices, not acquired here

[LINK](https://chesteklab.github.io/LINK_dataset/) is pinned public DANDI
[001201 version 0.251023.2336](https://dandiarchive.org/dandiset/001201/0.251023.2336),
CC-BY-4.0: 312 sessions on 303 days from a single monkey, spanning 1,242 days.
Its 96-channel threshold crossings and spiking-band power, with 20 ms finger
kinematics, provide a separate chronic channel-level task. They are not sorted
units or arm/cursor behavior. The reference repository also describes 32 ms
derived files; native NWB timing must take precedence. No LINK native file was
inspected or acquired, and no CEREBRO split is established.

The Perich release itself offers four subjects and is the most direct next
multisubject candidate, after native compatibility checks. The
[O’Doherty/Makin reaching dataset](https://zenodo.org/records/583331) offers
37 Indy and 10 Loco sessions, spike timestamps and 250 Hz arm/target positions.
Its newer version, exact license and asset identity need pinning before use;
its MATLAB/HDF5 schema needs a separate adapter. Finger and arm experiments
must remain distinct compatible-target analyses.
