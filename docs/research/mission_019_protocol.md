# Mission 019 frozen Brochier condition-classification protocol

Frozen before inspecting any classifier predictions or held-out scores. This is a two-animal, one-session-per-animal **instructed grip-by-load condition** case study. It is neither continuous movement decoding nor evidence of general subject invariance.

## Question and estimand

Does adding all labeled source-animal trials improve target-animal four-class balanced accuracy over a target-only linear classifier given the same five labeled target trials per class? The primary estimate is source-assisted minus target-only balanced accuracy on identical held-out target trials, reported separately for L→N and N→L. Equal-direction mean is descriptive. A nonpositive difference or confidence interval including zero does not support a transfer benefit.

## Immutable inputs and partitions

Use only the checksum-pinned native assets in `docs/datasets/mission_019_brochier_assets.json`: sorted NEV `l101210-001-02.nev` and `i140703-001-03.nev`, matching odML and 30 kHz NS5/NS6. Source single units are odML `OfflineSpikeSorting/SUAIDs`, excluding noise and MUA. Animal L and animal N are the biological source/target units, tested in both directions. Keep odML `PerformanceCode=255` trials with exactly one of `SGLF`, `SGHF`, `PGLF`, `PGHF`, a recorded GO-ON NEV event, and a fully sampled 280 ms post-go raw neural interval. If any class in either animal has fewer than six eligible trials, stop without modeling. Within each target animal, take the first five eligible trials *chronologically within each class* as calibration; every later eligible trial in that class is test. No test-trial information may fit preprocessing or choose settings. All eligible trials of the other animal are source training. Preserve source trial IDs, clocks and exclusion counts.

## Inputs, models and metrics

For each trial, count each selected unit's spikes in fourteen half-open 20 ms bins `[GO-ON, GO-ON+280 ms)`, using the native 30 kHz tick clock and no smoothing. Summarize each bin with the seven existing permutation-invariant `anonymous_features`; take the mean of each feature across the fourteen bins, giving seven features per trial. This intentionally discards unit identity and within-window timing. Do not equate neurons or electrode positions across animals.

Fit scikit-learn multinomial logistic regression with fixed `C=1`, L2 regularization, maximum 1000 iterations, deterministic class order, and feature standardization fitted only to each model's training rows. Compare: source-only zero-shot (all source trials), target-only (20 labeled target calibration trials), and source-assisted (all source plus the same 20 target trials). Include a majority-class prior baseline estimated on each method's allowed training data; report chance level 0.25. No hyperparameter or feature selection uses target test performance. Primary metric: four-class balanced accuracy on target test trials. Secondary: macro F1, per-class recall, confusion matrix, and ordinary accuracy.

Use 1000 fixed-seed stratified bootstrap resamples of target test trials for a conditional trial-level interval on the primary contrast. This does **not** quantify uncertainty over biological subjects; with two animals and one session each, subject and session effects are confounded. Show both directions separately and all negative results. No pooling of train/test trials or post-outcome protocol changes. If the linear fit fails, report the failure instead of silently changing the model. A strong score may reflect the instructed cue and task structure, not motor output or a transferable neural representation.

## Source-data gate established before this protocol

The full raw 30 kHz sampled streams were verified: L one block from 0 to 709.24797 s; N one block from 0.00273333 to 1003.21223 s. All 135 L and 142 N correct go windows are fully sampled and source GO-ON ticks match NEV. L has 41/30/31/33 and N 35/36/35/36 correct SGLF/SGHF/PGLF/PGHF trials. The native N odML says 161 total and 142 correct trials, while the primary paper's summary says 160/141; the discrepancy remains unresolved. Raw signal coverage is certified by sampled NSx blocks, not spike extrema. The root archive license says CC-BY-4.0, while a bundled dataset license contains CC-BY-SA-4.0 text; do not redistribute source assets while this conflict is unresolved.
