# Mission 018 validation and independent review

Scope: source-document and eligibility audit only. No scientific adapter, model, protocol, neural tensor, figure or new dependency was created. The isolated `codex/brochier-native-audit` branch began at PR head `94103e45be93ae69c071827a1fdd2a0d39d8bc1c` with a clean worktree. Historical reports and frozen protocols were not edited.

| Check | Result |
|---|---|
| Existing Conda environment | `cerebro` Python 3.11.16 present; Neo absent, so no unverified native reader was invoked. |
| Full applicable suite | `conda run -n cerebro python -m pytest -q`: **230 passed**, 20 upstream HDMF deprecation warnings, 78.11 s. Existing authentic-data tests used their local pinned assets; no Brochier test ran. |
| Dependency consistency | `conda run -n cerebro python -m pip check`: no broken requirements. |
| New and updated JSON | `python -m json.tool` passed on asset manifest, dataset inventory, completion matrix and release matrix. |
| Diff hygiene | `git diff --check` passed. No raw recording or generated binary added. |
| Brochier asset integrity | **NOT TESTED**: no native file obtained, so no measured SHA-256 or sampled coverage result exists. Manifest explicitly records null values. |
| Numerical reproducibility | **NOT APPLICABLE**: no new numerical experiment or figure executed. Historical result files are unchanged. |

Independent read-only source review checked the [primary article](https://pmc.ncbi.nlm.nih.gov/articles/PMC5892370/) and [publisher dataset DOI](https://doi.gin.g-node.org/10.12751/g-node.f83565/). Both reviewers independently identified one session per animal, source-reported 30–41 correct trials per condition, object-sensor rather than hand-trajectory targets, and unresolved native coverage/calibration. No reviewer claimed native-byte inspection. The documentary evidence supports the audit's refusal to run a strict cross-animal model. No P0/P1 software defect was identified in this documentation-only change; the scientific blocker is external data access and provenance.

Publisher access attempts: the GIN browser/archive returned HTTP 403 to the web reader; local `curl -IL` for the L `.odml` file timed out after 20 s; read-only `git ls-remote` produced no response within 30 s and was stopped. The outcome is host-specific and should be retried from a network with publisher access before any future protocol freeze.
