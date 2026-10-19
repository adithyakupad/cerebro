# M025 final optimization experiment

Protocol SHA256: `f0b5950ca7977e0f0781f6f9b1e60bd224b7078dfe6267bdcc5e6bbe7c1a6fee`.
Development promotion: **True**; reduction 0.5141076518450758.
This gate uses epoch-selection trials and is not independent evidence.

| Model | Equal-trial MSE (m/s)² |
| --- | ---: |
| mean | 0.0389789450 |
| go_time_template | 0.0382411475 |
| ridge | 0.0327981345 |
| history_ridge | 0.0220675991 |
| kalman | 0.0302108898 |
| CNN 20 | 0.0266053581 |
| CNN 200 | 0.0127916679 |

## Paired CNN200 contrasts

| Reference | Absolute difference | Relative reduction | Trial-bootstrap 95% interval |
| --- | ---: | ---: | --- |
| cnn20 | -0.013813690194418183 | 0.5192070755254306 | [-0.014491534902654701, -0.013133823708440066] |
| kalman | -0.0174192218754549 | 0.5765875145440453 | [-0.018188200944704122, -0.016680848015545254] |
| history_ridge | -0.00927593116045816 | 0.42034165632969755 | [-0.009745912019416684, -0.00882266016457585] |

CPU elapsed seconds: 1549.480882333126.

## Interpretation

A final-epoch choice does not establish undertraining. A development gain does not establish independent improvement.
Previously inspected Small outer trials are exploratory; final eligibility is audited separately.
No cross-subject, physiological cause, live BCI or foundation-model conclusion follows.

## Reproduction

`conda run -n cerebro python -m cerebro.optimization_study --stage final --replay`

Authentic source data and ignored checkpoints/arrays are required. Replay verifies hashes and restores predictions without fitting.
