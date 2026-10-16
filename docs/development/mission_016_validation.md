# Mission 016 validation record

All new model runs used the committed [protocol](../research/mission_016_protocol.json) at `5a7376a694825005500cd357694fa8e27e2ce31e`, and their stored reports record `git_dirty: false`. No historical result or configuration was replaced. Three [LINK manifests](../datasets/mission_016_eligibility.md) were verified against public DANDI metadata and local SHA256/byte sizes; native sample-reference, task, contact-key and behavioral-clock checks passed before modeling. Downloaded NWBs and numeric checkpoints remain Git-ignored.

Executed in the existing Conda `cerebro` environment (Python 3.11.16):

| Check | Outcome |
|---|---|
| New LINK native data test | 14 tests in `tests/test_link.py` passed, including three new real-asset cases. |
| Full applicable suite after all changes | **227 passed**, 20 upstream HDMF manufacturer-deprecation warnings; 82.96 s. |
| Public-CI-equivalent software subset | **212 passed**, 15 data cases deselected; the separate data collection found 15 cases. These 15 real-data cases passed in the full local suite, not in public CI. |
| New report consistency tests | 2 passed; paired primary arithmetic, split separation, protocol/report hashes and three-seed SSL summaries verified. |
| `python -m pip check` | No broken requirements. |
| Report regeneration | `tools/report_mission_016.py` verified all stored array inventories/digests and the frozen protocol SHA256. A second execution produced identical SHA256s for both summary files and all three figures. |
| Local registry refresh | `python -m cerebro.registry` completed: 14 datasets, 15 experiments and 405 checkpoint/array entries. The registry stays Git-ignored. |

Deterministic generated-output SHA256s: `reports/mission_016.json` `e1197b9423de1053a0962231860703a42b9c294dcb92e6149f0853ca1a1e0041`; `reports/mission_016.md` `cc4a5836ab6a337ace6910ef54be68d98f8eee941631b9ef14cca40085ef50e2`; calibration figure `dc13e287aec107d6be934c81440e530df1c3df2bd51086d28577165349a5e112`; primary-effect figure `e017165d063a1f06821a327063a973150e1885f6219183741c07736c14d4e3b1`; representation figure `39f07dfb3759de722cf6be969c98be7e862e802fb3a50658089362fb875557c5`.

Independent pre-freeze and post-result reviews found no primary train/evaluation leakage. They prompted explicit disclosure of latent-alignment information access, of frozen/source-mean controls outperforming both 15-label methods, and an immutable protocol-hash guard in the report generator. Date, session and within-day run remain confounded; trial-block bands and three optimization seeds are not biological population uncertainty.

No new clean-environment install, remote CI run, CUDA evaluation, independent-subject experiment or model rerun was performed for this mission. The Mission 014 release checks retain their documented scope.
