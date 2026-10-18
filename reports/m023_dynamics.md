# M023 observed population dynamics

Development study: one macaque, one source session and three previously inspected target sessions. Jan27 first300 trials train source models; Jan30/Feb4/Feb5 first45 trials supply local models, and next30 trials per date are development evaluation. Original rows75:375 are excluded. This is not independent final validation.

## Primary temporal comparison

Fixed source-trained PCA6 plus ridge AR1, one native sample ahead. Neural errors are source-standardized threshold-crossing count², averaged equally over trials. Intervals resample contiguous five-trial blocks within dates; dates are not animals. Static PCA/FA inference and behavior probes are offline; AR forecasts propagate from past neural observations.

| Control | Equal-date relative improvement | Paired MSE difference | Conditional 95% interval | Gate |
|---|---:|---:|---|---|
| neural_persistence | 42.364% | -1.079553 | [-1.133521, -1.031258] | PASS |
| training_mean | 3.594% | -0.058542 | [-0.069887, -0.045812] | FAIL |
| permuted_training_ar | 2.398% | -0.038528 | [-0.045734, -0.030474] | FAIL |

**The fixed temporal promotion gate failed.** Source PCA6 AR1 improves beyond a training mean and shuffled-training AR, but not by the prespecified 5% against both controls. No untouched-session temporal outcomes were evaluated. Beating neural persistence is insufficient: persistence carries preceding-bin observation noise, whereas low-rank predictions remove substantial observation variation.

## Complete prespecified ablations

PCA/FA dimensions3/6/12; source, local15/local45 models; dimension6 local-scaler sensitivity. AR ridge1, behavior ridge1000. Local training uses target pool rows only. No family or dimension is promoted retrospectively. The full machine report contains per-trial losses, all controls, likelihoods and conditional intervals.

| Date | Observation model | d | Fit | Reconstruction neural MSE | h1 neural MSE | h5 neural MSE | Offline behavior MSE flexion² |
|---|---|---:|---|---:|---:|---:|---:|
| 2020-01-30_CO_nwb | pca | 3 | source | 1.122384 | 1.196196 | 1.181257 | 0.030032 |
| 2020-01-30_CO_nwb | pca | 3 | local_15 | 0.980396 | 1.157713 | 1.144803 | 0.035888 |
| 2020-01-30_CO_nwb | pca | 3 | local_45 | 0.971043 | 1.151348 | 1.140021 | 0.031389 |
| 2020-01-30_CO_nwb | pca | 6 | source | 1.035454 | 1.176594 | 1.180799 | 0.028973 |
| 2020-01-30_CO_nwb | pca | 6 | local_15 | 0.893070 | 1.146308 | 1.142417 | 0.035620 |
| 2020-01-30_CO_nwb | pca | 6 | local_45 | 0.883099 | 1.140185 | 1.137209 | 0.031370 |
| 2020-01-30_CO_nwb | pca | 6 | local_45_pool_scaler | 0.985556 | 1.134151 | 1.135880 | 0.031204 |
| 2020-01-30_CO_nwb | pca | 12 | source | 0.958126 | 1.176498 | 1.180755 | 0.028749 |
| 2020-01-30_CO_nwb | pca | 12 | local_15 | 0.781853 | 1.146983 | 1.142162 | 0.036307 |
| 2020-01-30_CO_nwb | pca | 12 | local_45 | 0.762678 | 1.136848 | 1.136539 | 0.031392 |
| 2020-01-30_CO_nwb | fa | 3 | source | 1.132052 | 1.198342 | 1.181978 | 0.030036 |
| 2020-01-30_CO_nwb | fa | 3 | local_15 | 1.082877 | 1.148271 | 1.142332 | 0.035862 |
| 2020-01-30_CO_nwb | fa | 3 | local_45 | 1.008791 | 1.139840 | 1.136968 | 0.031380 |
| 2020-01-30_CO_nwb | fa | 6 | source | 1.096795 | 1.191610 | 1.181774 | 0.028968 |
| 2020-01-30_CO_nwb | fa | 6 | local_15 | 0.937974 | 1.147654 | 1.142061 | 0.035530 |
| 2020-01-30_CO_nwb | fa | 6 | local_45 | 0.914645 | 1.140982 | 1.136767 | 0.031259 |
| 2020-01-30_CO_nwb | fa | 6 | local_45_pool_scaler | 1.017819 | 1.136497 | 1.136589 | 0.031510 |
| 2020-01-30_CO_nwb | fa | 12 | source | 1.075744 | 1.189778 | 1.181678 | 0.029113 |
| 2020-01-30_CO_nwb | fa | 12 | local_15 | 0.855425 | 1.146946 | 1.142078 | 0.035085 |
| 2020-01-30_CO_nwb | fa | 12 | local_45 | 0.850693 | 1.138990 | 1.136687 | 0.030959 |
| 2020-02-04_CO_nwb | pca | 3 | source | 1.340808 | 1.534582 | 1.574447 | 0.028868 |
| 2020-02-04_CO_nwb | pca | 3 | local_15 | 1.169527 | 1.436013 | 1.500086 | 0.031124 |
| 2020-02-04_CO_nwb | pca | 3 | local_45 | 1.150487 | 1.432201 | 1.497111 | 0.028640 |
| 2020-02-04_CO_nwb | pca | 6 | source | 1.245778 | 1.510297 | 1.573923 | 0.028401 |
| 2020-02-04_CO_nwb | pca | 6 | local_15 | 1.056244 | 1.434354 | 1.497283 | 0.031319 |
| 2020-02-04_CO_nwb | pca | 6 | local_45 | 1.033150 | 1.427675 | 1.492564 | 0.028639 |
| 2020-02-04_CO_nwb | pca | 6 | local_45_pool_scaler | 1.151279 | 1.422882 | 1.490075 | 0.028556 |
| 2020-02-04_CO_nwb | pca | 12 | source | 1.154321 | 1.510715 | 1.573810 | 0.028299 |
| 2020-02-04_CO_nwb | pca | 12 | local_15 | 0.912773 | 1.433861 | 1.493845 | 0.031334 |
| 2020-02-04_CO_nwb | pca | 12 | local_45 | 0.862484 | 1.423349 | 1.489264 | 0.028671 |
| 2020-02-04_CO_nwb | fa | 3 | source | 1.355578 | 1.536196 | 1.575103 | 0.028815 |
| 2020-02-04_CO_nwb | fa | 3 | local_15 | 1.164070 | 1.436016 | 1.500924 | 0.030154 |
| 2020-02-04_CO_nwb | fa | 3 | local_45 | 1.221365 | 1.432827 | 1.492108 | 0.029033 |
| 2020-02-04_CO_nwb | fa | 6 | source | 1.323707 | 1.529959 | 1.574957 | 0.028279 |
| 2020-02-04_CO_nwb | fa | 6 | local_15 | 1.068209 | 1.435212 | 1.499365 | 0.030123 |
| 2020-02-04_CO_nwb | fa | 6 | local_45 | 1.018889 | 1.431148 | 1.497383 | 0.028557 |
| 2020-02-04_CO_nwb | fa | 6 | local_45_pool_scaler | 1.177102 | 1.426840 | 1.491235 | 0.028602 |
| 2020-02-04_CO_nwb | fa | 12 | source | 1.296246 | 1.526114 | 1.574863 | 0.028116 |
| 2020-02-04_CO_nwb | fa | 12 | local_15 | 0.976875 | 1.435083 | 1.495709 | 0.029954 |
| 2020-02-04_CO_nwb | fa | 12 | local_45 | 0.922659 | 1.424022 | 1.489708 | 0.028288 |
| 2020-02-05_CO_nwb | pca | 3 | source | 1.772913 | 1.852373 | 1.903348 | 0.027942 |
| 2020-02-05_CO_nwb | pca | 3 | local_15 | 1.190415 | 1.566056 | 1.704697 | 0.027483 |
| 2020-02-05_CO_nwb | pca | 3 | local_45 | 1.182815 | 1.553493 | 1.697881 | 0.028137 |
| 2020-02-05_CO_nwb | pca | 6 | source | 1.589545 | 1.785513 | 1.902846 | 0.027396 |
| 2020-02-05_CO_nwb | pca | 6 | local_15 | 1.008369 | 1.548475 | 1.684227 | 0.027513 |
| 2020-02-05_CO_nwb | pca | 6 | local_45 | 1.007474 | 1.539157 | 1.680468 | 0.028078 |
| 2020-02-05_CO_nwb | pca | 6 | local_45_pool_scaler | 1.331415 | 1.543705 | 1.678848 | 0.028298 |
| 2020-02-05_CO_nwb | pca | 12 | source | 1.462146 | 1.785849 | 1.902544 | 0.028107 |
| 2020-02-05_CO_nwb | pca | 12 | local_15 | 0.806821 | 1.552181 | 1.683228 | 0.027119 |
| 2020-02-05_CO_nwb | pca | 12 | local_45 | 0.796499 | 1.534929 | 1.674576 | 0.027508 |
| 2020-02-05_CO_nwb | fa | 3 | source | 1.788384 | 1.862314 | 1.905990 | 0.027981 |
| 2020-02-05_CO_nwb | fa | 3 | local_15 | 1.363326 | 1.567748 | 1.688704 | 0.027934 |
| 2020-02-05_CO_nwb | fa | 3 | local_45 | 1.295758 | 1.547709 | 1.684604 | 0.028193 |
| 2020-02-05_CO_nwb | fa | 6 | source | 1.720779 | 1.845026 | 1.905634 | 0.026697 |
| 2020-02-05_CO_nwb | fa | 6 | local_15 | 1.060270 | 1.551512 | 1.690080 | 0.027382 |
| 2020-02-05_CO_nwb | fa | 6 | local_45 | 1.068091 | 1.546031 | 1.684532 | 0.028216 |
| 2020-02-05_CO_nwb | fa | 6 | local_45_pool_scaler | 1.339367 | 1.547645 | 1.680667 | 0.028271 |
| 2020-02-05_CO_nwb | fa | 12 | source | 1.684203 | 1.837423 | 1.905361 | 0.026598 |
| 2020-02-05_CO_nwb | fa | 12 | local_15 | 0.857157 | 1.549685 | 1.687315 | 0.027119 |
| 2020-02-05_CO_nwb | fa | 12 | local_45 | 0.836715 | 1.535606 | 1.678866 | 0.027719 |

## Geometry, clocks and coverage

| Date | Training covariance cosine | Common commands with ≥2 trials each | Mean phase-trajectory cosine | h1 elapsed seconds | h5 elapsed seconds |
|---|---:|---:|---:|---|---|
| 2020-01-30_CO_nwb | 0.710868 | 6 | 0.295525 | [0.019, 0.020] | [0.099, 0.100] |
| 2020-02-04_CO_nwb | 0.535491 | 7 | 0.246371 | [0.019, 0.021] | [0.099, 0.101] |
| 2020-02-05_CO_nwb | 0.420153 | 7 | 0.293271 | [0.019, 0.021] | [0.099, 0.101] |

Contact-coordinate alignment establishes a shared recorded feature space, not stable neuron identity. Reported principal angles map source and local loadings into the same raw-count axes; this raw-count geometry weights contacts differently from source-standardized neural MSE. Covariance and geometry changes mix task sampling, observation noise, count statistics and possible physiology. Ten phase segments are acausal descriptive trial normalization, not synchronized physical movement phases. Condition subsets differ by date and contain few repeated trials; the cosines do not establish invariant population representations.

## Numerical and interpretation limits

All saved PCA/FA forecast checkpoints replayed with maximum absolute raw-count error 1.67e-15. Population fitting emitted 0 warnings. FA held-out scoring emitted 2700 NumPy slogdet runtime warnings (divide/overflow/invalid); these are recorded in the machine report. Every final reported Gaussian likelihood was finite, but this numerical caveat limits interpretation of FA likelihood differences. Gaussian observation scores describe this continuous approximation, not a count-data likelihood.

The model is a two-stage static observation projection plus affine latent AR, not a jointly estimated maximum-likelihood latent dynamical system or Kalman smoother. No physiological mechanism or causal neural connection is identified. Source-to-target distribution differences and extra local fit information can improve neural prediction without improving behavior decoding. A small positive development forecast effect does not independently validate an adaptation policy.

## Reproduction

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 conda run -n cerebro python -m cerebro.research_dynamics
conda run -n cerebro python tools/m023_dynamics_report.py
```

Pinned assets are listed in configs/m023_protocol.json and the referenced LINK manifests. Raw data and numerical checkpoints remain Git-ignored. Source/config hashes and array hashes are in reports/m023_dynamics.json. No historical experiment artifact is replaced.
