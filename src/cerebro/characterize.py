"""Descriptive count statistics on identical trials, with matched exposure."""

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys

import numpy as np

from cerebro.dataset import verify_asset
from cerebro.sense import bin_spikes, load_recording, validate_intervals


WIDTHS = (0.005, 0.02, 0.05)
METADATA_SOURCE = "https://neurallatents.github.io/datasets.html"


def count_statistics(values, durations):
    """Observed nonnegative integer counts; -1 is missing, not zero.

    Variance uses ddof=1; Fano = variance / mean across observed temporal bins.
    Undefined statistics use None, including zero-mean Fano and n < 2 variance.
    """
    values = np.asarray(values)
    durations = np.asarray(durations, dtype=float)
    if values.ndim != 1 or durations.shape != values.shape:
        raise ValueError("Counts and durations must be paired one-dimensional arrays")
    if (not np.all(np.isfinite(values)) or np.any(values < -1)
            or np.any(values != np.floor(values))
            or not np.all(np.isfinite(durations)) or np.any(durations <= 0)):
        raise ValueError("Counts must be integers >= -1 and durations positive seconds")
    observed = values >= 0
    samples = values[observed]
    exposure = durations[observed]
    n = len(samples)
    if n == 0:
        return {"observed_bins": 0, "spikes": 0, "exposure_seconds": 0.0,
                "zero_fraction": None, "mean_count": None, "count_variance": None,
                "fano_across_time": None, "mean_rate_hz": None,
                "count_histogram": [], "bin_rate_quantiles_hz": None}
    mean = float(samples.mean())
    variance = float(samples.var(ddof=1)) if n >= 2 else None
    # Fano comparisons are defined only for equal-duration observations.
    if not np.allclose(exposure, exposure[0], rtol=0, atol=1e-12):
        raise ValueError("Fano count statistics require equal-duration bins")
    unique, frequencies = np.unique(samples, return_counts=True)
    return {
        "observed_bins": n, "spikes": int(samples.sum()),
        "exposure_seconds": float(exposure.sum()),
        "zero_fraction": float(np.mean(samples == 0)),
        "mean_count": mean, "count_variance": variance,
        "fano_across_time": variance / mean if variance is not None and mean > 0 else None,
        "mean_rate_hz": float(samples.sum() / exposure.sum()),
        "count_histogram": [[int(k), int(v)] for k, v in zip(unique, frequencies)],
        "bin_rate_quantiles_hz": np.quantile(samples / exposure, [0, .25, .5, .75, 1]).tolist(),
    }


def summarize(counts):
    durations = counts.right - counts.left
    per_unit = []
    for unit_index, unit_id in enumerate(counts.unit_ids):
        unit_counts = counts.values[:, unit_index]
        unit_statistics = count_statistics(unit_counts, durations)
        per_unit.append(dict(unit_id=int(unit_id), **unit_statistics))
    population = np.where(counts.valid.all(axis=1), counts.values.sum(axis=1), -1)
    observed = counts.values[counts.valid]
    histogram = np.unique(observed, return_counts=True)
    return {
        "shape": list(counts.values.shape), "per_unit": per_unit,
        "valid_cells": int(counts.valid.sum()),
        "zero_fraction": float(np.mean(observed == 0)) if len(observed) else None,
        "population": count_statistics(population, durations),
        "pooled_count_histogram": [[int(k), int(v)] for k, v in zip(*histogram)],
    }


def matched_intervals(intervals, widths=WIDTHS):
    """Trim each trial to a common endpoint on the LCM grid in integer µs."""
    intervals = validate_intervals(intervals)
    ticks = np.rint(np.asarray(widths) * 1_000_000).astype(np.int64)
    if len(ticks) == 0 or np.any(ticks <= 0) or not np.allclose(ticks / 1_000_000, widths, atol=1e-12, rtol=0):
        raise ValueError("Widths must be positive integer microseconds")
    quantum = int(np.lcm.reduce(ticks)) / 1_000_000
    result = intervals.copy()
    number = np.floor((intervals[:, 1] - intervals[:, 0]) / quantum + 1e-10)
    result[:, 1] = np.round(intervals[:, 0] + number * quantum, 12)
    result[:, 1] = np.minimum(result[:, 1], intervals[:, 1])
    if np.any(result[:, 1] <= result[:, 0]):
        raise ValueError("A trial is shorter than the common grid; define a trial policy explicitly")
    return result, quantum


def metadata_audit(recording):
    """Compare unmodified electrode links to the publisher's unit-ID convention."""
    rows = []
    for unit_id, unit in recording.units.iterrows():
        prefix = str(unit_id)[0]
        documented_area = {"1": "PMd", "2": "M1"}.get(prefix)
        electrodes = unit.electrodes
        stored_ids = [int(i) for i in electrodes.index]
        locations = electrodes.location.astype(str).tolist()
        proposed = [i + 96 for i in stored_ids] if prefix == "2" else stored_ids
        proposed_locations = []
        for i in proposed:
            if recording.electrodes is not None and i in recording.electrodes.index:
                proposed_locations.append(str(recording.electrodes.loc[i, "location"]))
            else:
                proposed_locations.append(None)
        rows.append({
            "unit_id": int(unit_id), "prefix": prefix,
            "area_from_publisher_convention": documented_area,
            "stored_electrode_ids": stored_ids, "stored_locations": locations,
            "publisher_plus96_candidate_ids": proposed if prefix == "2" else None,
            "candidate_locations": proposed_locations if prefix == "2" else None,
            "stored_link_conflicts_with_convention": bool(documented_area is not None
                                                           and any(a != documented_area for a in locations)),
        })
    return {
        "authoritative_source": METADATA_SOURCE,
        "publisher_note": "Prefix 1 denotes PMd, 2 denotes M1; publisher documents M1 indices shifted by +96",
        "raw_metadata_modified": False,
        "conflicting_units": sum(r["stored_link_conflicts_with_convention"] for r in rows),
        "m1_candidates_all_link_to_m1": all(
            bool(r["candidate_locations"]) and all(a == "M1" for a in r["candidate_locations"])
            for r in rows if r["prefix"] == "2"
        ),
        "units": rows,
        "limitations": "Candidate +96 links reproduce the publisher convention, not independent anatomical verification; no corrections applied.",
    }


def analyze(recording, widths=WIDTHS):
    """All source trials, no fitted transform; separate native/matched coverage."""
    trials, units = recording.trials, recording.units
    source = trials[["start_time", "stop_time"]].to_numpy()
    common, quantum = matched_intervals(source, widths)
    trial_spike_totals = []
    for start, stop in source:
        unit_spike_totals = []
        for spike_times in units.spike_times:
            stop_index = np.searchsorted(spike_times, stop, side="left")
            start_index = np.searchsorted(spike_times, start, side="left")
            unit_spike_totals.append(stop_index - start_index)
        trial_spike_totals.append(unit_spike_totals)
    raw_per_trial = np.array(trial_spike_totals, dtype=np.int64)
    results = {}
    matched_unit_totals = []
    for width in widths:
        entry = {}
        for label, intervals in [("native", source), ("matched", common)]:
            counts = bin_spikes(units.spike_times, intervals, units.index, trials.index,
                                units.obs_intervals, width)
            if not counts.valid.all():
                raise ValueError("Characterization requires fully observed bins; choose a missing-coverage policy")
            summary = summarize(counts)
            summary["trials"] = []
            expected = np.zeros(len(units), dtype=np.int64)
            for k, trial_id in enumerate(trials.index):
                mask = counts.trial_ids == trial_id
                left, right = counts.left[mask], counts.right[mask]
                observed = counts.values[mask]
                duration = right - left
                actual = observed.sum(axis=0)
                independent = np.array([
                    np.searchsorted(s, right[-1], side="left") - np.searchsorted(s, left[0], side="left")
                    if len(left) else 0 for s in units.spike_times
                ])
                if not np.array_equal(actual, independent):
                    raise ValueError("Per-trial, per-unit spike conservation failed")
                expected += independent
                summary["trials"].append({
                    "trial_id": int(trial_id), "split": str(trials.iloc[k]["split"]),
                    "complete_bins": int(mask.sum()), "source_spikes": int(raw_per_trial[k].sum()),
                    "retained_spikes": int(actual.sum()),
                    "excluded_spikes": int(raw_per_trial[k].sum() - actual.sum()),
                    "retained_interval_seconds": [float(left[0]), float(right[-1])] if len(left) else None,
                    "retained_seconds": float(duration.sum()),
                    "excluded_seconds": float(source[k, 1] - source[k, 0] - duration.sum()),
                    "zero_fraction": float(np.mean(observed == 0)) if observed.size else None,
                    "population": count_statistics(observed.sum(axis=1), duration),
                })
            if not np.array_equal(expected, counts.values.sum(axis=0)):
                raise ValueError("Per-unit pooled spike conservation failed")
            summary["excluded_spikes"] = int(raw_per_trial.sum() - expected.sum())
            summary["excluded_per_unit"] = (raw_per_trial.sum(axis=0) - expected).tolist()
            summary["per_trial_per_unit_excluded_spikes"] = [
                (raw_per_trial[k] - counts.values[counts.trial_ids == trial_id].sum(axis=0)).tolist()
                for k, trial_id in enumerate(trials.index)
            ]
            summary["conservation_passed"] = True
            if label == "matched":
                matched_unit_totals.append(expected)
            entry[label] = summary
        results[f"{width * 1000:g}ms"] = entry
    if not all(np.array_equal(v, matched_unit_totals[0]) for v in matched_unit_totals):
        raise ValueError("Matched coverage does not conserve identical source spikes across widths")
    return {
        "trial_ids": [int(i) for i in trials.index], "unit_ids": [int(i) for i in units.index],
        "raw_spikes_in_trials": int(raw_per_trial.sum()),
        "source_intervals_seconds": source.tolist(), "matched_intervals_seconds": common.tolist(),
        "matched_grid_seconds": quantum,
        "heldout_unit_flags": units.heldout.to_numpy(dtype=bool).tolist(),
        "widths": results, "matched_source_spikes_identical": True,
        "metadata_audit": metadata_audit(recording),
    }


def write_report(manifest_path, output="reports/signal_characterization.json"):
    manifest = json.loads(Path(manifest_path).read_text())
    verify_asset(manifest["local_path"], manifest)
    recording = load_recording(manifest["local_path"])
    results = analyze(recording)
    results["provenance"] = manifest
    results["recording_identifier"] = recording.metadata["identifier"]
    results["python_version"] = sys.version
    results["environment"] = {name: importlib.metadata.version(name) for name in ["numpy", "pynwb", "matplotlib"]}
    results["git_revision"] = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    results["analysis_worktree_dirty"] = bool(subprocess.check_output(
        ["git", "status", "--porcelain"], text=True).strip())
    results["analysis_source_sha256"] = {
        name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
        for name in ["characterize.py", "sense.py", "dataset.py"]
    }
    results["definitions"] = {
        "sparsity": "observed zero-count cells / observed cells; -1 is missing",
        "mean_rate_hz": "total spikes / total observed seconds for each unit",
        "variance": "sample variance of counts across equal-duration temporal bins, ddof=1",
        "fano": "sample count variance / mean count; null if mean=0 or fewer than 2 bins",
        "population": "sum of counts over all 142 units; rate in population spikes/s",
        "coverage": "native full bins versus common trial endpoints on 100ms grid",
        "nonstationarity": "bins mix task epochs, conditions, and train/val trials; descriptive Fano is not repeated-trial noise variability",
    }
    # No wall-clock timestamp: unchanged data/code/environment serialize identically.
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(json.dumps(results, indent=2, sort_keys=True, allow_nan=False) + "\n")
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", default="reports/signal_characterization.json")
    args = parser.parse_args()
    results = write_report(args.manifest, args.output)
    print(json.dumps({key: {"bins": data["native"]["shape"][0],
                           "zero_fraction": data["native"]["zero_fraction"],
                           "excluded_spikes": data["native"]["excluded_spikes"]}
                      for key, data in results["widths"].items()}, indent=2))


if __name__ == "__main__":
    main()
