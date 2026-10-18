# Mission 024 fresh-install qualification

A public checkout of `99ef1831ba009e53bac05d97e49c3da22da5e455` was cloned into a new temporary directory. A fresh Conda prefix resolved Python 3.11.17 and installed only the declared `dev,classical,deep,brochier` extras. The existing `cerebro` environment was untouched. Exact commands, versions, timings, raw hashes, array comparisons, wheel contents and log digests are in [the machine record](m024_fresh_install.json).

## Executed evidence

| Check | Result |
|---|---|
| Public clone, fresh Conda creation, editable install | PASS |
| Imports and dependency consistency | PASS |
| Complete software suite | 252 passed; 22 data cases separately collected |
| Fresh official DANDI acquisition | Jan 27 native LINK file, 45,005,026 bytes; pinned SHA256 verified |
| Available authentic-data integration | 4 passed; 18 skipped because their declared historical/native assets were deliberately absent |
| Frozen M022 reconstruction | 823 arrays, 23,414,161 values exact versus canonical |
| M023 reliability reconstruction and repeat | 325 arrays, 12,834 values exact; repeated run also exact |
| M023 population reconstruction | 1,023 arrays, 198,396 values exact |
| Report and figure regeneration | Scientific evaluation/session fields exact; both M023 PDF files byte-identical |
| Wheel | Built; inspected contents exclude neural recordings, arrays and model checkpoints |

All experiments ran single-threaded on CPU with unchanged frozen configurations. Four source/development raw inputs were checksum-verified and linked through ignored relative repository paths; no processed arrays or checkpoints were copied or linked. This is a clean source-to-result reconstruction with explicitly available raw inputs, not a claim that every historical dataset was reacquired. A separate native Jan 27 file was actually downloaded from the official public endpoint and verified, so acquisition was tested independently of the cached raw links.

The initial wheel-build attempt lacked sandbox network access to its declared `setuptools` build dependency. The authorized network retry succeeded without source changes. No dependency constraint or test tolerance was weakened. Fresh Python's patch version differed from the historical run, but all compared numerical arrays remained exactly equal.

Neither frozen promotion gate passed; February 24, February 25 and June 26 model outcomes were not consumed. The new checkpoints replay in the authentic-data tests and experiment assertions. Historical checkpoint restoration is qualified separately in the main repository because the isolated checkout intentionally lacks those old checkpoints.

## Final integration candidate recheck

The isolated checkout fetched exact integration candidate `7b26f92ce6734972fbad2c8e1543a50e089d2401` from the local repository, reinstalled editable **1.1.0**, passed dependency checks, and built/inspected `cerebro-1.1.0-py3-none-any.whl` (38 members; no recordings, arrays or checkpoints). Scientific code was unchanged, so no model refit was needed. All prior numerical comparisons remained exact.

The final software suite passed **255 tests**, with 22 data cases deselected. The complete suite with reconstructed authentic inputs passed **259 tests**, with **18 explicit skips** for absent historical datasets/checkpoints and unscored candidate recordings. These fresh-checkout counts complement, rather than replace, the main repository's complete available-data validation.

One intermediate full-suite check found an expected provenance-context mismatch: 258 passed, 18 skipped, and the review-manifest byte-integrity assertion failed because regenerated reports contained the fresh runtime/Git metadata. Software tests passed with committed historical reports. In the reproduced-report context, the documented `python tools/build_review_package.py` command regenerated the review manifest; the full suite then passed. No numerical tolerance, success gate or test assertion changed. Preserve the committed historical report context when verifying its manifest, or rebuild the manifest after generating new reports; do not mix the two contexts.

The initial clone and fresh install came from public GitHub at the published M023 head. This final candidate was subsequently synchronized from the local integration commit, so the record does not claim a fresh public clone of a commit before its publication. The temporary prefix/checkout remain available for verification; no global tooling or original environment was changed.

GPU execution/performance and online biological control were not tested. No graphical presentation-app interaction was performed by this qualification.
