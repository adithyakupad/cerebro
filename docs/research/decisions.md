# Scientific decisions and access policies

- Preserve the human-selected go cue and20 ms bins. Scientific features follow
  PREDICT → LEARN → IMPLEMENT → INTERROGATE → VALIDATE; negative results remain.
- Maze decoding uses only107 held-in units and complete event windows. Source
  training75 is internally split60/15 before normalization or model selection.
  Source validation25 is exploratory evaluation; the separate test asset remains
  untouched. No final model is chosen by reported validation performance.
- PCA standardized-count reconstruction and FA Gaussian likelihood select separate
  dimensions. Neither identifies an intrinsic neuronal mechanism. Gaussian FA is
  a representation approximation to sparse counts, not a count likelihood model.
- Causal neural sequence means past/current bins at the bin-right time. Behavioral
  bin means and same-bin predictions are offline replay, not biological feedback.
- Kalman states are supervised behavior coordinates; latent AR(1) is one-step
  teacher-forced neural forecasting. They answer different questions.
- LINK counts are interpreted from the threshold-crossing description and integer
  values, preserving the contradictory native volts label. Native references
  exclude endpoint samples. Clocks and19–21 ms steps are preserved without a new
  regular time grid. Contacts are matched, not neurons.
- Longitudinal source selection never accesses target evaluation. Calibration
  prefixes are nested, but not necessarily condition balanced. All75 unlabeled
  calibration trials inform marginal normalization/target PCA. Smaller supervised
  budgets receive fewer labels; condition-anchor alignment additionally receives
  commanded-target metadata. Nonmonotonic curves are not repaired by test tuning.
- Two earlier LINK recordings pretrain the recurrent representation; a third
  session is reserved for calibration/evaluation. Three seeds and one-factor
  model/data/compute comparisons measure software sensitivity, not population
  replication. Source-session identity diagnostics use whole held-out trials.
- The human requires documented neural coverage for cross-subject modeling.
  Perich missing observation intervals remain unknown coverage and exclude those
  assets from modeling until authoritative coverage evidence is available.
  A continuous-acquisition assumption cannot substitute for that evidence.
  LINK has one subject; FALCON candidates require their own native coverage audit.
- The human owns interpretation, final model selection, physiological conclusions
  and the next hypothesis. Code automation does not approve research claims.
