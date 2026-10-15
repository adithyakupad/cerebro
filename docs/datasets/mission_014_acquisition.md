# Mission 014 additional recording audit

This records acquisition evidence collected on 2026-10-14, separately from model
results. Native files were inspected and their complete byte size and SHA256
matched published metadata. No challenge held-out or test asset was downloaded
for this audit. [The machine inventory](mission_014_inventory.json) preserves
exact paths, versions, UUIDs, checksums, metadata/download URLs and native fields.
These additional recordings are authentic observations, not synthetic fixtures.

## Six additional FALCON calibration sessions

[M1-A DANDI 000941 version 0.241029.1405](https://dandiarchive.org/dandiset/000941/0.241029.1405)
is an immutable published release;
[M1-B DANDI 001209 draft](https://dandiarchive.org/dandiset/001209/draft) remains
mutable. Both are CC-BY-4.0; attribute Adam G. Rouse and Marc H. Schieber;
Brianna Karpowicz is the release contact. Each asset below is **held-in-calib**.
All six contain 64 unit rows, 16 named EMG muscle series and acquisition groups
`eval_mask` and `preprocessed_emg`. None contains original raw EMG. Each channel
has one explicitly recorded `obs_intervals` entry, and all 64 channels in each
file agree on the listed interval. Bounds are relative to native session time.

| Animal/date | Asset UUID | Bytes | Trials | EMG samples | Recorded neural interval, s |
|---|---|---:|---:|---:|---|
| L / 2012-09-24 | 13163b3c-95b7-4b0e-8181-72d7bd658e0b | 73,077,382 | 414 | 182,498 | [0, 3649.953] |
| L / 2012-09-26 | 66b503dd-c311-42ce-983f-0810ed8c01ff | 80,268,327 | 409 | 172,325 | [0, 3446.498] |
| L / 2012-09-27 | 478c68a5-2434-428c-91f9-d678c8760dd6 | 78,481,526 | 376 | 177,606 | [0, 3552.117] |
| X / 2012-12-06 | 21ec556e-047d-4843-8316-a34967bc69fa | 59,352,818 | 395 | 180,444 | [0, 3608.867] |
| X / 2012-12-10 | 12b6eb45-0ade-4781-b812-85d46f63bd90 | 55,430,880 | 446 | 160,900 | [0, 3217.981] |
| X / 2012-12-12 | 36e04ea3-70d3-4b37-bd3e-a660425bc34e | 57,045,746 | 421 | 165,568 | [0, 3311.347] |

With the previously acquired L / 2012-09-28 and X / 2012-12-07 this provides eight
sessions from **two animals**. Release split pseudo-subjects and minival subsets
are not additional biological subjects or independent sessions. Recorded neural
intervals support complete-bin acquisition, not electrode quality or tracked
neurons. The six-file native audit did not calculate adapter complete-bin totals
or execute models. Later experiment evidence must be cited separately.

Additional sessions preserve the same preprocessing limitation:
[the detailed audit](falcon_preprocessing.md) establishes irreversible clipping,
global scalar quantiles across time and muscles, resampling and zero-phase
filtering before CEREBRO splits. They support a disclosed published-target
analysis; they do not supply raw targets or a training-only upstream pipeline.

## LINK 2020-02-05

[LINK DANDI 001201 version 0.251023.2336](https://dandiarchive.org/dandiset/001201/0.251023.2336)
contains 312 listed assets on 303 days for one monkey. Only four sessions
(Jan 27, Jan 30, Feb 4 and Feb 5, 2020) have been natively inspected here;
the remaining listed assets are discovered, not validated. Metadata spans 2020-01-27 through
2023-06-22; nine dates have two assets. The additional inspected session was
selected as the earliest date after the three previously acquired dates,
without selecting on decoding performance.

- Asset: `24b91bc3-92ba-457c-8718-490b508f6b8f`, path
  `sub-Monkey-N/sub-Monkey-N_ses-20200205_ecephys.nwb`.
- Size: 43,262,978 bytes; SHA256
  `a32df2043cf9d34a08bb1e0a43455049368fdb601d828930929c1b3d3dbcd0e5`.
- License: CC-BY-4.0; attribution Temmar and colleagues, LINK;
  [author documentation](https://chesteklab.github.io/LINK_dataset/).
- Subject: Monkey N; native identifier `2020-02-05_CO_nwb`; reference clock
  `2020-02-05T00:00:00+00:00`. Referenced absolute range is
  1580860807.476–1580861338.856 UNIX seconds.
- All 375 trials are CO, run ID 3; 188 central targets and 187 noncentral targets.
  Native threshold-crossing array shape is 26,571 × 96, integer values 0–9.
  Explicit nonoverlapping trial references retain 26,196 sampled rows;
  trial lengths are 43–208 rows (median 64), all at least 40 rows.
- Neural and behavioral reference slices and timestamps agree. Native clock
  steps are 19–21 ms (median 20 ms); keep these timestamps. Exactly 375 endpoint
  rows fall outside explicit references. `trial_count` is reference count + 1;
  use the reference counts rather than adding those endpoints.
- All 96 contact-coordinate keys match Jan 27, Jan 30 and Feb 4 exactly with
  identity column mappings. This is electrode-contact correspondence, not
  longitudinal neuron identity.
- Position is native normalized flexion (0 extension, 1 flexion); velocity is
  flexion units per time bin. ThresholdCrossings metadata says volts although
  the source description specifies −4.5 RMS crossings summed into 20 ms bins.
  Preserve the conflict and use the justified count interpretation. Finite
  values do not establish electrode quality; no explicit quality mask is present.

The [repository manifest](../../configs/link_20200205.json) pins acquisition.
This establishes **observed sampled neural coverage of referenced rows**, not
uninterrupted raw neural recording or per-unit spike observation intervals.
The author [pinned documentation](https://github.com/chesteklab/LINK_dataset/blob/5f9480831150d4877354e58668aa9c1cab04b637/docs/index.md)
and [loader](https://github.com/chesteklab/LINK_dataset/blob/5f9480831150d4877354e58668aa9c1cab04b637/utils/nwb_tools.py)
are at commit `5f9480831150d4877354e58668aa9c1cab04b637`; the separate 32 ms
processed-pickle format is not the native 20 ms NWB representation. Upstream
threshold/sensor calibration and curation precede CEREBRO splits; source-only
model normalization does not imply those acquisition calibrations were fitted
on CEREBRO training data. Raw voltage is unavailable for most released sessions.

## Coverage gate and scope

FALCON supplies explicit recorded per-channel observation intervals; LINK
supplies observed sampled counts through authoritative trial references.
Neither evidence type certifies signal quality or neuron identity. A behavioral
clock, trial duration, or first/last spike cannot substitute for neural coverage.
The inspected [Perich sessions](longitudinal_feasibility.md) have no recorded
`obs_intervals` and remain **audit-only** until authoritative neural coverage is
available. No additional model or preprocessing adapter was introduced by this
inventory, and no experiment was rerun to create these documents.
