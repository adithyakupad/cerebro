"""Inspect a checksum-verified NWB without inferring missing recording coverage."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from pynwb import NWBHDF5IO

from cerebro.dataset import verify_asset


def audit_recording(manifest):
    """Return native metadata; unit identities are local to the source session."""
    path = Path(manifest["local_path"])
    checksum = verify_asset(path, manifest)
    with NWBHDF5IO(str(path), "r") as io:
        recording = io.read()
        units = recording.units
        trials = recording.trials
        session_id = recording.session_id or recording.identifier
        unit_ids = [] if units is None else units.id[:].tolist()
        unit_columns = [] if units is None else list(units.colnames)
        observation_intervals_present = "obs_intervals" in unit_columns
        spike_counts = []
        spike_ordered = []
        for unit_index in range(len(unit_ids)):
            spike_times = np.asarray(units["spike_times"][unit_index])
            finite_times = bool(np.isfinite(spike_times).all())
            ordered_times = bool((np.diff(spike_times) >= 0).all())
            spike_counts.append(int(spike_times.size))
            spike_ordered.append(finite_times and ordered_times)
        behavioral_series = []

        def inspect_series(container):
            if hasattr(container, "data") and hasattr(container, "unit"):
                timestamps = container.timestamps
                timestamp_summary = None
                if timestamps is not None:
                    timestamp_values = np.asarray(timestamps[:])
                    timestamp_differences = np.diff(timestamp_values)
                    timestamp_summary = {
                        "count": int(timestamp_values.size),
                        "unit": "seconds",
                        "finite_and_strictly_ordered": bool(
                            np.isfinite(timestamp_values).all()
                            and (timestamp_differences > 0).all()
                        ),
                        "first": float(timestamp_values[0]) if timestamp_values.size else None,
                        "last": float(timestamp_values[-1]) if timestamp_values.size else None,
                        "median_interval_seconds": float(np.median(timestamp_differences))
                        if timestamp_differences.size else None,
                    }
                behavioral_series.append({
                    "name": container.name,
                    "shape": list(container.data.shape),
                    "unit": container.unit,
                    "conversion": float(container.conversion),
                    "offset": float(container.offset),
                    "timestamps": timestamp_summary,
                })
            for child_attribute in ("data_interfaces", "spatial_series", "time_series"):
                children = getattr(container, child_attribute, {})
                for child in children.values():
                    inspect_series(child)

        behavior = recording.processing.get("behavior")
        if behavior is not None:
            inspect_series(behavior)
        trial_summary = None
        if trials is not None:
            trial_frame = trials.to_dataframe()
            trial_summary = {"count": len(trial_frame), "columns": list(trial_frame.columns)}
            if "result" in trial_frame:
                outcome_counts = trial_frame["result"].value_counts()
                trial_summary["outcome_counts"] = {
                    str(outcome): int(count) for outcome, count in outcome_counts.items()
                }
        source_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        return {
            "provenance": dict(manifest),
            "verified_sha256": checksum,
            "audit_source_sha256": source_hash,
            "identifier": recording.identifier,
            "session_id": session_id,
            "subject_id": recording.subject.subject_id if recording.subject else None,
            "timestamps_reference_time": recording.timestamps_reference_time.isoformat(),
            "unit_count": len(unit_ids),
            "unit_columns": unit_columns,
            "unit_keys": [[session_id, unit_id] for unit_id in unit_ids],
            "per_unit_spike_count": spike_counts,
            "total_spikes": sum(spike_counts),
            "spike_times_finite_and_ordered": all(spike_ordered),
            "observation_intervals_present": observation_intervals_present,
            "neural_coverage_status": "source_intervals_available"
            if observation_intervals_present else "unknown",
            "neuron_correspondence": "not established across sessions",
            "trials": trial_summary,
            "behavioral_series": behavioral_series,
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    manifest = json.loads(arguments.manifest.read_text())
    results = audit_recording(manifest)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(results, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
