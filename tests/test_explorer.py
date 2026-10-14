"""Synthetic reports test the explorer, not neuroscience findings."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from cerebro.benchmark import array_digest
from cerebro.explorer import generate


def fixture_run(tmp_path):
    arrays = {
        "trial_ids": np.array([10, 30]), "velocity_m_s": np.zeros((2, 3, 2)),
        "counts": np.ones((2, 3, 2)), "unit_ids": np.array([1, 2]),
        "bin_right_seconds": np.array([[.02, .04, .06], [1.02, 1.04, 1.06]]),
        "mean_prediction_m_s": np.zeros((1, 3, 2)),
        "pca_validation_latents": np.zeros((1, 3, 2)),
    }
    report = {
        "evaluation_trial_ids": [30], "metrics": {"mean": {"mse_m2_s2": 0.}},
        "config": {"bin_width_seconds": .02}, "asset": {"label": "Synthetic </script><script>alert(1)</script>"},
        "limitations": ["Synthetic fixture"], "information_policy": "Fixture only",
        "arrays": {name: {"sha256": array_digest(values)} for name, values in arrays.items()},
    }
    np.savez(tmp_path / "arrays.npz", **arrays)
    (tmp_path / "results.json").write_text(json.dumps(report))
    return arrays


def test_generation_escapes_embedded_source_and_preserves_dimensions(tmp_path):
    fixture_run(tmp_path)
    destination = generate(tmp_path, output=tmp_path / "explorer.html")
    document = destination.read_text()
    assert "Synthetic \\u003c/script>" in document
    assert "Synthetic </script>" not in document
    assert '"trial_ids": [30]' in document
    assert '"heldin_units": 2' in document
    assert "textContent" in document and "innerHTML" not in document
    assert "https://" not in document
    assert "join('\\n')" in document


def test_tampered_arrays_rejected(tmp_path):
    arrays = fixture_run(tmp_path)
    arrays["counts"][0, 0, 0] = 99
    np.savez(tmp_path / "arrays.npz", **arrays)
    with pytest.raises(ValueError, match="provenance"):
        generate(tmp_path, output=tmp_path / "explorer.html")


def test_sequence_lineage_mismatch_rejected(tmp_path):
    fixture_run(tmp_path)
    sequence = tmp_path / "sequence"
    sequence.mkdir()
    (sequence / "results.json").write_text(json.dumps({"input_report_sha256": "wrong"}))
    with pytest.raises(ValueError, match="classical provenance"):
        generate(tmp_path, sequence, tmp_path / "explorer.html")


def test_verified_sequence_predictions_and_trial_identity(tmp_path):
    fixture_run(tmp_path)
    sequence = tmp_path / "sequence"
    sequence.mkdir()
    arrays = {"evaluation_trial_ids": np.array([30]),
              "gru_seed_4_prediction_m_s": np.zeros((1, 3, 2))}
    report = {
        "input_report_sha256": hashlib.sha256((tmp_path / "results.json").read_bytes()).hexdigest(),
        "results": [{"model": "gru", "seed": 4, "mse_m2_s2": 0.}],
        "arrays": {name: {"sha256": array_digest(values)} for name, values in arrays.items()},
    }
    np.savez(sequence / "predictions.npz", **arrays)
    (sequence / "results.json").write_text(json.dumps(report))
    destination = generate(tmp_path, sequence, tmp_path / "explorer.html")
    assert '"gru_seed_4"' in destination.read_text()
    arrays["evaluation_trial_ids"][0] = 10
    report["arrays"]["evaluation_trial_ids"]["sha256"] = array_digest(arrays["evaluation_trial_ids"])
    np.savez(sequence / "predictions.npz", **arrays)
    (sequence / "results.json").write_text(json.dumps(report))
    with pytest.raises(ValueError, match="identities"):
        generate(tmp_path, sequence, tmp_path / "explorer.html")


def test_real_local_explorer_generation(tmp_path):
    classical = Path("data/processed/classical_05")
    if not (classical / "results.json").exists():
        pytest.skip("Real benchmark has not run; no implicit acquisition")
    destination = generate(classical, output=tmp_path / "explorer.html")
    assert destination.stat().st_size > 1000
    assert '"heldin_units": 107' in destination.read_text()


def test_additional_longitudinal_integrity_and_native_units(tmp_path):
    from cerebro.explorer import additional_results
    arrays = {'fixture': np.zeros(2)}
    report = {
        'arrays': {'fixture': {'sha256': array_digest(arrays['fixture'])}},
        'config': {'calibration_budgets': [1, 5]},
        'metrics': {
            'frozen_source': {'mean_trial_mse_flexion2': .02},
            'direct_recalibration_1': {'mean_trial_mse_flexion2': .03},
        },
        'geometry': {}, 'source': {'asset_id': 'fixture'}, 'target': {'asset_id': 'fixture'},
        'information_policy': 'Synthetic test only', 'limitations': [],
    }
    np.savez(tmp_path / 'arrays.npz', **arrays)
    (tmp_path / 'results.json').write_text(json.dumps(report))
    data = additional_results(longitudinal=tmp_path)
    assert data['longitudinal']['curves']['direct_recalibration'] == [[1, .03]]
    arrays['fixture'][0] = 1
    np.savez(tmp_path / 'arrays.npz', **arrays)
    with pytest.raises(ValueError, match='provenance'):
        additional_results(longitudinal=tmp_path)
