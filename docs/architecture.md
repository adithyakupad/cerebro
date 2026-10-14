# Scientific architecture

CEREBRO's thesis is that learned neural population representations can support
behavioral decoding, generalization across recording sessions, and adaptation
with limited calibration. These are research objectives requiring evaluation.
Mission 001 established packaging; Mission 002 implements a minimal SENSE reader,
trial-local spike counts, alignment, and inspection figures. Other modules remain
conceptual boundaries, not empty Python frameworks.

| Module | Responsibility | Intended output |
| --- | --- | --- |
| SENSE | Load real recordings; validate timestamps, units, signals, and provenance; apply documented signal processing | Validated neural observations, behavior, events, quality masks |
| MAP | Estimate population geometry, representations, and temporal dynamics | Representations and fitted transforms with training provenance |
| DECODE | Predict behavioral variables from neural observations or representations | Predictions and evaluation against held-out behavior |
| REMEMBER | Compare representations longitudinally, retaining session identity and uncertainty | Session comparisons and drift measurements |
| ADAPT | Calibrate decoders across sessions under an explicit calibration budget | Adapted predictions evaluated on untouched target-session data |
| INTERACT | Expose scientific plots and diagnostics; future closed-loop interfaces require separate design | Auditable visualizations; no hardware control in this milestone |

Intended data flow: immutable raw recordings → SENSE → validated observations
and synchronized behavior → MAP → DECODE → held-out evaluation. DECODE may also
use observations directly for baselines. REMEMBER compares session-specific
observations and MAP outputs; ADAPT uses these with an explicitly bounded
target-session calibration split. INTERACT visualizes inputs, diagnostics, and
evaluations across modules.

Every boundary must preserve session/trial/unit identity, timestamp conventions,
physical units, missing-data masks, processing configuration, and source lineage.
Neural timestamps and behavior share an explicit time reference; conversion,
binning, interpolation, and prediction lags require documented choices. Split
assignment precedes fitted preprocessing. Representation fitting, decoder
selection, and calibration must not inspect evaluation targets.

The human researcher owns representation/model choice, comparison hypotheses,
calibration budgets, and conclusions. No assumption of stable unit identity,
beneficial adaptation, or a neural foundation model is made. MC_Maze inspection
alone cannot demonstrate longitudinal generalization.
