# M023 native LINK eligibility audit

Native acquisition and compatibility checks were executed on 2026-10-18, without any decoder execution or outcome scoring. The three dates were selected in the M022 metadata-only audit before acquisition. Each supports the prespecified **within-subject, sampled-trial contact-level prediction** setting; none supplies an independent animal.

## Pinned public source

DANDI `001201`, version `0.251023.2336`, [DOI](https://doi.org/10.48324/dandi.001201/0.251023.2336). Versioned metadata specifies `spdx:CC-BY-4.0`; attribution: Temmar and colleagues, LINK (2025). Original NWBs are stored only in ignored `data/raw/link/`, with exact manifests in `configs/link_DATE.json`. Full identifiers, published and locally verified SHA-256 hashes, per-trial sample counts/identities, contact keys, and criterion-level evidence are in [the machine-readable audit](m023_native_eligibility.json).

| Session | Asset ID | Native neural shape | Referenced neural samples | Trials |
|---|---|---:|---:|---:|
| 20200224 | `ed7d5522-a1f8-4725-948d-8f05c884a22f` | 23973 × 96 | 23598 | 375 |
| 20200225 | `15299ea6-cffb-46e8-9175-a822e4f52f1d` | 26621 × 96 | 26246 | 375 |
| 20200626 | `88039197-6170-4d06-ba3e-f58b68c6eb7f` | 27055 × 96 | 26680 | 375 |

## Eligibility decisions

| Criterion | Decision | Direct evidence / limit |
|---|---|---|
| Published identity, size and checksum | PASS | Existing `download_asset` independently checked versioned API metadata and file SHA-256; native loader repeated verification. |
| Public reuse conditions | PASS | Versioned DANDI metadata: CC-BY-4.0. Raw files are not redistributed. |
| Subject, date and task | PASS | Native subject `Monkey N`; unique date-stamped identifiers/reference times; all 375 trials per date say `CO`. |
| Native sampled-neural coverage | PASS | Positive in-bounds trial references; finite, nonnegative integer crossing counts in 96 columns; timestamps strictly increase. |
| Neural–behavior synchronization | PASS | Every trial modality has exactly equal native sample references and timestamps. Original timestamps are retained. |
| Contact correspondence | PASS | All six-field contact keys match Jan27 exactly, in identity column order. This establishes contact mapping only. |
| Behavioral target compatibility | PASS | Source and all targets have identical index/MRS normalized-flexion descriptions, units, conversions and offsets; positions and commands are finite. |
| Calibration/evaluation capacity | PASS | 375 chronological, nonoverlapping trials: first75 calibration, rows75:375 evaluation. No scores were inspected. |
| Longitudinal neuron identity / quality mask | INCONCLUSIVE | No native quality mask or proof of stable neuronal identities. |
| Continuous acquisition outside trial references | INCONCLUSIVE | Not required or assumed; only explicitly referenced bins are eligible. |
| External prior exposure | INCONCLUSIVE | Local history found no candidate decoder outcomes before this audit; outside human exposure cannot be certified. |

## Timing and coverage

Native `ThresholdCrossings` is described as crossings at −4.5 RMS in 20 ms bins. Its NWB `ElectricalSeries` unit is nevertheless `volts`; this source contradiction is retained, and no calibrated-voltage claim is made. All referenced values pass the established integer-count validator.

Each trial start marker equals its first referenced sample. Its stop marker is approximately20ms after its last referenced sample. There is exactly one native row between consecutive trial references, and375 native rows per recording lie outside references. These rows are excluded rather than filled or used to join trials. Within-trial timestamp increments are19,20 or21ms; intertrial referenced-sample steps are39–41ms. No interpolation or clock regularization occurred.

The two targets are index and MRS flexion positions, from fully extended0 to fully flexed1, in native `flexion units`. Their units are not centimeters. Native velocity samples are finite but are not silently substituted for position targets.

## Interpretation restrictions

The three new dates supply three session-level evaluation units from **one animal**. They cannot establish cross-subject generalization. Contact correspondence does not establish neuron identity or distinguish recording changes from neural computations. Valid referenced counts certify sampled observations, not uninterrupted hardware acquisition or physiological stationarity.

No model fitting, decoder predictions, test loss, reliability score, or method selection was performed during this audit. A committed final-evaluation protocol remains necessary before scoring these candidates.
