# M025 development optimization experiment

Protocol SHA256: `f0b5950ca7977e0f0781f6f9b1e60bd224b7078dfe6267bdcc5e6bbe7c1a6fee`.
Development promotion: **True**; reduction 0.18601181340661532.
This gate uses epoch-selection trials and is not independent evidence.

| Model | Equal-trial MSE (m/s)² |
| --- | ---: |
| mean | 0.0406446236 |
| go_time_template | 0.0397588143 |
| ridge | 0.0375004500 |
| history_ridge | 0.0295760255 |
| kalman | 0.0332080717 |
| CNN 20 | 0.0328837984 |
| CNN 200 | 0.0256874678 |

## Paired CNN200 contrasts

| Reference | Absolute difference | Relative reduction | Trial-bootstrap 95% interval |
| --- | ---: | ---: | --- |
| cnn20 | -0.007196330657007419 | 0.21884122286596186 | [-0.010004347810910457, -0.004288344354983725] |
| kalman | -0.007520603976990885 | 0.22646915598229067 | [-0.011136746788340254, -0.0039426389539673696] |
| history_ridge | -0.0038885577852799526 | 0.13147668472075402 | [-0.00549905306241724, -0.0021211024976800666] |

CPU elapsed seconds: 22.22025658399798.

## Interpretation

A final-epoch choice does not establish undertraining. A development gain does not establish independent improvement.
Previously inspected Small outer trials are exploratory; final eligibility is audited separately.
No cross-subject, physiological cause, live BCI or foundation-model conclusion follows.

## Reproduction

`conda run -n cerebro python -m cerebro.optimization_study --stage development --replay`

Authentic source data and ignored checkpoints/arrays are required. Replay verifies hashes and restores predictions without fitting.
