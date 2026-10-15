"""Check the versioned Mission 016 claims against their stored trial results."""

import hashlib
import json
from pathlib import Path

import numpy as np


def file_sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def test_mission_016_primary_results_and_provenance():
    summary = json.loads(Path("reports/mission_016.json").read_text())
    protocol_path = Path("docs/research/mission_016_protocol.json")
    assert summary["protocol_sha256"] == file_sha256(protocol_path)
    assert summary["experiment_git_revision"] == "5a7376a694825005500cd357694fa8e27e2ce31e"

    differences = []
    for row in summary["primary"]["per_date"]:
        date = row["date"]
        report_path = Path(f"reports/longitudinal_16_{date}.json")
        report = json.loads(report_path.read_text())
        assert file_sha256(report_path) == summary["source_report_sha256"][date]
        assert report["target"]["sha256"] == row["asset_sha256"]
        assert report["git_revision"] == summary["experiment_git_revision"]
        assert not report["git_dirty"]

        splits = report["splits"]
        calibration_ids = set(splits["target_unlabeled_calibration_pool"])
        evaluation_ids = set(splits["target_evaluation"])
        assert len(calibration_ids) == 75
        assert len(evaluation_ids) == 300
        assert calibration_ids.isdisjoint(evaluation_ids)
        assert set(splits["target_label_budgets"]["15"]).issubset(calibration_ids)

        direct = np.asarray(report["metrics"]["direct_recalibration_15"]["trial_mse_flexion2"])
        residual = np.asarray(report["metrics"]["source_plus_residual_15"]["trial_mse_flexion2"])
        assert direct.shape == residual.shape == (300,)
        difference = float(np.mean(residual - direct))
        np.testing.assert_allclose(difference, row["residual_minus_direct_15_flexion_squared"])
        differences.append(difference)

    equal_date_mean = float(np.mean(differences))
    np.testing.assert_allclose(
        equal_date_mean,
        summary["primary"]["equal_date_mean_residual_minus_direct_15_flexion_squared"],
    )
    assert summary["primary"]["all_three_dates_benefit"] == all(value < 0 for value in differences)


def test_mission_016_representation_controls_preserved():
    summary = json.loads(Path("reports/mission_016.json").read_text())
    report_path = Path("reports/representation_16_20200206.json")
    report = json.loads(report_path.read_text())
    assert file_sha256(report_path) == summary["representation_report_sha256"]
    assert report["git_revision"] == summary["experiment_git_revision"]
    assert not report["git_dirty"]
    assert len(report["results"]) == 42
    for control, budgets in summary["representation_earliest_target_only"].items():
        for budget, published in budgets.items():
            selected = [row["mse_native_position_squared"] for row in report["results"]
                        if row["control"] == control
                        and row["target_label_budget"] == int(budget)]
            assert len(selected) == 3
            np.testing.assert_allclose(np.mean(selected), published["mean_mse_flexion_squared"])
