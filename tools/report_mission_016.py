"""Verify stored Mission 016 experiments and render their fixed reports."""

import hashlib
import json
from pathlib import Path
import shutil

import matplotlib.pyplot as plt
import numpy as np

from cerebro.extended_figures import verified_results
from cerebro.longitudinal import block_interval


DATES = ("20200206", "20200211", "20200222")
PROTOCOL_COMMIT = "5a7376a694825005500cd357694fa8e27e2ce31e"
PROTOCOL_SHA256 = "ad6411175ffa82e6d2064178ef62c811e2eed4e184d3b058bf50f31e9193068f"


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    report_root = Path("reports")
    figure_root = report_root / "figures"
    figure_root.mkdir(parents=True, exist_ok=True)
    protocol_path = Path("docs/research/mission_016_protocol.json")
    protocol = json.loads(protocol_path.read_text())
    if (protocol["status"] != "frozen_before_mission_016_model_outcomes"
            or digest(protocol_path) != PROTOCOL_SHA256):
        raise ValueError("Mission 016 frozen protocol changed")

    summaries = []
    reports = {}
    source_hashes = {}
    for date in DATES:
        directory = Path(f"data/processed/longitudinal_16_{date}")
        report, report_hash = verified_results(directory, "arrays.npz")
        manifest_path = Path(f"configs/link_{date}.json")
        manifest = json.loads(manifest_path.read_text())
        if report["git_revision"] != PROTOCOL_COMMIT or report["git_dirty"]:
            raise ValueError(f"Unexpected code revision or dirty run for {date}")
        if report["target"]["sha256"] != manifest["sha256"]:
            raise ValueError(f"Target asset changed for {date}")
        if len(report["splits"]["target_evaluation"]) != 300:
            raise ValueError(f"Target evaluation size changed for {date}")
        source_path = directory / "results.json"
        destination_path = report_root / f"longitudinal_16_{date}.json"
        shutil.copyfile(source_path, destination_path)
        source_hashes[date] = report_hash
        reports[date] = report

        direct_metric = report["metrics"]["direct_recalibration_15"]
        residual_metric = report["metrics"]["source_plus_residual_15"]
        direct_losses = np.asarray(direct_metric["trial_mse_flexion2"])
        residual_losses = np.asarray(residual_metric["trial_mse_flexion2"])
        paired_change = residual_losses - direct_losses
        if paired_change.shape != (300,):
            raise ValueError(f"Primary trial pairing changed for {date}")
        mean_change = float(paired_change.mean())
        direct_mean = float(direct_losses.mean())
        relative_change_percent = 100.0 * mean_change / direct_mean
        sensitivity_interval = block_interval(paired_change, 1000, 5, 8)
        summaries.append({
            "date": date,
            "asset_id": manifest["asset_id"],
            "asset_sha256": manifest["sha256"],
            "source_mse_flexion_squared": report["source_evaluation_mse_flexion2"],
            "frozen_mse_flexion_squared": report["metrics"]["frozen_source"]["mean_trial_mse_flexion2"],
            "source_mean_mse_flexion_squared": report["metrics"]["source_mean"]["mean_trial_mse_flexion2"],
            "direct_15_mse_flexion_squared": direct_mean,
            "residual_15_mse_flexion_squared": float(residual_losses.mean()),
            "residual_minus_direct_15_flexion_squared": mean_change,
            "residual_minus_direct_15_percent": relative_change_percent,
            "five_trial_block_sensitivity_interval": sensitivity_interval,
            "target_evaluation_trials": len(paired_change),
            "target_evaluation_samples": report["target_evaluation_samples"],
            "alignment_status": report["alignment_status"],
        })

    representation_directory = Path("data/processed/representation_16_20200206")
    representation, representation_hash = verified_results(
        representation_directory, "predictions.npz"
    )
    if representation["git_revision"] != PROTOCOL_COMMIT or representation["git_dirty"]:
        raise ValueError("Unexpected code revision or dirty representation run")
    shutil.copyfile(
        representation_directory / "results.json",
        report_root / "representation_16_20200206.json",
    )
    representation_summary = {}
    controls = sorted({row["control"] for row in representation["results"]})
    for control in controls:
        budget_rows = {}
        for budget in (0, 5, 15, 75):
            selected = [row for row in representation["results"]
                        if row["control"] == control
                        and row["target_label_budget"] == budget]
            if not selected:
                continue
            if len(selected) != 3:
                raise ValueError(f"Seed count changed for {control}/{budget}")
            losses = np.asarray([row["mse_native_position_squared"] for row in selected])
            budget_rows[str(budget)] = {
                "mean_mse_flexion_squared": float(losses.mean()),
                "seed_min": float(losses.min()),
                "seed_max": float(losses.max()),
            }
        representation_summary[control] = budget_rows

    effects = np.asarray([row["residual_minus_direct_15_flexion_squared"] for row in summaries])
    summary = {
        "schema_version": 1,
        "status": "observed_authentic_neural_recordings",
        "protocol_sha256": digest(protocol_path),
        "experiment_git_revision": PROTOCOL_COMMIT,
        "source_report_sha256": source_hashes,
        "representation_report_sha256": representation_hash,
        "source_subjects": ["Monkey N"],
        "primary": {
            "per_date": summaries,
            "equal_date_mean_residual_minus_direct_15_flexion_squared": float(effects.mean()),
            "date_effect_range_flexion_squared": [float(effects.min()), float(effects.max())],
            "all_three_dates_benefit": bool(np.all(effects < 0)),
            "population_inference": "unsupported: three sessions of one monkey",
        },
        "representation_earliest_target_only": representation_summary,
        "cross_subject": "not executed: no eligible independent-subject recording with certified coverage and split-safe original targets",
        "limits": [
            "same-bin offline position prediction, not closed-loop behavior",
            "source and targets are different dates and run IDs within one animal",
            "contact coordinates do not identify stable neurons",
            "LINK upstream thresholding and sensor calibration predate CEREBRO splits",
            "block intervals are sensitivity analyses, not population confidence intervals",
            "latent alignment uses different calibration information and is secondary",
            "representation first-40-bin MSE is not pooled with full-trial ridge MSE",
        ],
    }
    summary_path = report_root / "mission_016.json"
    summary_path.write_text(json.dumps(summary, sort_keys=True, indent=2, allow_nan=False) + "\n")

    figure, axes = plt.subplots(1, 3, figsize=(15, 4.8), sharey=True)
    for axis, date in zip(axes, DATES):
        report = reports[date]
        budgets = report["config"]["calibration_budgets"]
        for method, label in (("direct_recalibration", "target-only"),
                              ("source_plus_residual", "source + residual"),
                              ("condition_anchor_alignment", "latent alignment")):
            available_budgets = [budget for budget in budgets
                                 if f"{method}_{budget}" in report["metrics"]]
            losses = [report["metrics"][f"{method}_{budget}"]["mean_trial_mse_flexion2"]
                      for budget in available_budgets]
            axis.plot(available_budgets, losses, marker="o", label=label)
        frozen = report["metrics"]["frozen_source"]["mean_trial_mse_flexion2"]
        axis.axhline(frozen, color="black", linestyle="--", label="frozen source")
        axis.set_title(f"LINK 2020-{date[4:6]}-{date[6:]}")
        axis.set_xlabel("Labeled target trials")
        axis.set_xticks(budgets)
        axis.grid(alpha=0.2)
    axes[0].set_ylabel("Equal-trial position MSE (flexion units²)")
    axes[-1].legend(fontsize=7)
    figure.suptitle("Monkey N, Jan 27 source → fixed future CO sessions; native 20 ms bins")
    figure.text(0.01, 0.01, "DANDI 001201 v0.251023.2336; target assets 008fc384, 9c0ac931, 19a1f617. Alignment uses additional calibration metadata.", fontsize=7)
    figure.tight_layout(rect=(0, 0.06, 1, 0.94))
    figure.savefig(figure_root / "mission_016_calibration.png", dpi=150)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(8, 4.5))
    positions = np.arange(len(DATES))
    lower = np.asarray([row["five_trial_block_sensitivity_interval"][0] for row in summaries])
    upper = np.asarray([row["five_trial_block_sensitivity_interval"][1] for row in summaries])
    errors = np.vstack((effects - lower, upper - effects))
    axis.errorbar(positions, effects, yerr=errors, marker="o", linestyle="none", capsize=4)
    axis.axhline(0, color="black", linewidth=0.8)
    axis.set_xticks(positions, [f"2020-{date[4:6]}-{date[6:]}" for date in DATES])
    axis.set_ylabel("Source + residual minus target-only MSE (flexion units²)")
    axis.set_title("Prespecified 15-label contrast; positive favors target-only")
    axis.grid(axis="y", alpha=0.2)
    figure.text(0.01, 0.01, "Five-trial block bands are within-session sensitivity, not biological population confidence intervals.", fontsize=7)
    figure.tight_layout(rect=(0, 0.06, 1, 1))
    figure.savefig(figure_root / "mission_016_primary_effect.png", dpi=150)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(9, 4.8))
    for control in controls:
        budget_rows = representation_summary[control]
        budgets = [int(budget) for budget in budget_rows]
        means = [budget_rows[str(budget)]["mean_mse_flexion_squared"] for budget in budgets]
        axis.plot(budgets, means, marker="o", label=control)
    axis.set_xticks((0, 5, 15, 75))
    axis.set_xlabel("Labeled target trials")
    axis.set_ylabel("First-40-bin position MSE (flexion units²); 3-seed mean")
    axis.set_title("LINK Feb 6: prespecified SSL and matched controls")
    axis.grid(alpha=0.2)
    axis.legend(fontsize=7)
    figure.text(0.01, 0.01, "LINK DANDI 001201 v0.251023.2336, target 008fc384; native 20 ms bins. Seed variation is not biological replication.", fontsize=7)
    figure.tight_layout(rect=(0, 0.06, 1, 1))
    figure.savefig(figure_root / "mission_016_representation.png", dpi=150)
    plt.close(figure)

    rows = []
    frozen_rows = []
    for row in summaries:
        rows.append(
            f"| {row['date']} | {row['direct_15_mse_flexion_squared']:.8f} | "
            f"{row['residual_15_mse_flexion_squared']:.8f} | "
            f"{row['residual_minus_direct_15_flexion_squared']:+.8f} | "
            f"{row['residual_minus_direct_15_percent']:+.2f}% |"
        )
        frozen_rows.append(
            f"| {row['date']} | {row['frozen_mse_flexion_squared']:.8f} | "
            f"{row['source_mean_mse_flexion_squared']:.8f} |"
        )
    ssl_rows = []
    for pretrained, random_control, budget in (
        ("pretrained_zero_shot", "random_zero_shot", 0),
        ("pretrained_frozen_ridge", "random_frozen_ridge", 15),
        ("pretrained_finetuned", "random_supervised_only", 15),
    ):
        pretrained_mse = representation_summary[pretrained][str(budget)]["mean_mse_flexion_squared"]
        random_mse = representation_summary[random_control][str(budget)]["mean_mse_flexion_squared"]
        difference = pretrained_mse - random_mse
        ssl_rows.append(
            f"| {pretrained} vs {random_control} | {budget} | "
            f"{pretrained_mse:.8f} | {random_mse:.8f} | {difference:+.8f} |"
        )
    markdown = (
        "# Mission 016: independent-date LINK transfer\n\n"
        "Observed results from authentic [LINK DANDI 001201 v0.251023.2336](https://dandiarchive.org/dandiset/001201/0.251023.2336) "
        "recordings, CC-BY-4.0 (Temmar and colleagues). The [frozen protocol](../docs/research/mission_016_protocol.json) "
        "was committed before these model runs. Source Jan 27, 2020; target Feb 6, 11 and 22, 2020. "
        "The three targets were selected by date/metadata, not scores. Native sampled clocks and trial identities are preserved.\n\n"
        "## Primary 15-label comparison\n\n"
        "Each target has 75 chronological calibration trials and 300 later evaluation trials. "
        "MSE is averaged within trial over two finger-position coordinates, then equally across trials. "
        "The contrast is source-assisted residual ridge minus target-only ridge; negative favors source assistance.\n\n"
        "| Target date | Target-only MSE (flexion²) | Source + residual MSE (flexion²) | Difference (flexion²) | Relative difference |\n"
        "|---|---:|---:|---:|---:|\n" + "\n".join(rows) + "\n\n"
        f"Equal-date mean difference: **{effects.mean():+.8f} flexion²**; all-three-date benefit criterion: "
        f"**{'met' if np.all(effects < 0) else 'not met'}**. This is a negative transfer finding for the fixed comparison, "
        "not a software failure. Source mean, frozen decoder, complete budget curves and available latent alignment "
        "are preserved in the machine report and figure. Alignment uses additional commanded-target metadata and "
        "all 75 unlabeled calibration trials; it is secondary, not an equal-input head-to-head claim.\n\n"
        "## Within-session and frozen cross-session evidence\n\n"
        f"The Jan 27 source decoder's within-session reserved 75-trial MSE is "
        f"{summaries[0]['source_mse_flexion_squared']:.8f} flexion² (previously inspected; descriptive only). "
        "Frozen source transfer on each new target is compared with the source-position mean:\n\n"
        "| Target date | Frozen-source MSE (flexion²) | Source-mean MSE (flexion²) |\n"
        "|---|---:|---:|\n" + "\n".join(frozen_rows) + "\n\n"
        "Frozen-source and source-mean controls both outperform the 15-label target-only and "
        "source-assisted ridge methods on all three dates; the primary contrast does not establish "
        "target-only recalibration as the best overall method. "
        "The full 1/5/15/50/75-label target-only and source-assisted curves are plotted without choosing "
        "a favorable budget. With three dates from one monkey, date-level effects are descriptive, not "
        "independent-subject inference.\n\n"
        "## Self-supervised representation transfer\n\n"
        "The earliest unseen target has the prespecified three-seed controls below; differences are "
        "pretrained minus matched random/supervised MSE, so negative favors pretraining.\n\n"
        "| Comparison | Target labels | Pretrained MSE (flexion²) | Control MSE (flexion²) | Difference (flexion²) |\n"
        "|---|---:|---:|---:|---:|\n" + "\n".join(ssl_rows) + "\n\n"
        "All controls, budgets and seed ranges are in the machine report. These small mixed effects do not "
        "establish transferable or foundation-model advantage. Its first-40-bin MSE must not be pooled "
        "with full-trial ridge MSE.\n\n"
        "## Cross-subject status and limits\n\n"
        "Cross-subject validation was not run because no audited public candidate meets both "
        "neural-coverage and original-target preprocessing gates.\n\n"
        "All recordings are from one monkey. Contacts are mapped by coordinates, not neuron identity. "
        "Run ID 3 in the source and 2 in targets is within-day order per the authors, but date and run effects "
        "cannot be causally separated. The native threshold-crossing series has a contradictory volts unit label; "
        "the count interpretation follows source description. Native flexion targets and upstream sensor calibration "
        "are retained. Five-trial block bands are within-session sensitivity, not population confidence intervals. "
        "No foundation-model, online-control or cross-subject success follows.\n\n"
        "Reproduce with the acquisition manifests, then run the four experiment commands in "
        "[the workflow guide](../docs/research/workflows.md). Run `python tools/report_mission_016.py` "
        "to verify stored arrays and regenerate the reports/figures.\n\n"
        "![Calibration curves](figures/mission_016_calibration.png)\n\n"
        "![Primary paired effect](figures/mission_016_primary_effect.png)\n\n"
        "![Representation controls](figures/mission_016_representation.png)\n"
    )
    (report_root / "mission_016.md").write_text(markdown)
    print(json.dumps({"dates": len(DATES), "primary_effect": float(effects.mean()),
                      "all_dates_benefit": bool(np.all(effects < 0)),
                      "representation_rows": len(representation["results"])}, indent=2))


if __name__ == "__main__":
    main()
