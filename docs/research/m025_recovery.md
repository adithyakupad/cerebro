# M025 explicit pre-scoring recovery

The original final attempt stopped after preserving seed0 CNN20/CNN200 checkpoints
and classical parameters. It produced **no final loss, contrast, gate or results
report**. Original `final_started.json`, split manifest and model files remain
unchanged. This is a disclosed recovery of the same frozen evaluation occasion,
not a new cohort, new method, threshold change or repeated outcome-driven test.

## Verified failure

The runner asserted float32 prefix/full agreement at rtol=atol1e-6. Three of40,180
values in seed0CNN200 exceeded that check; maximum absolute discrepancy was
1.3113021850585938e-6 normalized target units. Source architecture is causal
padding, two convolutions, ReLU and binwise readout. Independent synthetic checks
using the source-trained checkpoint reproduced float32 cross-length/same-shape
roundoff while a double-precision validation copy had zero discrepancy.
No final behavioral labels or errors were used for that diagnosis.

The repaired check retains the production float32 architecture, weights,
preprocessing, training and predictions. A copied double-precision model must
pass both prefix/full and same-shape future-perturbation tests at rtol=atol1e-12;
an intentionally acausal fixture must fail. Float32 discrepancies are recorded,
not silently asserted to be bitwise causal. This establishes structural/mathematical
causality, not bitwise future invariance of a float32 convolution backend.
Exact production checkpoint-restoration checks remain unchanged.

## Explicit recovery and immutable lineage

The original frozen protocol permits a reported crash and explicit recovery.
The researcher authorized correcting genuine software defects; independent
methodology review judged this validation-only repair compatible with that
approval, provided no model choice, scientific threshold or scored outcome changes.
The original protocol and development reports remain byte-identical.

`m025_recovery.json` binds the original runner digest from the committed
development report to the exact reviewed recovery runner/helper digests. It also
binds the original marker, checkpoints, controls and split-manifest bytes.
Every other scientific source digest must still match development exactly;
there is no general source-hash bypass. The recovery evidence itself must be
committed before access. A second exclusive `recovery_started.json` records this
one explicit continuation without deleting the original final marker.

Use `--stage final --recover-final` only after those guards and regression checks
pass. Recompute unchanged source-only inner trajectories because the failed
process had not saved their curves. Existing seed0 selected epochs and every
normalization parameter must match exactly before reusing the saved weights;
never overwrite them. Recomputed classical parameters must match the original
NPZ exactly. Train only the remaining fixed seeds/caps not already saved.
No final MSE is computed until all frozen models and verification checks finish.
The final source report explicitly records recovery and checkpoint reuse.

The failed attempt's elapsed duration is estimated from its original marker/log
file timestamps, not presented as a measured per-epoch profile. Resumed wall time
is reported separately; repeated preparation and source-only work must be included
when discussing total compute. No fresh-install, GPU or online-control claim follows.
