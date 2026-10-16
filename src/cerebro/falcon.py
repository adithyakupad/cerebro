"""Read published FALCON calibration samples using recorded neural coverage."""

import numpy as np
from pynwb import NWBHDF5IO

from cerebro.dataset import verify_asset
from cerebro.sense import validate_intervals, validate_timestamps


def load_falcon(manifest, bin_width=0.02):
    """Return trial-local half-open counts and native sampled preprocessed EMG."""
    if bin_width != 0.02:
        raise ValueError("This adapter requires the native 20 ms EMG clock")
    checksum = verify_asset(manifest["local_path"], manifest)
    if manifest.get("source_split") != "held-in-calib":
        raise ValueError("Only disclosed public calibration assets are supported")
    with NWBHDF5IO(manifest["local_path"], "r") as io:
        recording = io.read()
        units = recording.units
        if units is None or "obs_intervals" not in units.colnames:
            raise ValueError("Source neural observation intervals are required")
        spike_times = []
        observation_intervals = []
        reordered_unit_ids = []
        for unit_index in range(len(units)):
            native_spikes = np.asarray(units["spike_times"][unit_index])
            if not np.isfinite(native_spikes).all():
                raise ValueError("Native spike timestamps must be finite")
            if (np.diff(native_spikes) < 0).any():
                reordered_unit_ids.append(int(units.id[unit_index]))
            ordered_spikes = np.sort(native_spikes, kind="stable")
            spike_times.append(validate_timestamps(ordered_spikes, strict=False))
            observation_intervals.append(validate_intervals(units["obs_intervals"][unit_index]))
        muscle_series = recording.acquisition["preprocessed_emg"].time_series
        muscle_names = sorted(muscle_series)
        if not muscle_names:
            raise ValueError("Source EMG targets are missing")
        reference_series = muscle_series[muscle_names[0]]
        timestamps = validate_timestamps(reference_series.timestamps[:])
        if not np.allclose(np.diff(timestamps), bin_width, atol=1e-9, rtol=0):
            raise ValueError("Source EMG clock differs from native 20 ms samples")
        emg_columns = []
        source_units = []
        for name in muscle_names:
            series = muscle_series[name]
            if not np.array_equal(timestamps, series.timestamps[:]):
                raise ValueError("Muscle timestamps differ")
            native_values = np.asarray(series.data[:])
            if native_values.shape != timestamps.shape:
                raise ValueError("Muscle dimensions differ from timestamps")
            converted_values = native_values * series.conversion
            converted_values = converted_values + series.offset
            emg_columns.append(converted_values)
            source_units.append(series.unit)
        targets = np.column_stack(emg_columns)
        mask_series = recording.acquisition["eval_mask"]
        if not np.array_equal(timestamps, mask_series.timestamps[:]):
            raise ValueError("Source evaluation mask clock differs")
        evaluation_mask = np.asarray(mask_series.data[:])
        if evaluation_mask.dtype != np.bool_ or evaluation_mask.shape != timestamps.shape:
            raise ValueError("Source evaluation mask must be sample-aligned Boolean data")
        trial_frame = recording.trials.to_dataframe()
        trial_list = []
        right_edges = np.round(timestamps + bin_width, 12)
        for trial_id, row in trial_frame.iterrows():
            inside_trial = (timestamps >= row.start_time) & (right_edges <= row.stop_time + 1e-10)
            sample_indices = np.flatnonzero(inside_trial)
            left = timestamps[sample_indices]
            right = right_edges[sample_indices]
            counts = np.empty((len(left), len(units)), dtype=np.int64)
            neural_valid = np.zeros(counts.shape, dtype=bool)
            for column, spikes in enumerate(spike_times):
                stop_indices = np.searchsorted(spikes, right, side="left")
                start_indices = np.searchsorted(spikes, left, side="left")
                counts[:, column] = stop_indices - start_indices
                for observation_start, observation_stop in observation_intervals[column]:
                    covered = (left >= observation_start) & (right <= observation_stop)
                    neural_valid[:, column] |= covered
            counts[~neural_valid] = -1
            trial_targets = targets[sample_indices]
            target_valid = np.isfinite(trial_targets).all(axis=1)
            trial_list.append({
                "trial_id": int(trial_id),
                "source_trial_number": int(row.number),
                "counts": counts,
                "neural_valid": neural_valid,
                "targets": trial_targets,
                "target_valid": target_valid,
                "timestamps": left,
                "bin_right_seconds": right,
                "source_eval_mask": evaluation_mask[sample_indices],
                "condition_id": int(row.condition_id),
                "target_object": str(row.tgt_obj),
                "target_location": float(row.tgt_loc),
                "result": str(row.result),
                "events_seconds": {name: float(row[name]) for name in
                                   ("gocue_time", "move_onset_time", "contact_time", "reward_time")},
            })
        return {
            "provenance": dict(manifest),
            "verified_sha256": checksum,
            "session_id": recording.session_id or recording.identifier,
            "subject_id": recording.subject.subject_id,
            "unit_keys": [(recording.identifier, int(unit_id)) for unit_id in units.id[:]],
            "muscle_names": muscle_names,
            "source_target_units": source_units,
            "observation_intervals": observation_intervals,
            "metadata": {
                "identifier": recording.identifier,
                "timestamps_reference_time": recording.timestamps_reference_time.isoformat(),
                "target_interpretation": "published quantile-normalized preprocessed EMG native values",
                "target_units_limitation": "NWB says mV despite author quantile scaling; not calibrated absolute amplitude",
                "alignment": "native target samples at left edge of offline half-open 20 ms neural bins",
                "mask_interpretation": "source within-trial keep mask; not a held-out split or quality certificate",
                "source_preprocessing_limitation": "Author EMG quantiles and filters precede CEREBRO trial splits",
                "neuron_correspondence": "not established across subjects or sessions",
                "derived_spike_ordering": "stable sorting of copies; original times and duplicates preserved",
                "native_unordered_unit_ids": reordered_unit_ids,
            },
            "trials": trial_list,
        }
