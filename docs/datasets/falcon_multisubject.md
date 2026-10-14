# FALCON multisubject acquisition and documented coverage

## Authentic public calibration assets

Two independently checksum-verified, public **held-in-calib** recordings were
acquired. No held-out challenge or test assets were downloaded. Exact metadata,
sizes, SHA256, attribution and URLs are pinned in `configs/falcon_m1_a.json`
and `configs/falcon_m1_b.json`. Raw files are Git ignored.

| Field | M1-A, Monkey L | M1-B, Monkey X |
|---|---|---|
| DANDI / version | 000941 / 0.241029.1405 | 001209 / draft |
| Session date | 2012-09-28 | 2012-12-07 |
| Asset UUID | 61dbe78b-58da-4089-b308-96378c5a95b9 | 4c3140ea-abe6-4c3c-a2ea-1025e5bef288 |
| Bytes | 68,337,100 | 52,469,272 |
| Multiunit channels | 64 | 64 |
| Rewarded trials | 412 | 429 |
| Native EMG samples | 160,436 × 16 | 157,134 × 16 |
| Recorded neural observation interval, s | [0, 3208.705] | [0, 3142.676] |
| Complete trial-local 20 ms bins | 54,633 | 58,552 |
| Spikes retained in those bins | 1,216,399 | 569,581 |

Both datasets are CC-BY-4.0. Attribute Adam G. Rouse and Marc H. Schieber
(M1-A authors; M1-B data collectors), and Brianna Karpowicz as the M1-B contact.
[Published M1-A release](https://dandiarchive.org/dandiset/000941/0.241029.1405),
[M1-B draft](https://dandiarchive.org/dandiset/001209/draft), and
[official FALCON task documentation](https://snel-repo.github.io/falcon/datasets.html).
M1-B has no immutable published release at acquisition: UUID, size and SHA256
pin the acquired bytes, while the draft metadata remains mutable. This limitation
must accompany reproduction claims.

## Coverage and identity

Unlike the inspected Perich recordings, both native NWB unit tables explicitly
contain `obs_intervals`. All 64 channels share the respective interval shown
above. The [official converter](https://github.com/snel-repo/falcon-challenge/blob/770c9b9597b8f58bf67b5a9ec6401ef705a2cb0f/preproc/m1_reachgrasp_preprocv2.py#L481)
writes source cutoff intervals for each channel, including empty spike lists.
CEREBRO reads these recorded intervals; it does not infer coverage from behavior,
spike extrema or source trial bounds. Every retained neural bin is completely
covered by every channel's recorded observation interval. Recorded coverage
still does not independently establish electrode quality.

Native spike vectors are unordered for 33 A channels and 15 B channels. The
adapter explicitly stable-sorts derived copies for counting, preserving every
timestamp and duplicate; source files remain unchanged. The reordered channel
IDs are reported. No reason for source ordering is assumed. Each feature is a
source channel/multiunit population, not a persistent identified neuron. Use
`(source_identifier, unit_id)` keys and do not map neural rows between animals.

Both source `session_id` fields are absent; use native identifiers
`L_20120928_held_in_calib` and `X_20121207_held_in_calib`. Subject labels include
the release split (`MonkeyL_held_in_calib`, `MonkeyX_held_in_calib`); they identify
two animals, not separate subjects for every dataset split.

## Targets, source preprocessing and masks

The recordings share these exact muscle names: APL, BCPs, DLTa, DLTp, ECRB,
ECU, EDC, FCR, FCU, FDI, FDPr, FDPu, Hypoth, PECmaj, TCPlat and Thenar.
Names provide shared output coordinates; they do not prove equal sensor gain or
absolute activation calibration between subjects. The adapter sorts names
explicitly and retains each source unit label and conversion.

Native series say **mV**, conversion 1 and offset 0, but the official converter
clips rectified EMG at the 99th percentile and scales by the 95th percentile
before storing `preprocessed_emg`. Its filters and resampling also precede
CEREBRO splits. Therefore interpret targets as **published quantile-normalized
preprocessed EMG native values**, not calibrated physical mV or physiological
force. Source normalization uses the releasing authors' input data; CEREBRO
cannot undo it or claim that all upstream transformations were training-only.
[Converter preprocessing, lines 298–337](https://github.com/snel-repo/falcon-challenge/blob/770c9b9597b8f58bf67b5a9ec6401ef705a2cb0f/preproc/m1_reachgrasp_preprocv2.py#L298).

All 16 muscles and Boolean `eval_mask` share exact source timestamps at 20 ms
intervals. All target values are finite. Mask description says to keep these
samples for training/evaluation; the converter builds it from trial windows.
It is a **within-trial keep mask**, not a held-out split or quality mask.
All retained complete trial bins have this mask true. Trials carry start/stop,
go cue, movement onset, contact, reward, outcome, source number and object/
location/condition metadata. All acquired trials are rewarded.

## Adapter protocol and limits

`cerebro.falcon.load_falcon(manifest)` returns original trial identities,
native EMG samples, source masks and 64-channel counts in full half-open
`[native_timestamp, native_timestamp + 20 ms)` windows within each trial.
Original sample timestamps are unchanged; only derived right edges are rounded
to picosecond precision. No interpolation, cross-trial pooling or extrapolation
is used. This is an explicit **offline same-bin** alignment convention, not a
claim about causal prediction or exact raw EMG bin phase. Unsupported bin widths
and non-calibration source splits are rejected.

This pair provides documented-coverage intracortical recordings from two
subjects performing the same reach-to-grasp task, with compatible named EMG
outputs. It supports a separate disclosed cross-subject baseline experiment,
not pooling with Maze velocity or LINK finger targets. Different neurons and
contacts require a model strategy that does not assume neural row identity.
The two subjects alone cannot establish broad population generalization.
Challenge performance cannot be claimed from this calibration-only experiment.

Reproduce acquisition:

```bash
python -m cerebro.dataset configs/falcon_m1_a.json
python -m cerebro.dataset configs/falcon_m1_b.json
python -m pytest tests/test_falcon.py
```

The native audit is `reports/falcon_native_audit.json`; it preserves the exact
manifests, recorded intervals, target names, source preprocessing limitations,
per-trial sample counts and adapter source hash.
