# M023 calibration-only adaptation reliability

**Result: no reliability model passes the prespecified promotion gate.** This is a development study, not independently validated reliability.

Protocol `a2861a2`, pre-execution reliability clarification `ca5a0ad`; see [protocol](../docs/research/m023_protocol.md). Only the previously permitted first 75 trials of Jan 30/Feb 4/Feb 5 are used, with pool 45 and evaluation 30. One source date and three development dates belong to one Monkey N. Each budget has 20 uniform subsets/date and three entire-session folds. 369 total allocations include chronological/balanced sensitivity cases; overlapping subsets are not biological replicates.

Inputs are recomputed from calibration data: selected-command coverage, 20 within-B trial-bootstrap prediction dispersion, neural mean shift, frozen/direct disagreement on 45 unlabeled pool trials, calibration-label moments and a source-neural dynamics mismatch. No evaluation means, evaluation neural probes, post-hoc M022 prediction dispersion or extra position labels enter features. All scalers/risk regressors fit on the other two dates only. B selected command labels are additional information for coverage features.

Leave-one-session-out development folds may train on dates later than the held-out date; this is not rolling chronological deployment validation. Only the gated later cohort could supply independent forward evaluation, and its outcomes remain unscored.

## Primary 15-label comparison

| Model | Risk MSE (flexion⁴) | Pooled two-class balanced accuracy |
|---|---:|---:|
| combined | 1.093746724e-05 | 0.675 |
| constant | 1.207965153e-05 | 0.5 |
| coverage | 1.212426056e-05 | 0.45 |
| disagreement | 3.890973094e-05 | 0.3375 |
| instability | 1.214092923e-05 | 0.3875 |
| label_only | 7.20229323e-06 | 0.7625 |
| permuted_combined | 1.249747854e-05 | 0.675 |
| shift | 7.276299647e-05 | 0.6625000000000001 |
| task_control | 7.23305494e-06 | 0.7625 |
| task_plus_dynamics | 7.313017385e-06 | 0.6875 |

Majority-class balanced accuracy: 0.5.
Balanced accuracy is undefined within single-class folds; only the pooled session-equally weighted two-class metric is used for promotion. The combined model improves aggregate risk MSE 9.46% versus constant but is 51.86% worse than label-only. Its balanced accuracy 67.5% equals the permuted-combined control and trails label-only 76.25%. Classification alone therefore provides insufficient evidence of useful neural reliability information.

## Primary contrasts and uncertainty

| Candidate | Control | Aggregate relative risk-MSE improvement | Better every date | Conditional 95% risk-MSE difference interval | Pass |
|---|---|---:|---|---|---|
| disagreement | constant | -222.11% | False | [-7.891276e-06, 6.593125e-05] | False |
| disagreement | label_only | -440.24% | False | [-1.980825e-07, 6.633381e-05] | False |
| disagreement | shift | 46.53% | False | [-0.0001197363, 6.319174e-05] | False |
| coverage | constant | -0.37% | False | [-1.990928e-07, 3.027956e-07] | False |
| coverage | label_only | -68.34% | False | [-2.107939e-06, 9.328281e-06] | False |
| coverage | shift | 83.34% | False | [-0.0001133774, -2.624762e-06] | False |
| instability | constant | -0.51% | False | [-1.252165e-06, 1.464357e-06] | False |
| instability | label_only | -68.57% | False | [-1.802572e-06, 9.051494e-06] | False |
| instability | shift | 83.31% | False | [-0.0001132406, -1.853015e-06] | False |
| combined | constant | 9.46% | False | [-1.764842e-05, 2.259096e-05] | False |
| combined | label_only | -51.86% | False | [-9.755603e-06, 2.153193e-05] | False |
| combined | shift | 84.97% | True | [-0.0001288578, 1.962627e-05] | False |

Relative improvement is one minus the ratio of equal-date mean risk errors, not the mean of date-wise percentages. Intervals resample shared ordered five-trial blocks across every overlapping allocation within each date, while fitted risk models stay fixed. They exclude risk-training uncertainty and population variability; only three development dates from one animal exist. Every primary candidate fails. No best-budget or balanced-allocation fallback is promoted.

## Complete budget and action-policy controls

| Budget | Model | Held-out date | Risk MSE flexion⁴ | Harm fraction | Adaptive-policy MSE flexion² | Always frozen | Always direct |
|---:|---|---|---:|---:|---:|---:|---:|
| 15 | combined | 20200130 | 3.6041468e-06 | 0.950 | 0.02841389 | 0.02841389 | 0.03194134 |
| 15 | combined | 20200204 | 1.5471882e-06 | 0.600 | 0.02969521 | 0.02980624 | 0.03009968 |
| 15 | combined | 20200205 | 2.7661067e-05 | 0.450 | 0.02861882 | 0.02930611 | 0.02920618 |
| 15 | constant | 20200130 | 1.7653461e-05 | 0.950 | 0.02841389 | 0.02841389 | 0.03194134 |
| 15 | constant | 20200204 | 4.64501e-06 | 0.600 | 0.02980624 | 0.02980624 | 0.03009968 |
| 15 | constant | 20200205 | 1.3940483e-05 | 0.450 | 0.02930611 | 0.02930611 | 0.02920618 |
| 15 | coverage | 20200130 | 1.7838882e-05 | 0.950 | 0.02963372 | 0.02841389 | 0.03194134 |
| 15 | coverage | 20200204 | 4.6339365e-06 | 0.600 | 0.02980624 | 0.02980624 | 0.03009968 |
| 15 | coverage | 20200205 | 1.3899963e-05 | 0.450 | 0.02930611 | 0.02930611 | 0.02920618 |
| 15 | disagreement | 20200130 | 1.8406357e-05 | 0.950 | 0.03052903 | 0.02841389 | 0.03194134 |
| 15 | disagreement | 20200204 | 2.0948499e-06 | 0.600 | 0.02980624 | 0.02980624 | 0.03009968 |
| 15 | disagreement | 20200205 | 9.6227986e-05 | 0.450 | 0.02930611 | 0.02930611 | 0.02920618 |
| 15 | instability | 20200130 | 1.8043032e-05 | 0.950 | 0.02992674 | 0.02841389 | 0.03194134 |
| 15 | instability | 20200204 | 5.6044392e-06 | 0.600 | 0.02983912 | 0.02980624 | 0.03009968 |
| 15 | instability | 20200205 | 1.2775317e-05 | 0.450 | 0.02930611 | 0.02930611 | 0.02920618 |
| 15 | label_only | 20200130 | 1.0948148e-05 | 0.950 | 0.02895074 | 0.02841389 | 0.03194134 |
| 15 | label_only | 20200204 | 3.4784477e-06 | 0.600 | 0.02958245 | 0.02980624 | 0.03009968 |
| 15 | label_only | 20200205 | 7.1802837e-06 | 0.450 | 0.02818567 | 0.02930611 | 0.02920618 |
| 15 | permuted_combined | 20200130 | 1.1847412e-05 | 0.950 | 0.02841389 | 0.02841389 | 0.03194134 |
| 15 | permuted_combined | 20200204 | 1.4226393e-05 | 0.600 | 0.02980624 | 0.02980624 | 0.03009968 |
| 15 | permuted_combined | 20200205 | 1.1418631e-05 | 0.450 | 0.02880351 | 0.02930611 | 0.02920618 |
| 15 | shift | 20200130 | 1.2557488e-05 | 0.950 | 0.02841389 | 0.02841389 | 0.03194134 |
| 15 | shift | 20200204 | 1.1292777e-05 | 0.600 | 0.02980624 | 0.02980624 | 0.03009968 |
| 15 | shift | 20200205 | 0.00019443872 | 0.450 | 0.02920618 | 0.02930611 | 0.02920618 |
| 15 | task_control | 20200130 | 1.0927064e-05 | 0.950 | 0.02895074 | 0.02841389 | 0.03194134 |
| 15 | task_control | 20200204 | 3.8083654e-06 | 0.600 | 0.02958245 | 0.02980624 | 0.03009968 |
| 15 | task_control | 20200205 | 6.9637358e-06 | 0.450 | 0.02818567 | 0.02930611 | 0.02920618 |
| 15 | task_plus_dynamics | 20200130 | 9.1139829e-06 | 0.950 | 0.02895074 | 0.02841389 | 0.03194134 |
| 15 | task_plus_dynamics | 20200204 | 7.6542497e-06 | 0.600 | 0.02979565 | 0.02980624 | 0.03009968 |
| 15 | task_plus_dynamics | 20200205 | 5.1708196e-06 | 0.450 | 0.02818567 | 0.02930611 | 0.02920618 |
| 30 | combined | 20200130 | 1.2600606e-06 | 1.000 | 0.02841389 | 0.02841389 | 0.03041468 |
| 30 | combined | 20200204 | 3.4505094e-07 | 0.150 | 0.02914216 | 0.02980624 | 0.02908774 |
| 30 | combined | 20200205 | 1.0439836e-05 | 0.100 | 0.02838034 | 0.02930611 | 0.02724041 |
| 30 | constant | 20200130 | 1.2373961e-05 | 1.000 | 0.03041468 | 0.02841389 | 0.03041468 |
| 30 | constant | 20200204 | 7.6193441e-07 | 0.150 | 0.02908774 | 0.02980624 | 0.02908774 |
| 30 | constant | 20200205 | 9.2423128e-06 | 0.100 | 0.02930611 | 0.02930611 | 0.02724041 |
| 30 | coverage | 20200130 | 1.2424069e-05 | 1.000 | 0.03041468 | 0.02841389 | 0.03041468 |
| 30 | coverage | 20200204 | 1.0480225e-06 | 0.150 | 0.02949304 | 0.02980624 | 0.02908774 |
| 30 | coverage | 20200205 | 9.7991681e-06 | 0.100 | 0.02930611 | 0.02930611 | 0.02724041 |
| 30 | disagreement | 20200130 | 1.1934748e-05 | 1.000 | 0.03041468 | 0.02841389 | 0.03041468 |
| 30 | disagreement | 20200204 | 8.3324257e-06 | 0.150 | 0.02980624 | 0.02980624 | 0.02908774 |
| 30 | disagreement | 20200205 | 7.2148713e-05 | 0.100 | 0.02930611 | 0.02930611 | 0.02724041 |
| 30 | instability | 20200130 | 1.2365396e-05 | 1.000 | 0.03041468 | 0.02841389 | 0.03041468 |
| 30 | instability | 20200204 | 8.45179e-07 | 0.150 | 0.02936850 | 0.02980624 | 0.02908774 |
| 30 | instability | 20200205 | 9.6219328e-06 | 0.100 | 0.02930611 | 0.02930611 | 0.02724041 |
| 30 | label_only | 20200130 | 3.763414e-06 | 1.000 | 0.02915900 | 0.02841389 | 0.03041468 |
| 30 | label_only | 20200204 | 1.1066861e-06 | 0.150 | 0.02907005 | 0.02980624 | 0.02908774 |
| 30 | label_only | 20200205 | 6.8241625e-06 | 0.100 | 0.02800902 | 0.02930611 | 0.02724041 |
| 30 | permuted_combined | 20200130 | 9.1031742e-06 | 1.000 | 0.03041468 | 0.02841389 | 0.03041468 |
| 30 | permuted_combined | 20200204 | 6.8647847e-06 | 0.150 | 0.02980624 | 0.02980624 | 0.02908774 |
| 30 | permuted_combined | 20200205 | 0.00014562045 | 0.100 | 0.02724041 | 0.02930611 | 0.02724041 |
| 30 | shift | 20200130 | 7.0380845e-06 | 1.000 | 0.03041468 | 0.02841389 | 0.03041468 |
| 30 | shift | 20200204 | 4.9633997e-06 | 0.150 | 0.02980624 | 0.02980624 | 0.02908774 |
| 30 | shift | 20200205 | 0.00021709906 | 0.100 | 0.02724041 | 0.02930611 | 0.02724041 |
| 30 | task_control | 20200130 | 3.7541075e-06 | 1.000 | 0.02915900 | 0.02841389 | 0.03041468 |
| 30 | task_control | 20200204 | 1.1060527e-06 | 0.150 | 0.02907005 | 0.02980624 | 0.02908774 |
| 30 | task_control | 20200205 | 6.780797e-06 | 0.100 | 0.02800902 | 0.02930611 | 0.02724041 |
| 30 | task_plus_dynamics | 20200130 | 2.1906212e-06 | 1.000 | 0.02855059 | 0.02841389 | 0.03041468 |
| 30 | task_plus_dynamics | 20200204 | 1.4726581e-06 | 0.150 | 0.02942198 | 0.02980624 | 0.02908774 |
| 30 | task_plus_dynamics | 20200205 | 3.2334011e-05 | 0.100 | 0.02930611 | 0.02930611 | 0.02724041 |
| 5 | combined | 20200130 | 2.4658983e-05 | 0.950 | 0.02841389 | 0.02841389 | 0.03828014 |
| 5 | combined | 20200204 | 9.3975981e-06 | 1.000 | 0.03029684 | 0.02980624 | 0.03425957 |
| 5 | combined | 20200205 | 8.5438679e-05 | 0.700 | 0.02930611 | 0.02930611 | 0.03086262 |
| 5 | constant | 20200130 | 0.00010748859 | 0.950 | 0.02841389 | 0.02841389 | 0.03828014 |
| 5 | constant | 20200204 | 2.1147222e-05 | 1.000 | 0.02980624 | 0.02980624 | 0.03425957 |
| 5 | constant | 20200205 | 4.6163242e-05 | 0.700 | 0.02930611 | 0.02930611 | 0.03086262 |
| 5 | coverage | 20200130 | 0.00011335779 | 0.950 | 0.02841389 | 0.02841389 | 0.03828014 |
| 5 | coverage | 20200204 | 2.5731988e-05 | 1.000 | 0.02980624 | 0.02980624 | 0.03425957 |
| 5 | coverage | 20200205 | 4.6917676e-05 | 0.700 | 0.02930611 | 0.02930611 | 0.03086262 |
| 5 | disagreement | 20200130 | 6.5500842e-05 | 0.950 | 0.02847772 | 0.02841389 | 0.03828014 |
| 5 | disagreement | 20200204 | 1.1639901e-05 | 1.000 | 0.03015248 | 0.02980624 | 0.03425957 |
| 5 | disagreement | 20200205 | 0.00010714288 | 0.700 | 0.02930611 | 0.02930611 | 0.03086262 |
| 5 | instability | 20200130 | 0.00010787515 | 0.950 | 0.02841389 | 0.02841389 | 0.03828014 |
| 5 | instability | 20200204 | 2.3589726e-05 | 1.000 | 0.02980624 | 0.02980624 | 0.03425957 |
| 5 | instability | 20200205 | 4.6142048e-05 | 0.700 | 0.02930611 | 0.02930611 | 0.03086262 |
| 5 | label_only | 20200130 | 8.1340212e-05 | 0.950 | 0.02841389 | 0.02841389 | 0.03828014 |
| 5 | label_only | 20200204 | 3.0972635e-05 | 1.000 | 0.03068234 | 0.02980624 | 0.03425957 |
| 5 | label_only | 20200205 | 3.1896672e-05 | 0.700 | 0.02930611 | 0.02930611 | 0.03086262 |
| 5 | permuted_combined | 20200130 | 0.00010496431 | 0.950 | 0.02841389 | 0.02841389 | 0.03828014 |
| 5 | permuted_combined | 20200204 | 2.5979761e-05 | 1.000 | 0.02980624 | 0.02980624 | 0.03425957 |
| 5 | permuted_combined | 20200205 | 1.5234689e-05 | 0.700 | 0.02895476 | 0.02930611 | 0.03086262 |
| 5 | shift | 20200130 | 8.9811137e-05 | 0.950 | 0.02841389 | 0.02841389 | 0.03828014 |
| 5 | shift | 20200204 | 3.1400183e-05 | 1.000 | 0.02980624 | 0.02980624 | 0.03425957 |
| 5 | shift | 20200205 | 1.7899938e-05 | 0.700 | 0.02932602 | 0.02930611 | 0.03086262 |
| 5 | task_control | 20200130 | 9.2201423e-05 | 0.950 | 0.02841389 | 0.02841389 | 0.03828014 |
| 5 | task_control | 20200204 | 3.3940015e-05 | 1.000 | 0.03060897 | 0.02980624 | 0.03425957 |
| 5 | task_control | 20200205 | 3.2178952e-05 | 0.700 | 0.02930611 | 0.02930611 | 0.03086262 |
| 5 | task_plus_dynamics | 20200130 | 8.1202155e-05 | 0.950 | 0.02841389 | 0.02841389 | 0.03828014 |
| 5 | task_plus_dynamics | 20200204 | 3.2048776e-05 | 1.000 | 0.03015311 | 0.02980624 | 0.03425957 |
| 5 | task_plus_dynamics | 20200205 | 2.2291032e-05 | 0.700 | 0.02918053 | 0.02930611 | 0.03086262 |

## Dynamics information beyond task/label controls

Adding the source-neural forecast mismatch to coverage+label moments changes primary risk MSE from 7.23305494e-06 to 7.313017385e-06 flexion⁴ (1.11% worse). This secondary comparison supplies no consistent added predictive benefit. Complete per-date errors, chronological/balanced allocation transfer and training-date-only prediction stability remain in the [machine report](m023_reliability.json).

## Independent validation and interpretation

[Native eligibility](../docs/datasets/m023_native_eligibility.md) passes for Feb 24/Feb 25/Jun 26. **No new-session model outcomes were scored**, because the frozen development promotion gate failed. This is a null-rule decision, not an unavailable-data blocker. New native arrays were audited for coverage and compatibility only. The results support a bounded negative finding for these fixed reliability models; they do not establish that all possible reliability diagnostics fail. M022 statistical calibration effects do not automatically become prospective harm predictors, and none identifies physiological drift.

Data: Temmar and colleagues, LINK, [DANDI001201 v0.251023.2336](https://doi.org/10.48324/dandi.001201/0.251023.2336), CC-BY-4.0. Native 20-ms timestamps and count/unit caveats remain unchanged. [Reviewer reproduction guide](../docs/research/m023_reproduction.md) and [primary figure](figures/m023_reliability.pdf).
