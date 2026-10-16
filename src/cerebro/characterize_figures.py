"""Render the saved empirical report without recomputing or fitting statistics."""

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def render(report_path="reports/signal_characterization.json", figures_dir="reports/figures",
           markdown_path="reports/signal_characterization.md"):
    report_path = Path(report_path)
    report = json.loads(report_path.read_text())
    names = ["5ms", "20ms", "50ms"]
    colors = ["#2274A5", "#D65A31", "#4B8B3B"]
    widths = [.005, .02, .05]
    data = [report["widths"][name] for name in names]
    figures_dir = Path(figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    provenance = report["provenance"]
    title = (f"MC_Maze Small / Jenkins | DANDI {provenance['dandiset']} v{provenance['version']}\n"
             f"asset {provenance['asset_id']} | 100 trial-local intervals, 0–293.666 s | 5/20/50 ms")
    paths = []

    def save(fig, suffix):
        fig.suptitle(title, fontsize=8)
        fig.tight_layout(rect=(0, 0, 1, .90))
        path = figures_dir / f"signal_03_{suffix}.png"
        fig.savefig(path, dpi=160)
        plt.close(fig)
        paths.append(str(path))

    def cdf(ax, values, label, color):
        values = np.sort([v for v in values if v is not None])
        if len(values):
            ax.step(values, np.arange(1, len(values) + 1) / len(values), where="post", label=label, color=color)

    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    x = np.arange(3)
    for coverage, shift in [("native", -.17), ("matched", .17)]:
        axes[0, 0].bar(x + shift, [d[coverage]["zero_fraction"] * 100 for d in data],
                       width=.32, label=coverage)
    axes[0, 0].set(xticks=x, xticklabels=names, ylabel="Zero count cells (%)", title="Observed count sparsity")
    axes[0, 0].legend()
    for name, color, entry in zip(names, colors, data):
        matched = entry["matched"]
        histogram = np.array(matched["pooled_count_histogram"])
        axes[0, 1].plot(histogram[:, 0], histogram[:, 1] / histogram[:, 1].sum(), "o-", label=name, color=color)
        cdf(axes[1, 0], [u["fano_across_time"] for u in matched["per_unit"]], name, color)
        histogram = np.array(matched["population"]["count_histogram"])
        axes[1, 1].plot(histogram[:, 0], histogram[:, 1] / histogram[:, 1].sum(), label=name, color=color)
    axes[0, 1].set(xlabel="Unit spikes / bin", ylabel="Empirical probability (log)", yscale="log", title="Matched coverage: pooled counts")
    axes[1, 0].set(xlabel="Across-time count variance / mean", ylabel="Fraction of units ≤ value", title="Descriptive Fano (task epochs mixed)")
    axes[1, 1].set(xlabel="Population spikes / bin", ylabel="Empirical probability", title="Matched coverage: population counts")
    for ax in [axes[0, 1], axes[1, 0], axes[1, 1]]:
        ax.legend()
    save(fig, "statistics")

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    for name, color, width, entry in zip(names, colors, widths, data):
        matched = entry["matched"]
        cdf(axes[0], [u["mean_rate_hz"] for u in matched["per_unit"]], name, color)
        hist = np.array(matched["pooled_count_histogram"])
        axes[1].step(hist[:, 0] / width, np.cumsum(hist[:, 1]) / hist[:, 1].sum(), where="post", label=name, color=color)
    axes[0].set(xlabel="Per-unit pooled rate (spikes/s)", ylabel="Fraction of units ≤ value", title="Identical matched-exposure rates (overlaid)")
    axes[1].set(xlabel="Binwise rate estimate (spikes/s)", ylabel="Fraction of unit-bin cells ≤ value", title="Count / bin duration; no smoothing")
    for ax in axes:
        ax.legend()
    save(fig, "rates")

    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    for name, color, entry in zip(names, colors, data):
        native, matched = entry["native"], entry["matched"]
        axes[0, 0].plot(np.arange(len(report["unit_ids"])), [u["zero_fraction"] for u in matched["per_unit"]], label=name, color=color)
        axes[0, 1].plot(report["trial_ids"], [t["zero_fraction"] for t in matched["trials"]], label=name, color=color)
        axes[1, 0].plot(np.arange(len(report["unit_ids"])), [a["mean_rate_hz"] - b["mean_rate_hz"]
                              for a, b in zip(native["per_unit"], matched["per_unit"])], label=name, color=color)
        axes[1, 1].plot(report["trial_ids"], [a["population"]["mean_rate_hz"] - b["population"]["mean_rate_hz"]
                              for a, b in zip(native["trials"], matched["trials"])], label=name, color=color)
    axes[0, 0].set(xlabel="Unit row (IDs in JSON)", ylabel="Zero count fraction", title="Matched coverage: per-unit sparsity")
    axes[0, 1].set(xlabel="Source trial ID", ylabel="Zero count fraction", title="Matched coverage: per-trial sparsity")
    axes[1, 0].set(xlabel="Unit row (IDs in JSON)", ylabel="Native − matched rate (spikes/s)", title="Rate shifts from tail coverage")
    axes[1, 1].set(xlabel="Source trial ID", ylabel="Native − matched population spikes/s", title="Per-trial tail sensitivity")
    for ax in axes.flat:
        ax.legend()
    save(fig, "sensitivity")

    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    for name, color, entry in zip(names, colors, data):
        native = entry["native"]
        axes[0, 0].plot(report["trial_ids"], [t["complete_bins"] for t in native["trials"]], label=name, color=color)
        axes[0, 1].plot(report["trial_ids"], [t["excluded_spikes"] for t in native["trials"]], label=name, color=color)
        axes[1, 0].plot(report["trial_ids"], [t["excluded_seconds"] * 1000 for t in native["trials"]], label=name, color=color)
    native_exclusions = np.array([d["native"]["excluded_spikes"] for d in data])
    additional = np.array([d["matched"]["excluded_spikes"] for d in data]) - native_exclusions
    axes[1, 1].bar(names, native_exclusions, label="Native incomplete tails")
    axes[1, 1].bar(names, additional, bottom=native_exclusions, label="Additional matched trimming")
    axes[0, 0].set(xlabel="Source trial ID", ylabel="Complete bins", title="Native bins per source trial")
    axes[0, 1].set(xlabel="Source trial ID", ylabel="Excluded spikes (all units)", title="Native tail exclusions")
    axes[1, 0].set(xlabel="Source trial ID", ylabel="Omitted tail duration (ms)", title="Native incomplete tail duration")
    axes[1, 1].set(ylabel="Excluded spikes (all units)", title="Native versus identical matched coverage")
    for ax in axes.flat:
        ax.legend()
    save(fig, "exclusions")

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    audit = report["metadata_audit"]
    pmd = [u for u in audit["units"] if u["prefix"] == "1"]
    m1 = [u for u in audit["units"] if u["prefix"] == "2"]
    axes[0].bar(["Prefix 1: stored PMd", "Prefix 2: stored PMd", "Prefix 2: +96 candidate M1"],
                [len(pmd), len(m1), sum(u["candidate_locations"] == ["M1"] for u in m1)])
    axes[0].set(ylabel="Units", title="Stored links versus publisher's candidate rule")
    axes[0].tick_params(axis="x", labelrotation=20)
    axes[1].scatter([u["unit_id"] for u in m1], [u["stored_electrode_ids"][0] for u in m1], label="Stored reference", s=12)
    axes[1].scatter([u["unit_id"] for u in m1], [u["publisher_plus96_candidate_ids"][0] for u in m1], label="Publisher +96 candidate", s=12)
    axes[1].set(xlabel="Unit ID", ylabel="Electrode table ID", title="No raw metadata changed")
    axes[1].legend()
    save(fig, "metadata")

    lines = ["# Mission 003: empirical neural signal characterization", "",
        f"Source: DANDI {provenance['dandiset']} v{provenance['version']}, asset `{provenance['asset_id']}`.",
        f"SHA-256: `{provenance['sha256']}`. CC-BY-4.0; Churchland and Kaufman (2022).",
        "", "All 100 successful source trials (75 train, 25 val) and 142 units are used.",
        "No model selection, fitting, decoding, or inference of an optimal bin width is performed.", "",
        "## Observed native coverage", "",
        "| Bin | Bins | Zero cells | Exposure (s) | Mean unit rate (Hz) | Median temporal Fano | Tail spikes |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for name, entry in zip(names, data):
        s = entry["native"]
        lines.append(f"| {name} | {s['shape'][0]:,} | {s['zero_fraction']:.4%} | {s['population']['exposure_seconds']:.3f} | "
                     f"{np.mean([u['mean_rate_hz'] for u in s['per_unit']]):.6f} | "
                     f"{np.median([u['fano_across_time'] for u in s['per_unit']]):.6f} | {s['excluded_spikes']:,} |")
    matched = data[0]["matched"]
    rates = np.array([u["mean_rate_hz"] for u in matched["per_unit"]])
    lines += ["", "## Coverage-controlled comparison", "",
        "Native grids stop at different endpoints. Matched grids use the same per-trial",
        "endpoints on a shared 100 ms grid (LCM of 5/20/50 ms), removing that confound.",
        f"Matched exposure is {matched['population']['exposure_seconds']:.3f} s and retains {matched['population']['spikes']:,} spikes,",
        f"excluding {matched['excluded_spikes']:,} relative to all source trials at every width.",
        f"Mean unit rate is {rates.mean():.6f} Hz; range {rates.min():.6f}–{rates.max():.6f} Hz.",
        "Per-unit retained spikes are identical across widths; pooled rates agree to numerical precision.", "",
        "| Bin | Matched bins | Zero cells | Median temporal Fano | Mean population count/bin | Population count variance |",
        "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for name, entry in zip(names, data):
        s = entry["matched"]
        lines.append(f"| {name} | {s['shape'][0]:,} | {s['zero_fraction']:.4%} | "
                     f"{np.median([u['fano_across_time'] for u in s['per_unit']]):.6f} | "
                     f"{s['population']['mean_count']:.6f} | {s['population']['count_variance']:.6f} |")
    lines += ["", "## Definitions, interpretation, and limits", "",
        "Sparsity is the observed zero-count fraction. Mean rate is spikes / observed seconds.",
        "Binwise counts / duration are unsmoothed rate estimates, not continuous latent rates.",
        "Variance uses ddof=1 across temporal bins; Fano is count variance / mean count.",
        "Zero-mean or fewer-than-two-bin Fano values are null, not evidence of zero variability.",
        "", "Narrower bins have more zeros; rate differences on native coverage arise from different",
        "retained intervals. Matched rates are invariant while count distributions change.",
        "Bins mix task epochs, conditions, and train/val trials. Temporal Fano values therefore",
        "include nonstationarity and are not repeated-trial noise Fano estimates; near-one",
        "values do not establish Poisson spiking. No significance tests or causal claims are made.",
        "[Churchland et al. (2010)](https://www.nature.com/articles/nn.2501) discusses across-trial variability,",
        "a distinct sampling design from the pooled temporal summaries here.", "",
        "## Metadata audit", "",
        "72 prefix-1 and 70 prefix-2 IDs all link to PMd-labeled electrode entries in the original NWB.",
        "The [publisher notes](https://neurallatents.github.io/datasets.html) specify prefix 1 = PMd,",
        "prefix 2 = M1, and +96 for erroneous M1 electrode indices. All 70 +96 candidate links",
        "resolve to M1-labeled entries in this file. Original links, IDs, and locations remain unchanged.",
        "This confirms internal consistency with the published rule, not independent anatomical",
        "localization or unit identity. Physical coordinates and spike-sorting quality remain unresolved.", "",
        "## Reproduce and inspect", "", "```sh", "conda activate cerebro",
        "python -m cerebro.characterize configs/mc_maze_small.json",
        "python -m cerebro.characterize_figures", "python -m pytest", "```", "",
        "The JSON contains each unit's histogram, rates, variances, Fano statistics, each trial's",
        "complete-bin/exposure statistics, per-unit/per-trial exclusions, all source/matched",
        "intervals and original metadata comparisons. Serialization has no wall-clock timestamp;",
        "unchanged data, code and environment reproduce identical JSON. Source hashes and",
        "the published foundation revision identify the analysis provenance.", "",
        f"Results JSON SHA-256: `{hashlib.sha256(report_path.read_bytes()).hexdigest()}`.", "",
        "Figures:"]
    lines += [f"- [{Path(p).stem}](figures/{Path(p).name})" for p in paths]
    lines += ["", "## Recommended next experiment", "",
        "After human approval, characterize event-aligned counts within repeated maze conditions",
        "and separate task-epoch changes from across-trial variability. Select alignment events,",
        "condition inclusion/minimum trial counts and exposure policy before implementation.",
        "No PCA, decoding or bin-width optimization against prediction accuracy is proposed here.", ""]
    Path(markdown_path).write_text("\n".join(lines))
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", default="reports/signal_characterization.json")
    args = parser.parse_args()
    print("\n".join(render(args.report)))


if __name__ == "__main__":
    main()
