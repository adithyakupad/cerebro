# Mission 014 release notes and terminology

This hardens development version **0.2.0.dev0** on PR1. It does not declare the
full research program complete, merge PR1, change v0.1.0 or create a final tag.
The [acceptance matrix](acceptance_matrix.md) separates verified software from
scientific outcomes and unresolved full-scope criteria. Public incremental
research software can be reviewed without asserting every research hypothesis
succeeded. Original scope remains in the completion matrix.

## Changes

Three independently reproduced boundary defects were fixed: frozen split lineage
now binds original-row chronology/config/preparation source; LINK counts reject
int64 overflow; sequence fitting rejects invalid gradient bounds before updating
parameters. Target calibration-mean controls expose label-budget fairness. A
custom cross-subject report now prints its actual reproduction arguments.
The checkpoint validator creates its output directory independently.

Added targeted later-date LINK and FALCON protocols without model-family changes
or outcome-driven tuning. New reports append to historical artifacts; they do
not replace previous negative findings. New acquisition manifests pin public
UUIDs, checksums, licenses and relative paths. Raw recordings and checkpoints
remain ignored. All original report files remain byte-for-byte preserved.

## Executed validation

Fresh Conda Python3.11.17 creation, editable dependency installation and all46
workflow commands passed in an isolated committed clone. Full suite222 passed;
software-only210 passed/12 deselected. Eleven experiments reproduced all526
shared arrays and100,827 selected scientific numeric values exactly. This is
host-specific numerical agreement, not proof of scientific generalization.
350 artifact/529 reported-array digests passed;229 raw-count prediction replays
passed (227 exact). Six sequence architectures passed CPU and Apple MPS software
smokes. All scientific workflows ran on CPU. CUDA, GPU real-data equivalence,
new Windows/Linux installs and standalone type checking were not tested.

The explorer was regenerated from authentic stored outputs and its controls
checked in browser. MIT source license and dataset-specific CC-BY-4.0 attribution
remain distinct. Security checks are heuristic tracked-file screening; neither
history nor arbitrary encoded secrets nor dependency vulnerabilities were
comprehensively audited. Detailed evidence is in
[release validation](../development/mission_014_validation.md) and the
[independent findings](../development/mission_014_audit.md).

## Foundation terminology audit

| Category | Evidence | Permitted description |
|---|---|---|
| Implemented self-supervised objectives | Masked neural reconstruction and within-trial next-step prediction | Implemented objectives with software tests |
| Executed pretraining | Maze Small and two-source LINK pretraining; original four ablations and new fixed reference experiment | Executed finite SSL experiments |
| Learned transferable features | Frozen probes/fine-tuning execute on later LINK dates; paired random/supervised controls retained | Measured transfer outputs; learned features do not imply useful universal transfer |
| Cross-session improvement | Some calibrated baselines improve; LINK Feb05 frozen decoder is worse than source mean; SSL differences tiny/mixed | Specific method/date/budget measurements, not general SSL superiority |
| Cross-subject improvement | FALCON anonymous moments, same16 muscle names; new target frozen slightly below source mean, target calibration helps, residual75 not better than direct ridge | Exploratory author-preprocessed target prediction; not leakage-free raw-target validation or learned cross-subject representation alignment |
| Validated general-purpose neural foundation model | No broad independent-animal/task transfer evidence; identity remains decodable | **Not established**; remains a research objective |

Negative or mixed scientific outcomes do not constitute broken software.
Conversely, passing software checks cannot establish an absent scientific result.
No platform feature or original research criterion was removed to obtain a pass.

## Remaining release and research actions

1. Human review of PR1, acceptance matrix and unresolved full-scope evidence.
   No merge or final-tag approval has been supplied. Do not publish a final
   full-scope tag while completion criteria remain unsatisfied.
2. Resolve the strict cross-subject target-provenance gate with authoritative
   raw EMG/clock/calibration files or an independently suitable recording.
   Published rectified/clipped/resampled normalized EMG is not invertible;
   raw files were not found in the inspected authoritative public sources.
   Preserve existing exploratory reports. Do not contact data owners without
   human authorization.
3. Keep Perich audit-only until recorded neural coverage is established.
   Extra LINK/FALCON dates add sessions, not new animals. Prespecify prospective
   datasets, practical effect criteria and uncertainty before further selection;
   the newly inspected evaluations are no longer untouched.
4. Broader neural foundation-model validity remains scientifically inconclusive.
   Retain random/supervised controls, identity diagnostics and negative findings.
   No additional broad model implementation is justified by this audit.
5. After the approved completion/release gate passes, verify the exact proposed
   head, obtain explicit publication approval, then merge/tag normally. No force
   push, alteration of prior tags or dataset/binary upload is authorized here.
