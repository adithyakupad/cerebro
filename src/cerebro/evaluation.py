"""Trial-level uncertainty from stored empirical losses, without model selection."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from cerebro.benchmark import array_digest


def loss_summary(losses, trial_ids, reference=None, *, block_length=1, draws=1000, seed=5):
    """Average seed losses per trial before resampling independent trial units."""
    values = np.asarray(losses, dtype=float)
    identities = np.asarray(trial_ids)
    if values.ndim == 1:
        values = values[None, :]
    if values.ndim != 2 or min(values.shape) < 1 or not np.isfinite(values).all():
        raise ValueError("Finite seed × trial losses required")
    if identities.ndim != 1 or len(identities) != values.shape[1] or len(np.unique(identities)) != len(identities):
        raise ValueError("Loss lengths require unique matching trial identities")
    if block_length < 1 or block_length > len(identities) or draws < 2:
        raise ValueError("Invalid resampling block length or draw count")
    trial_means = values.mean(axis=0)
    seed_means = values.mean(axis=1)
    generator = np.random.default_rng(seed)
    block_count = int(np.ceil(len(identities) / block_length))
    starts = generator.integers(len(identities) - block_length + 1, size=(draws, block_count))
    blocks = starts[:, :, None] + np.arange(block_length)
    block_indices = blocks.reshape(draws, -1)
    indices = block_indices[:, :len(identities)]
    sampled_losses = trial_means[indices]
    sampled_means = sampled_losses.mean(axis=1)
    interval = np.quantile(sampled_means, [.025, .975])
    result = {
        "mean_trial_loss": float(trial_means.mean()), "percentile_interval": interval.tolist(),
        "evaluation_trials": len(identities), "initialization_repeats": len(values),
        "seed_mean_loss_range": [float(seed_means.min()), float(seed_means.max())],
        "resampling": {"draws": draws, "seed": seed, "block_length_trials": block_length},
    }
    if reference is not None:
        reference_values = np.asarray(reference, dtype=float)
        if reference_values.ndim == 2:
            reference_values = reference_values.mean(axis=0)
        if reference_values.shape != trial_means.shape or not np.isfinite(reference_values).all():
            raise ValueError("Paired reference requires matching finite trial losses")
        paired_changes = trial_means - reference_values
        sampled_trial_changes = paired_changes[indices]
        sampled_changes = sampled_trial_changes.mean(axis=1)
        result["paired_mean_change"] = float(paired_changes.mean())
        result["paired_percentile_interval"] = np.quantile(sampled_changes, [.025, .975]).tolist()
    return result


def read_bound_report(directory, archive_name):
    directory = Path(directory)
    report_bytes = (directory / "results.json").read_bytes()
    report = json.loads(report_bytes)
    with np.load(directory / archive_name, allow_pickle=False) as archive:
        arrays = {name: archive[name] for name in archive.files}
    if set(arrays) != set(report["arrays"]):
        raise ValueError("Report does not bind every stored array")
    for name, metadata in report["arrays"].items():
        if array_digest(arrays[name]) != metadata["sha256"]:
            raise ValueError(f"Input array provenance mismatch: {name}")
    digest = hashlib.sha256(report_bytes).hexdigest()
    return report, arrays, digest


def grouped_losses(rows, fields, loss_field):
    groups = {}
    seeds = {}
    for row in rows:
        key = tuple(row[field] for field in fields)
        if row["seed"] in seeds.setdefault(key, set()):
            raise ValueError("Duplicate initialization identity within one experiment")
        seeds[key].add(row["seed"])
        groups.setdefault(key, []).append(row[loss_field])
    return groups


def run(data_root="data/processed", output="reports/evaluation_11.json", markdown="reports/evaluation_11.md"):
    root = Path(data_root)
    classical, classical_arrays, classical_digest = read_bound_report(root / "classical_05", "arrays.npz")
    maze_ids = classical["evaluation_trial_ids"]
    if maze_ids != classical["splits"]["source_validation"]:
        raise ValueError("Classical evaluation identities disagree with source split")
    evaluation_mask = np.isin(classical_arrays["trial_ids"], maze_ids)
    stored_evaluation_ids = classical_arrays["trial_ids"][evaluation_mask].tolist()
    if stored_evaluation_ids != maze_ids:
        raise ValueError("Classical array evaluation identities disagree")
    mean_losses = classical["metrics"]["mean"]["trial_mse_m2_s2"]
    summaries = []
    input_digests = {"classical_05": classical_digest}
    for name, values in classical["metrics"].items():
        summary = loss_summary(values["trial_mse_m2_s2"], maze_ids, mean_losses)
        summaries.append({"experiment": "classical_05", "method": name, "units": "m²/s²",
                          "paired_reference": "classical training-only mean", **summary})
    for experiment, fields in [("sequence_06", ("model",)),
                               ("representation_07", ("control", "label_budget_trials"))]:
        report, arrays, digest = read_bound_report(root / experiment, "predictions.npz")
        if report["input_report_sha256"] != classical_digest or report["splits"] != classical["splits"]:
            raise ValueError("Within-session experiment input lineage differs")
        if arrays["evaluation_trial_ids"].tolist() != maze_ids:
            raise ValueError("Within-session evaluation identities differ")
        input_digests[experiment] = digest
        groups = grouped_losses(report["results"], fields, "trial_mse_m2_s2")
        for key, losses in sorted(groups.items()):
            summary = loss_summary(losses, maze_ids, mean_losses)
            summaries.append({"experiment": experiment, "method": dict(zip(fields, key)),
                              "units": "m²/s²", "paired_reference": "classical training-only mean", **summary})
    longitudinal, _, longitudinal_digest = read_bound_report(root / "longitudinal_08", "arrays.npz")
    link_ids = longitudinal["splits"]["target_evaluation"]
    split_path = root / "longitudinal_08" / "split_manifest.json"
    if json.loads(split_path.read_text()) != longitudinal["splits"]:
        raise ValueError("Longitudinal evaluation split lineage differs")
    frozen_losses = longitudinal["metrics"]["frozen_source"]["trial_mse_flexion2"]
    input_digests["longitudinal_08"] = longitudinal_digest
    for name, values in longitudinal["metrics"].items():
        summary = loss_summary(values["trial_mse_flexion2"], link_ids, frozen_losses, block_length=5, seed=8)
        summaries.append({"experiment": "longitudinal_08", "method": name, "units": "flexion²",
                          "paired_reference": "frozen source decoder", **summary})
    transfer, arrays, transfer_digest = read_bound_report(root / "representation_09", "predictions.npz")
    input_digests["representation_09"] = transfer_digest
    fields = ("setting", "control", "target_label_budget")
    groups = grouped_losses(transfer["results"], fields, "trial_mse_native_position_squared")
    comparisons = {"pretrained_zero_shot": "random_zero_shot",
                   "pretrained_frozen_ridge": "random_frozen_ridge",
                   "pretrained_finetuned": "random_supervised_only"}
    for key, losses in sorted(groups.items()):
        setting, control, budget = key
        identities = transfer["splits"][setting]["target_evaluation"]
        if arrays["evaluation_trial_ids"].tolist() != identities:
            raise ValueError("Cross-session representation evaluation identities differ")
        reference_name = comparisons.get(control)
        reference = None
        if reference_name is not None:
            reference_key = (setting, reference_name, budget)
            if reference_key not in groups:
                raise ValueError("Matched random representation control missing")
            reference = groups[reference_key]
        summary = loss_summary(losses, identities, reference, block_length=5, seed=8)
        summaries.append({"experiment": "representation_09", "method": dict(zip(fields, key)),
                          "units": "flexion²", "paired_reference": reference_name, **summary})
    for name, digest in input_digests.items():
        current_digest = hashlib.sha256((root / name / "results.json").read_bytes()).hexdigest()
        if current_digest != digest:
            raise ValueError("Input experiment changed during evaluation")
    report = {
        "schema_version": 1, "input_report_sha256": input_digests,
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "dataset_provenance": {"MC_Maze": classical["asset"],
                               "LINK08_source": longitudinal["source"],
                               "LINK08_target": longitudinal["target"],
                               "LINK09_sessions": transfer["manifests"]},
        "evaluation_trial_ids": {"MC_Maze": maze_ids, "LINK08": link_ids,
                                 "LINK09": arrays["evaluation_trial_ids"].tolist()},
        "summaries": summaries,
        "assumptions": ["MC_Maze resamples 25 whole trials assuming independent curated-session trials",
                        "LINK uses moving blocks of five chronological target trials as sensitivity analysis",
                        "Seeds are averaged within each biological trial, not treated as new biological samples",
                        "Percentile bands are not calibrated population confidence intervals",
                        "No test-winner selection, p-values, significance or multiplicity-adjusted claims",
                        "Within-session m²/s² and LINK flexion² are distinct outcomes and are never pooled",
                        "Paired change is method minus reference; negative values mean lower observed loss"],
    }
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    lines = ["# Common trial-level evaluation", "", "Stored empirical loss summaries; no models were trained or selected.", ""]
    lines.extend("- " + assumption for assumption in report["assumptions"])
    lines.extend(["", "Initialization-seed ranges describe optimization variation separately from trial uncertainty. Single-fit methods have a degenerate seed range.", "",
                  "| Experiment / method | Units | Mean loss | Trial percentile band | Paired change | Paired band | Seed mean range |",
                  "|---|---|---:|---|---:|---|---|"])
    for summary in summaries:
        interval = summary["percentile_interval"]
        seed_range = summary["seed_mean_loss_range"]
        change = summary.get("paired_mean_change")
        paired_interval = summary.get("paired_percentile_interval")
        label = str(summary["method"])
        change_text = "—" if change is None else f"{change:.6f}"
        paired_text = "—" if paired_interval is None else f"[{paired_interval[0]:.6f}, {paired_interval[1]:.6f}]"
        lines.append(f"| {summary['experiment']} / {label} | {summary['units']} | {summary['mean_trial_loss']:.6f} | [{interval[0]:.6f}, {interval[1]:.6f}] | {change_text} | {paired_text} | [{seed_range[0]:.6f}, {seed_range[1]:.6f}] |")
    lines.extend(["", "Paired references: MC_Maze training mean; LINK08 frozen source; LINK09 matched setting/budget random control for each pretrained method.", "",
                  "Input report hashes and complete trial identities are recorded in `evaluation_11.json`.",
                  "Reproduce: `python -m cerebro.evaluation`."])
    Path(markdown).write_text("\n".join(lines) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", default="data/processed")
    parser.add_argument("--output", default="reports/evaluation_11.json")
    parser.add_argument("--markdown", default="reports/evaluation_11.md")
    args = parser.parse_args()
    run(args.data_root, args.output, args.markdown)


if __name__ == "__main__":
    main()
