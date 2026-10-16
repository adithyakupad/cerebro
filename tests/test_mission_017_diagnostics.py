"""Check descriptive diagnostics and their versioned provenance."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from tools.diagnose_mission_017 import group_statistics


def test_group_statistics_preserves_trials_and_units():
    trials = [
        {"position": np.array([[0.2, 0.4], [0.4, 0.6]]),
         "counts": np.array([[0, 1], [2, 0]]), "target": np.array([0.3, 0.5])},
        {"position": np.array([[0.6, 0.8]]),
         "counts": np.array([[0, 0]]), "target": np.array([0.7, 0.9])},
    ]
    result = group_statistics(trials)
    assert result["trials"] == 2
    assert result["bins"] == 3
    assert result["channels"] == 2
    assert result["median_bins_per_trial"] == 1.5
    assert result["zero_count_fraction"] == pytest.approx(4 / 6)
    assert result["mean_count_per_contact_20ms_bin"] == pytest.approx(3 / 6)
    assert result["active_contact_count"] == 2
    assert result["unique_commanded_targets"] == 2
    np.testing.assert_allclose(result["position_mean_flexion"], [0.4, 0.6])


def test_group_statistics_rejects_empty_group():
    with pytest.raises(ValueError, match="trial group"):
        group_statistics([])


def test_versioned_diagnostic_matches_inputs():
    report = json.loads(Path("reports/mission_017_adaptation.json").read_text())
    manifest = json.loads(Path("configs/link_20200127.json").read_text())
    generator_bytes = Path("tools/diagnose_mission_017.py").read_bytes()
    historical_bytes = Path("reports/longitudinal_16_20200206.json").read_bytes()
    assert report["generator_sha256"] == hashlib.sha256(generator_bytes).hexdigest()
    assert report["historical_report_sha256"] == hashlib.sha256(historical_bytes).hexdigest()
    assert report["source_sha256"] == manifest["sha256"]
    assert len(report["retrospective_previously_inspected_targets"]) == 3
    assert report["source_trial_groups"]["first_15_development_trials"]["trials"] == 15
