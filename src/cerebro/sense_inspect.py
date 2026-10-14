"""Inspect a verified MC_Maze asset and write arrays, checks, and four figures."""

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pynwb import validate

from cerebro.dataset import verify_asset
from cerebro.sense import align_behavior, bin_spikes, load_recording


def inspect(manifest_path, *, bin_width=0.02, max_gap=0.002,
            processed_dir="data/processed", figures_dir="reports/figures",
            report_path="reports/sense_01.json"):
    manifest = json.loads(Path(manifest_path).read_text())
    path = Path(manifest["local_path"])
    verify_asset(path, manifest)
    schema_errors = validate(path=path)
    if schema_errors:
        raise ValueError(f"NWB schema errors: {schema_errors}")
    recording = load_recording(path)
    units, trials = recording.units, recording.trials
    intervals = trials[["start_time", "stop_time"]].to_numpy()
    counts = bin_spikes(units.spike_times, intervals, units.index, trials.index,
                        units.obs_intervals, bin_width)
    if len(counts.left) == 0:
        raise ValueError("No full bins; choose a smaller bin width")
    aligned = {name: align_behavior(series, counts, max_gap=max_gap)
               for name, series in recording.behavior.items()}
    if "hand_pos" not in aligned or "hand_vel" not in aligned:
        raise ValueError("This inspection requires available hand_pos and hand_vel")
    if recording.behavior["hand_pos"].unit != "meters" or recording.behavior["hand_vel"].unit != "m/s":
        raise ValueError("Unexpected hand units; do not label inferred physical units")
    train_trials = trials[trials["split"] == "train"] if "split" in trials else trials
    if len(train_trials) == 0:
        raise ValueError("No training trial available for inspection figures")
    trial_id = train_trials.index[0]
    selected = counts.trial_ids == trial_id
    row = trials.loc[trial_id]
    start, stop = counts.left[selected][0], counts.right[selected][-1]
    arrays = {
        "spike_counts": counts.values, "neural_valid": counts.valid,
        "bin_left_seconds": counts.left, "bin_right_seconds": counts.right,
        "bin_center_seconds": counts.centers, "trial_ids": counts.trial_ids,
        "unit_ids": counts.unit_ids,
        "trial_intervals_seconds": intervals,
        "trial_table_ids": trials.index.to_numpy(),
        "trial_split": trials["split"].to_numpy(dtype=str),
        "heldout_units": units.heldout.to_numpy(dtype=bool),
        "spike_times_seconds": np.concatenate(units.spike_times.to_list()),
        "spike_offsets": np.r_[0, np.cumsum([len(s) for s in units.spike_times])],
        "observation_intervals_seconds": np.concatenate(units.obs_intervals.to_list()),
        "observation_offsets": np.r_[0, np.cumsum([len(s) for s in units.obs_intervals])],
    }
    for name, series in recording.behavior.items():
        arrays[f"{name}_raw"] = series.raw_data
        arrays[f"{name}_timestamps_seconds"] = series.timestamps
        arrays[f"{name}_aligned"] = aligned[name][0]
        arrays[f"{name}_valid"] = aligned[name][1]
    processed_dir, figures_dir = Path(processed_dir), Path(figures_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(processed_dir / "sense_01.npz", **arrays)
    # CSVs preserve the source metadata tables for inspection, not model input.
    trials.to_csv(processed_dir / "trials.csv")
    if recording.electrodes is not None:
        recording.electrodes.to_csv(processed_dir / "electrodes.csv")
    unit_table = units.drop(columns=["spike_times", "obs_intervals", "electrodes"]).copy()
    unit_table["electrode_ids_as_stored"] = [
        ";".join(map(str, table.index)) for table in units.electrodes
    ]
    unit_table.to_csv(processed_dir / "units.csv")
    source = (f"DANDI {manifest['dandiset']} v{manifest['version']} | "
              f"asset {manifest['asset_id']}\n"
              f"Jenkins / small | trial {trial_id} ({row['split']}) | "
              f"[{start:.3f}, {stop:.3f}) s | bins {bin_width * 1000:g} ms")

    def save(fig, name):
        fig.suptitle(source, fontsize=8)
        fig.tight_layout(rect=(0, 0, 1, 0.89))
        target = figures_dir / f"{name}.png"
        fig.savefig(target, dpi=160)
        plt.close(fig)
        return str(target)

    figures = []
    fig, ax = plt.subplots(figsize=(10, 5))
    for i, spikes in enumerate(units.spike_times):
        spikes = spikes[(spikes >= start) & (spikes < stop)]
        ax.scatter(spikes, np.full(len(spikes), i), marker="|", s=9, color="#273c75")
    ax.set(xlabel="NWB reference time (s)", ylabel="Sorted unit row (see unit_ids)",
           title="Extracellular spike raster", xlim=(start, stop))
    figures.append(save(fig, "sense_01_raster"))
    population = np.where(counts.valid.all(axis=1), counts.values.sum(axis=1), np.nan)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(counts.centers[selected], population[selected], color="#273c75")
    ax.set(xlabel="NWB reference time (s)", ylabel=f"Population spikes / {bin_width * 1000:g} ms bin",
           title=f"Population spike counts (all {len(units)} recorded units; no rate estimate)", xlim=(start, stop))
    figures.append(save(fig, "sense_01_population"))
    fig, ax = plt.subplots(figsize=(6, 6))
    for name in ["hand_pos", "cursor_pos"]:
        if name in recording.behavior:
            series = recording.behavior[name]
            if series.unit != "meters" or series.raw_data.shape[1] != 2:
                raise ValueError("Trajectory requires two coordinates in meters")
            mask = (series.timestamps >= start) & (series.timestamps < stop)
            xy = series.physical_data[mask]
            ax.plot(xy[:, 0], xy[:, 1], label=name)
    ax.set(xlabel="x (m)", ylabel="y (m)", title="Native hand / cursor trajectory")
    ax.set_aspect("equal", adjustable="datalim"); ax.legend()
    figures.append(save(fig, "sense_01_trajectory"))
    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    axes[0].plot(counts.centers[selected], population[selected])
    axes[0].set(ylabel="Population spikes / bin", title="Common timestamp alignment; no fitted lag")
    velocity = aligned["hand_vel"][0]
    axes[1].plot(counts.centers[selected], velocity[selected, 0], label="hand vx")
    axes[1].plot(counts.centers[selected], velocity[selected, 1], label="hand vy")
    axes[1].set(xlabel="NWB reference time (s)", ylabel="Mean velocity (m/s)", xlim=(start, stop))
    for key in ["go_cue_time", "move_onset_time"]:
        if key in row and np.isfinite(row[key]):
            for ax in axes:
                ax.axvline(row[key], linestyle="--", color="gray", alpha=0.6)
            axes[0].text(row[key], axes[0].get_ylim()[1], key, rotation=90, va="top", fontsize=7)
    axes[1].legend()
    figures.append(save(fig, "sense_01_aligned"))

    behavior_summary = {}
    for name, series in recording.behavior.items():
        times = series.timestamps
        behavior_summary[name] = {
            "raw_shape": list(series.raw_data.shape), "timestamp_shape": list(times.shape),
            "unit": series.unit, "conversion": series.conversion, "offset": series.offset,
            "description": series.description, "comments": series.comments,
            "time_range_seconds": [float(times[0]), float(times[-1])] if len(times) else None,
            "max_sample_gap_seconds": float(np.diff(times).max()) if len(times) > 1 else None,
            "nonfinite_values": int((~np.isfinite(series.raw_data)).sum()),
            "aligned_shape": list(aligned[name][0].shape),
            "valid_bins": int(aligned[name][1].sum()),
        }
    expected_counts = np.array([
        sum(np.sum((s >= a) & (s < b)) for a, b in zip(counts.left, counts.right))
        for s in units.spike_times
    ])
    conserved = bool(counts.valid.all() and np.array_equal(counts.values.sum(axis=0), expected_counts))
    if not conserved:
        raise ValueError("Selected recording must have observed bins with conserved spikes")
    outside_observation = 0
    for spikes, obs in zip(units.spike_times, units.obs_intervals):
        observed = np.zeros(len(spikes), dtype=bool)
        for a, b in obs:
            observed |= (spikes >= a) & (spikes < b)
        outside_observation += int((~observed).sum())
    report = {
        "provenance": manifest, "inspected_at": datetime.now(timezone.utc).isoformat(),
        "recording": recording.metadata,
        "environment": {name: importlib.metadata.version(name) for name in
                        ["cerebro", "numpy", "pynwb", "hdmf", "h5py", "matplotlib"]},
        "python_version": sys.version,
        "source_sha256": {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                          for name in ["dataset.py", "sense.py", "sense_inspect.py"]},
        "git_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "git_worktree_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], text=True).strip()),
        "raw_spikes": int(sum(map(len, units.spike_times))), "units": len(units),
        "trials": len(trials), "trial_columns": list(trials.columns),
        "split_counts": {str(k): int(v) for k, v in trials.split.value_counts().items()},
        "heldout_units": int(units.heldout.sum()),
        "counts_shape": list(counts.values.shape), "bin_width_seconds": bin_width,
        "bin_convention": "[left, right), full bins reset at each trial start; tail dropped",
        "derived_edge_precision_seconds": 1e-12,
        "behavior_alignment": "mean physical samples within each bin; no interpolation",
        "max_behavior_gap_seconds": max_gap,
        "selected_trial_id": int(trial_id), "figure_interval_seconds": [float(start), float(stop)],
        "behavior": behavior_summary, "figures": figures,
        "checks": {
            "nwb_schema_errors": [],
            "checksum_matches": True, "ordered_finite_spike_timestamps": True,
            "ordered_behavior_timestamps": True, "unique_unit_and_trial_ids": True,
            "ordered_nonoverlapping_trials": True,
            "empty_units": sum(len(s) == 0 for s in units.spike_times),
            "duplicate_spike_timestamps": int(sum(np.sum(np.diff(s) == 0) for s in units.spike_times)),
            "all_neural_bins_observed": bool(counts.valid.all()),
            "per_unit_spike_conservation_on_retained_bins": conserved,
            "spikes_outside_observation_intervals": outside_observation,
            "all_retained_trials_successful": bool(trials.success.all()),
            "m1_prefix_units_linked_to_pmd_electrodes": int(sum(
                str(unit_id).startswith("2") and table.location.iloc[0] == "PMd"
                for unit_id, table in zip(units.index, units.electrodes)
            )),
            "retained_spikes": int(counts.values.sum()),
            "spikes_excluded_by_full_bin_tail_policy": int(sum(map(len, units.spike_times)) - counts.values.sum()),
            "dropped_trial_tail_seconds": counts.dropped_tail_seconds.tolist(),
            "all_behavior_bins_valid": all(bool(mask.all()) for _, mask in aligned.values()),
        },
    }
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    Path(report_path).write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--bin-width", type=float, default=0.02, help="seconds")
    parser.add_argument("--max-gap", type=float, default=0.002, help="behavior coverage tolerance, seconds")
    args = parser.parse_args()
    report = inspect(args.manifest, bin_width=args.bin_width, max_gap=args.max_gap)
    print(json.dumps({key: report[key] for key in ["counts_shape", "behavior", "checks", "figures"]}, indent=2))


if __name__ == "__main__":
    main()
