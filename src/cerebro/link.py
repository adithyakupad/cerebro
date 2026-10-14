"""Load observed LINK trial samples with explicit source channel coordinates."""

import numpy as np
from pynwb import NWBHDF5IO

from cerebro.dataset import verify_asset


def align_channel_keys(source_keys, target_keys):
    """Return target column indices in source order using contact coordinates."""
    source_keys = [tuple(key) for key in source_keys]
    target_keys = [tuple(key) for key in target_keys]
    if len(set(source_keys)) != len(source_keys) or len(set(target_keys)) != len(target_keys):
        raise ValueError("Channel coordinates must be unique")
    target_lookup = {key: index for index, key in enumerate(target_keys)}
    if set(source_keys) != set(target_keys):
        raise ValueError("Source and target channel coordinates differ")
    target_indices = [target_lookup[key] for key in source_keys]
    return np.asarray(target_indices, dtype=int)


def validate_crossing_counts(values):
    """Accept only finite, nonnegative integer-valued native crossing counts."""
    values = np.asarray(values)
    finite_values = np.isfinite(values)
    nonnegative_values = values >= 0
    integer_values = values == np.floor(values)
    valid_values = finite_values & nonnegative_values & integer_values
    if not valid_values.all():
        raise ValueError("Threshold-crossing data must contain nonnegative integers")
    return values.astype(np.int64)


def load_link(manifest):
    """Materialize referenced samples; do not infer units or endpoint coverage."""
    checksum = verify_asset(manifest["local_path"], manifest)
    with NWBHDF5IO(manifest["local_path"], "r") as io:
        recording = io.read()
        if recording.trials is None or len(recording.trials) == 0:
            raise ValueError("LINK requires nonempty source trial references")
        trial_list = []
        channel_keys = None
        native_metadata = None
        for trial_index in range(len(recording.trials)):
            references = recording.trials["timeseries"][trial_index]
            reference_lookup = {reference[2].name: reference for reference in references}
            required_names = ("ThresholdCrossings", "index_velocity", "mrs_velocity",
                              "index_position", "mrs_position")
            if not all(name in reference_lookup for name in required_names):
                raise ValueError("Required LINK neural or behavioral series is missing")
            neural_reference = reference_lookup["ThresholdCrossings"]
            sample_start = int(neural_reference[0])
            sample_count = int(neural_reference[1])
            sample_stop = sample_start + sample_count
            neural_series = neural_reference[2]
            if sample_start < 0 or sample_count <= 0 or sample_stop > len(neural_series.data):
                raise ValueError("Invalid native LINK sample reference")
            timestamps = np.asarray(neural_series.timestamps[sample_start:sample_stop])
            valid_clock = np.isfinite(timestamps).all() and (np.diff(timestamps) > 0).all()
            if not valid_clock:
                raise ValueError("LINK timestamps must be finite and strictly ordered")
            for reference in references:
                reference_indices = (int(reference[0]), int(reference[1]))
                if reference_indices != (sample_start, sample_count):
                    raise ValueError("LINK modalities have incompatible trial references")
                series_timestamps = reference[2].timestamps[sample_start:sample_stop]
                if not np.array_equal(timestamps, series_timestamps):
                    raise ValueError("LINK modalities have incompatible sample clocks")
            neural_values = neural_series.data[sample_start:sample_stop]
            counts = validate_crossing_counts(neural_values)
            electrode_indices = neural_series.electrodes.data[:]
            electrode_frame = recording.electrodes.to_dataframe().iloc[electrode_indices]
            current_keys = []
            for electrode_id, row in electrode_frame.iterrows():
                current_keys.append((str(row.array_name), str(row.bank), int(row.pin),
                                     int(row.row), int(row.col), int(electrode_id)))
            if channel_keys is None:
                channel_keys = current_keys
            elif channel_keys != current_keys:
                raise ValueError("Channel coordinates change within a recording")
            if counts.ndim != 2 or counts.shape[1] != len(channel_keys):
                raise ValueError("Count dimensions disagree with source electrodes")
            velocity_components = []
            velocity_units = []
            for name in ("index_velocity", "mrs_velocity"):
                series = reference_lookup[name][2]
                native_values = np.asarray(series.data[sample_start:sample_stop])
                if native_values.shape != (sample_count, 1):
                    raise ValueError("LINK velocity must have one value per sample")
                physical_values = native_values * series.conversion
                physical_values = physical_values + series.offset
                velocity_components.append(physical_values[:, 0])
                velocity_units.append(series.unit)
            velocity = np.column_stack(velocity_components)
            velocity_valid = np.isfinite(velocity).all(axis=1)
            position_components = []
            position_units = []
            for name in ("index_position", "mrs_position"):
                series = reference_lookup[name][2]
                native_values = np.asarray(series.data[sample_start:sample_stop])
                if native_values.shape != (sample_count, 1):
                    raise ValueError("LINK position must have one value per sample")
                physical_values = native_values * series.conversion
                physical_values = physical_values + series.offset
                position_components.append(physical_values[:, 0])
                position_units.append(series.unit)
            position = np.column_stack(position_components)
            position_valid = np.isfinite(position).all(axis=1)
            trials = recording.trials
            target_position = [float(trials["index_target_position"][trial_index]),
                               float(trials["mrs_target_position"][trial_index])]
            trial_list.append({
                "trial_id": int(trials.id[trial_index]),
                "source_trial_number": int(trials["trial_number"][trial_index]),
                "sample_start": sample_start,
                "sample_count": sample_count,
                "timestamps": timestamps,
                "counts": counts,
                "position": position,
                "position_valid": position_valid,
                "position_units": position_units,
                "velocity": velocity,
                "velocity_valid": velocity_valid,
                "velocity_units": velocity_units,
                "target": np.asarray(target_position),
                "target_style": str(trials["target_style"][trial_index]),
                "run_id": int(trials["run_id"][trial_index]),
            })
            native_metadata = {
                "count_source_unit": neural_series.unit,
                "count_source_description": neural_series.description,
                "count_interpretation": "threshold crossings per native 20 ms bin",
                "unit_conflict": "ElectricalSeries says volts; description and values specify counts",
            }
        return {
            "provenance": dict(manifest),
            "verified_sha256": checksum,
            "session_id": recording.session_id or recording.identifier,
            "source_session_id": recording.session_id,
            "subject_id": recording.subject.subject_id,
            "timestamps_reference_time": recording.timestamps_reference_time.isoformat(),
            "channel_keys": channel_keys,
            "channel_mapping_policy": "source contact coordinates only; neuron correspondence unknown",
            "native_metadata": native_metadata,
            "metadata": {
                "subject_id": recording.subject.subject_id,
                "identifier": recording.identifier,
                "native_count_unit": native_metadata["count_source_unit"],
                "native_count_description": native_metadata["count_source_description"],
                "position_units": position_units,
                "velocity_units": velocity_units,
                "neuron_correspondence": "not established; contact coordinates only",
                "quality_mask": "no explicit source quality mask",
            },
            "trials": trial_list,
        }
