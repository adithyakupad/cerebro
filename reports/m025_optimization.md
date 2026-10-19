# M025: a controlled optimization-budget study

**PRACTICAL_IMPROVEMENT_IN_ONE_ADDITIONAL_SESSION**. The architecture, training loss, optimizer and seeds were held fixed. Historical results remain unchanged.

## Abstract

We tested whether optimization budget limits an existing causal temporal CNN on authentic intracortical MC_Maze recordings. A fixed 20-versus-200-update protocol used training-only preprocessing, physical-MSE epoch selection, three seeds and matched classical controls. The development promotion reduction was 18.60%. In one separately recorded session of the same animal, CNN200 achieved 0.01279167 (m/s)², 51.92% lower than CNN20 and 57.66% lower than Kalman. Paired trial and ordered-block uncertainty are reported without treating seeds as biological replicates. These are offline same-bin reconstruction results from session-specific fits, not decoder transfer, new-subject generalization or physiological mechanism identification.

## Design and lineage

Diagnostic commit 35e8dd9; frozen protocol 7f756c2; shape guard ce588f5; reviewed implementation 477ed95; validation-only recovery 8d459de.
Primary comparison: maximum 20 versus 200 full-batch Adam updates, physical-MSE inner epoch selection, three seeds. Mean seed losses within trial; no best-seed selection.
Development: original Small: 75 training / 25 already-inspected validation trials, inner 60/15. Promotion uses the same inner trials as epoch selection, so it is selection-conditioned.
Standard: original source train/val and new internal split, separately fitted 137-unit model. Historical raw eager loading is disclosed; there was no documented decoder scoring or selection on its 574 validation trials.
No unit correspondence or trained-decoder transfer across dates is assumed. One animal and one additional recording cannot establish population-wide/session-invariant performance.

## Measured outcomes


| Stage | CNN20 | CNN200 | Kalman | History ridge | MSE units |
| --- | ---: | ---: | ---: | ---: | --- |
| Small development (previously inspected) | 0.0328837984 | 0.0256874678 | 0.0332080717 | 0.0295760255 | (m/s)² |

### Small development (previously inspected)

Full counts/targets: [100, 70, 107] / [100, 70, 2]; exclusions 0.
Within each session, both caps have the same input units and identical hidden size 32, two width-3 convolutions and 2-coordinate readout. Across sessions the input-layer size follows the separately observed unit count; no shared-neuron identity is inferred.
Within-stage inner selected loss by cap (only Small defines the promotion gate): {'20': 0.03427131259755268, '200': 0.027896443593456926}.
Selected epochs: [(20, 0, 20), (200, 0, 78), (20, 1, 20), (200, 1, 48), (20, 2, 20), (200, 2, 52)].
Seed-specific evaluation MSE: {'cnn_20_seed_0': 0.032634002737669185, 'cnn_200_seed_0': 0.024987687944758728, 'cnn_20_seed_1': 0.03235572449624626, 'cnn_200_seed_1': 0.026426693023125423, 'cnn_20_seed_2': 0.03366166800273662, 'cnn_200_seed_2': 0.025648022297745657}.
Seconds total: 22.22025658399798; per-epoch, refit and forward costs are in the machine stage report.

| CNN200 relative to | Absolute MSE difference | Relative reduction | Paired 95% trial CI | Ordered-block-five CI |
| --- | ---: | ---: | --- | --- |
| cnn20 | -0.0071963307 | 21.884% | [-0.010004347810910457, -0.004288344354983725] | [-0.009939018985575924, -0.002972297272789758] |
| kalman | -0.0075206040 | 22.647% | [-0.011136746788340254, -0.0039426389539673696] | [-0.010800400536259034, -0.004309958179834813] |
| history_ridge | -0.0038885578 | 13.148% | [-0.00549905306241724, -0.0021211024976800666] | [-0.005167237555810476, -0.002224739129422204] |

Authorized mean / event-template / instantaneous-ridge MSE: [0.040644623592904744, 0.039758814306538624, 0.037500450030202165].

| Fixed inference sensitivity | CNN20 | CNN200 | Kalman | History ridge |
| --- | ---: | ---: | ---: | ---: |
| training_mean_feature_replacement | 0.0334066170 | 0.0256927952 | 0.0332785774 | 0.0297078100 |
| within_condition_trial_permutation | 0.0328837984 | 0.0256874678 | 0.0332080717 | 0.0295760255 |

Condition-permutation null: 0 changed / 25 evaluation trials; 25 singleton trials.
**NOT INFORMATIVE**: no trials change; singleton labels do not provide an effective neural null.
Mean/template, train-mean feature replacement, every seed, coordinate R² and all 70-bin sensitivities remain in the stage report. No sensitivity selected a new primary model.

| Stage | CNN20 | CNN200 | Kalman | History ridge | MSE units |
| --- | ---: | ---: | ---: | ---: | --- |
| Standard session (previously performance-unscored) | 0.0266053581 | 0.0127916679 | 0.0302108898 | 0.0220675991 | (m/s)² |

### Standard session (previously performance-unscored)

Full counts/targets: [2295, 70, 137] / [2295, 70, 2]; exclusions 0.
Within each session, both caps have the same input units and identical hidden size 32, two width-3 convolutions and 2-coordinate readout. Across sessions the input-layer size follows the separately observed unit count; no shared-neuron identity is inferred.
Within-stage inner selected loss by cap (only Small defines the promotion gate): {'20': 0.026644023512080728, '200': 0.012946127148579916}.
Selected epochs: [(20, 0, 20), (200, 0, 174), (20, 1, 20), (200, 1, 187), (20, 2, 20), (200, 2, 174)].
Seed-specific evaluation MSE: {'cnn_20_seed_0': 0.026289050628017514, 'cnn_200_seed_0': 0.012820015942213199, 'cnn_20_seed_1': 0.025826950903091932, 'cnn_200_seed_1': 0.012828942228901158, 'cnn_20_seed_2': 0.027700072896067313, 'cnn_200_seed_2': 0.012726045672807853}.
Seconds total: 1549.480882333126; per-epoch, refit and forward costs are in the machine stage report.

| CNN200 relative to | Absolute MSE difference | Relative reduction | Paired 95% trial CI | Ordered-block-five CI |
| --- | ---: | ---: | --- | --- |
| cnn20 | -0.0138136902 | 51.921% | [-0.014491534902654701, -0.013133823708440066] | [-0.014457172662402753, -0.013175898434880142] |
| kalman | -0.0174192219 | 57.659% | [-0.018188200944704122, -0.016680848015545254] | [-0.01809782902640276, -0.01674710977883639] |
| history_ridge | -0.0092759312 | 42.034% | [-0.009745912019416684, -0.00882266016457585] | [-0.009722460746356697, -0.00883748668097109] |

Authorized mean / event-template / instantaneous-ridge MSE: [0.03897894495133024, 0.03824114746265374, 0.03279813447057358].

| Fixed inference sensitivity | CNN20 | CNN200 | Kalman | History ridge |
| --- | ---: | ---: | ---: | ---: |
| training_mean_feature_replacement | 0.0270317643 | 0.0135726642 | 0.0295702339 | 0.0225504649 |
| within_condition_trial_permutation | 0.0304296013 | 0.0261724034 | 0.0344337039 | 0.0296090138 |

Condition-permutation null: 445 changed / 574 evaluation trials; 0 singleton trials.
The partial condition permutation retains task phase and condition structure, including unchanged fixed points; interpret it descriptively.
Mean/template, train-mean feature replacement, every seed, coordinate R² and all 70-bin sensitivities remain in the stage report. No sensitivity selected a new primary model.

## Interpretation and limitations

The frozen contrasts support a practical improvement in the optimization-and-epoch-selection recipe on this additional recording; this does not identify a physiological mechanism. A longer-cap selected epoch is not itself evidence of undertraining. The intervention expands both optimizer updates and available epoch-selection candidates; it does not isolate their effects under a fixed selected epoch.
The CNN training loss and Kalman fitting use all 70 training bins; ridge controls fit bins 5–70 because complete five-bin histories start there. All selection/primary evaluation masks match, but training target masks across families do not. The CNN20-versus200 intervention itself holds this constant.
Task clock and strong velocity autocorrelation remain competing explanations for predictable structure. History-ridge tests linear temporal integration; an ineffective condition permutation cannot rule out task-phase explanations. Other neural architectures were not retuned, so this is not a new ranking across CNN, GRU/LSTM and Transformer families.
No neural–behavior lag was optimized. Native distributed velocity targets and their physical conversion were used as supplied; upstream velocity estimation was not independently reconstructed. Current/past counts reconstruct same-bin mean velocity at bin right, not future forecasting or online control. Original interleaved source partitions are offline held-out trials, not chronological deployment. Different alignment, lag and endpoint conventions mean these are not NLB leaderboard scores.
Causality is within extracted sequences. Pre-cue windows and sequence reset are indexed offline using the recorded later go cue; the task-phase control receives that clock. Prefix tests do not demonstrate prospective event detection or live initialization.
Uncertainty conditions on fixed model fits and trials from one session. Seed spread is optimization variation; no bootstrap sample is another animal. Ordered blocks are a sensitivity, not a guarantee of independence.
The known nondefault permuted-risk alpha defect is unrelated and remains unfixed. Shape mismatch rejection was isolated and tested without changing valid-shape updates or RNG state.

## Compute interpretation

Total stage wall time includes recording preparation. A source audit found repeated full-recording timestamp/spike validation and full physical-velocity conversion inside the per-trial preparation loop. For 6,809,920 two-coordinate samples over 2,295 trials, conversion alone implies roughly 500 GB cumulative intermediate writes; this is an analytical workload estimate, not measured bandwidth or resident memory. Native metadata also give 2,295 observation intervals per unit: the reference coverage loop entails 137×2,295×2,295 ≈ 722 million Python interval iterations. Preparation was not separately profiled and was not optimized during this frozen study.
Per-epoch, refit and batch-forward costs are recorded separately. For recovered seed0 checkpoints, fit_seconds=0 means no additional refit in the continuation, not free original training. The failed-attempt duration is preserved separately in the recovery manifest; add it when discussing total study compute. These are CPU offline costs, not streaming or hardware latency; GPU performance and clinical/live BCI operation were not tested.

## Disclosed pre-scoring recovery

The first standard attempt stopped in a float32 cross-length verification check after saving seed0 models, before any final metric was calculated. Synthetic independent diagnosis reproduced discrepancies consistent with floating-point roundoff. The reviewed correction uses a double-precision validation copy at 1e-12 and records production float32 discrepancies; production weights, dtype and forward procedure are unchanged. Initial forward arrays had not been saved, so a bitwise comparison against those lost arrays is unavailable; preserved checkpoint bytes and exact completed-run restoration provide the direct evidence. This is structural/mathematical causality, not bitwise future invariance of float32 convolution.
The [official PyTorch numerical-accuracy notes](https://docs.pytorch.org/docs/main/notes/numerical_accuracy.html) explain why mathematically equivalent batched/sliced floating-point computations need not match bitwise. Our synthetic measurements provide the case-specific evidence; no particular backend algorithm was forensically identified.
The original marker and seed0 checkpoints are preserved. Exact old/new source hashes and protected artifact hashes are bound in docs/research/m025_recovery.json. This explicit continuation reuses saved source-trained models, reconstructs only source inner curves, and never changes the frozen 5% gates or consumes partial final errors to choose a method. Recovery is part of the disclosed evaluation occasion, not an additional independent replication.

## Verification and reproduction

289 software tests and 22 authentic-data tests passed (311 total); 20 existing HDMF deprecation warnings in the data suite. 31 focused pre-training tests also passed and overlap these counts.
All three CNN20 development prediction arrays exactly match sequence06 historical predictions. Model replay verifies numerical checkpoint restoration and saved array/file digests.
`conda run -n cerebro python -m cerebro.optimization_study --stage development --replay`
`conda run -n cerebro python -m cerebro.optimization_study --stage final --replay` (only if executed)
`conda run -n cerebro python tools/m025_report.py` regenerates this synthesis and comparison figure without fitting.
Training commands are identical without --replay; existing stage results refuse overwriting. Final access additionally requires committed passing development/eligibility evidence, unchanged source/protocol hashes and an exclusive final-start marker. Never delete that marker to repeat a final evaluation.
Pinned CC-BY-4.0 DANDI sources: [Small](https://doi.org/10.48324/dandi.000140/0.220113.0408), [standard](https://doi.org/10.48324/dandi.000128/0.220113.0400), Churchland and Kaufman (2022). Exact native assets/checksums, units and session clocks are in the stage reports and eligibility audit. Raw data and checkpoints are excluded from Git.

## Application evidence and next decision

Defensible contribution: a prospectively frozen optimization-budget comparison with matched histories, independent classical tuning, separate target-shape regression protection, numerical replay and explicitly qualified session replication. Claim only the measured gates reported above.
Earlier LINK adaptation/reliability negative findings are unchanged and concern different normalized finger-position targets. This study does not establish successful calibration-efficient adaptation. Researcher selected and authorized the design; agents assisted implementation and review. This artifact does not establish independent human reconstruction of every implementation, hiring suitability, physiological neural drift, general subject invariance or foundation-model validity.
Next decision: review the result and uncertainty before proposing any new recording cohort or change of prediction horizon. Do not reuse the scored standard validation outcomes for another supposedly confirmatory tuning cycle.

## Interview defense questions

1. Why can a 200-epoch cap select fewer than 200 epochs, and why is a selected last epoch not proof of undertraining?
2. How does standardized-coordinate training loss differ from physical velocity MSE, and where are both scalers fitted?
3. Why do five-bin history ridge and CNN have matched information, while Kalman receives a different recursive prior?
4. Why are seeds/bins not independent biological units, and what uncertainty is missing from fixed-model trial bootstrap?
5. What is left unproven by a gain on one separately fitted session, especially when raw data were previously opened and task conditions repeat?
6. How can mathematical causality coexist with tiny float32 prefix discrepancies, and what exactly does the double-precision verification establish?
