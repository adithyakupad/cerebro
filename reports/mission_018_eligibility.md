# Mission 018: cross-animal eligibility and timing

**No conditional model experiment executed.** Source-documented facts support a plausible future two-animal case study, but native acquisition coverage and comparable targets were not established. A frozen protocol would be premature.

| Gate | Status | Evidence and consequence |
|---|---|---|
| Authentic neural source and public reuse | PASS at dataset level | [Publisher DOI](https://doi.gin.g-node.org/10.12751/g-node.f83565/) identifies extracellular recordings and CC-BY-4.0. Individual file identity/integrity is unverified. |
| Two biological subjects and explicit session IDs | PASS | [Primary paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC5892370/) names L `l101210-001` and N `i140703-001`. Exactly one published session per subject confounds subject and session. |
| Unit/channel definitions without cross-animal identity assumption | PASS for a design policy | Offline SUA/MUA and array geometry are documented. Any later protocol must use anonymous or independently aligned features; no common neuron ordering is justified. No actual feature matrix was extracted. |
| Recorded observation boundaries, gaps and event alignment | INCONCLUSIVE | Paper documents NSP streams and an N `.ns6` start offset, but native headers/blocks were not inspected. No complete-bin coverage mask can be certified. |
| Comparable physical behavioral target and split-safe preprocessing | INCONCLUSIVE | Analog object sensors exist, but common physical calibration and sensor response across animals are not established. Task condition can support categorical comparisons; it does not substitute for continuous motor behavior. |
| Held-out behavioral prediction with independent biological replication | FAIL for a strict claim | No native tensors, admissible target or coverage; only two subjects with one session each. Trials cannot estimate cross-subject population uncertainty. |
| Condition-matched repeated-trial analysis | INCONCLUSIVE pending native checks | Paper's correct-trial counts per SG-LF/SG-HF/PG-LF/PG-HF are L 41/30/31/33 and N 35/35/35/36. Nominal counts appear adequate for descriptive within-session residual analysis, but event/coverage/condition membership must be verified from source assets. |

## Native timing/coverage checklist

For each exact `.nev`, `.ns2`, `.ns5`/`.ns6`, and `.odml`: record publisher revision and SHA-256; inspect header time origins, sample rate, every contiguous acquisition block, dropped samples, and event/sample clock mapping. Confirm sorted-unit references and trial markers. Check the documented N 82-sample offset against native headers. Derive a per-trial observation mask from recorded samples, not spike minima/maxima. Preserve raw timestamps and analog units. Determine whether sensor calibrations yield the *same* target quantity across L and N, and reserve an untouched subject/session partition before any fitting.

The primary source supports no claim of source-to-target decoding, subject-invariant representation, or statistical superiority. Repeated trials within one animal are not independent animals. Brochier is excluded from model training under the existing CEREBRO data-integrity policy.

## Bounded Indy/Loco fallback

The [authoritative Zenodo release](https://zenodo.org/records/3854034) lists MAT spike/behavior sessions for both subjects and broadband supplements for **Indy** dates only; the named [Indy broadband supplement](https://zenodo.org/records/1302867) documents sampled neural acquisition. The official list does not identify a Loco broadband timeline. This targeted source check does not establish Loco neural observation intervals; Indy/Loco remains ineligible for strict cross-subject validation. No alternative data were downloaded or modeled.
