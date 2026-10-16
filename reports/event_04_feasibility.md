# Mission 004: event and condition feasibility

Audit performed before finalizing the event-alignment analysis.

Source: DANDI 000140 v0.220113.0408, asset `7821971e-c6a4-4568-8773-1bfa205c13f8` (SHA-256 verified).
75 train trials are available; 25 validation trials are excluded from estimation.

Grouping by maze alone appears to give 6–9 repetitions, but mixes task variants.
Compatible keys retain maze_id / trial_type / trial_version / active_target and
check identical target/barrier geometry. There are **27 conditions**:
**21 have 3 training trials; 6 have 2**. No condition has adequate replication
for a reliable trial-residual covariance claim. No compatible conditions are pooled.

| Event | Source | Finite train markers | Complete −0.4 to +1.0 s windows |
| --- | --- | ---: | ---: |
| target_on_time | photobox target presentation | 75 | 75 |
| go_cue_time | photobox go cue | 75 | 75 |
| move_onset_time | offline source algorithm | 75 | 75 |

Go-to-source-movement latency ranges 0.243–0.606 s (median 0.322 s).
Existing movement markers can be used without deriving onset again, but their
offline detection algorithm is not specified fully in this asset. The go cue is
the primary candidate because its photobox detection is documented; secondary
movement-marker alignment can describe timing sensitivity without treating the
marker as a verified hardware event.

## Supported scope and reliability screen

Peri-event averages and their trial-bootstrap uncertainty are feasible. A three-trial
minimum permits descriptive condition means for 21 conditions (63 trials), with
explicitly weak precision. Residuals can be calculated around condition- and
event-time-specific means, but correlation inference is not supported by 2–3 repeats.
A conservative 20-repetition screen is a declared triage rule, not a theorem of
statistical sufficiency; no condition passes it. Reliable covariance may need more
than that, depending on sparsity, effect size and population dimension.

Use [standard MC_Maze DANDI 000128](https://dandiarchive.org/dandiset/000128/0.220113.0400)
for a next feasibility audit, without assuming its repetitions or fields are sufficient.
No larger recording is downloaded by this mission. The
[official NLB documentation](https://neurallatents.github.io/datasets.html) describes
the delayed reaching task and published variants; event provenance and repetitions
above come from this actual NWB file.

## Training condition inventory

| Key (maze/type/version/active target) | Repetitions | Trial IDs |
| --- | ---: | --- |
| 10/8/0/0 | 2 | 11, 74 |
| 10/8/1/0 | 2 | 91, 93 |
| 10/8/2/1 | 2 | 6, 20 |
| 2/2/0/0 | 3 | 14, 62, 76 |
| 2/2/1/0 | 3 | 21, 64, 71 |
| 2/2/2/2 | 3 | 67, 69, 94 |
| 3/3/0/0 | 3 | 24, 50, 66 |
| 3/3/1/0 | 3 | 9, 13, 58 |
| 3/3/2/1 | 3 | 18, 39, 57 |
| 4/4/0/0 | 3 | 16, 43, 96 |
| 4/4/1/0 | 3 | 2, 31, 79 |
| 4/4/2/0 | 2 | 48, 63 |
| 7/6/0/0 | 3 | 22, 38, 61 |
| 7/6/1/0 | 3 | 32, 33, 92 |
| 7/6/2/2 | 3 | 35, 42, 45 |
| 75/10/0/0 | 2 | 49, 85 |
| 75/10/1/0 | 3 | 36, 46, 56 |
| 75/10/2/0 | 3 | 10, 15, 27 |
| 76/11/0/0 | 2 | 73, 99 |
| 76/11/1/0 | 3 | 30, 44, 59 |
| 76/11/2/1 | 3 | 72, 78, 88 |
| 77/12/0/0 | 3 | 1, 53, 90 |
| 77/12/1/0 | 3 | 23, 65, 87 |
| 77/12/2/2 | 3 | 77, 80, 89 |
| 8/7/0/0 | 3 | 7, 19, 82 |
| 8/7/1/0 | 3 | 17, 70, 84 |
| 8/7/2/0 | 3 | 4, 51, 75 |
