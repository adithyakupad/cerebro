# Remaining work for full-scope CEREBRO

This plan follows the [requirement audit](full_scope_audit.md) at `dd335c291e324cf460f26409e0431e6f2c4983ad`. It does not authorize experiments, model changes, PR merge or a tag. Existing working baselines are retained. A negative result satisfies a correctly executed experiment; it is never an implementation defect.

Relative effort is qualitative: small = protocol/document decision, medium = bounded new analysis, high = new data or multi-session study, very high = hardware/online work. A blocked item has no credible schedule until its external dependency is met.

## P0 — scientific validity and release gate

1. **Resolve FALCON target provenance** (`D3`, feeds `D4`/`F3`): obtain authentic raw EMG with clock, calibration, license and author processing details, or select an independently suitable corpus. The currently published normalized targets cannot be inverted; preserve historical exploratory results. Codex can audit supplied data and implement a locked split-safe pipeline, but cannot manufacture lost raw signals. **Acceptance:** raw/source identity verified and preprocessing fitted only on allowed training data, with held-out evaluation and all old results labeled separately.

2. **Reserve an untouched evaluation and freeze claims** (`Q2`, `E2`): the researcher selects the primary contrast, independent unit, effect threshold, multiplicity/dependence rule and genuinely new sessions/subjects before outcomes. Codex can prepare manifests/protocols after approval. **Acceptance:** pre-outcome protocol and source-only selection, one honest execution, complete favorable and unfavorable reporting.

3. **Full-scope publication decision** (`L2`): after scientific criteria are met or explicitly classified as blocked under the original completion rule, review the exact proposed head, reports and licenses. The human approves interpretation, PR merge and final tag. **Acceptance:** evidence matrix matches claims, no unresolved defect disguised as data limitation, explicit human publication approval. This task cannot be completed by Codex alone.

## P1 — original scientific scope

4. **Independent subject and session transfer** (`D4`, `R3`, `F2`, `F3`, `Q1`): use suitable authentic recordings with documented neural coverage, compatible targets and valid preprocessing; maintain anonymous/contact-only feature policies, target calibration budgets and matched random/supervised controls. Existing 4 LINK dates and 8 FALCON dates are inspected, and only one/two animals respectively are represented. **Acceptance:** prospective fixed protocols across independent sessions and subjects, exact access masks, calibrated baseline comparisons, and uncertainty using independent biological units. Small/mixed/negative outcomes remain valid.

5. **Population geometry and variability inference** (`M2`, `M3`, `E3`): first audit repetitions and event/coverage consistency in larger Maze or another suitable dataset. Maze Small has only 2–3 compatible training trials per condition. The researcher chooses residual covariance and dynamics estimands; Codex can run bounded analyses. **Acceptance:** adequate independent replication, condition/time-specific expectations, held-out dynamics or geometry controls and uncertainty justified by the data structure. Do not infer causality or neuron identity.

6. **Perich coverage gate** (`D2`): seek authoritative observation intervals/acquisition documentation. Keep audit-only until coverage is proved. **Acceptance:** source-backed per-unit or continuous-acquisition bounds and clock mapping, with tested complete-bin masks. No continuous-recording assumption substitutes for documentation.

## P2 — reliability, usability and conditional extensions

7. **Only when justified by a new supported dataset, reduce adapter duplication** (`A2`); retain current result semantics. **Acceptance:** common trial/coverage/units contract exercised by the new adapter and regressions for existing Maze/LINK/FALCON.

8. **Tighten export/platform assurance** (`P2`, `P4`): independently restore any advertised standalone checkpoint from raw counts, and test full-data workflows on each platform actually claimed. Current Mission014 replays 229 predictions, while some formats have integrity checks only. **Acceptance:** fresh-process raw-to-output restoration and platform-specific pass logs. Do not claim CUDA or Windows validation before execution.

9. **Conditional speech/online scope** (`D5`, `N2`, `K2`): decide whether legally compatible speech data or low-latency streaming belongs in a later project mandate. The original full-scope directive treats speech as later/conditional and does not require a live implant interface. **Acceptance if added:** legal data access, defined target/latency/safety protocol and real evidence; simulated replay cannot validate biological control.

## Parallelism and order

- Independent now: researcher/data-owner inquiries for FALCON raw provenance and Perich coverage; researcher selection of a new valid cohort and primary estimand; Codex can statically prepare protocol drafts and artifact export checks. These do not depend on new model implementation.
- Once data and protocol exist: native coverage/target audits can run independently from methodological checks; then fixed transfer and condition analyses can be executed in parallel on separate reserved data. Integrate only after leakage, provenance and uncertainty review.
- Final sequence: data and scope decisions → frozen protocol/independent assets → validation experiments and negative-result preservation → evidence/acceptance review → explicit human publication decision. No release tag is justified before the final gate.

**Do not rebuild** the working PCA/FA, classical or six sequence decoders, longitudinal calibration methods, SSL objectives, registry or explorer. The highest-priority work is evidence acquisition and evaluation design, not a broad model pass.
