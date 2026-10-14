# Tooling inventory — Mission 001

Inspected locally on 2026-10-14. Initial repository: README only, clean `main`,
commit `7bb7156`, origin `https://github.com/adithyakupad/cerebro.git`.
No project hooks/configuration existed. Global Codex `AGENTS.md` was empty.

| Tool | Evidence and interface | Appropriate use / Mission 001 usage |
| --- | --- | --- |
| Conda / Python | `/opt/anaconda3/bin/conda`; `conda env list`; base active with Python 3.14.6; existing `/opt/anaconda3/envs/cerebro/bin/python` is 3.11.16 | Explicit target interpreter for installation/tests; no environment creation |
| Git / ripgrep | `/usr/bin/git`; bundled `rg` on PATH | Status, remote, file inspection, diff review; used |
| ECC 2.2.3 | Enabled `ecc@ecc` in Codex configuration; local plugin under `~/.codex/plugins/cache/ecc/ecc/2.2.3` | Read `skills/ecc-guide/SKILL.md` and followed live-file discovery; inspected planning, verification, review, memory, hooks, workflow surfaces |
| Ponytail 5.2.0 | Enabled `ponytail@ponytail`; local plugin under `~/.codex/plugins/cache/ponytail/ponytail/5.2.0` | Read `skills/ponytail/SKILL.md` and review instructions; used minimal-change guidance and manual review principles |
| Graphify (`graphifyy` 0.9.62) | `/Users/adithyaupad/.local/bin/graphify`; launcher uses base Python; distribution in user Python 3.14 site-packages | Executed `graphify --help`, read `skill-codex.md` and Codex hook reference; graph building deferred because there is no substantive code graph yet |
| Node / Claude / Codex | `node`, `claude`, `codex` executables found on PATH | Available for plugin scripts and other agent hosts; no nested agent CLI or plugin scripts executed |
| Codex integrations | Session exposes GitHub, PR-check review, web search, document tools, browser/computer tools, and Resolve bridge | Web used for official NLB references only; other integrations unnecessary for packaging. Exposure does not verify credentials or service health |

## Verified tooling surfaces

ECC's `commands/plan.md` provides an inline plan and confirmation gate; its
`agents/code-reviewer.md` covers correctness, safety, tests, and architecture
drift. `skills/verification-loop/SKILL.md` describes build, types, lint, tests,
security, and diff review. These were inspected, not invoked as slash commands.
Mission 001's explicit execution authorization supplies scope; its small Python
foundation does not need the generic JavaScript checks or extra lint/type/coverage
dependencies in that workflow.

ECC's `workflows/README.md` describes a Claude Workflow-tool pilot with parallel
reviewers and verification. This is not an available Codex Workflow interface;
it was not executed. `skills/ck/SKILL.md` describes Node-backed Context Keeper
commands and a Claude SessionStart hook, with global state under `~/.claude/ck`.
No Context Keeper initialization or global memory writes were performed. Use
repository `AGENTS.md`, architecture, and next-milestone docs for portable memory.

ECC `hooks/codex-hooks.json` declares a SessionStart bootstrap. Ponytail
`hooks/claude-codex-hooks.json` declares SessionStart, SubagentStart, and
UserPromptSubmit hooks. Codex config records trusted hashes for these entries.
This proves configuration presence, not successful execution of every hook.
No hooks were installed or changed; Claude-only hook profiles are not assumed
to run in Codex.

Ponytail ships command definitions for `ponytail`, `ponytail-review`,
`ponytail-audit`, `ponytail-debt`, `ponytail-gain`, and `ponytail-help`.
These are agent workflows, not `ponytail` shell commands; no such executable was
found. Likewise, no `ecc` shell executable was found.

Graphify help verifies CLI commands including `update`, `query`, `path`,
`explain`, `watch`, and `hook`; its references describe post-commit rebuilding
and host instruction integration. No graph, watcher, hook, or MCP integration
was created. Its local skill includes automatic installation suggestions, which
are outside this mission's prohibition on additional global tooling.

## Bounded project workflow

Use INSPECT → PLAN → IMPLEMENT → TEST → REVIEW → REFINE. Repeat only for a
concrete failure or missing acceptance criterion; stop after three unsuccessful
attempts on the same failure. Planning uses the actual scope and persistent
constraints; implementation uses the smallest complete change; tests use the
target environment; review inspects all changed files including untracked ones.
Retain decisions and unresolved findings in versionable documentation. Future
scientific work follows the learning workflow in `AGENTS.md`, with human model
selection and scientific interpretation.

No agent fan-out, new services, global installation, or external account writes
are necessary for this bootstrap. Reassess Graphify and bounded delegated review
when the codebase has enough behavior and relationships to justify them.

## Mission 001 verification

Executed with existing Conda `cerebro`, Python 3.11.16:

- Editable install: `python -m pip install --no-build-isolation -e '.[dev]'`
  succeeded using existing setuptools 83.0.0. CEREBRO 0.1.0 has no runtime
  dependencies. Installed pytest 8.4.2 and its required iniconfig 2.3.1,
  pluggy 1.6.0, and Pygments 2.21.0; packaging 26.3 was already present.
- `python -m pip show cerebro pytest`, package import, and `python -m pip check`
  passed. Import resolves to this repository's `src/cerebro/__init__.py`.
- First pytest run: 3 passed, 1 failed because the test compared version
  constraints in a fixed order. Refinement compares the constraint set.
  Final run: **4 passed**, including isolated import outside the repository.
- A regular wheel built with `python -m pip wheel --no-build-isolation
  --no-deps --no-cache-dir --wheel-dir /private/tmp/cerebro-mission001-wheel .`.
  Its contents include the package and exclude tests/data.
- `conda run -n cerebro python --version` confirmed environment selection.
  `git diff --check` passed; Git status was inspected, including untracked files.
  Raw/processed data and generated-figure ignore rules were checked.
- Manual review read all implementation and documentation files against mission
  scope. No remaining acceptance failures. No lint, type-check, coverage,
  independent-agent review, or real-data checks were run; this milestone contains
  no scientific algorithm or data adapter.

The invoking shell remains in Conda base; activate `cerebro` before manual work.
Pip reported an unwritable default cache and disabled it; installation succeeded.
Dependency versions above record this run, not a lockfile or a clean-machine
replication. No commit, push, PR, dataset download, or CEREBRO-1 code was made.

## Mission 002 update

Mission 001's uncommitted files were inspected and retained. Existing Conda
`cerebro` still uses Python 3.11.16. Installed three direct runtime dependencies:
NumPy 2.4.6, PyNWB 4.2.0, Matplotlib 3.11.2, plus required transitive libraries.
The environment versions, source-code hashes, dirty-worktree flag, and source
revision are recorded in `reports/sense_01.json`. No new environment or global
tooling was installed. `python -m pip check` passes.

Used Ponytail's existing minimal-change/review principles, Git/ripgrep, Conda,
pytest, official web/API references, and PyNWB's established reader/schema
validator. ECC/Graphify interfaces remain as previously inspected; no graph,
hooks, agent fan-out, or orchestration was needed. Reference NLB loader source
was read without installing its full toolkit. Live DANDI metadata was accessed
with the Python standard library; the reusable acquisition command was executed
against the pinned release and existing verified asset.

First scientific test run: 29 passed, 2 failed on decimal boundary arithmetic.
After stabilizing derived bin edges: 31 passed. Adding acquisition protection and
another boundary test exposed a misplaced test assertion (32 passed, 1 failed);
it was moved back to the provenance test. Final suite: **33 passed, 2 warnings**,
including the local genuine-recording check; no tests skipped. The two warnings
concern legacy NWB device `manufacturer` metadata in the source recording.

The real pipeline was rerun after refinement. SHA-256 and size match; NWB schema
validation reports no errors; all retained neural and behavioral bins pass
coverage checks; per-unit retained-bin spike conservation passes. All four
rendered figures were visually reviewed. Raw recordings, derived arrays, and
figures were confirmed Git-ignored. `git diff --check` passes. Manual review
also verified exported array shapes, preserved raw spike totals, aligned masks,
retained-count totals, and report/source hash consistency without pickle loading.
Manual review
covered all new/updated code and scientific assumptions; no separate reviewer,
lint, type-check, or coverage tool was run.

First PyNWB import needed permission to initialize its ordinary schema cache;
subsequent reads work. Matplotlib's cache was directed to `/private/tmp/cerebro-mpl`
for sandboxed runs. Initial font-cache warnings did not prevent figure creation.
Remaining scientific limits and human choices are in
`docs/datasets/mc_maze_small.md`. No model, push, PR, or subsequent milestone was
started.
