# Remaining work for full-scope CEREBRO

## Mission 022 current-state addendum

v1.0.0 is published at `b780e5cc53f246f4b305d413c4bd1afb962ff42c`. The historical release gates below describe their earlier execution states. [M022](../../reports/m022_calibration_mechanisms.md) supplies new development evidence for calibration allocation sensitivity and finite-sample prediction dispersion, with mixed regularization/scaling effects. No prespecified candidate passes the owner-confirmed 5%/all-date promotion rule; no mitigation is promoted.

The first later CO metadata candidates, Feb 24/Feb 25/Jun 26, remain unscored and require native eligibility checks before any future separately approved protocol. Independent mitigation validation was **not executed because the development gate failed**, rather than being blocked by proven lack of accessible recordings. Do not recycle the inspected development dates or Mission 016 evaluation dates as untouched tests, tune a new candidate against them without explicit developmental labeling, or promote balanced allocation without accounting for all 45 commanded-target labels.

Remaining scientific gates retain the original scope: independently justified practical adaptation benefit; subject-general representation evidence; valid raw-target/coverage provenance where absent; sufficient biological replication and hardware evidence for any broader claims. No model-family rebuild is indicated by this study. Human review of the mechanism/estimand and a separately frozen future study must precede additional outcomes. Original requirements and historical results below are unchanged.

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

## Mission 016 evidence update (2026-10-15)

This addendum preserves the Mission 015 audit above. The [frozen protocol](mission_016_protocol.json) selected three previously uninspected LINK sessions by date before model outcomes; [results](../../reports/mission_016.md) cover one Monkey N and do not create independent subjects.

| Prior gap | New evidence | Remaining acceptance gate | Priority |
|---|---|---|---|
| `R3` independent-date calibration robustness | Feb 6/11/22 2020 each have 375 compatible CO trials and documented sampled neural/behavioral coverage. Prespecified 15-label source-assisted minus target-only MSE is positive on all three dates (equal-date +0.00061488 flexion²). Negative transfer is a valid scientific outcome. | Multiple biological subjects or independently prespecified later cohorts are needed for a broad robustness claim; do not tune against these now-inspected dates. | P1 |
| `F2` transferable SSL features | Fixed three-seed Feb 6 reference experiment and random/supervised controls executed; differences are small and mixed. | Independent tasks/subjects and practical effect criteria selected before new outcomes; foundation-model validity remains unestablished. | P1 |
| `D3`/`D4` strict cross-subject targets | Eligibility screen confirms FALCON native coverage but irreversible author EMG preprocessing; Zenodo Indy/Loco is promising but native coverage not certified. | Obtain raw FALCON targets plus clock/provenance, or validate a suitable independent corpus with documented neural observation coverage and split-safe targets. | P0; external data |
| `D2` Perich | No new authoritative observation intervals. | Remains audit-only pending source-backed neural coverage. | P1; external documentation |
| `L2` final release | Software and negative scientific results remain preserved; Mission 016 adds reproducible same-subject evidence only. | Full-scope evidence review and explicit human approval. No merge or final tag. | P0; human decision |

## Mission 017 continuation gate

1. **P0, external data:** seek an authentic Loco neural acquisition timeline/quality source, or directly audit the Brochier repository's exact assets, checksums, reuse terms, native time offsets and original labels. The [ranking](../datasets/mission_017_eligibility.md) is evidence-backed but neither candidate is yet model-eligible. FALCON raw EMG remains an alternative only if the authors publish synchronized original targets and preprocessing provenance. Perich remains audit-only.
2. **P0, prospective human research choice:** once a corpus clears the gates, select a compatible target and biological estimand, then commit an immutable source/target subject partition, feature policy, calibration budgets, primary baseline contrast and failure rule **before** any held-out model outcome. Two animals allow a bounded case study, not population confidence.
3. **P1, adaptation mechanism:** use Jan 27 source-development pseudo-target trials to test label-coverage balancing, ridge-prior/alpha sensitivity and contact scaling under internal validation. The [Mission 017 diagnosis](../../reports/mission_017_adaptation.md) is descriptive; Mission 016 Feb 6/11/22 dates are already inspected and cannot select revisions. Validate any frozen revision on genuinely new recordings.
4. **P0, publication:** retain PR #1 as draft, preserve main/v0.1.0, and seek human interpretation and release approval only after the original full-scope scientific gate is met or explicitly adjudicated. Public CI validates software without downloaded data.

## Mission 018 continuation gate

Brochier publisher documents establish two named sessions and nominal condition repetitions, but native GIN assets could not be retrieved here. The [asset audit](../datasets/mission_018_brochier.md) and [eligibility report](../../reports/mission_018_eligibility.md) leave per-file hashes, sampled recording coverage and physically comparable sensor calibration unresolved. Obtain the exact native files (or publisher-supported access) and independently verify their clocks, coverage and sensor definitions before freezing a cross-animal protocol. One session per animal will still preclude disentangling subject from session. The bounded Indy/Loco check found no official Loco broadband acquisition timeline. No model redesign is indicated by this blocker; preserve earlier negative and exploratory findings.

## Mission 019 updated remaining gates

1. **P0, continuous-target validity:** Native Brochier neural samples and four instructed labels are now verified, but cross-animal physical force/displacement calibration is not. FALCON original EMG remains unavailable; Loco neural acquisition coverage and Perich observation intervals remain undocumented. Obtain authoritative sensor calibration or a new corpus with raw, synchronized, comparable behavior before claiming strict continuous cross-subject decoding. This is a data/provenance gap, not a decoder defect.
2. **P1, biological generality:** The frozen Brochier four-class case study found no clear source-assisted gain in either direction. One session from each of two animals cannot separate subject from session or estimate across-subject variability. Replicate on additional independent animals/sessions under a new committed protocol, with source/target restrictions and practical effects specified before test outcomes.
3. **P1, population variability:** Brochier has 30–41/35–36 correct trials per class and verified sampled go windows. A separately prespecified condition-and-event-time residual-covariance analysis is now feasible, subject to trial independence and task-epoch review. Do not treat pooled temporal covariance as noise correlation or infer causal connectivity.
4. **P2, data terms:** Publisher root text says CC-BY-4.0 while bundled `datasets/LICENSE.txt` is CC-BY-SA-4.0. Ask the publisher to clarify which governs raw asset redistribution; keep original files local meanwhile.

The [Mission 019 audit](../datasets/mission_019_brochier.md), [protocol](mission_019_protocol.md) and [negative-result report](../../reports/mission_019_brochier_transfer.md) supersede Mission 018's access blocker without rewriting historical records. Human release approval remains pending; no merge or final tag is authorized.

## Mission 020 updated remaining gates

The [frozen Brochier population analysis](../../reports/mission_020_brochier_population.md) closes Mission 019's **descriptive** event-aligned variability task. Its source-matched trial residuals, 300 whole-trial bootstrap draws and 200 shuffles do not overcome the per-condition covariance rank ceiling (L 29–40; N 34–35, versus 93/156 units) or one-session-per-animal biological replication. The [33-requirement traceability matrix](mission_020_traceability.md) advances M2 to PARTIAL and leaves the original broader criterion intact.

1. **P0, external target evidence:** Resolve comparable, synchronized raw continuous behavior in independent animals; FALCON upstream EMG cannot be inverted, Brochier sensor calibration is unresolved, and Perich/Loco neural coverage remains uncertified. Do not treat classification as continuous decoding.
2. **P1, independent biological replication:** A prospective cohort with multiple animals/sessions and adequately repeated conditions is needed for general subject-transfer, residual variability, stable-manifold and foundation claims. Set practical effects and splits before outcomes. More trials of L/N do not create more biological subjects.
3. **P1, population precision:** For reliable high-dimensional residual covariance, gather enough independent condition-matched trials relative to recorded units or predeclare a lower-dimensional/shrinkage estimand and validate its uncertainty. Current pairwise distributions and participation ratios are descriptive.
4. **P2, release evidence:** Review the integrated report, clarify the Brochier root-versus-bundled license-text conflict before redistributing raw assets, and assess packaging/platform scope. Preserve the historical negative experiments.
5. **Human decision:** The researcher decides scientific claims and whether the software platform can be publicly released with explicitly incomplete hypotheses. Draft PR #1 remains unmerged and no final tag is justified by this mission alone.
