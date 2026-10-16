"""Frozen, descriptive Brochier event-aligned population analysis."""

import hashlib
import importlib.metadata
import json
import argparse
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA

from cerebro.dataset import verify_asset
from cerebro.event_aligned import condition_residuals, covariance_correlation
from tools.audit_brochier import RAW_DIR, covered, read_sorting_counts, read_trials, sampled_intervals
from tools.run_brochier_transfer import single_unit_indices


CONFIG_PATH = Path("configs/brochier_population_20.json")
PROTOCOL_PATH = Path("docs/research/mission_020_protocol.md")
REPORT_PATH = Path("reports/mission_020_brochier_population.json")
TENSOR_PATH = Path("data/processed/brochier_population_20.npz")
FIGURE_DIR = Path("reports/figures")
EXPECTED_CONFIG = {
    "dataset_manifest": "docs/datasets/mission_019_brochier_assets.json",
    "event": "SR",
    "conditions": ["SGLF", "SGHF", "PGLF", "PGHF"],
    "performance_code": 255,
    "pre_ticks": 6000,
    "post_ticks": 12000,
    "bin_ticks": 600,
    "tick_rate_hz": 30000,
    "condition_min_trials": 20,
    "fano_min_mean_post_count": 1.0,
    "bootstrap_draws": 300,
    "permutation_draws": 200,
    "random_seed": 20020,
}


def validate_config(config):
    if config != EXPECTED_CONFIG:
        raise ValueError("Mission 020 configuration differs from the committed protocol")


def file_sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def window_counts(unit_spikes, event_tick, config):
    """Half-open native-tick bins with units ordered by source odML."""
    bin_count = (config["pre_ticks"] + config["post_ticks"]) // config["bin_ticks"]
    first_tick = event_tick - config["pre_ticks"]
    edges = first_tick + np.arange(bin_count + 1, dtype=np.int64) * config["bin_ticks"]
    columns = []
    for timestamps in unit_spikes:
        timestamps = np.asarray(timestamps, dtype=np.int64)
        if np.any(np.diff(timestamps) < 0):
            raise ValueError("Native spike ticks must be ordered")
        edge_positions = np.searchsorted(timestamps, edges, side="left")
        bin_counts = np.diff(edge_positions)
        columns.append(bin_counts)
    counts = np.column_stack(columns)
    if counts.shape != (bin_count, len(unit_spikes)):
        raise ValueError("Binned trial dimensions differ from protocol")
    if np.any(counts < 0) or not np.issubdtype(counts.dtype, np.integer):
        raise ValueError("Spike counts must be nonnegative integers")
    return counts


def load_session(session, manifest, config):
    """Check original assets and construct trials × bins × source SUAs."""
    from neo.rawio import BlackrockRawIO

    prefix = session["id"]
    sorted_name = session["sorted_nev"]
    raw_name = session["neural_nsx"]
    odml_name = f"{prefix}.odml"
    required = (sorted_name, raw_name, odml_name)
    verified = {}
    for name in required:
        verified[name] = verify_asset(RAW_DIR / name, manifest["assets"][name])

    sorted_prefix = sorted_name.removesuffix(".nev")
    reader = BlackrockRawIO(
        filename=str(RAW_DIR / prefix),
        nev_override=str(RAW_DIR / sorted_prefix),
        nsx_to_load=session["neural_stream"],
    )
    reader.parse_header()
    if reader.segment_count(0) != 1:
        raise ValueError("Frozen analysis requires one recorded neural segment")
    neural_rate, intervals = sampled_intervals(reader)
    event_rate = int(reader._nev_basic_header["timestamp_resolution"])
    if neural_rate != config["tick_rate_hz"] or event_rate != config["tick_rate_hz"]:
        raise ValueError("Native neural/event clock differs from protocol")
    event_ticks, _, _ = reader.get_event_timestamps(0, 0, 0)
    native_event_ticks = set(int(tick) for tick in event_ticks)

    odml_path = RAW_DIR / odml_name
    unit_indices = single_unit_indices(odml_path, reader.header["spike_channels"])
    unit_ids = [str(reader.header["spike_channels"][index]["name"]) for index in unit_indices]
    sorting_version = sorted_prefix.removeprefix(prefix)
    sorting_counts = read_sorting_counts(odml_path, sorting_version)
    if len(unit_ids) != sorting_counts["single_units"]:
        raise ValueError("Selected SUAs disagree with source sorting summary")
    unit_spikes = [reader.get_spike_timestamps(0, 0, index) for index in unit_indices]

    eligible = []
    exclusions = {}
    for trial in read_trials(odml_path):
        label = trial["condition"]
        events = trial["events_ticks"]
        reason = None
        if trial["performance_code"] != config["performance_code"] or label not in config["conditions"]:
            reason = "not_correct_four_condition"
        elif events.get(config["event"], -1) < 0:
            reason = "missing_source_event"
        elif events[config["event"]] not in native_event_ticks:
            reason = "source_event_not_in_nev"
        else:
            event_tick = events[config["event"]]
            first_tick = event_tick - config["pre_ticks"]
            final_tick = event_tick + config["post_ticks"]
            if events.get("TS-ON", -1) > first_tick or events.get("STOP", -1) < final_tick:
                reason = "window_crosses_trial_boundary"
            elif not covered(intervals, first_tick / event_rate, final_tick / event_rate):
                reason = "raw_neural_samples_missing"
        if reason is not None:
            exclusions[reason] = exclusions.get(reason, 0) + 1
            continue
        counts = window_counts(unit_spikes, event_tick, config)
        first_tick = event_tick - config["pre_ticks"]
        final_tick = event_tick + config["post_ticks"]
        source_spike_total = sum(
            int(np.count_nonzero((spikes >= first_tick) & (spikes < final_tick)))
            for spikes in unit_spikes
        )
        if counts.sum() != source_spike_total:
            raise ValueError("Native-window spikes were lost during binning")
        eligible.append((event_tick, trial["id"], label, counts))

    eligible.sort(key=lambda row: row[0])
    if not eligible:
        raise ValueError("No source trials have complete neural coverage")
    labels = np.asarray([row[2] for row in eligible])
    trial_ids = np.asarray([row[1] for row in eligible], dtype=np.int64)
    event_ticks = np.asarray([row[0] for row in eligible], dtype=np.int64)
    counts = np.stack([row[3] for row in eligible])
    if len(np.unique(trial_ids)) != len(trial_ids):
        raise ValueError("Eligible source trial identities are not unique")
    for condition in config["conditions"]:
        if np.sum(labels == condition) < config["condition_min_trials"]:
            raise ValueError("A source condition has insufficient repetitions")
    return {
        "subject": session["subject"],
        "counts": counts,
        "labels": labels,
        "trial_ids": trial_ids,
        "event_ticks": event_ticks,
        "unit_ids": np.asarray(unit_ids),
        "intervals": intervals,
        "verified_assets": verified,
        "exclusions": exclusions,
    }


def fano_by_condition(counts, labels, config):
    """Across-trial variance/mean of complete 400-ms post-event counts."""
    pre_bins = config["pre_ticks"] // config["bin_ticks"]
    post_totals = counts[:, pre_bins:, :].sum(axis=1)
    factors = np.full((len(config["conditions"]), counts.shape[2]), np.nan)
    below_threshold = 0
    for condition_index, condition in enumerate(config["conditions"]):
        selected = post_totals[labels == condition]
        mean_counts = selected.mean(axis=0)
        variance_counts = selected.var(axis=0, ddof=1)
        eligible = mean_counts >= config["fano_min_mean_post_count"]
        factors[condition_index, eligible] = variance_counts[eligible] / mean_counts[eligible]
        below_threshold += int(np.sum(~eligible))
    return factors, below_threshold


def signal_participation(condition_means):
    """Descriptive effective rank of condition×time expected rate vectors."""
    observations = condition_means.reshape(-1, condition_means.shape[-1])
    centered = observations - observations.mean(axis=0)
    gram = centered @ centered.T
    eigenvalues = np.linalg.eigvalsh(gram)
    eigenvalues = np.maximum(eigenvalues, 0)
    eigen_sum = eigenvalues.sum()
    squared_sum = np.square(eigenvalues).sum()
    if squared_sum == 0:
        return float("nan")
    return float(eigen_sum ** 2 / squared_sum)


def pair_summary(correlation):
    upper = correlation[np.triu_indices_from(correlation, k=1)]
    finite = upper[np.isfinite(upper)]
    if len(finite) == 0:
        return {"finite_pairs": 0, "undefined_pairs": len(upper),
                "median_signed": None, "median_absolute": None}
    return {
        "finite_pairs": int(len(finite)),
        "undefined_pairs": int(len(upper) - len(finite)),
        "median_signed": float(np.median(finite)),
        "median_absolute": float(np.median(np.abs(finite))),
    }


def shared_variance_ratio(trial_residual_rates):
    """Population-mean variance relative to diagonal-only unit variances."""
    observations = np.asarray(trial_residual_rates, dtype=float)
    if observations.ndim != 2 or len(observations) < 2 or not np.isfinite(observations).all():
        raise ValueError("Finite trial × unit residual rates required")
    unit_count = observations.shape[1]
    unit_variances = observations.var(axis=0, ddof=1)
    independent_reference = unit_variances.sum() / unit_count ** 2
    if independent_reference <= 0:
        return float("nan")
    population_variance = observations.mean(axis=1).var(ddof=1)
    return float(population_variance / independent_reference)


def scalar_statistics(counts, labels, config):
    """Compute only prespecified session-level descriptive scalars."""
    bin_seconds = config["bin_ticks"] / config["tick_rate_hz"]
    pre_bins = config["pre_ticks"] // config["bin_ticks"]
    rates = counts / bin_seconds
    pre_trial_rates = rates[:, :pre_bins].mean(axis=(1, 2))
    post_trial_rates = rates[:, pre_bins:].mean(axis=(1, 2))
    paired_changes = post_trial_rates - pre_trial_rates

    expected_counts, expected_labels, indices, residual_counts = condition_residuals(
        counts, labels, config["condition_min_trials"]
    )
    if not np.array_equal(indices, np.arange(len(counts))):
        raise ValueError("Condition residuals excluded an eligible trial")
    condition_means = np.stack([
        expected_counts[np.flatnonzero(expected_labels == condition)[0]] / bin_seconds
        for condition in config["conditions"]
    ])
    residual_rate_trials = residual_counts[:, pre_bins:].mean(axis=1) / bin_seconds
    _, signal_correlation = covariance_correlation(condition_means.reshape(-1, counts.shape[2]))
    _, residual_correlation = covariance_correlation(residual_rate_trials)
    fano_factors, below_threshold = fano_by_condition(counts, labels, config)
    finite_fano = fano_factors[np.isfinite(fano_factors)]
    fano_median = float(np.median(finite_fano)) if len(finite_fano) else float("nan")
    signal_dimension = signal_participation(condition_means)
    shared_ratio = shared_variance_ratio(residual_rate_trials)
    residual_pairs = pair_summary(residual_correlation)
    return {
        "paired_rate_change_hz": float(paired_changes.mean()),
        "fano_median": fano_median,
        "fano_eligible_cells": int(len(finite_fano)),
        "fano_below_threshold_cells": below_threshold,
        "signal_participation_ratio": signal_dimension,
        "residual_median_absolute_correlation": residual_pairs["median_absolute"],
        "residual_shared_variance_ratio": shared_ratio,
        "signal_pairs": pair_summary(signal_correlation),
        "residual_pairs": residual_pairs,
        "signal_correlation": signal_correlation,
        "residual_correlation": residual_correlation,
        "condition_means_hz": condition_means,
        "fano_factors": fano_factors,
        "residual_rate_trials_hz": residual_rate_trials,
        "residual_count_sum_max": float(max(
            np.abs(residual_counts[labels == condition].sum(axis=0)).max()
            for condition in config["conditions"]
        )),
    }


def bootstrap_statistics(counts, labels, config, seed):
    """Resample whole trials within condition; never treat bins as replicates."""
    rng = np.random.default_rng(seed)
    conditions = config["conditions"]
    group_indices = [np.flatnonzero(labels == condition) for condition in conditions]
    metric_names = (
        "paired_rate_change_hz", "fano_median", "signal_participation_ratio",
        "residual_median_absolute_correlation", "residual_shared_variance_ratio",
    )
    metric_draws = {name: [] for name in metric_names}
    trajectory_draws = []
    for _ in range(config["bootstrap_draws"]):
        selected_groups = [
            rng.choice(group, size=len(group), replace=True) for group in group_indices
        ]
        selected_indices = np.concatenate(selected_groups)
        sampled_counts = counts[selected_indices]
        sampled_labels = labels[selected_indices]
        estimates = scalar_statistics(sampled_counts, sampled_labels, config)
        for name in metric_names:
            metric_draws[name].append(estimates[name])
        population_trajectories = estimates["condition_means_hz"].mean(axis=2)
        trajectory_draws.append(population_trajectories)

    intervals = {}
    for name, values in metric_draws.items():
        finite = np.asarray(values, dtype=float)
        finite = finite[np.isfinite(finite)]
        intervals[name] = {
            "finite_draws": int(len(finite)),
            "undefined_draws": int(config["bootstrap_draws"] - len(finite)),
            "percentile_95": np.quantile(finite, [0.025, 0.975]).tolist()
            if len(finite) >= 20 else None,
        }
    trajectory_array = np.stack(trajectory_draws)
    trajectory_bands = np.quantile(trajectory_array, [0.025, 0.975], axis=0)
    return intervals, trajectory_bands


def permutation_reference(residual_rates, labels, config, seed):
    """Independently shuffle each unit's whole-trial residuals within condition."""
    rng = np.random.default_rng(seed)
    groups = [np.flatnonzero(labels == condition) for condition in config["conditions"]]
    absolute_correlations = []
    shared_ratios = []
    for _ in range(config["permutation_draws"]):
        shuffled = np.empty_like(residual_rates)
        for group in groups:
            within_condition = residual_rates[group]
            random_keys = rng.random(within_condition.shape)
            orders = np.argsort(random_keys, axis=0)
            shuffled[group] = np.take_along_axis(within_condition, orders, axis=0)
        _, correlation = covariance_correlation(shuffled)
        absolute_correlations.append(pair_summary(correlation)["median_absolute"])
        shared_ratios.append(shared_variance_ratio(shuffled))
    return {
        "median_absolute_residual_correlation": np.quantile(
            absolute_correlations, [0.025, 0.5, 0.975]
        ).tolist(),
        "shared_variance_ratio": np.quantile(
            shared_ratios, [0.025, 0.5, 0.975]
        ).tolist(),
    }


def half_session_shared_ratios(residual_rates, labels, config):
    """Simple chronological sensitivity, retaining the condition strata."""
    midpoint = len(labels) // 2
    results = {}
    for name, subset in (("early", slice(None, midpoint)), ("late", slice(midpoint, None))):
        half_rates = residual_rates[subset].copy()
        half_labels = labels[subset]
        for condition in config["conditions"]:
            group = half_labels == condition
            if not np.any(group):
                raise ValueError("Chronological half lacks a source condition")
            half_rates[group] -= half_rates[group].mean(axis=0)
        results[name] = {
            "trial_count": len(half_rates),
            "shared_variance_ratio": shared_variance_ratio(half_rates),
        }
    return results


def trajectory_coordinates(counts, labels, condition_means, config):
    """Fit descriptive PCA on condition means only, project fixed early trials."""
    observations = condition_means.reshape(-1, counts.shape[2])
    pca = PCA(n_components=2, svd_solver="full")
    pca.fit(observations)
    condition_coordinates = pca.transform(observations).reshape(4, 30, 2)
    bin_seconds = config["bin_ticks"] / config["tick_rate_hz"]
    selected = {}
    for condition in config["conditions"]:
        indices = np.flatnonzero(labels == condition)[:3]
        rates = counts[indices] / bin_seconds
        projected = pca.transform(rates.reshape(-1, rates.shape[2]))
        selected[condition] = {"indices": indices.tolist(),
                               "coordinates": projected.reshape(len(indices), 30, 2)}
    return condition_coordinates, selected, pca.explained_variance_ratio_


def finite_correlation_pairs(matrix):
    pairs = matrix[np.triu_indices_from(matrix, k=1)]
    return pairs[np.isfinite(pairs)]


def plot_figures(sessions, figure_dir, config):
    """Export three labeled, source-attributed figures in PNG and vector PDF."""
    figure_dir.mkdir(parents=True, exist_ok=True)
    colors = {"SGLF": "#0072B2", "SGHF": "#D55E00", "PGLF": "#009E73", "PGHF": "#CC79A7"}
    bin_seconds = config["bin_ticks"] / config["tick_rate_hz"]
    relative_edges = np.arange(-config["pre_ticks"], config["post_ticks"] + 1,
                               config["bin_ticks"]) / config["tick_rate_hz"]
    relative_centers = relative_edges[:-1] + bin_seconds / 2
    figure_paths = []

    figure, axes = plt.subplots(2, 1, figsize=(8, 7), sharex=True, constrained_layout=True)
    for axis, (subject, result) in zip(axes, sessions.items()):
        means = result["statistics"]["condition_means_hz"].mean(axis=2)
        bands = result["trajectory_bands"]
        for condition_index, condition in enumerate(config["conditions"]):
            color = colors[condition]
            axis.plot(relative_centers, means[condition_index], label=condition, color=color)
            axis.fill_between(relative_centers, bands[0, condition_index],
                              bands[1, condition_index], color=color, alpha=0.13)
        axis.axvline(0, color="black", linewidth=0.8)
        axis.set_ylabel("Mean single-unit rate (spikes/s)")
        axis.set_title(f"Animal {subject}: recorded table-switch release (SR); {len(result['data']['counts'])} trials")
        axis.legend(ncol=4, fontsize=8)
    axes[-1].set_xlabel("Time from SR (s); 20-ms bins")
    figure.suptitle("Brochier condition-aligned population activity; shaded: trial-bootstrap 95% bands\n"
                     "doi:10.12751/g-node.f83565; conditional trial uncertainty, not subject uncertainty",
                     fontsize=11)
    for extension in ("png", "pdf"):
        path = figure_dir / f"mission_020_brochier_rates.{extension}"
        figure.savefig(path, dpi=220)
        figure_paths.append(str(path))
    plt.close(figure)

    figure, axes = plt.subplots(2, 2, figsize=(10, 7), constrained_layout=True)
    for row_index, (subject, result) in enumerate(sessions.items()):
        statistics = result["statistics"]
        fano = statistics["fano_factors"]
        finite_fano = fano[np.isfinite(fano)]
        axes[row_index, 0].hist(finite_fano, bins=25, color="#0072B2", alpha=0.8)
        axes[row_index, 0].set_xlabel("400-ms post-SR Fano factor (count variance / mean)")
        axes[row_index, 0].set_ylabel("Condition × unit cells")
        axes[row_index, 0].set_title(f"Animal {subject}: trial-count variability; mean count ≥ 1")
        signal_pairs = finite_correlation_pairs(statistics["signal_correlation"])
        residual_pairs = finite_correlation_pairs(statistics["residual_correlation"])
        axes[row_index, 1].hist(signal_pairs, bins=30, range=(-1, 1), alpha=0.55,
                                label="condition × time means", color="#D55E00", density=True)
        axes[row_index, 1].hist(residual_pairs, bins=30, range=(-1, 1), alpha=0.55,
                                label="trial residuals", color="#009E73", density=True)
        axes[row_index, 1].set_xlabel("Pairwise Pearson correlation (descriptive)")
        axes[row_index, 1].set_ylabel("Pair density")
        axes[row_index, 1].set_title(f"Animal {subject}: signal-like vs residual correlation")
        axes[row_index, 1].legend(fontsize=7)
    figure.suptitle("Brochier post-SR count variability and unit-pair correlations\n"
                     "doi:10.12751/g-node.f83565; dependent pairs; rank-limited covariance; no connectivity claim",
                     fontsize=11)
    for extension in ("png", "pdf"):
        path = figure_dir / f"mission_020_brochier_variability.{extension}"
        figure.savefig(path, dpi=220)
        figure_paths.append(str(path))
    plt.close(figure)

    figure, axes = plt.subplots(1, 2, figsize=(10, 4.5), constrained_layout=True)
    for axis, (subject, result) in zip(axes, sessions.items()):
        condition_coordinates = result["condition_coordinates"]
        selected = result["selected_trajectories"]
        for condition_index, condition in enumerate(config["conditions"]):
            color = colors[condition]
            for path in selected[condition]["coordinates"]:
                axis.plot(path[:, 0], path[:, 1], color=color, alpha=0.16, linewidth=0.8)
            path = condition_coordinates[condition_index]
            axis.plot(path[:, 0], path[:, 1], color=color, linewidth=2, label=condition)
            axis.scatter(path[10, 0], path[10, 1], color=color, s=20)
        axis.set_xlabel("Condition-mean PC1 coordinate (spikes/s)")
        axis.set_ylabel("Condition-mean PC2 coordinate (spikes/s)")
        axis.set_title(f"Animal {subject}: dot = first post-SR bin; faint = 3 trials/class", fontsize=10)
        axis.legend(fontsize=7)
    figure.suptitle("Descriptive trajectories; PCA fit on all condition means\n"
                     "doi:10.12751/g-node.f83565; descriptive projection, not held-out dynamics",
                     fontsize=11)
    for extension in ("png", "pdf"):
        path = figure_dir / f"mission_020_brochier_trajectories.{extension}"
        figure.savefig(path, dpi=220)
        figure_paths.append(str(path))
    plt.close(figure)
    return figure_paths


def analyze_session(data, config, seed):
    counts = data["counts"]
    labels = data["labels"]
    statistics = scalar_statistics(counts, labels, config)
    intervals, trajectory_bands = bootstrap_statistics(counts, labels, config, seed)
    shuffled = permutation_reference(statistics["residual_rate_trials_hz"], labels, config, seed + 1)
    halves = half_session_shared_ratios(statistics["residual_rate_trials_hz"], labels, config)
    coordinates, selected, explained = trajectory_coordinates(
        counts, labels, statistics["condition_means_hz"], config
    )
    return {
        "data": data,
        "statistics": statistics,
        "bootstrap": intervals,
        "trajectory_bands": trajectory_bands,
        "shuffle_reference": shuffled,
        "chronological_halves": halves,
        "condition_coordinates": coordinates,
        "selected_trajectories": selected,
        "pca_explained_variance_ratio": explained,
    }


def json_session(result, config):
    data = result["data"]
    statistics = result["statistics"]
    labels = data["labels"]
    unit_count = len(data["unit_ids"])
    condition_counts = {
        condition: int(np.sum(labels == condition)) for condition in config["conditions"]
    }
    condition_rank_ceiling = {
        condition: min(trials - 1, unit_count) for condition, trials in condition_counts.items()
    }
    numeric_metrics = (
        "paired_rate_change_hz", "fano_median", "fano_eligible_cells",
        "fano_below_threshold_cells", "signal_participation_ratio",
        "residual_median_absolute_correlation", "residual_shared_variance_ratio",
        "residual_count_sum_max",
    )
    summary = {name: statistics[name] for name in numeric_metrics}
    summary["pre_mean_unit_rate_hz"] = float(data["counts"][:, :10].mean() / 0.02)
    summary["post_mean_unit_rate_hz"] = float(data["counts"][:, 10:].mean() / 0.02)
    summary["signal_pairs"] = statistics["signal_pairs"]
    summary["residual_pairs"] = statistics["residual_pairs"]
    summary["pca_explained_variance_ratio"] = result["pca_explained_variance_ratio"].tolist()
    return {
        "subject": data["subject"],
        "tensor_shape_trials_bins_units": list(data["counts"].shape),
        "tensor_sha256": hashlib.sha256(data["counts"].tobytes()).hexdigest(),
        "trial_ids": data["trial_ids"].tolist(),
        "source_event_ticks": data["event_ticks"].tolist(),
        "unit_ids": data["unit_ids"].tolist(),
        "condition_counts": condition_counts,
        "condition_rank_ceiling": condition_rank_ceiling,
        "excluded_trials": data["exclusions"],
        "sampled_neural_intervals_seconds": [list(interval) for interval in data["intervals"]],
        "verified_asset_sha256": data["verified_assets"],
        "spikes_in_complete_bins": int(data["counts"].sum()),
        "statistics": summary,
        "bootstrap_whole_trial_95_percentile": result["bootstrap"],
        "condition_unit_mean_rate_hz": statistics["condition_means_hz"].mean(axis=1).tolist(),
        "condition_population_trajectory_hz": statistics["condition_means_hz"].mean(axis=2).tolist(),
        "condition_population_trajectory_bootstrap_95_hz": result["trajectory_bands"].tolist(),
        "fano_factors_by_condition_unit": [
            [float(value) if np.isfinite(value) else None for value in row]
            for row in statistics["fano_factors"]
        ],
        "shuffle_reference_2p5_50_97p5": result["shuffle_reference"],
        "chronological_halves": result["chronological_halves"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    validate_config(config)
    manifest_path = Path(config["dataset_manifest"])
    manifest = json.loads(manifest_path.read_text())
    sessions = {}
    for index, source_session in enumerate(manifest["sessions"]):
        data = load_session(source_session, manifest, config)
        seed = config["random_seed"] + index * 100
        sessions[data["subject"]] = analyze_session(data, config, seed)
        print(f"Analyzed animal {data['subject']}: {data['counts'].shape}", flush=True)

    figure_paths = plot_figures(sessions, FIGURE_DIR, config)
    TENSOR_PATH.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(TENSOR_PATH, **{
        f"{subject}_{field}": result["data"][field]
        for subject, result in sessions.items()
        for field in ("counts", "labels", "trial_ids", "event_ticks", "unit_ids")
    })
    report = {
        "dataset_doi": manifest["dataset_doi"],
        "protocol_commit": "d792f182b3f9d3f1dab0cf9ff5a5f41f1f1c547d",
        "protocol_sha256": file_sha256(PROTOCOL_PATH),
        "config_sha256": file_sha256(args.config),
        "dataset_manifest_sha256": file_sha256(manifest_path),
        "analysis_code_sha256": file_sha256(__file__),
        "environment": {
            "python": sys.version.split()[0],
            **{name: importlib.metadata.version(name) for name in
               ("numpy", "neo", "scikit-learn", "matplotlib")},
        },
        "clock": "native 30000-Hz ticks; half-open [SR-6000, SR+12000); 600-tick bins",
        "subject_uncertainty": "not estimated: two confounded animals and sessions",
        "tensor_local_path": str(TENSOR_PATH),
        "tensor_file_sha256": file_sha256(TENSOR_PATH),
        "figures": figure_paths,
        "sessions": {subject: json_session(result, config) for subject, result in sessions.items()},
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(f"Wrote {REPORT_PATH}", flush=True)


if __name__ == "__main__":
    main()
