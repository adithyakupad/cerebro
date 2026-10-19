"""Training-only peri-event summaries; unsupported residual inference is withheld."""

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess

import numpy as np

from cerebro.dataset import verify_asset
from cerebro.event_audit import condition_keys, distribution, window_reason
from cerebro.sense import align_behavior, bin_spikes, load_recording


def validate_publication_protocol(protocol):
    """Keep the fixed experiment's scientific labels consistent with calculations."""
    supported = {
        "primary_event": "go_cue_time", "secondary_event": "move_onset_time",
        "pre_seconds": -.4, "post_seconds": 1., "bin_width_seconds": .02,
        "behavior_max_gap_seconds": .002, "condition_min_repetitions": 3,
        "residual_reliability_screen_repetitions": 20,
        "baseline_seconds": [-.4, -.2], "response_seconds": [.2, .6],
        "total_covariance_bin_start_seconds": .3,
        "bootstrap_draws": 1000, "bootstrap_seed": 4,
    }
    for parameter, expected in supported.items():
        if parameter not in protocol or protocol[parameter] != expected:
            raise ValueError(f"Unsupported publication protocol parameter: {parameter}")


def relative_grid(pre, post, width):
    if not np.all(np.isfinite([pre, post, width])) or width <= 0 or pre >= post:
        raise ValueError("Finite ordered intervals and positive bin width required")
    number = round((post - pre) / width)
    if number < 1 or not np.isclose(number * width, post - pre, rtol=0, atol=1e-12):
        raise ValueError("Event interval must contain an integer number of full bins")
    return np.round(pre + np.arange(number + 1) * width, 12)


def align_training(recording, event_field, protocol):
    """Exclude incomplete trials globally, preserving original trial/event IDs."""
    pre, post, width = [protocol[k] for k in ["pre_seconds", "post_seconds", "bin_width_seconds"]]
    relative = relative_grid(pre, post, width)
    train = recording.trials[recording.trials["split"] == "train"]
    keys = condition_keys(train)
    counts = []
    velocities = []
    accepted = []
    exclusions = []
    labels = []
    events = []
    starts = []
    stops = []
    for (_, row), trial_id, key in zip(train.iterrows(), train.index, keys):
        event = row.get(event_field, np.nan)
        reason = window_reason(recording, row, event, pre, post, protocol["behavior_max_gap_seconds"])
        if reason is not None:
            exclusions.append({"trial_id": int(trial_id), "condition": key, "reason": reason})
            continue
        start, stop = np.round([event + pre, event + post], 12)
        # Snap only ≤1 ps numerical boundary discrepancies to original coverage.
        start, stop = max(start, row.start_time), min(stop, row.stop_time)
        for obs in recording.units.obs_intervals:
            matching = obs[(obs[:, 0] <= start + 1e-12) & (obs[:, 1] >= stop - 1e-12)]
            start, stop = max(start, matching[0, 0]), min(stop, matching[0, 1])
        binned = bin_spikes(recording.units.spike_times, [[start, stop]],
                            recording.units.index, [trial_id], recording.units.obs_intervals, width)
        velocity, valid = align_behavior(recording.behavior["hand_vel"], binned,
                                         max_gap=protocol["behavior_max_gap_seconds"])
        if len(binned.left) != len(relative) - 1 or not binned.valid.all() or not valid.all():
            exclusions.append({"trial_id": int(trial_id), "condition": key, "reason": "bin_coverage"})
            continue
        independent = np.array([np.sum((s >= start) & (s < stop)) for s in recording.units.spike_times])
        if not np.array_equal(binned.values.sum(axis=0), independent):
            raise ValueError("Aligned spike conservation failed")
        counts.append(binned.values)
        velocities.append(velocity)
        accepted.append(int(trial_id))
        labels.append(key)
        events.append(float(event))
        starts.append(binned.left)
        stops.append(binned.right)
    if not counts:
        raise ValueError("No training trials have complete event coverage")
    if recording.behavior["hand_vel"].unit != "m/s":
        raise ValueError("Hand velocity requires explicitly interpretable physical units")
    return {
        "counts": np.stack(counts), "hand_velocity": np.stack(velocities),
        "trial_ids": np.array(accepted), "condition_keys": np.array(labels),
        "source_event_seconds": np.array(events), "absolute_left_seconds": np.stack(starts),
        "absolute_right_seconds": np.stack(stops), "relative_edges_seconds": relative,
        "exclusions": exclusions,
    }


def condition_residuals(counts, keys, minimum=3):
    counts = np.asarray(counts, dtype=float)
    keys = np.asarray(keys)
    if counts.ndim != 3 or len(keys) != len(counts) or minimum < 2:
        raise ValueError("Trials × event bins × units and paired condition labels required")
    if not np.all(np.isfinite(counts)):
        raise ValueError("Condition summaries require complete finite counts")
    means = []
    included_keys = []
    indices = []
    expected = np.full(counts.shape, np.nan)
    for key in sorted(set(keys)):
        group = np.flatnonzero(keys == key)
        if len(group) < minimum:
            continue
        mean = counts[group].mean(axis=0)
        means.append(mean)
        included_keys.append(key)
        indices.extend(group.tolist())
        expected[group] = mean
    indices = np.array(sorted(indices), dtype=int)
    shape = (0, *counts.shape[1:])
    condition_means = np.stack(means) if means else np.empty(shape)
    condition_labels = np.array(included_keys, dtype=str)
    residuals = counts[indices] - expected[indices]
    return condition_means, condition_labels, indices, residuals


def covariance_correlation(samples):
    """Sample covariance; undefined constant-column correlations remain NaN."""
    samples = np.asarray(samples, dtype=float)
    if samples.ndim != 2 or not np.all(np.isfinite(samples)):
        raise ValueError("Finite observations × units required; no pairwise missing-data deletion")
    num_samples, num_units = samples.shape
    if num_samples < 2:
        return np.full((num_units, num_units), np.nan), np.full((num_units, num_units), np.nan)
    centered = samples - samples.mean(axis=0)
    cross_products = centered.T @ centered
    covariance = cross_products / (num_samples - 1)
    scale = np.sqrt(np.maximum(np.diag(covariance), 0))
    denominator = scale[:, None] * scale[None, :]
    correlation = np.full(covariance.shape, np.nan)
    np.divide(covariance, denominator, out=correlation, where=denominator > 0)
    return covariance, np.clip(correlation, -1, 1)


def trial_bootstrap(values, keys, draws=1000, seed=4):
    """Percentile bands from whole-trial resampling within compatible conditions."""
    values = np.asarray(values, dtype=float)
    keys = np.asarray(keys)
    if (values.ndim != 2 or len(keys) != len(values) or len(values) == 0
            or not np.all(np.isfinite(values)) or draws < 2):
        raise ValueError("Finite trial rows, matching condition labels and >=2 draws required")
    rng = np.random.default_rng(seed)
    weights = np.zeros((draws, len(values)))
    for key in sorted(set(keys)):
        group = np.flatnonzero(keys == key)
        weights[:, group] = rng.multinomial(len(group), np.full(len(group), 1 / len(group)), size=draws)
    replicates = weights @ values / len(values)
    return np.quantile(replicates, [.025, .975], axis=0)


def correlation_summary(matrix):
    pairs = matrix[np.triu_indices(len(matrix), k=1)]
    finite = pairs[np.isfinite(pairs)]
    return {"finite_pairs": len(finite), "undefined_pairs": int((~np.isfinite(pairs)).sum()),
            "coefficient_distribution": distribution(finite)}


def analyze_events(recording, protocol):
    validate_publication_protocol(protocol)
    primary = align_training(recording, protocol["primary_event"], protocol)
    secondary = align_training(recording, protocol["secondary_event"], protocol)
    counts, keys = primary["counts"], primary["condition_keys"]
    width = protocol["bin_width_seconds"]
    centers = (primary["relative_edges_seconds"][:-1] + primary["relative_edges_seconds"][1:]) / 2
    baseline = (centers >= protocol["baseline_seconds"][0]) & (centers < protocol["baseline_seconds"][1])
    response = (centers >= protocol["response_seconds"][0]) & (centers < protocol["response_seconds"][1])
    if not baseline.any() or not response.any():
        raise ValueError("Analysis epochs must contain aligned bins")
    means, included_keys, indices, residuals = condition_residuals(counts, keys, protocol["condition_min_repetitions"])
    population = counts.sum(axis=2) / width
    speed = np.linalg.norm(primary["hand_velocity"], axis=2)
    selected_units = np.arange(min(4, counts.shape[2]))  # fixed file order, no response-based selection
    response_rates = population[:, response].mean(axis=1)
    baseline_rates = population[:, baseline].mean(axis=1)
    paired_change = response_rates - baseline_rates
    selected_unit_rates = counts[:, :, selected_units] / width
    flat_unit_rates = selected_unit_rates.reshape(len(counts), -1)
    bootstrap_values = np.column_stack([population, speed, flat_unit_rates, paired_change])
    bands = trial_bootstrap(bootstrap_values, keys, protocol["bootstrap_draws"], protocol["bootstrap_seed"])
    time_bins = counts.shape[1]
    population_bands = bands[:, :time_bins]
    speed_bands = bands[:, time_bins:2 * time_bins]
    unit_bands = bands[:, 2 * time_bins:-1].reshape(2, time_bins, len(selected_units))
    secondary_population = secondary["counts"].sum(axis=2) / width
    secondary_speed = np.linalg.norm(secondary["hand_velocity"], axis=2)
    secondary_bands = trial_bootstrap(np.column_stack([secondary_population, secondary_speed]),
                                      secondary["condition_keys"], protocol["bootstrap_draws"], protocol["bootstrap_seed"])
    condition_population = means.sum(axis=2) / width
    condition_bands = []
    for i, key in enumerate(included_keys):
        group = np.flatnonzero(keys == key)
        condition_bands.append(trial_bootstrap(population[group], keys[group], protocol["bootstrap_draws"],
                                              protocol["bootstrap_seed"] + i + 1))
    tuning = means[:, response].mean(axis=1) / width
    signal_covariance, signal_correlation = covariance_correlation(tuning)
    cov_indices = np.flatnonzero(np.isclose(primary["relative_edges_seconds"][:-1],
                                          protocol["total_covariance_bin_start_seconds"], atol=1e-12, rtol=0))
    if len(cov_indices) != 1:
        raise ValueError("Covariance start must identify one exact event bin")
    covariance_bin = int(cov_indices[0])
    total_covariance, total_correlation = covariance_correlation(counts[:, covariance_bin])
    arrays = {
        "counts": counts, "rates_hz": counts / width, "trial_ids": primary["trial_ids"],
        "condition_keys": keys, "unit_ids": recording.units.index.to_numpy(),
        "source_go_cue_seconds": primary["source_event_seconds"],
        "absolute_left_seconds": primary["absolute_left_seconds"],
        "absolute_right_seconds": primary["absolute_right_seconds"],
        "relative_edges_seconds": primary["relative_edges_seconds"],
        "mean_unit_counts": counts.mean(axis=0), "mean_unit_rates_hz": counts.mean(axis=0) / width,
        "selected_unit_indices": selected_units, "selected_unit_rate_bands_hz": unit_bands,
        "population_rates_hz": population, "population_rate_bands_hz": population_bands,
        "hand_velocity_m_per_s": primary["hand_velocity"], "hand_speed_m_per_s": speed,
        "hand_speed_bands_m_per_s": speed_bands,
        "condition_mean_counts": means, "condition_mean_rates_hz": means / width,
        "included_condition_keys": included_keys, "condition_population_rates_hz": condition_population,
        "condition_population_bands_hz": np.stack(condition_bands) if condition_bands else np.empty((0, 2, time_bins)),
        "residual_counts": residuals, "residual_rates_hz": residuals / width,
        "residual_trial_ids": primary["trial_ids"][indices], "residual_condition_keys": keys[indices],
        "signal_like_covariance_hz2": signal_covariance, "signal_like_correlation": signal_correlation,
        "mixed_total_covariance_counts2": total_covariance, "mixed_total_correlation": total_correlation,
        "secondary_counts": secondary["counts"], "secondary_trial_ids": secondary["trial_ids"],
        "source_movement_onset_seconds": secondary["source_event_seconds"],
        "secondary_absolute_left_seconds": secondary["absolute_left_seconds"],
        "secondary_absolute_right_seconds": secondary["absolute_right_seconds"],
        "secondary_hand_velocity_m_per_s": secondary["hand_velocity"],
        "secondary_population_rate_bands_hz": secondary_bands[:, :time_bins],
        "secondary_hand_speed_bands_m_per_s": secondary_bands[:, time_bins:],
    }
    paired_mean_unit_change = paired_change / counts.shape[2]
    summary = {
        "protocol": protocol, "training_trial_ids": primary["trial_ids"].tolist(),
        "validation_trials_used": 0, "primary_exclusions": primary["exclusions"],
        "secondary_exclusions": secondary["exclusions"],
        "array_shapes": {k: list(v.shape) for k, v in arrays.items()},
        "included_conditions": [{"key": key, "trials": int(np.sum(keys == key))} for key in included_keys.tolist()],
        "excluded_low_repetition_trial_ids": primary["trial_ids"][~np.isin(np.arange(len(counts)), indices)].tolist(),
        "primary_retained_spikes": int(counts.sum()), "secondary_retained_spikes": int(secondary["counts"].sum()),
        "source_movement_latency_seconds": distribution(
            recording.trials.loc[primary["trial_ids"], "move_onset_time"] - primary["source_event_seconds"]),
        "mean_unit_baseline_rate_hz": float(population[:, baseline].mean() / counts.shape[2]),
        "mean_unit_response_rate_hz": float(population[:, response].mean() / counts.shape[2]),
        "paired_mean_unit_change_hz": float(paired_mean_unit_change.mean()),
        "paired_trial_change_distribution_hz": distribution(paired_mean_unit_change),
        "trials_with_positive_mean_unit_change": int(np.sum(paired_mean_unit_change > 0)),
        "paired_change_bootstrap_percentile_band_hz": (bands[:, -1] / counts.shape[2]).tolist(),
        "population_peak_bin_seconds": float(centers[np.argmax(population.mean(axis=0))]),
        "hand_speed_peak_bin_seconds": float(centers[np.argmax(speed.mean(axis=0))]),
        "signal_like_correlations": correlation_summary(signal_correlation),
        "mixed_total_correlations": correlation_summary(total_correlation),
        "signal_like_constant_unit_ids": recording.units.index[~np.isfinite(np.diag(signal_correlation))].tolist(),
        "mixed_total_constant_unit_ids": recording.units.index[~np.isfinite(np.diag(total_correlation))].tolist(),
        "covariance_bin_seconds": [float(primary["relative_edges_seconds"][covariance_bin]),
                                   float(primary["relative_edges_seconds"][covariance_bin + 1])],
        "residual_correlations": {
            "status": "not estimated: inadequate compatible-condition repetitions",
            "qualifying_conditions": int(sum(np.sum(keys == key) >= protocol["residual_reliability_screen_repetitions"] for key in set(keys))),
            "per_condition_time_covariance_rank_ceiling": int(max(np.sum(keys == key) - 1 for key in set(keys))),
            "units": counts.shape[2],
        },
        "checks": {"spike_conservation": True, "complete_training_coverage": True,
                   "validation_trials_excluded": True, "compatible_geometry_checked": True,
                   "condition_residual_zero_sum_max_absolute": float(max(
                       np.abs(residuals[keys[indices] == key].sum(axis=0)).max() for key in included_keys
                   )) if len(included_keys) else None},
    }
    return arrays, summary


def write_experiment(manifest_path, protocol_path="configs/event_04.json",
                     output="reports/event_04_results.json", tensor_path="data/processed/event_04.npz"):
    manifest = json.loads(Path(manifest_path).read_text())
    protocol = json.loads(Path(protocol_path).read_text())
    verify_asset(manifest["local_path"], manifest)
    recording = load_recording(manifest["local_path"])
    arrays, results = analyze_events(recording, protocol)
    Path(tensor_path).parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(tensor_path, **arrays)
    results["tensor_path"] = str(tensor_path)
    results["tensor_array_sha256"] = {k: hashlib.sha256(v.tobytes()).hexdigest() for k, v in arrays.items()}
    results["provenance"] = manifest
    results["recording_metadata"] = recording.metadata
    results["hand_velocity_unit"] = recording.behavior["hand_vel"].unit
    results["git_revision"] = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    results["source_sha256"] = {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                                for name in ["event_aligned.py", "event_audit.py", "sense.py"]}
    results["environment"] = {name: importlib.metadata.version(name) for name in ["numpy", "pynwb", "matplotlib"]}
    results["interpretation"] = {
        "binning": "20ms half-open observation intervals; bins labeled by centers are acausal summaries; no smoothing",
        "bootstrap": "1000 stratified whole-trial resamples, seed 4; pointwise percentile bands, not simultaneous or calibrated for n=2–3",
        "condition_means": "training-only condition × event-time expectations; in-sample residuals centered by construction",
        "signal_like": "Pearson across compatible-condition response-epoch means; few-repetition means contain estimation noise",
        "mixed_total": "simultaneous counts across training trials at fixed event bin; mixes condition-dependent signal and residual variation",
        "residual": "no residual correlation matrix estimated; maximum per-condition rank 2 for 142 units",
        "causality": "correlation/covariance and peak ordering do not establish causal connectivity or neural lead/lag",
    }
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(json.dumps(results, indent=2, sort_keys=True, allow_nan=False) + "\n")
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--protocol", default="configs/event_04.json")
    args = parser.parse_args()
    results = write_experiment(args.manifest, args.protocol)
    print(json.dumps({k: results[k] for k in ["primary_retained_spikes", "paired_mean_unit_change_hz", "residual_correlations", "primary_exclusions"]}, indent=2))


if __name__ == "__main__":
    main()
