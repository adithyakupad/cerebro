"""Render verified stored representation and longitudinal experiments; never fit."""

import argparse
import hashlib
import json
from pathlib import Path
import textwrap

import matplotlib.pyplot as plt
import numpy as np

from cerebro.benchmark import array_digest


def verified_results(directory, archive_name):
    directory = Path(directory)
    report_path = directory / "results.json"
    report = json.loads(report_path.read_text())
    with np.load(directory / archive_name, allow_pickle=False) as archive:
        if set(archive.files) != set(report["arrays"]):
            raise ValueError("Stored array inventory differs from report")
        for name, metadata in report["arrays"].items():
            values = archive[name]
            if list(values.shape) != metadata["shape"] or array_digest(values) != metadata["sha256"]:
                raise ValueError("Stored array integrity mismatch")
    report_hash = hashlib.sha256(report_path.read_bytes()).hexdigest()
    return report, report_hash


def save_figure(figure, path, source_label, protocol):
    source_lines = textwrap.fill(source_label, width=145)
    protocol_lines = textwrap.fill(protocol, width=145)
    figure.text(0.01, 0.01, source_lines + "\n" + protocol_lines, fontsize=7)
    figure.tight_layout(rect=(0, 0.12, 1, 1))
    figure.savefig(path, dpi=150)
    plt.close(figure)


def publish_report(report, report_hash, name, text, output):
    rendered_report = dict(report)
    rendered_report["render_input_report_sha256"] = report_hash
    rendered_report["render_source_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    json_path = output / f"{name}.json"
    json_path.write_text(json.dumps(rendered_report, sort_keys=True, indent=2, allow_nan=False) + "\n")
    (output / f"{name}.md").write_text(text + "\n")


def render_representation(directory, output):
    report, report_hash = verified_results(directory, "predictions.npz")
    classical_path = Path(report["config"]["classical_run"]) / "results.json"
    classical_bytes = classical_path.read_bytes()
    if hashlib.sha256(classical_bytes).hexdigest() != report["input_report_sha256"]:
        raise ValueError("Classical input report integrity mismatch")
    classical = json.loads(classical_bytes)
    asset = classical["asset"]
    dandiset_id = asset.get("dandiset_id", asset.get("dandiset"))
    source_label = f"DANDI {dandiset_id} v{asset['version']} | asset {asset['asset_id']}"
    config = classical["config"]
    protocol = (f"{config['event']}: {config['pre_seconds']} to {config['post_seconds']} s; "
                f"{report['config']['bin_width_seconds'] * 1000:g} ms bins; original validation trials")
    controls = sorted({row["control"] for row in report["results"]})
    budgets = report["config"]["label_budgets"]
    figure, axes = plt.subplots(1, 2, figsize=(12, 5))
    summaries = []
    for control in controls:
        mean_mse = []
        lower_mse = []
        upper_mse = []
        mean_r2 = []
        for budget in budgets:
            rows = [row for row in report["results"]
                    if row["control"] == control and row["label_budget_trials"] == budget]
            losses = np.asarray([row["mse_m2_s2"] for row in rows])
            scores = np.asarray([np.mean(row["pooled_r2_by_coordinate"]) for row in rows])
            mean_mse.append(float(losses.mean()))
            lower_mse.append(float(losses.min()))
            upper_mse.append(float(losses.max()))
            mean_r2.append(float(scores.mean()))
            summaries.append(f"| {control} | {budget} | {losses.mean():.6g} | {scores.mean():.6g} |")
        axes[0].plot(budgets, mean_mse, marker="o", label=control)
        axes[0].fill_between(budgets, lower_mse, upper_mse, alpha=0.12)
        axes[1].plot(budgets, mean_r2, marker="o", label=control)
    axes[0].set_ylabel("Velocity MSE (m²/s²); seed mean and range")
    axes[1].set_ylabel("Mean coordinate pooled R²; seed mean")
    axes[1].axhline(0, color="gray", linewidth=0.8)
    for axis in axes:
        axis.set_xlabel("Labeled training trials")
        axis.set_xticks(budgets)
        axis.grid(alpha=0.2)
    axes[0].legend(fontsize=7)
    figure.suptitle("Stored representation controls: all prespecified budgets and seeds")
    save_figure(figure, output / "figures/representation_07_budget.png", source_label, protocol)
    text = ("# Representation experiment 07\n\n" + source_label + "\n\n" + protocol
            + "\n\n" + report["protocol"]
            + f"\n\nSeeds: {report['config']['seeds']}. Ranges reflect optimization seeds, not trial uncertainty."
            + " Negative R² and nonmonotonic budgets remain visible; no best test result selected."
            + " This small single-session experiment does not establish foundation-model performance.\n\n"
            + "| Control | Labeled trials | Mean MSE (m²/s²) | Mean coordinate R² |\n|---|---:|---:|---:|\n"
            + "\n".join(summaries)
            + "\n\nDataset: Churchland, Mark; Kaufman, Matthew. MC_Maze, CC-BY-4.0. "
            + f"[Pinned release](https://dandiarchive.org/dandiset/{dandiset_id}/{asset['version']}).\n\n"
            + "Limitations: " + "; ".join(report["limitations"])
            + "\n\n![Budget comparison](figures/representation_07_budget.png)")
    publish_report(report, report_hash, "representation_07", text, output)


def render_longitudinal(directory, output):
    report, report_hash = verified_results(directory, "arrays.npz")
    source = report["source"]
    target = report["target"]
    label = (f"DANDI {source['dandiset_id']} v{source['version']} | source {source['asset_id']}\n"
             f"Target {target['asset_id']}; native 20 ms sampled clocks (up to 1 ms jitter)")
    protocol = (f"Source train {report['config']['source_training_trials']} trials; "
                f"target calibration prefix {report['config']['target_calibration_pool_trials']} trials; "
                "remaining target trials untouched; same-bin finger position")
    budgets = report["config"]["calibration_budgets"]
    figure, axis = plt.subplots(figsize=(10, 5))
    baseline = report["metrics"]["frozen_source"]["mean_trial_mse_flexion2"]
    axis.axhline(baseline, color="black", linestyle="--", label="frozen_source")
    for name in ("source_mean", "unlabeled_marginal_normalization"):
        metric = report["metrics"].get(name)
        if metric is not None:
            axis.axhline(metric["mean_trial_mse_flexion2"], linestyle=":", label=name)
    for method in ("direct_recalibration", "source_plus_residual", "condition_anchor_alignment"):
        available_budgets = []
        losses = []
        for budget in budgets:
            metric = report["metrics"].get(f"{method}_{budget}")
            if metric is not None:
                available_budgets.append(budget)
                losses.append(metric["mean_trial_mse_flexion2"])
        axis.plot(available_budgets, losses, marker="o", label=method)
    axis.set_xlabel("Labeled target calibration trials")
    axis.set_ylabel("Mean target-trial position MSE (flexion units²)")
    axis.legend(fontsize=8)
    axis.grid(alpha=0.2)
    save_figure(figure, output / "figures/longitudinal_08_calibration.png", label, protocol)
    geometry = report["geometry"]
    figure, axes = plt.subplots(1, 2, figsize=(10, 5))
    angles = np.asarray(geometry["principal_angles_radians"])
    axes[0].bar(np.arange(1, len(angles) + 1), angles)
    axes[0].set_ylabel("Principal angle (radians)")
    axes[0].set_xlabel("Stored subspace angle index")
    correlations = geometry.get("cca_in_sample_anchor_correlations", [])
    axes[1].bar(np.arange(1, len(correlations) + 1), correlations)
    axes[1].set_ylabel("In-sample anchor canonical correlation")
    axes[1].set_xlabel("Canonical coordinate")
    axes[1].set_ylim(0, 1)
    figure.suptitle(f"Exploratory geometry; covariance cosine {geometry['covariance_frobenius_cosine']:.3f}")
    save_figure(figure, output / "figures/longitudinal_08_shift.png", label,
                geometry["target_data_access"] + "; CCA is in-sample, not independent transfer validation")
    rows = []
    for name, metric in report["metrics"].items():
        interval = metric["paired_moving_block_interval"]
        rows.append(f"| {name} | {metric['mean_trial_mse_flexion2']:.6g} | {metric['paired_mse_change_from_frozen']:.6g} | {interval} |")
    text = ("# Longitudinal experiment 08\n\n" + label + "\n\n" + protocol
            + "\n\n" + report["information_policy"]
            + "\n\n| Method | MSE (flexion units²) | Paired change from frozen | Moving-block sensitivity interval |\n|---|---:|---:|---|\n"
            + "\n".join(rows)
            + f"\n\nCovariance cosine: {geometry['covariance_frobenius_cosine']:.6g}. "
            + geometry.get("cca_limitations", "No CCA result available.")
            + " Two sessions from one Monkey N do not establish subject generalization or a foundation model."
            + " Moving-block intervals are sensitivity analyses, not validated population uncertainty.\n\n"
            + "Attribution: Temmar, Hisham; Gill, Nina; Wang, Yixuan; and LINK contributors, CC-BY-4.0; "
            + f"[pinned LINK release](https://dandiarchive.org/dandiset/{source['dandiset_id']}/{source['version']}).\n\n"
            + "Limitations: " + "; ".join(report["limitations"])
            + "\n\n![Calibration](figures/longitudinal_08_calibration.png)\n\n![Exploratory geometry](figures/longitudinal_08_shift.png)")
    publish_report(report, report_hash, "longitudinal_08", text, output)


def render_transfer(directory, output):
    report, report_hash = verified_results(directory, "predictions.npz")
    config = report["config"]
    manifests = report["manifests"]
    asset_labels = "; ".join(manifest["asset_id"] for manifest in manifests)
    source_label = f"LINK DANDI {manifests[0]['dandiset_id']} v{manifests[0]['version']}; assets {asset_labels}"
    protocol = (f"First {config['native_bins_per_trial']} native bins/trial; nominal "
                f"{config['native_bins_per_trial'] * report['native_bin_width_seconds']:g} s; 19–21 ms clocks. "
                f"Two sources {config['source_probe_trials_each']} trials/session; "
                f"third session {config['target_calibration_trials']} calibration / "
                f"{config['target_evaluation_trials']} evaluation trials.")
    settings = [setting["name"] for setting in config["settings"]]
    controls = sorted({row["control"] for row in report["results"]})
    figure, axis = plt.subplots(figsize=(11, 5))
    summary_rows = []
    for control in controls:
        rows = [row for row in report["results"]
                if row["setting"] == "reference" and row["control"] == control]
        budgets = sorted({row["target_label_budget"] for row in rows})
        means = []
        minima = []
        maxima = []
        for budget in budgets:
            losses = np.asarray([row["mse_native_position_squared"] for row in rows
                                 if row["target_label_budget"] == budget])
            means.append(float(losses.mean()))
            minima.append(float(losses.min()))
            maxima.append(float(losses.max()))
            summary_rows.append(f"| {control} | {budget} | {losses.mean():.7g} | {losses.min():.7g}–{losses.max():.7g} |")
        axis.plot(budgets, means, marker="o", label=control)
        axis.fill_between(budgets, minima, maxima, alpha=0.12)
    axis.set_xlabel("Labeled target calibration trials; zero = source-only probe")
    axis.set_ylabel("Position MSE (flexion units²); seed mean and range")
    axis.legend(fontsize=7)
    axis.grid(alpha=0.2)
    save_figure(figure, output / "figures/representation_09_controls.png", source_label, protocol)
    figure, axis = plt.subplots(figsize=(11, 5))
    for control in controls:
        values = []
        lower_values = []
        upper_values = []
        for setting in settings:
            selected_rows = [row for row in report["results"]
                             if row["setting"] == setting and row["control"] == control]
            maximum_budget = max(row["target_label_budget"] for row in selected_rows)
            losses = [row["mse_native_position_squared"] for row in selected_rows
                      if row["target_label_budget"] == maximum_budget]
            values.append(float(np.mean(losses)))
            lower_values.append(float(np.min(losses)))
            upper_values.append(float(np.max(losses)))
        axis.plot(settings, values, marker="o", label=control)
        axis.fill_between(np.arange(len(settings)), lower_values, upper_values, alpha=0.1)
    setting_labels = []
    for setting in config["settings"]:
        setting_labels.append(f"{setting['name']}\nhidden {setting['hidden']}; epochs {setting['epochs']}\n"
                              f"SSL trials/source {setting['source_trials_each']}")
    axis.set_xticks(np.arange(len(settings)), setting_labels)
    axis.set_ylabel("Position MSE (flexion units²); seed mean and range")
    axis.set_title("Prespecified ablations; each control at its maximum label budget")
    axis.legend(fontsize=7)
    axis.grid(alpha=0.2)
    save_figure(figure, output / "figures/representation_09_ablations.png", source_label, protocol)
    diagnostics = report["session_identity_diagnostics"]
    figure, axis = plt.subplots(figsize=(10, 5))
    for encoder in sorted({row["encoder"] for row in diagnostics}):
        means = []
        lower = []
        upper = []
        for setting in settings:
            scores = np.asarray([row["accuracy"] for row in diagnostics
                                 if row["encoder"] == encoder and row["setting"] == setting])
            means.append(float(scores.mean()))
            lower.append(float(scores.min()))
            upper.append(float(scores.max()))
        axis.plot(settings, means, marker="o", label=encoder)
        axis.fill_between(np.arange(len(settings)), lower, upper, alpha=0.12)
    chance = diagnostics[0]["balanced_chance_accuracy"]
    axis.axhline(chance, color="black", linestyle="--", label="balanced chance")
    axis.set_ylabel("Source-session classifier accuracy; seed mean and range")
    axis.set_ylim(0, 1.02)
    axis.legend()
    identity_trials = diagnostics[0]["evaluation_trial_rows"]
    reference_identity_scores = [row["accuracy"] for row in diagnostics
                                 if row["setting"] == "reference" and row["encoder"] == "pretrained"]
    reference_identity_mean = float(np.mean(reference_identity_scores))
    axis.set_title(f"Date remains identifiable: {identity_trials} held-out source trials")
    save_figure(figure, output / "figures/representation_09_identity.png", source_label,
                protocol + " Optimization seed ranges, not biological confidence intervals; source-date classification only")
    text = ("# Representation transfer experiment 09\n\n" + source_label + "\n\n" + protocol
            + f"\n\nSeeds {config['seeds']}; {len(report['results'])} control rows and "
            + f"{len(diagnostics)} identity diagnostics. All prespecified results retained."
            + " Seed ranges measure optimization variation, not biological confidence intervals."
            + " Random and self-supervised frozen controls are near-identical in these runs;"
            + " this does not demonstrate a learned transfer advantage. Source-date classification"
            + f" accuracy is {reference_identity_mean:.1%} (reference pretrained seed mean) on "
            + f"{identity_trials} untouched source trials, so latent session invariance is unsupported."
            + " Three sessions of one Monkey N do not establish subject generalization or a foundation model.\n\n"
            + "| Reference control | Target labeled trials | Mean MSE (flexion units²) | Seed range |\n|---|---:|---:|---|\n"
            + "\n".join(summary_rows)
            + "\n\n[Evaluation uncertainty and null controls](evaluation_11.md) are reported separately;"
            + " these plots do not select a best test configuration.\n\n"
            + "Attribution: Temmar, Hisham; Gill, Nina; Wang, Yixuan; and LINK contributors, CC-BY-4.0; "
            + f"[pinned release](https://dandiarchive.org/dandiset/{manifests[0]['dandiset_id']}/{manifests[0]['version']}).\n\n"
            + "Limitations: " + "; ".join(report["limitations"])
            + "\n\n![Controls](figures/representation_09_controls.png)\n\n"
            + "![Ablations](figures/representation_09_ablations.png)\n\n"
            + "![Source identity](figures/representation_09_identity.png)")
    publish_report(report, report_hash, "representation_09", text, output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--representation", default="data/processed/representation_07")
    parser.add_argument("--longitudinal", default="data/processed/longitudinal_08")
    parser.add_argument("--transfer", default="data/processed/representation_09")
    parser.add_argument("--output", type=Path, default=Path("reports"))
    arguments = parser.parse_args()
    (arguments.output / "figures").mkdir(parents=True, exist_ok=True)
    render_representation(arguments.representation, arguments.output)
    render_longitudinal(arguments.longitudinal, arguments.output)
    if (Path(arguments.transfer) / "results.json").exists():
        render_transfer(arguments.transfer, arguments.output)


if __name__ == "__main__":
    main()
