# Mission 014 release validation

Executed on local 2026-10-14 (UTC execution timestamps extend into October 15).
Source revision: `a3a2dfd04daf3d923a47d133ce4acf30b5983571`; reviewed starting
PR revision: `491921c436aa22f9b8b1dcd969af6f9f974542ab`.
[Command results](mission_014_workflows.json) contain all 46 commands, exit codes,
run times, output, verified source bytes and the final PASS status.

## Installation and authentic-data execution

A committed local clone was created in a temporary directory using
`git clone --no-hardlinks --local`; ordinary hard links were denied by the sandbox.
No processed arrays, checkpoints or previous experiment results were copied.
A fresh Conda prefix was actually created from `environment.yml`, then installed
with `python -m pip install -e '.[dev,classical,deep]'`.
The existing development environment was preserved. Fresh Python was 3.11.17;
development Python was 3.11.16. Both are within the declared Python 3.11 constraint.
Package import under isolated Python resolved to the clone; `pip check` passed.
Fresh versions included NumPy 2.4.6, PyNWB 4.2.0, Matplotlib 3.11.2, SciPy 1.17.1,
scikit-learn 1.9.1, PyTorch 2.14.1 and pytest 8.4.2. Direct-version agreement does
not establish identical transitive dependencies or a portable lock.

MC_Maze Small was downloaded anew from its public source and byte-verified.
Ten other already acquired public assets were reused after SHA256 verification;
each acquisition command revalidated official metadata. This verifies fresh
network acquisition for Small, not eleven independent fresh downloads.
Two newly selected recordings were separately downloaded and natively audited
before use; five additional FALCON candidates were downloaded/audited only.
No official challenge held-out or test recording was acquired.

All documented SENSE, characterization, event, larger-Maze feasibility, native
Perich audit, classical, sequence, within-session representation, longitudinal,
held-out-session representation, dynamics, evaluation, cross-subject, identity,
registry and explorer commands passed. The three preregistered Mission 014
configurations also passed. Outputs were generated from real recordings on CPU.
Scientific agreement is evaluated separately in
[reproduction comparisons](mission_014_reproduction.json); revision and archive
byte changes are not themselves numerical disagreement.

## Tests and packaging

- Full fresh suite: **222 passed**, 20 upstream HDMF manufacturer deprecation
  warnings, 26.19 seconds; no skipped or failed cases.
- Software-only selection: **210 passed, 12 deselected**, 4.57 seconds.
- Data-marked collection: **12 cases**, 210 deselected. Public CI executes the
  software selection and only collects the data cases; collecting is not running.
- Existing environment software suite: 210 passed, 12 deselected, 12.87 seconds.
- `compileall` passed for source, tests and tools. Ruff F checks passed using
  the already installed tool. A standalone static type checker was not installed
  or run.
- A wheel was built from the fresh clone with no dependencies/build isolation:
  `cerebro-0.2.0.dev0-py3-none-any.whl`, 119,448 bytes,
  SHA256 `622417fcf61b772da8477e02f900fe9d6d1ed2d775b68905b2dcddae6e91d0cf`.
  Archive inspection found 35 entries, the MIT license, and no recordings,
  research reports or tests. This checks wheel construction, not a second
  wheel-installed environment.

## Checkpoints and hardware

[Checkpoint evidence](mission_014_checkpoints.json): 350 registry file digests
and 529 reported array digests verified before checkpoint loading. 229 CPU
raw-count-to-output predictions were replayed for classical, sequence and
representation 07/09 workflows: 227 were bitwise exact; two PCA/FA comparisons
passed `rtol=1e-7, atol=1e-9` with errors below 1.4e-16. The additional experiment
artifacts received integrity checks and their workflow restoration checks;
this independent tool does not replay every experiment format.
Random frozen representation-07 probes depend on the original architecture,
seed and Torch initialization behavior to recreate their encoder; their NPZ
probe is not a standalone exported full encoder. The audit checks the recorded
architecture hash and runtime, rather than pretending it is portable inference.

[Hardware evidence](mission_014_hardware.json): CPU and actual Apple MPS each
passed forward, backward, optimizer-update and weights-only restoration for all
six sequence architectures. MPS was probed outside the filesystem sandbox,
without silent CPU fallback. CUDA was unavailable and **NOT TESTED**.
These dimensionless synthetic smoke checks establish backend software operation;
real-data training/evaluation in this mission was CPU. GPU scientific equivalence,
long training and performance were not tested.

## Explorer

The fresh generated HTML was opened in the in-app browser through a temporary
localhost server. Changed trial selection to displayed original trial 8, model
to temporal CNN seed 0, PCA horizontal coordinate to PC3, calibration control
to source-plus-residual and representation setting to reference. Updated plots,
counts and metric rows were observed; browser warning/error log was empty.
The trial selector's internal value is a display-array index; its label remains
the original trial ID. Screenshot retained locally at
`data/processed/mission_014/explorer_verified.png` (Git-ignored). The temporary
server and agent-created tab were closed. A missing optional favicon returned
404; it did not prevent explorer operation. No browser access to raw data or
external service is required by the self-contained explorer.

Historical report files are preserved. Current frozen-source checks intentionally
reject historical cross-subject inputs with an earlier whole-file preparation
hash: use their recorded revision, or rerun cross-subject before the identity
diagnostic. Do not edit historical hashes to make that guard pass.
