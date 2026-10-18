"""Integration tables expose preserved outcomes without another experiment."""

import csv
import importlib.util
import io
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('m024_tables', ROOT / 'tools/m024_tables.py')
TABLES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TABLES)


def test_integration_tables_match_committed_inputs_and_are_deterministic():
    first = TABLES.integration_tables()
    second = TABLES.integration_tables()
    assert first == second
    for name, content in first.items():
        assert content == (ROOT / 'reports/v1_1_tables' / name).read_text()
    mitigation = list(csv.DictReader(io.StringIO(first['m022_promotion.csv'])))
    risk = list(csv.DictReader(io.StringIO(first['m023_risk.csv'])))
    temporal = list(csv.DictReader(io.StringIO(first['m023_temporal.csv'])))
    assert len(mitigation) == 14
    assert len(risk) == 90
    assert len(temporal) == 3
    assert all(row['candidate_passed'] == 'False' for row in mitigation)
    combined = [row for row in risk if row['budget'] == '15' and row['model'] == 'combined']
    mean_risk = sum(float(row['risk_mse_flexion4']) for row in combined) / len(combined)
    assert abs(mean_risk - 1.093746724e-5) < 1e-14
    assert all(float(row['pooled_balanced_accuracy']) == 0.675 for row in combined)

    assert all(row['primary_passed'] == 'False' for row in temporal)
