"""Render event-aligned empirical tensors and their feasibility limitations."""

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from cerebro.event_aligned import validate_publication_protocol


def matched_event_latencies(arrays):
    """Pair source event timestamps by original trial identity, returning seconds."""
    primary_ids = arrays["trial_ids"]
    secondary_ids = arrays["secondary_trial_ids"]
    if len(np.unique(primary_ids)) != len(primary_ids) or len(np.unique(secondary_ids)) != len(secondary_ids):
        raise ValueError("Event timestamps require unique original trial IDs")
    _, primary_indices, secondary_indices = np.intersect1d(
        primary_ids, secondary_ids, return_indices=True
    )
    cue_seconds = arrays["source_go_cue_seconds"][primary_indices]
    onset_seconds = arrays["source_movement_onset_seconds"][secondary_indices]
    return onset_seconds - cue_seconds


def render(results_path="reports/event_04_results.json", audit_path="reports/event_04_feasibility.json",
           figures_dir="reports/figures", markdown_path="reports/event_04.md"):
    results_path = Path(results_path)
    results = json.loads(results_path.read_text())
    audit = json.loads(Path(audit_path).read_text())
    with np.load(results["tensor_path"], allow_pickle=False) as archive:
        arrays = {key: archive[key] for key in archive.files}
    for key, digest in results["tensor_array_sha256"].items():
        if hashlib.sha256(arrays[key].tobytes()).hexdigest() != digest:
            raise ValueError("Tensor content does not match the scientific report")
    protocol = results["protocol"]
    validate_publication_protocol(protocol)
    width = protocol["bin_width_seconds"]
    edges = arrays["relative_edges_seconds"]
    time_ms = (edges[:-1] + edges[1:]) / 2 * 1000
    source = results["provenance"]
    header = (f"MC_Maze Small / Jenkins | DANDI {source['dandiset']} v{source['version']}\n"
              f"asset {source['asset_id']} | 75 training trials | 20 ms bins\n"
              "Go cue primary: −400 to +1000 ms; source offline movement marker secondary")
    figures_dir = Path(figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    figures = []

    def save(fig, suffix):
        fig.suptitle(header, fontsize=8)
        fig.tight_layout(rect=(0, 0, 1, .87))
        path = figures_dir / f"event_04_{suffix}.png"
        fig.savefig(path, dpi=160)
        plt.close(fig)
        figures.append(str(path))

    def event_line(ax):
        ax.axvline(0, color="gray", linestyle="--", linewidth=1)

    selected = arrays["selected_unit_indices"]
    fig, axes = plt.subplots(2, len(selected), figsize=(12, 6), squeeze=False)
    bands = arrays["selected_unit_rate_bands_hz"]
    for column, unit in enumerate(selected):
        for row, multiplier, label in [(0, width, "Mean spikes / 20 ms bin"), (1, 1, "Mean rate (spikes/s)")]:
            ax = axes[row, column]
            ax.plot(time_ms, arrays["mean_unit_rates_hz"][:, unit] * multiplier)
            ax.fill_between(time_ms, bands[0, :, column] * multiplier, bands[1, :, column] * multiplier, alpha=.2)
            ax.set(xlabel="From go cue (ms)", ylabel=label, title=f"Unit {arrays['unit_ids'][unit]}")
            event_line(ax)
    save(fig, "units")

    fig, axes = plt.subplots(2, 1, figsize=(11, 7))
    bands = arrays["population_rate_bands_hz"]
    axes[0].plot(time_ms, arrays["population_rates_hz"].mean(axis=0), label="Pooled training trials")
    axes[0].fill_between(time_ms, bands[0], bands[1], alpha=.2, label="Whole-trial bootstrap percentile band")
    axes[0].set(xlabel="From go cue (ms)", ylabel="Population spikes/s", title="Pooled event profile: mixed conditions")
    axes[0].legend(fontsize=8); event_line(axes[0])
    image = axes[1].imshow(arrays["mean_unit_rates_hz"].T, aspect="auto", origin="lower",
                           extent=[edges[0] * 1000, edges[-1] * 1000, -.5, len(arrays["unit_ids"]) - .5])
    axes[1].set(xlabel="From go cue (ms)", ylabel="Unit row (source order)", title="Mean rates, no smoothing or normalization")
    fig.colorbar(image, ax=axes[1], label="Mean spikes/s"); event_line(axes[1])
    save(fig, "population")

    fig, ax = plt.subplots(figsize=(11, 8))
    profiles = arrays["condition_population_rates_hz"]
    image = ax.imshow(profiles, aspect="auto", origin="lower",
                      extent=[edges[0] * 1000, edges[-1] * 1000, -.5, len(profiles) - .5])
    ax.set(yticks=np.arange(len(profiles)), yticklabels=arrays["included_condition_keys"],
           xlabel="From go cue (ms)", ylabel="Maze / type / variant / active target",
           title="Descriptive compatible-condition means: 3 trials each, weak precision")
    ax.tick_params(axis="y", labelsize=8)
    event_line(ax); fig.colorbar(image, ax=ax, label="Mean population spikes/s")
    save(fig, "conditions")

    fig, axes = plt.subplots(2, 1, figsize=(11, 7))
    key = arrays["included_condition_keys"][0]
    primary = arrays["condition_keys"] == key
    residual = arrays["residual_condition_keys"] == key
    for trial, values in zip(arrays["trial_ids"][primary], arrays["counts"][primary].sum(axis=2)):
        axes[0].plot(time_ms, values, alpha=.65, label=f"Trial {trial}")
    axes[0].plot(time_ms, arrays["condition_mean_counts"][0].sum(axis=1), color="black", linewidth=2, label="Condition × event-time mean")
    for trial, values in zip(arrays["residual_trial_ids"][residual], arrays["residual_counts"][residual].sum(axis=2)):
        axes[1].plot(time_ms, values, label=f"Trial {trial}")
    axes[0].set(ylabel="Population spikes / bin", title=f"First eligible condition {key}; no response-based choice")
    axes[1].set(xlabel="From go cue (ms)", ylabel="Residual population spikes / bin", title="In-sample deviations; zero-sum by construction")
    axes[1].axhline(0, color="gray", linewidth=1)
    for ax in axes:
        event_line(ax); ax.legend(fontsize=8)
    save(fig, "residuals")

    fig, axes = plt.subplots(1, 3, figsize=(13, 5))
    cmap = plt.get_cmap("coolwarm").copy(); cmap.set_bad("#dddddd")
    for ax, matrix, title in [(axes[0], arrays["signal_like_correlation"], "Mean-response correlation\n21 conditions, noisy means"),
                               (axes[1], arrays["mixed_total_correlation"], "Mixed-condition total correlation\n75 trials, +300 to +320 ms")]:
        image = ax.imshow(matrix, vmin=-1, vmax=1, cmap=cmap, origin="lower")
        ax.set(xlabel="Unit row", ylabel="Unit row", title=title)
        fig.colorbar(image, ax=ax, label="Pearson r", shrink=.75)
    axes[2].axis("off")
    axes[2].text(.05, .65, "Residual correlations\nNOT ESTIMATED\n\n2–3 repetitions / condition\nRank ceiling: 2 versus 142 units\n\nNo connectivity or reliable\nnoise-correlation claim\n\nGray = undefined correlation", fontsize=10, va="center")
    save(fig, "correlations")

    fig, axes = plt.subplots(2, 2, figsize=(11, 7))
    primary_population = arrays["population_rates_hz"].mean(axis=0)
    secondary_population = arrays["secondary_counts"].sum(axis=2).mean(axis=0) / width
    for ax, curve, bands, label in [
        (axes[0, 0], primary_population, arrays["population_rate_bands_hz"], "Photobox go cue alignment"),
        (axes[0, 1], secondary_population, arrays["secondary_population_rate_bands_hz"], "Offline source onset alignment"),
        (axes[1, 0], arrays["hand_speed_m_per_s"].mean(axis=0), arrays["hand_speed_bands_m_per_s"], "Go cue: hand speed"),
        (axes[1, 1], np.linalg.norm(arrays["secondary_hand_velocity_m_per_s"], axis=2).mean(axis=0), arrays["secondary_hand_speed_bands_m_per_s"], "Source onset: hand speed")]:
        ax.plot(time_ms, curve)
        ax.fill_between(time_ms, bands[0], bands[1], alpha=.2)
        ax.set(xlabel="From indicated event (ms)", title=label)
        event_line(ax)
    for ax in axes[0]: ax.set_ylabel("Population spikes/s")
    for ax in axes[1]: ax.set_ylabel("Norm of bin-mean velocity (m/s)")
    save(fig, "timing")

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    repetitions = [c["training_trials"] for c in audit["conditions"]]
    axes[0].bar(np.arange(len(repetitions)), repetitions, color=["#2274a5" if n >= 3 else "#d65a31" for n in repetitions])
    axes[0].axhline(3, linestyle="--", color="gray", label="Descriptive minimum = 3")
    axes[0].set(xlabel="Compatible condition row (audit JSON)", ylabel="Training repetitions", yticks=[0, 1, 2, 3],
                title="21 conditions × 3; 6 × 2; none ≥20")
    axes[0].legend(fontsize=8)
    latency_seconds = matched_event_latencies(arrays)
    axes[1].hist(latency_seconds * 1000, bins=15)
    axes[1].set(xlabel="Source movement onset − go cue (ms)", ylabel="Training trials", title="Timing variability; no coverage exclusions")
    save(fig, "coverage")

    ci = results["paired_change_bootstrap_percentile_band_hz"]
    lines = ["# Mission 004: event-aligned neural population activity", "",
        f"Source: DANDI {source['dandiset']} v{source['version']}, asset `{source['asset_id']}`.",
        f"SHA-256 `{source['sha256']}`; CC-BY-4.0, Churchland and Kaufman (2022).", "",
        "## Feasibility and protocol", "",
        "The [feasibility audit](event_04_feasibility.md) preceded analysis. 75 training",
        "trials form 27 geometry-compatible conditions: 21 × 3 repetitions and 6 × 2.",
        "Grouping maze IDs alone would pool incompatible task variants. All 25 validation",
        "trials are excluded from means, residuals, bootstrap, and covariance calculations.", "",
        "Human-selected primary event: `go_cue_time`, detected by the source photobox.",
        "Window: **[−0.400, +1.000) s**, 70 half-open **20 ms** bins. Secondary alignment",
        "uses existing `move_onset_time`, calculated offline by the source, not a newly",
        "derived kinematic onset. Its full detection rule and timing uncertainty are absent.",
        "All 75 train trials have complete coverage around both events; no events are missing.", "",
        "Counts are trial-local; incomplete windows or neural/behavior gaps exclude whole",
        "trials. Original timestamps remain unchanged; derived grid rounding/snap tolerance",
        "is 1 ps. Behavioral endpoints/internal sample gaps use the declared 2 ms policy.",
        "There is no interpolation or smoothing. Center-labeled bins use up to 10 ms of",
        "future observations and are acausal summaries, not an online control protocol.", "",
        "## Observed tensors and activity", "",
        "| Tensor | Shape | Scope |", "| --- | --- | --- |",
        "| Counts / rates | 75 × 70 × 142 | Complete primary training windows |",
        "| Hand velocity | 75 × 70 × 2 | Bin-mean vx/vy in m/s |",
        "| Condition means | 21 × 70 × 142 | Three repetitions per condition |",
        "| Condition-time residuals | 63 × 70 × 142 | 12 low-repetition trials excluded |",
        "| Secondary counts | 75 × 70 × 142 | Existing source movement marker |", "",
        f"Primary windows retain **{results['primary_retained_spikes']:,} spikes** with per-unit/trial conservation checks.",
        f"Mean unit rate: **{results['mean_unit_baseline_rate_hz']:.6f} Hz** in [−400,−200) ms,",
        f"and **{results['mean_unit_response_rate_hz']:.6f} Hz** in [+200,+600) ms.",
        f"Paired trial-mean change: **{results['paired_mean_unit_change_hz']:.6f} Hz**; stratified whole-trial",
        f"bootstrap percentile band **[{ci[0]:.6f}, {ci[1]:.6f}] Hz** (1,000 draws, seed 4).",
        f"**{results['trials_with_positive_mean_unit_change']} of 75 trials** have a positive paired population-mean unit-rate change.",
        "Bands resample entire simultaneous trial vectors within compatible conditions,",
        "not bins or neurons. Pointwise bands are not simultaneous intervals; 2–3 repeats",
        "give weak, potentially miscalibrated bootstrap uncertainty. Independent trials are",
        "an assumption; within-session dependence and curated sampling are not ruled out.", "",
        f"Pooled population and hand-speed curves peak at **{results['population_peak_bin_seconds'] * 1000:.0f} ms**",
        f"and **{results['hand_speed_peak_bin_seconds'] * 1000:.0f} ms** after the go cue. These peak bins are descriptive,",
        "not a fitted lag, evidence of neural prediction, or causal ordering. Source movement",
        "onset latency is 243–606 ms (median 322 ms). Target-to-go delays vary 31–999 ms,",
        "so the pre-go baseline does not represent an identical task stage on every trial.", "",
        "## Correlation and residual limitations", "",
        "Mean-response ('signal-like') Pearson coefficients compare 21 compatible-condition",
        "mean response-epoch rates. These three-trial means contain substantial sampling",
        "noise; the coefficients are not noise-corrected or validated estimates of shared tuning.",
        "The simultaneous total covariance uses counts across 75 trials in the fixed",
        "+300 to +320 ms bin. It mixes condition-dependent signal and residual variation.",
        "Its rank is at most 74; covariance across 21 condition means has rank at most 20.",
        "Undefined correlations for constant units remain NaN/gray, not zero. Sparse",
        "coincidences can yield extreme coefficients, including 1, without robust coupling.", "",
        "Expected responses are calculated separately at every condition and event-time bin.",
        "Residuals subtract these in-sample means and sum to zero by construction. With three",
        "repetitions, each condition-time residual covariance has rank at most two for 142 units.",
        "**Residual correlation matrices and reliable noise-correlation claims are withheld.**",
        "No condition meets the declared ≥20-repeat screening policy; even 20 repeats would",
        "not guarantee reliable high-dimensional covariance. Time bins are not independent",
        "trial repetitions. Correlation and covariance do not establish causal connectivity.",
        "See [Cohen and Kohn (2011)](https://www.nature.com/articles/nn.2842) for the distinction",
        "between tuning similarity and trial-to-trial response fluctuations.", "",
        "## Adequacy and next decision", "",
        "| Attempted analysis | MC_Maze Small adequacy |",
        "| --- | --- |",
        "| Pooled peri-event profiles / timing | Descriptive, 75 training trials |",
        "| Compatible-condition means / residual illustrations | Limited precision, 3 repeats in 21 conditions |",
        "| Mean-response correlations | Exploratory only, noisy three-trial means |",
        "| Simultaneous total covariance | Descriptive mixture; singular for 142 units |",
        "| Reliable condition-time residual correlations | Unsupported; no condition meets the screening policy |", "",
        "MC_Maze Small supports software validation, descriptive peri-event profiles,",
        "illustrative condition means and condition-time deviations. It does not support",
        "reliable condition-specific population residual covariance here. Audit repetitions",
        "in [standard MC_Maze 000128](https://dandiarchive.org/dandiset/000128/0.220113.0400)",
        "next, after approval, before selecting an event-time/condition variability analysis.",
        "Do not assume the larger release guarantees sufficient replication or identical fields.",
        "The known 70 M1-prefix/electrode-link inconsistencies remain unchanged. No PCA,",
        "decoder, learned transformation, representation alignment, push, or merge is performed.", "",
        "## Reproduce and inspect", "", "```sh", "conda activate cerebro",
        "python -m cerebro.event_audit configs/mc_maze_small.json",
        "python -m cerebro.event_aligned configs/mc_maze_small.json",
        "python -m cerebro.event_figures", "python -m pytest", "```", "",
        "Protocol: `configs/event_04.json`. Results: `event_04_results.json` and Git-ignored",
        "`data/processed/event_04.npz`, including source trial/event IDs, absolute boundaries,",
        "condition means/residuals, covariance/correlation matrices and whole-trial bands.",
        "Array hashes bind the tensor contents to the JSON; no wall-clock field is used.",
        f"Results JSON SHA-256: `{hashlib.sha256(results_path.read_bytes()).hexdigest()}`.", "",
        "## Figures", ""]
    lines += [f"- [{Path(p).stem}](figures/{Path(p).name})" for p in figures]
    Path(markdown_path).write_text("\n".join(lines) + "\n")
    return figures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", default="reports/event_04_results.json")
    args = parser.parse_args()
    print("\n".join(render(args.results)))


if __name__ == "__main__":
    main()
