# FALCON M1 source preprocessing audit

Mission 014 inspected the official converter at commit
`770c9b9597b8f58bf67b5a9ec6401ef705a2cb0f` and eight public held-in calibration
NWB recordings from monkeys L and X. The files expose published preprocessed
EMG, not original unnormalized EMG. None of the six additional recordings has a
raw-EMG acquisition or intermediate preprocessing series. Their exact identities
and recorded neural coverage are in [the acquisition audit](mission_014_acquisition.md)
and [the machine inventory](mission_014_inventory.json).

## Authoritative transformation

The pinned [converter](https://github.com/snel-repo/falcon-challenge/blob/770c9b9597b8f58bf67b5a9ec6401ef705a2cb0f/preproc/m1_reachgrasp_preprocv2.py#L63)
reads `{MONKEY}{EXP_DATE}_AD_Unrect_EMG.mat` and
`unsorted_unit/{MONKEY}_*_{EXP_DATE}-data.mat` from a local laboratory directory
(lines 46–71). `EMGRawData`, `EMGSettings.ChanNames`, `samp_rate` and
`analog_start_time` supply values, muscle names, sample rate and clock offset
(lines 103–114). These paths are not public download URLs. Raw NWB acquisition
creation is commented out (lines 256–259), as is storage of the intermediate
signals (lines 326–340).

[Preprocessing lines 270–324](https://github.com/snel-repo/falcon-challenge/blob/770c9b9597b8f58bf67b5a9ec6401ef705a2cb0f/preproc/m1_reachgrasp_preprocv2.py#L270)
apply notch filters at 60, 180, 200, 300 and 400 Hz, each with 2 Hz bandwidth;
a 65 Hz high pass; absolute-value rectification; clipping at quantile 0.99;
scaling by quantile 0.95 of the clipped values; resampling to 50 Hz;
rectification again; and a 10 Hz low pass. The
[pinned filtering implementation](https://github.com/snel-repo/falcon-challenge/blob/770c9b9597b8f58bf67b5a9ec6401ef705a2cb0f/preproc/filtering.py#L62)
uses zero-phase `scipy.signal.filtfilt` along time and fourth-order Butterworth
filters. Notch quality factors equal center frequency divided by bandwidth.

Crucially, [lines 111–121](https://github.com/snel-repo/falcon-challenge/blob/770c9b9597b8f58bf67b5a9ec6401ef705a2cb0f/preproc/filtering.py#L111)
call `np.quantile(np.abs(x), q)` **without an axis**: each quantile is one global
scalar across all time samples **and all muscles**, not a separate value per
muscle. Numeric clipping/scaling values are not saved in the inspected NWBs.
[The resampler](https://github.com/snel-repo/falcon-challenge/blob/770c9b9597b8f58bf67b5a9ec6401ef705a2cb0f/preproc/filtering.py#L241)
calls `scipy.signal.resample_poly` with integer target/source rates; its stale
Chebyshev/order-500 docstring does not describe parameters supplied by the code.
Output is stored with an mV label despite quantile scaling; retain the native
metadata but interpret values as published normalized EMG, not calibrated
absolute muscle activation.

## Reconstruction and split limits

Clipping and rectification are many-to-one transformations, and downsampling
removes detail. Even known quantile scalars could not recover clipped peaks or
raw polarity; the published series cannot be inverted to original raw EMG.
Training-only rescaling of published values does not undo these upstream steps.
The converter processes the held-in calibration raw prefix as a whole before
CEREBRO's later trial splits; zero-phase filters can mix samples across those
later boundaries. This prevents a claim that the complete target pipeline was
fitted or applied independently within CEREBRO training data.

No authoritative public download for the named source MAT files was located in
the inspected releases, official documentation or linked original study. This
is an availability finding, not proof that no external copy exists. The
[original study](https://pmc.ncbi.nlm.nih.gov/articles/PMC6361546/) directs resource
requests to the lead contact; its key-resources table references the
[earlier neuronal-recordings paper](https://doi.org/10.1523/JNEUROSCI.1716-16.2016)
rather than a raw-data archive. No contact message was sent.

Reconstructing comparable targets requires owner-provided EMG/spike MAT files,
checksums, access terms, units, sample rates, clock offsets and neural coverage
provenance. Exact reproduction additionally needs environment versions and any
B-specific converter configuration: the pinned script's date lists explicitly
cover L, so its existence alone does not establish every B conversion parameter.
A researcher must select target definition, quantile scope, split boundaries and
filtering conventions before a new raw-data experiment. Fit quantiles only on
training samples and freeze them; use split-aware filtering or justified temporal
guards for bidirectional filters and resampling. Preserve source clock mappings.

Neural coverage is a separate requirement. The converter
[writes source cutoffs into every unit's `obs_intervals`](https://github.com/snel-repo/falcon-challenge/blob/770c9b9597b8f58bf67b5a9ec6401ef705a2cb0f/preproc/m1_reachgrasp_preprocv2.py#L481),
including units with empty spike vectors. Retain only complete neural bins within
every required recorded interval. EMG timestamps, trial bounds and spike extrema
do not establish neural coverage, nor do recorded intervals establish electrode
quality or persistent neuron identity.
