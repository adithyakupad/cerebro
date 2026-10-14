# Exploratory population and velocity benchmarks

MC_Maze Small | DANDI 000140 v0.220113.0408
asset 7821971e-c6a4-4568-8773-1bfa205c13f8 | 20 ms bins, 107 held-in units
75 source training / 25 source validation trials; offline exploratory evaluation

Hypothesis: neural observations may predict held-out-trial hand velocity better than training-only baselines. No architecture superiority was presumed.

Source trial identities are immutable in `split_manifest.json`. Inner training/validation are 60/15 trials; fitted preprocessing and selection exclude all 25 source validation trials. Final models refit on 75 training trials. Published benchmark test remains unacquired.

Counts tensor: 100 × 70 × 107; velocity: 100 × 70 × 2 in m/s. No missing-window exclusions. Standardization fits training only. Predictions use current and, for temporal models, past bins and become available at each bin right edge. No future smoothing or lag optimization. The go-time baseline also receives recorded event timing.

| Classical model | Velocity MSE (m²/s²) |
| --- | ---: |
| fa_ridge | 0.03734294 |
| go_time_template | 0.03748736 |
| kalman | 0.03131415 |
| linear | 0.03545681 |
| mean | 0.03832482 |
| pca_ridge | 0.03622569 |
| ridge | 0.03542144 |

| Sequence model | Mean across 3 seeds | Seed range |
| --- | ---: | --- |
| mlp | 0.03737999 | 0.03664760–0.03823750 |
| gru | 0.03667213 | 0.03649207–0.03684104 |
| lstm | 0.03663704 | 0.03659162–0.03672080 |
| temporal_cnn | 0.03105193 | 0.03056817–0.03178065 |
| transformer | 0.03594738 | 0.03531601–0.03628865 |
| state_space | 0.03458228 | 0.03408232–0.03493961 |

PCA selected 20 components by inner reconstruction loss; FA selected 5 by inner Gaussian likelihood. Reconstruction loss often prefers the largest candidate; this is not a claim of intrinsic neural dimensionality. The two family scores are not directly comparable.

Kalman uses supervised velocity state transitions within trials, regularized observation/process covariance, and independent initial priors per trial. Covariance floor is 1e-5 in corresponding squared units; transition stability is not enforced. The neural state-space baseline is a stable diagonal exponential recurrence with fixed 20 ms steps and learned input/output maps, not a Mamba or foundation model.

Deep models use a common Adam optimizer, full-trial batches, 20-epoch cap, inner-only epoch selection, and three seeds. Parameter counts differ. Saved checkpoints restore identical predictions including saved normalization. No GPU run was performed.

Whole-trial bootstrap assumes independent curated trials; seed spread describes initialization only. No significance or corrected multiple-model comparison is claimed. There is one subject/session, unequal conditions, no cross-session or cross-subject conclusion. Source validation has been viewed and is now exploratory, not a final untouched test. Latent ridge inherits the raw-ridge alpha rather than separate tuning.

All numerical results arise from the checksum-verified real NWB. Dataset: Churchland and Kaufman (2022), [DANDI 000140 v0.220113.0408](https://doi.org/10.48324/dandi.000140/0.220113.0408), CC-BY-4.0. Established [PCA](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html), [FA](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.FactorAnalysis.html), and [ridge](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Ridge.html) implementations are used.

Next experiment: establish a justified longitudinal feature policy and coverage assumption before interpreting adaptation; run fixed held-out protocols on standard Maze and compare temporal models under matched parameter/data/compute budgets.

## Figures

- [benchmark_errors.png](figures/benchmark_errors.png)
- [benchmark_dimensions.png](figures/benchmark_dimensions.png)
- [benchmark_geometry.png](figures/benchmark_geometry.png)
- [benchmark_predictions.png](figures/benchmark_predictions.png)
