"""NWB observations and trial-local spike counts; no models or interpolation."""

from dataclasses import dataclass

import numpy as np
from pynwb import NWBHDF5IO, TimeSeries


def validate_timestamps(times, *, unit="seconds", strict=True):
    times = np.asarray(times, dtype=float)
    if unit != "seconds":
        raise ValueError("Timestamps must be in seconds; convert explicitly")
    if times.ndim != 1 or not np.all(np.isfinite(times)):
        raise ValueError("Timestamps must be a finite one-dimensional array")
    differences = np.diff(times)
    if np.any(differences <= 0 if strict else differences < 0):
        raise ValueError("Timestamps are not ordered")
    return times


def validate_intervals(intervals):
    intervals = np.asarray(intervals, dtype=float)
    if (intervals.ndim != 2 or intervals.shape[1] != 2
            or not np.all(np.isfinite(intervals))
            or np.any(intervals[:, 1] <= intervals[:, 0])
            or np.any(intervals[1:, 0] < intervals[:-1, 1])):
        raise ValueError("Intervals must be finite, ordered, nonoverlapping [start, stop)")
    return intervals


@dataclass
class Behavior:
    timestamps: np.ndarray
    raw_data: np.ndarray
    unit: str
    conversion: float
    offset: float
    description: str
    comments: str

    @property
    def physical_data(self):
        return self.raw_data * self.conversion + self.offset


@dataclass
class Recording:
    metadata: dict
    units: object
    trials: object
    electrodes: object
    behavior: dict[str, Behavior]


def load_recording(path):
    """Materialize observations before closing the established NWB reader."""
    with NWBHDF5IO(path, "r") as io:
        nwb = io.read()
        if nwb.units is None or len(nwb.units) == 0:
            raise ValueError("Recording contains no neural units")
        if nwb.trials is None or len(nwb.trials) == 0:
            raise ValueError("Recording contains no trials")
        units = nwb.units.to_dataframe()
        trials = nwb.trials.to_dataframe()
        if not units.index.is_unique or not trials.index.is_unique:
            raise ValueError("Unit and trial IDs must be unique")
        validate_intervals(trials[["start_time", "stop_time"]].to_numpy())
        for spikes in units.spike_times:
            validate_timestamps(spikes, strict=False)
        if "obs_intervals" not in units:
            raise ValueError("Observation intervals are required; silence is not coverage")
        for intervals in units.obs_intervals:
            validate_intervals(intervals)
        behavior = {}
        for obj in nwb.objects.values():
            if not isinstance(obj, TimeSeries):
                continue
            # This milestone supports numeric behavior TimeSeries in processing.
            parent = obj.parent
            while parent is not None and parent is not nwb:
                if parent is nwb.processing.get("behavior"):
                    break
                parent = parent.parent
            if parent is None or parent is nwb:
                continue
            if obj.name in behavior:
                raise ValueError("Duplicate behavior names are ambiguous")
            raw = np.asarray(obj.data[:]).copy()
            if raw.ndim == 1:
                raw = raw[:, None]
            if raw.ndim != 2 or not np.issubdtype(raw.dtype, np.number):
                raise ValueError("Behavior must be numeric samples × coordinates")
            if obj.timestamps is not None:
                times = validate_timestamps(obj.timestamps[:], unit=obj.timestamps_unit)
            else:
                if obj.rate is None or not np.isfinite(obj.rate) or obj.rate <= 0:
                    raise ValueError("Behavior requires timestamps or a positive rate")
                times = validate_timestamps(obj.starting_time + np.arange(len(raw)) / obj.rate)
            if len(times) != len(raw):
                raise ValueError("Behavior timestamp/data dimensions differ")
            if not np.all(np.isfinite([obj.conversion, obj.offset])):
                raise ValueError("Behavior conversion metadata is invalid")
            behavior[obj.name] = Behavior(
                times, raw, obj.unit, obj.conversion, obj.offset,
                obj.description, obj.comments,
            )
        metadata = {
            "identifier": nwb.identifier, "session_id": nwb.session_id,
            "session_start_time": nwb.session_start_time.isoformat(),
            "timestamps_reference_time": nwb.timestamps_reference_time.isoformat(),
            "session_description": nwb.session_description,
            "subject_id": nwb.subject.subject_id if nwb.subject else None,
            "timestamp_unit": "seconds",
            "trial_descriptions": {c: nwb.trials[c].description for c in trials.columns},
            "unit_columns": list(units.columns),
        }
        electrodes = nwb.electrodes.to_dataframe() if nwb.electrodes is not None else None
    return Recording(metadata, units, trials, electrodes, behavior)


@dataclass
class Counts:
    values: np.ndarray
    valid: np.ndarray
    left: np.ndarray
    right: np.ndarray
    trial_ids: np.ndarray
    unit_ids: np.ndarray
    dropped_tail_seconds: np.ndarray

    @property
    def centers(self):
        return (self.left + self.right) / 2


def bin_spikes(spike_times, trial_intervals, unit_ids, trial_ids,
               observation_intervals, bin_width=0.02):
    """Full-width, half-open trial-local bins; -1 marks unobserved counts.

    Derived edges are rounded to picosecond precision to stabilize decimal
    boundaries; original observation and spike timestamps are never rounded.
    """
    if not np.isfinite(bin_width) or bin_width <= 0:
        raise ValueError("Bin width must be positive seconds")
    trials = validate_intervals(trial_intervals)
    if len(trials) != len(trial_ids) or len(spike_times) != len(unit_ids):
        raise ValueError("ID dimensions differ from observations")
    if len(observation_intervals) != len(unit_ids):
        raise ValueError("Observation interval dimensions differ from units")
    if len(set(unit_ids)) != len(unit_ids) or len(set(trial_ids)) != len(trial_ids):
        raise ValueError("IDs must be unique")
    left = []
    right = []
    labels = []
    tails = []
    for (start, stop), trial_id in zip(trials, trial_ids):
        duration = stop - start
        num_bins = int(np.floor(duration / bin_width + 1e-10))
        edge_offsets = np.arange(num_bins + 1) * bin_width
        edges = np.round(start + edge_offsets, 12)
        edges[0] = start
        if abs(edges[-1] - stop) <= 1e-12:
            edges[-1] = stop
        if edges[-1] > stop:
            edges = edges[:-1]
        left.extend(edges[:-1])
        right.extend(edges[1:])
        labels.extend([trial_id] * (len(edges) - 1))
        tails.append(stop - edges[-1])
    left = np.asarray(left)
    right = np.asarray(right)
    values = np.empty((len(left), len(unit_ids)), dtype=np.int64)
    valid = np.zeros(values.shape, dtype=bool)
    for column, (spikes, intervals) in enumerate(zip(spike_times, observation_intervals)):
        spikes = validate_timestamps(spikes, strict=False)
        intervals = validate_intervals(intervals)
        stop_indices = np.searchsorted(spikes, right, side="left")
        start_indices = np.searchsorted(spikes, left, side="left")
        counts = stop_indices - start_indices
        for start, stop in intervals:
            valid[:, column] |= (left >= start) & (right <= stop)
        values[:, column] = np.where(valid[:, column], counts, -1)
    return Counts(values, valid, left, right, np.asarray(labels),
                  np.asarray(unit_ids), np.asarray(tails))


def align_behavior(series, counts, *, max_gap=0.002):
    """Mean native samples in each bin, masked on missing values or timing gaps.

    Samples never leave their bin/trial. No interpolation, extrapolation, or
    inferred lag correction; a coverage tolerance is explicit in seconds.
    """
    if not np.isfinite(max_gap) or max_gap <= 0:
        raise ValueError("Maximum sample gap must be positive seconds")
    times = validate_timestamps(series.timestamps)
    data = series.physical_data
    if data.ndim != 2 or len(times) != len(data):
        raise ValueError("Behavior timestamp/data dimensions differ")
    aligned = np.full((len(counts.left), data.shape[1]), np.nan)
    valid = np.zeros(len(counts.left), dtype=bool)
    for i, (left, right) in enumerate(zip(counts.left, counts.right)):
        start, stop = np.searchsorted(times, [left, right], side="left")
        sample_times = times[start:stop]
        samples = data[start:stop]
        if (len(sample_times) == 0 or sample_times[0] - left > max_gap
                or right - sample_times[-1] > max_gap
                or np.any(np.diff(sample_times) > max_gap)
                or not np.all(np.isfinite(samples))):
            continue
        aligned[i] = samples.mean(axis=0)
        valid[i] = True
    return aligned, valid
