"""Describe source-only LINK calibration coverage without fitting a new model."""

import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from cerebro.extended_figures import verified_results
from cerebro.link import load_link


SOURCE_MANIFEST = Path("configs/link_20200127.json")
HISTORICAL_REPORT = Path("reports/longitudinal_16_20200206.json")
OUTPUT = Path("reports/mission_017_adaptation.json")
FIGURE = Path("reports/figures/mission_017_source_coverage.png")
INPUT_CODE_REVISION = "fda96d87c3bc9c43a038b8b727f3519724a6ee9b"


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def group_statistics(trials):
    if not trials:
        raise ValueError("A trial group is required")
    positions = np.concatenate([trial["position"] for trial in trials], axis=0)
    counts = np.concatenate([trial["counts"] for trial in trials], axis=0)
    targets = np.stack([trial["target"] for trial in trials])
    lengths = np.asarray([len(trial["counts"]) for trial in trials])
    return {
        "trials": len(trials),
        "bins": len(counts),
        "channels": counts.shape[1],
        "median_bins_per_trial": float(np.median(lengths)),
        "position_mean_flexion": positions.mean(axis=0).tolist(),
        "position_std_flexion": positions.std(axis=0).tolist(),
        "target_min_flexion": targets.min(axis=0).tolist(),
        "target_max_flexion": targets.max(axis=0).tolist(),
        "unique_commanded_targets": len(np.unique(targets, axis=0)),
        "zero_count_fraction": float(np.mean(counts == 0)),
        "mean_count_per_contact_20ms_bin": float(counts.mean()),
        "active_contact_count": int(np.count_nonzero(counts.sum(axis=0))),
    }


def main():
    manifest = json.loads(SOURCE_MANIFEST.read_text())
    source = load_link(manifest)
    trials = source["trials"]
    if len(trials) != 375:
        raise ValueError("Source trial inventory changed")
    if source["verified_sha256"] != manifest["sha256"]:
        raise ValueError("Source recording checksum changed")

    historical = json.loads(HISTORICAL_REPORT.read_text())
    if historical["source"]["sha256"] != manifest["sha256"]:
        raise ValueError("Historical source asset changed")
    if historical["splits"]["source_inner_training"] != [row["trial_id"] for row in trials[:225]]:
        raise ValueError("Historical source training split changed")
    if historical["splits"]["source_inner_validation"] != [row["trial_id"] for row in trials[225:300]]:
        raise ValueError("Historical source validation split changed")
    if historical["splits"]["source_evaluation"] != [row["trial_id"] for row in trials[300:]]:
        raise ValueError("Historical source evaluation split changed")

    groups = {
        "first_15_development_trials": trials[:15],
        "following_60_development_trials": trials[15:75],
        "remaining_150_inner_training_trials": trials[75:225],
        "source_inner_validation_75": trials[225:300],
        "historically_inspected_source_evaluation_75": trials[300:375],
    }
    group_results = {name: group_statistics(group) for name, group in groups.items()}
    retrospective_targets = {}
    for date in ("20200206", "20200211", "20200222"):
        target_manifest_path = Path(f"configs/link_{date}.json")
        target_manifest = json.loads(target_manifest_path.read_text())
        target_recording = load_link(target_manifest)
        experiment_directory = Path(f"data/processed/longitudinal_16_{date}")
        experiment_report, experiment_hash = verified_results(experiment_directory, "arrays.npz")
        if experiment_report["target"]["sha256"] != target_recording["verified_sha256"]:
            raise ValueError(f"Target asset does not match stored experiment: {date}")
        target_trials = target_recording["trials"]
        if experiment_report["splits"]["target_unlabeled_calibration_pool"] != [trial["trial_id"] for trial in target_trials[:75]]:
            raise ValueError(f"Target calibration split changed: {date}")
        if experiment_report["splits"]["target_evaluation"] != [trial["trial_id"] for trial in target_trials[75:]]:
            raise ValueError(f"Target evaluation split changed: {date}")
        with np.load(experiment_directory / "arrays.npz", allow_pickle=False) as arrays:
            predictions = {}
            for method in ("source_mean", "frozen_source", "target_calibration_mean_15",
                           "direct_recalibration_15", "source_plus_residual_15"):
                values = arrays[f"{method}_prediction_flexion"]
                predictions[method] = {
                    "mean_flexion": values.mean(axis=0).tolist(),
                    "std_flexion": values.std(axis=0).tolist(),
                }
        retrospective_targets[date] = {
            "asset_id": target_manifest["asset_id"],
            "asset_sha256": target_recording["verified_sha256"],
            "experiment_report_sha256": experiment_hash,
            "first_15_calibration_trials": group_statistics(target_trials[:15]),
            "evaluation_300_trials": group_statistics(target_trials[75:]),
            "saved_prediction_distribution": predictions,
        }

    report = {
        "schema_version": 1,
        "status": "observed_descriptive_diagnostic_no_new_model_fit",
        "input_code_revision": INPUT_CODE_REVISION,
        "generator_sha256": digest(__file__),
        "source_asset_id": manifest["asset_id"],
        "source_sha256": manifest["sha256"],
        "source_version": manifest["version"],
        "historical_report_sha256": digest(HISTORICAL_REPORT),
        "bin_width_seconds": 0.02,
        "features": "96 contact-coordinate threshold-crossing counts; not neuron identities",
        "target": "two native finger-position coordinates, flexion units",
        "source_only_alpha_candidates": historical["selection"],
        "selected_alpha": historical["selected_alpha"],
        "source_trial_groups": group_results,
        "retrospective_previously_inspected_targets": retrospective_targets,
        "limits": [
            "Mission016 target dates were previously inspected; their distributions and saved predictions are described but not used for selection or fitting.",
            "Adjacent 20 ms bins are correlated; bin count is not independent trial count.",
            "These observational differences cannot identify the cause of future-session failure.",
            "Ridge alpha was selected for source training, not optimized for 15 target trials.",
        ],
    }
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")

    block_starts = np.arange(0, 300, 15)
    block_means = []
    for start in block_starts:
        positions = np.concatenate([trial["position"] for trial in trials[start:start + 15]])
        block_means.append(positions.mean(axis=0))
    block_means = np.asarray(block_means)
    figure, axis = plt.subplots(figsize=(9, 4.5))
    centers = block_starts + 7.5
    axis.plot(centers, block_means[:, 0], marker="o", label="index position")
    axis.plot(centers, block_means[:, 1], marker="o", label="middle/ring/pinky position")
    axis.axvspan(0, 15, alpha=0.12, color="orange", label="first 15 trials")
    axis.axvline(225, color="black", linestyle="--", linewidth=0.8, label="source inner validation")
    axis.set_xlabel("Original chronological source trial row")
    axis.set_ylabel("Sample-weighted mean position (flexion units)")
    axis.set_title("LINK Monkey N, 2020-01-27: source-only label coverage")
    axis.grid(alpha=0.2)
    axis.legend(fontsize=8)
    figure.text(0.01, 0.01, "DANDI 001201 v0.251023.2336, asset c002a9a1; original 20 ms sampled bins. Figure uses source only.", fontsize=7)
    figure.tight_layout(rect=(0, 0.05, 1, 1))
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIGURE, dpi=150)
    plt.close(figure)
    print(json.dumps({"source_trials": len(trials), "groups": len(groups), "selected_alpha": historical["selected_alpha"]}))


if __name__ == "__main__":
    main()
