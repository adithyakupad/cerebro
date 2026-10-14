# v0.1.0 publication validation

Executed 2026-10-14 before publishing the foundation. Mission 001/002 source,
tests, documentation, initial JSON report, and four compact figures are retained.
Raw NWB recordings, large NPZ arrays, caches, and environment directories are
excluded from the published file set. No credential patterns or machine-specific
absolute paths were found in executable configuration. Local tooling paths in
the historical development inventory are documentation, not runtime inputs.

## Equivalent isolated checkout procedure

A temporary Git clone of the original repository received only the intended
publication files from the working tree (26 files before this validation note).
It received no ignored data, caches, or processed arrays. The existing Conda
`cerebro` environment, Python 3.11.16, installed that candidate in editable mode
using `python -m pip install -e '.[dev]'`, exactly as documented. A separate pip
resolution with `--dry-run --ignore-installed '.[dev]'` confirmed that declared
requirements resolve without relying on already-installed packages.

Executed in that checkout:

```sh
python -c "import cerebro; print(cerebro.__file__)"
python -m cerebro.dataset configs/mc_maze_small.json
python -m cerebro.sense_inspect configs/mc_maze_small.json --bin-width 0.02 --max-gap 0.002
python -m pytest
```

Import resolved to the candidate's source. Acquisition downloaded from the public
version-specific DANDI source, starting without a recording; the published size
and SHA-256 matched. The SENSE run generated NPZ arrays, CSV metadata, a JSON
report, and four nonempty PNGs. Counts were `(14342, 142)`, retaining 131,262
spikes and excluding 407 from incomplete tails; all retained behavioral bins
were valid. The suite passed **33 tests**, no skips, with two legacy device
metadata deprecation warnings. No local-only file was needed beyond files selected
for publication. The main workspace editable installation was restored afterward.

This was isolated source/data reproduction in the existing environment, not
creation of a fresh Conda environment or a test on another operating system.
Scientific results, not report timestamps, worktree flags, paths, or binary image
identity across dependency/platform versions, are the reproduction target.
PyNWB/Matplotlib used their ordinary local caches; no additional service was
required. The report records the numerical-library versions used.

## Scope and review

The README now supplies environment setup, declared dependencies, acquisition,
execution/testing commands, output paths, source attribution, and limitations.
One runtime dependency bug was fixed: the scientific report no longer requests
optional pytest metadata. Existing scientific measurements were not altered.

Manual review covered source, tests, configuration, documentation, and artifacts.
ECC/Ponytail conventions and the previously verified tooling inventory informed
the bounded workflow; no Graphify graph or redundant orchestration was needed.
Publication requires a normal forward push and remote verification. The tag is
conditional on these reproduced results; no dataset/binary GitHub Release is
created. Metadata ambiguity and single-session limitations remain documented.
