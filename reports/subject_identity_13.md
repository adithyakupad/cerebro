# Anonymous-feature subject-discriminability diagnostic

MonkeyL_held_in_calib versus MonkeyX_held_in_calib, using authentic public FALCON calibration recordings.

Fixed logistic regression (C1, balanced class weights) receives one mean anonymous-moment vector per eligible trial. No explicit subject, session, timestamp, or trial identifier is a predictor.

Fit trial counts: [300, 75]; evaluation trial counts: [112, 354].

Observed balanced accuracy: **100.00%**, versus balanced chance **50%**. Per-subject accuracy: [100.0, 100.0]%.

Confusion matrix, true subject rows and predicted subject columns ordered source/target: `[[112, 0], [0, 354]]`.

Above-chance subject classification indicates subject-correlated information remains in anonymous features. This does not identify its physiological cause or establish subject-independent representations.

The diagnostic uses the complete75-trial target calibration feature pool in addition to source300 training trial rows. Its scaler also fits both pools. This access is separate from the5/15/75-label decoder experiments; diagnostic outputs never choose decoder models or preprocessing.

## Limitations

- A fixed supervised subject-discriminability probe, not evidence of biological subject recognition
- Fixed protocol added after observing the cross-subject benchmark; it was not preregistered before data inspection
- One recording per subject confounds subject with session/date/task-distribution and recording differences
- Above-chance balanced accuracy indicates retained subject-correlated information, not an identity-free representation
- Per-trial mean features use the entire eligible trial offline; this diagnostic is not an online classifier
- Balanced class weights compensate the unequal training trial counts; balanced evaluation chance is50%, while raw accuracy has unequal evaluation class priors
- Trial independence and confidence/significance are not established; reported accuracy is descriptive
- Shared cross12 mask eligibility includes native source masks/coverage and finite author-preprocessed EMG; no EMG amplitudes are predictor inputs

Checkpoints and predictions are Git-ignored under `data/processed/subject_identity_13/`; numeric parameters were restored with identical predictions. Frozen cross12 split/report digests, exact asset checksums, code revision, environment versions, and output hashes are recorded in JSON.

Reproduce: `python -m cerebro.subject_identity --config configs/subject_identity_13.json --output data/processed/subject_identity_13`.
