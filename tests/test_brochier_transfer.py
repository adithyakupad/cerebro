"""Small synthetic checks of the frozen native-data analysis mechanics."""

import numpy as np
import pytest

from tools.run_brochier_transfer import (
    bootstrap_contrast,
    count_trial_spikes,
    single_unit_indices,
    split_calibration,
)


def test_binning_preserves_half_open_boundaries_and_unit_axis():
    unit_spikes = [np.array([999, 1000, 1599, 1600, 9400]), np.array([], dtype=int)]
    counts = count_trial_spikes(unit_spikes, go_tick=1000)
    assert counts.shape == (14, 2)
    assert counts[0].tolist() == [2, 0]
    assert counts[1].tolist() == [1, 0]
    assert counts.sum() == 3
    assert counts[-1, 0] == 0  # right endpoint at 9400 is excluded


def test_multiple_source_sua_ids_are_not_collapsed(tmp_path):
    xml = """<odML><section><name>Electrode_003</name><section>
    <name>OfflineSpikeSorting</name><property><name>SUAIDs</name>
    <value>1</value><value>2</value></property></section></section></odML>"""
    path = tmp_path / "source.odml"
    path.write_text(xml)
    channels = np.array([("ch3#1",), ("ch3#2",), ("ch3#255",)], dtype=[("name", "U20")])
    assert single_unit_indices(path, channels) == [0, 1]


def test_chronological_target_calibration_is_class_stratified():
    labels = ["SGLF", "SGHF"] * 6
    rows = [{"trial_id": index, "condition": label} for index, label in enumerate(labels)]
    calibration, evaluation = split_calibration(rows)
    assert [row["trial_id"] for row in calibration] == list(range(10))
    assert [row["trial_id"] for row in evaluation] == [10, 11]


def test_trial_conditional_bootstrap_is_reproducible():
    labels = np.array(["SGLF", "SGHF", "PGLF", "PGHF"] * 3)
    assisted = labels.copy()
    target = np.array(["SGLF"] * len(labels))
    first = bootstrap_contrast(labels, assisted, target, repetitions=20)
    second = bootstrap_contrast(labels, assisted, target, repetitions=20)
    assert first == second
    assert first == pytest.approx([0.75, 0.75])
