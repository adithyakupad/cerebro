# SENSE 01: what these arrays mean

An extracellular recording measures electrical potential outside cells.
A sorted spike timestamp marks a detected event assigned to a unit; it is not
a membrane-voltage trace. Sorting can be imperfect. This NWB file provides
sorted events, not continuous raw voltage or spike waveforms. The
[PyNWB electrophysiology documentation](https://pynwb.readthedocs.io/en/stable/tutorials/domain/ecephys.html)
describes the distinction between recorded electrical series and units.

An electrode is a physical recording contact; a channel is a signal acquisition
path; a sorted unit is a group of events assigned by spike sorting. They are not
interchangeable. Multiple units can share an electrode, and an electrode need
not have a unit. This file has 192 electrode entries and 142 unit IDs. The
documented MC_Maze M1 electrode-index error means stored electrode links must
not be treated as reliable anatomical assignments without review. We preserve
them; we do not silently repair them.

`spike_counts` is a T × N integer matrix: rows are retained time bins and columns
are sorted units. Here T = 14,342 and N = 142 at 20 ms. A zero means no spikes
in an observed bin; -1 and `neural_valid=False` indicate missing coverage.
These are counts. Counts divided by bin duration give a binwise rate estimate
in spikes/s, but that conversion and smoothing are not performed here.

Smaller bins resolve timing more finely but produce sparser counts; larger bins
aggregate more events and obscure faster changes. No optimal width is established.
The human-selected 20 ms inspection grid uses half-open intervals, restarts per
trial, and drops incomplete final bins. Only derived grid edges are rounded to
picoseconds to stabilize floating-point arithmetic; raw timestamps stay intact.

Behavior has a separate timestamp vector. Neural counts and mean behavior samples
are associated only within the same bin. `conversion=0.001` turns stored mm into
meters and mm/s into m/s. Gaps or nonfinite samples produce missing aligned
behavior; no samples are borrowed from another trial. The explicit 2 ms coverage
tolerance is a sampling assumption, not a measured hardware synchronization error.

This establishes consistent file-time alignment, not independently verified
hardware latency. A raster and trajectory cannot establish causality, decoding
accuracy, cognition, stable neuron identity across sessions, or adaptation.
This curated single-session training asset excludes unsuccessful trials and
contains train/validation labels. Human review of preprocessing and evaluation
choices is still required before a model experiment.
