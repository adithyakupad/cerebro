"""Reproduce integration tables from immutable public results; no fitting or raw data."""

import csv
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def integration_tables(root=ROOT):
    """Return deterministic CSV text, keeping each original estimand distinct."""
    mechanism = json.loads((root / 'reports/m022_calibration_mechanisms.json').read_text())
    reliability = json.loads((root / 'reports/m023_reliability.json').read_text())
    dynamics = json.loads((root / 'reports/m023_dynamics.json').read_text())
    tables = {}
    rows = [['candidate', 'control', 'mean_date_relative_improvement', 'paired_mse_flexion2',
             'conditional_95_low', 'conditional_95_high', 'every_date_better', 'comparison_passed', 'candidate_passed']]
    for decision in mechanism['promotion']['candidate_decisions']:
        for control, comparison in sorted(decision['comparisons'].items()):
            interval = comparison['conditional_block_interval']
            rows.append([decision['candidate'], control, comparison['mean_relative_improvement'],
                         comparison['paired_mse_difference'], *interval,
                         comparison['every_date_better'], comparison['passed'], decision['passed']])
    tables['m022_promotion.csv'] = rows
    rows = [['budget', 'model', 'session', 'risk_mse_flexion4', 'pooled_balanced_accuracy',
             'harm_fraction', 'policy_mse_flexion2', 'always_frozen_mse_flexion2',
             'always_direct_mse_flexion2']]
    for budget, results in sorted(reliability['evaluation']['budgets'].items(), key=lambda item: int(item[0])):
        for model, values in sorted(results['models'].items()):
            for session in values['per_session']:
                rows.append([budget, model, session['session'], session['risk_mse_flexion4'],
                             values['pooled_session_weighted_balanced_accuracy'], session['harm_fraction'],
                             session['policy_mse_flexion2'], session['always_frozen_mse_flexion2'],
                             session['always_direct_mse_flexion2']])
    tables['m023_risk.csv'] = rows
    rows = [['control', 'mean_date_relative_improvement', 'paired_mse_standardized_count2',
             'conditional_95_low', 'conditional_95_high', 'comparison_passed', 'primary_passed']]
    for comparison in dynamics['temporal_gate']['comparisons']:
        rows.append([comparison['control'], comparison['equal_date_mean_relative_improvement'],
                     comparison['equal_date_paired_mse_difference'], *comparison['conditional_95_block_interval'],
                     comparison['passed'], dynamics['temporal_gate']['passed']])
    tables['m023_temporal.csv'] = rows
    rendered = {}
    for name, table_rows in tables.items():
        buffer = io.StringIO(newline='')
        writer = csv.writer(buffer, lineterminator='\n')
        writer.writerows(table_rows)
        rendered[name] = buffer.getvalue()
    return rendered


def main():
    output = ROOT / 'reports/v1_1_tables'
    output.mkdir(parents=True, exist_ok=True)
    for name, content in integration_tables().items():
        (output / name).write_text(content)


if __name__ == '__main__':
    main()
