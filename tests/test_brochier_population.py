"""Small synthetic checks for the frozen population measurements."""

import json
from pathlib import Path

import numpy as np
import pytest

from tools.brochier_population import (
    EXPECTED_CONFIG,
    bootstrap_statistics,
    file_sha256,
    fano_by_condition,
    pair_summary,
    scalar_statistics,
    shared_variance_ratio,
    window_counts,
)


def test_native_tick_bins_are_half_open_and_conserve_window_spikes():
    config = {**EXPECTED_CONFIG, "pre_ticks": 600, "post_ticks": 1200}
    spikes = [np.array([9399, 9400, 9999, 10000, 10599, 10600, 11199, 11200])]
    counts = window_counts(spikes, event_tick=10000, config=config)
    assert counts.shape == (3, 1)
    assert counts[:, 0].tolist() == [2, 2, 2]
    assert counts.sum() == 6


def test_fano_excludes_low_mean_cells_and_uses_sample_variance():
    config = {**EXPECTED_CONFIG, "pre_ticks": 600, "post_ticks": 600}
    labels = np.repeat(config["conditions"], 3)
    counts = np.zeros((12, 2, 2), dtype=int)
    counts[:, 1, 0] = np.tile([1, 2, 3], 4)
    factors, excluded = fano_by_condition(counts, labels, config)
    np.testing.assert_allclose(factors[:, 0], 0.5)
    assert np.isnan(factors[:, 1]).all()
    assert excluded == 4


def test_residuals_match_condition_and_event_time_without_cross_trial_leakage():
    config = {**EXPECTED_CONFIG, "condition_min_trials": 2}
    labels = np.repeat(config["conditions"], 2)
    counts = np.zeros((8, 30, 2), dtype=int)
    counts[1::2, 10:, 0] = 2
    counts[:, 10:, 1] = 1
    estimates = scalar_statistics(counts, labels, config)
    assert estimates["residual_count_sum_max"] == 0
    assert estimates["fano_eligible_cells"] == 8
    assert estimates["residual_pairs"]["undefined_pairs"] == 1


def test_shared_variance_reference_and_undefined_edges():
    rates = np.array([[1, 1], [-1, -1], [1, 1], [-1, -1]], dtype=float)
    assert shared_variance_ratio(rates) == pytest.approx(2.0)
    assert np.isnan(shared_variance_ratio(np.zeros((4, 2))))
    with pytest.raises(ValueError):
        shared_variance_ratio(np.zeros((1, 2)))
    assert pair_summary(np.eye(2) * np.nan)["undefined_pairs"] == 1


def test_whole_trial_bootstrap_is_seed_reproducible():
    config = {**EXPECTED_CONFIG, "condition_min_trials": 3, "bootstrap_draws": 20}
    labels = np.repeat(config["conditions"], 3)
    counts = np.random.default_rng(8).poisson(0.4, size=(12, 30, 3))
    first_metrics, first_bands = bootstrap_statistics(counts, labels, config, seed=42)
    second_metrics, second_bands = bootstrap_statistics(counts, labels, config, seed=42)
    assert first_metrics == second_metrics
    np.testing.assert_array_equal(first_bands, second_bands)


def test_published_report_is_tied_to_protocol_code_and_source_manifest():
    report = json.loads(Path("reports/mission_020_brochier_population.json").read_text())
    manifest = json.loads(Path("docs/datasets/mission_019_brochier_assets.json").read_text())
    assert report["protocol_sha256"] == file_sha256("docs/research/mission_020_protocol.md")
    assert report["config_sha256"] == file_sha256("configs/brochier_population_20.json")
    assert report["analysis_code_sha256"] == file_sha256("tools/brochier_population.py")
    assert report["dataset_manifest_sha256"] == file_sha256("docs/datasets/mission_019_brochier_assets.json")
    for session in manifest["sessions"]:
        observed = report["sessions"][session["subject"]]
        for name in (session["sorted_nev"], session["neural_nsx"], f"{session['id']}.odml"):
            assert observed["verified_asset_sha256"][name] == manifest["assets"][name]["sha256"]
        assert observed["tensor_shape_trials_bins_units"][1] == 30
        assert min(observed["condition_counts"].values()) >= 20
        assert observed["statistics"]["residual_count_sum_max"] < 1e-9
