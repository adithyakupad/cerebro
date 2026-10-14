# CEREBRO repository instructions

CEREBRO studies adaptive neural intelligence: representations of real neural
population activity supporting decoding, cross-session generalization, and
calibration-efficient adaptation. This is a research thesis, not a demonstrated
capability. Module boundaries and data flow are in `docs/architecture.md`.

## Engineering workflow

- Use INSPECT → PLAN → IMPLEMENT → TEST → REVIEW → REFINE for small, testable
  increments. Inspect repository instructions, Git status, environment, and
  affected files before editing; state scope and acceptance checks first.
- Repeat only for actionable failures or unmet acceptance criteria. Each
  iteration must improve something concrete or identify a blocker. Stop after
  three unsuccessful attempts at the same failure and report evidence.
- Use the existing Conda `cerebro` environment with Python 3.11. Activate with
  `conda activate cerebro`, or use `conda run -n cerebro`. Run installation and
  tests with that environment's `python -m pip` and `python -m pytest`.
- Keep the `src/` layout. Add dependencies only for the current milestone.
  Use the existing environment for repository work; the README's Conda creation
  instruction is for researchers who do not yet have it. No uv, Docker, databases,
  cloud infrastructure, global tooling installations, or speculative scaffolding.
  The full-scope directive authorizes a local interactive research interface.
- Agents own repetitive coding, infrastructure, tests, and precise documentation.
  Delegate only bounded independent work when it reduces effort; avoid redundant
  agents. The lead agent integrates changes and reviews all affected files.
- Review correctness, installation, reproducibility, dependency scope, data
  handling, and unsupported claims. Execute relevant checks; distinguish passed,
  failed, and unexecuted checks. Inspect final Git status. Never claim a check ran
  without its output. Preserve unrelated user changes.
- Keep persistent decisions and next steps in repository documentation. Installed
  ECC/Ponytail conventions are useful where compatible; verify interfaces before
  invoking them. Do not assume cached hooks or workflows are active.
- Do not commit, push, create a PR, or start a subsequent milestone without
  explicit human approval.
  The full-scope directive supplies authorization for reviewed incremental commits,
  branch publication and PRs. Preserve prior tags, avoid force pushes, and create
  a final release tag only after every completion criterion is satisfied.

## Scientific coding style

- Use an explicit, variable-oriented style for new scientific code. Define
  meaningful intermediate variables before calculations so data flow can be
  traced line by line and intermediate results inspected.
- Express algorithms as clear transformations, with one conceptual operation
  per statement. Keep function structure simple and readable.
- Use NumPy vectorization, broadcasting, and boolean masking where appropriate.
  Avoid unnecessarily condensed expressions, nested comprehensions, and long
  method chains.
- Make array dimensions, physical units, and scientific assumptions explicit.
  Use descriptive names without redundant verbosity; prioritize correctness,
  reproducibility, and maintainability.
- Apply this convention to new code. Do not refactor existing working code
  solely for stylistic consistency.

## Scientific workflow and ownership

- For each scientific feature use PREDICT → LEARN → IMPLEMENT → INTERROGATE →
  VALIDATE. State the question, predicted outcome, assumptions, and falsification
  criteria. Identify human decisions before substantial math or scientific code.
- Human researchers select models, preprocessing choices, evaluation designs,
  and interpretation. Agents support implementation and critique; research
  conclusions and scientific claims remain human responsibilities.
- Neuroscience claims require real neural recordings and reproducible evidence.
  Never fabricate data-derived results, benchmarks, figures, or citations.
  Label observed results, simulations, and hypotheses separately. Synthetic
  fixtures test software; they do not establish neuroscience findings.
- Record dataset source/version, asset identifiers and checksums, units, clocks,
  preprocessing, split provenance, random seeds, configurations, code revision,
  and environment/package versions for experiments. Preserve raw data and keep
  data files out of Git. Record missing metadata and scientific assumptions.
- Prevent trial/session leakage. Fit transforms on training data only; preserve
  held-out units and time masks. Do not infer longitudinal neuron identity from
  channel numbers or claim cross-session adaptation from one session.
- Prefer interpretable baselines before complex models. Document negative
  results, uncertainty, and limitations alongside observed measurements.
- The full-scope completion matrix in `docs/research/completion_matrix.md` must
  distinguish software tests from authentic-data validation and incomplete work.
  A within-session representation model is not a validated neural foundation
  model. Channel correspondence is not longitudinal neuron identity.
