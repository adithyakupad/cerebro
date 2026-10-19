# Reproducing the readability qualification

Use existing Conda `cerebro`, Python3.11, from repository root. No new environment/tool is required. The [baseline inventory](baseline.json) records exact original source/report/checkpoint hashes; [replay values](replay_values.json) retain actual baseline array digests and scientific summaries. Synthetic fixtures below are software checks, not neural findings.

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MPLCONFIGDIR=/tmp/cerebro-mpl conda run -n cerebro python -m pytest -q
conda run -n cerebro python tools/validate_checkpoints.py
conda run -n cerebro python -m pip check
conda run -n cerebro python -m compileall -q src tests tools
ruff check src tools tests --select F,E701,E702,E101,E111,E114,E117,W291,W292,W293 --preview
git diff --check
```

Full authentic-data execution requires the already acquired datasets and ignored checkpoints named in the existing research reproduction guides. Public CI/software-only execution is not a substitute. The checkpoint tool does not train models; it verifies hashes, restores parameters and writes an ignored audit record. Restricted/raw data remain excluded from Git.

## Exact baseline prediction comparison

This observer repeats current CPU checkpoint predictions and compares dtype, shape and bytes to the captured baseline predictions—not only a tolerance against the old published arrays. It observes local function inputs without changing predictions, RNG or model parameters. Requires the historical registry and checkpoints. Save the following to `/tmp/cerebro-readability-check.py`, then run it with `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n cerebro python /tmp/cerebro-readability-check.py`:

```python
import hashlib
import json
from pathlib import Path
import runpy
import sys
import numpy as np

baseline_path = Path('docs/development/readability/replay_values.json')
baseline = json.loads(baseline_path.read_text())
expected = baseline['historical_checkpoint_predictions']
observed = []
validator = runpy.run_path('tools/validate_checkpoints.py')


def capture(frame, event, argument):
    filename = frame.f_code.co_filename
    is_validator = filename.endswith('tools/validate_checkpoints.py')
    if event != 'call' or frame.f_code.co_name != 'check' or not is_validator:
        return
    prediction = np.ascontiguousarray(frame.f_locals['prediction'])
    observed.append({
        'name': frame.f_locals['name'],
        'shape': list(prediction.shape),
        'dtype': str(prediction.dtype),
        'sha256': hashlib.sha256(prediction.tobytes()).hexdigest(),
    })


sys.setprofile(capture)
try:
    validator['main']()
finally:
    sys.setprofile(None)
assert observed == expected
print(f'{len(observed)} prediction arrays match the baseline exactly')
```

Executed baseline qualification used the original Git-exported package and original validator text, with the existing repository as the data root; the final run used the refactored package/validator. Their229 observed prediction manifests were byte-identical. The original historical expected-array check separately remains227 exact and2 within its unchanged tolerance; those two old tolerances are not being called bit-exact.

## Other numerical probes and scientific artifacts

Differential tests additionally exercised genuine SENSE/events, full MC_Maze characterization, rendering, seeded synthetic classical/sequence/SSL/transfer pipelines and fixed resampling. They reused fixtures in `test_benchmark.py`, `test_representation_benchmark.py`, `test_representation_transfer.py`, `test_research_dynamics.py`, `test_reliability.py`, `test_cross_subject.py` and `test_subject_identity.py`. [Verification](verification.json) records scopes/counts; [replay values](replay_values.json) retain array signatures and summary outputs. These are overlapping software/path checks, not independent biological experiments or counts to pool into a scientific sample size.

The real-data differential replay compared all54 SENSE/event arrays and their summary/audit,31 inspector arrays and full characterization results. It also regenerated12 event/count PNGs and4 inspector PNGs in temporary directories; bytes matched. The electrode CSV's pre-existing native-object addresses prevent literal cross-process byte identity; its remaining contents matched, as did the other two CSVs. New reports carry changed source hashes/Git metadata; old reports were preserved rather than regenerated in place.

For a separate source export, use `git archive d506ff408b62a7d79b14c59987f20c1d7b46fef4` into a temporary directory. Set `PYTHONPATH` to that export's `src` when observing old functions. Keep old/new source imports in separate Python processes and write new artifacts to temporary/ignored destinations. Do not bypass a provenance failure, replace a source hash in an old report or use untouched LINK outcomes to test this refactor.

Whole-file `ruff format --check src tools tests` is optional and currently fails on78 files in both baseline and refactor; no newly flagged files were introduced. It was measured, not silently called a passing formatter gate. The repository has no configured canonical formatter. The selected indentation/whitespace/compound-statement and F checks passed. No static type checker, GPU benchmark, fresh installation or remote CI was executed for this local refactor; package building and existing-environment dependency/import checks were executed.
