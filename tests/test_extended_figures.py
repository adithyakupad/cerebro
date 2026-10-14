"""Rendering consumes verified stored results without rerunning scientific fits."""

import json
from pathlib import Path

import numpy as np
import pytest

from cerebro.benchmark import array_digest
from cerebro.extended_figures import verified_results, render_representation, render_longitudinal, render_transfer


def test_array_integrity_rejects_tampering(tmp_path):
    values = np.arange(4)
    report = {"arrays": {"values": {"shape": [4], "sha256": array_digest(values)}}}
    (tmp_path / "results.json").write_text(json.dumps(report))
    np.savez(tmp_path / "arrays.npz", values=values + 1)
    with pytest.raises(ValueError, match="integrity"):
        verified_results(tmp_path, "arrays.npz")


def test_real_stored_render(tmp_path):
    paths = [Path("data/processed/representation_07"), Path("data/processed/longitudinal_08")]
    if not all((path / "results.json").exists() for path in paths):
        pytest.skip("Stored authentic experiments have not been executed")
    (tmp_path / "figures").mkdir()
    render_representation(paths[0], tmp_path)
    render_longitudinal(paths[1], tmp_path)
    for name in ("representation_07", "longitudinal_08"):
        report = json.loads((tmp_path / f"{name}.json").read_text())
        assert len(report["render_input_report_sha256"]) == 64
        assert (tmp_path / f"{name}.md").exists()
    assert "not trial uncertainty" in (tmp_path / "representation_07.md").read_text()
    assert "in-sample" in (tmp_path / "longitudinal_08.md").read_text().lower()
    for name in ("representation_07_budget", "longitudinal_08_calibration", "longitudinal_08_shift"):
        assert (tmp_path / "figures" / f"{name}.png").stat().st_size > 1000


def test_real_transfer_render(tmp_path):
    path = Path("data/processed/representation_09")
    if not (path / "results.json").exists():
        pytest.skip("Stored transfer experiment has not been executed")
    (tmp_path / "figures").mkdir()
    render_transfer(path, tmp_path)
    rendered = json.loads((tmp_path / "representation_09.json").read_text())
    original = json.loads((path / "results.json").read_text())
    assert rendered["results"] == original["results"]
    assert rendered["session_identity_diagnostics"] == original["session_identity_diagnostics"]
    text = (tmp_path / "representation_09.md").read_text()
    assert "not biological confidence intervals" in text
    assert "evaluation_11.md" in text
    for name in ("controls", "ablations", "identity"):
        assert (tmp_path / "figures" / f"representation_09_{name}.png").stat().st_size > 1000
