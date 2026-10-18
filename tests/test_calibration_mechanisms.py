"""Synthetic fixtures verify software identities, not biological findings."""

import numpy as np
import pytest
import json
from pathlib import Path
import runpy

from cerebro.calibration_mechanisms import (
    allocate, coefficient_dispersion, development_split, ensemble_diagnostics,
    error_components, paired_session_interval, promotion_results, shrink, source_split,
)


def trials(number=12):
    rows = []
    for index in range(number):
        rows.append({'trial_id': index, 'timestamps': np.array([index * 2., index * 2. + .02]),
                     'target': np.array([index % 3, 0]), 'position': np.zeros((2, 2))})
    return rows


@pytest.mark.parametrize('policy', ['chronological', 'uniform', 'balanced'])
def test_allocation_budget_no_replacement_and_reproducibility(policy):
    rows = trials()
    selected = allocate(rows, 6, policy, 22)
    np.testing.assert_array_equal(selected, allocate(rows, 6, policy, 22))
    assert len(set(selected)) == 6
    assert np.all(np.diff(selected) > 0)
    assert selected.min() >= 0 and selected.max() < len(rows)
    if policy == 'balanced':
        assert len({tuple(rows[index]['target']) for index in selected}) == 3


def test_balanced_exhausts_unequal_strata():
    rows = trials(8)
    np.testing.assert_array_equal(allocate(rows, 8, 'balanced', 2), np.arange(8))
    for budget in (0, 9):
        with pytest.raises(ValueError):
            allocate(rows, budget, 'uniform', 0)


def test_split_isolates_permitted_rows_before_validation():
    rows = trials()
    rows[-1]['timestamps'][:] = np.nan
    recording = {'trials': rows, 'timestamps_reference_time': '2020-01-01T00:00:00+00:00'}
    pool, evaluation = development_split(recording, 10, 6)
    assert [row['trial_id'] for row in pool] == list(range(6))
    assert [row['trial_id'] for row in evaluation] == list(range(6, 10))
    assert not set(row['trial_id'] for row in pool) & set(row['trial_id'] for row in evaluation)
    rows[2]['trial_id'] = rows[1]['trial_id']
    with pytest.raises(ValueError, match='unique'):
        development_split(recording, 10, 6)


def test_shrink_endpoints_and_validation():
    frozen = np.array([[1., 2.]])
    direct = np.array([[3., 6.]])
    np.testing.assert_array_equal(shrink(frozen, direct, 0), frozen)
    np.testing.assert_array_equal(shrink(frozen, direct, 1), direct)
    np.testing.assert_array_equal(shrink(frozen, direct, .5), [[2., 4.]])
    with pytest.raises(ValueError):
        shrink(frozen, direct, 1.1)


def test_source_partition_fails_closed():
    assert len(source_split(trials(), 10, 7)) == 10
    for training, inner in ((13, 7), (10, 10), (10, 0)):
        with pytest.raises(ValueError):
            source_split(trials(), training, inner)


def test_equal_trial_bias_variance_and_offset_identity():
    rows = trials(2)
    rows[1]['position'] = np.zeros((6, 2))
    prediction = np.concatenate([np.ones((2, 2)), np.full((6, 2), 3.)])
    predictions = np.stack([prediction, prediction * 2])
    coefficients = np.stack([np.zeros((2, 3)), np.ones((2, 3))])
    summary = ensemble_diagnostics(rows, predictions, coefficients)
    assert summary['mean_subset_mse'] == pytest.approx(12.5)
    assert summary['bias_variance_identity_error'] == pytest.approx(0., abs=1e-12)
    offset, centered = error_components(rows, prediction)
    assert offset + centered == pytest.approx(5.)
    assert coefficient_dispersion(coefficients) == pytest.approx(.25)
    assert coefficient_dispersion(coefficients[:1]) == 0


def test_common_coefficient_frame_and_interval_reproducibility():
    raw_coefficients = np.array([[1., 2.]])
    scales = np.array([[1., 2.], [3., 4.]])
    scaled_coefficients = raw_coefficients[None, :, :] * scales[:, None, :]
    recovered = scaled_coefficients / scales[:, None, :]
    assert coefficient_dispersion(recovered) == 0
    values = [np.arange(10.), np.arange(10.) + 1]
    interval = paired_session_interval(values, 100, 2, 22)
    assert interval == paired_session_interval(values, 100, 2, 22)
    with pytest.raises(ValueError):
        paired_session_interval([np.ones(2)], 100, 3, 22)


def test_null_gate_preserves_no_promotion():
    model_names = ['direct_1', 'direct_100']
    for weight in (.1, .25, .5):
        model_names.extend([f'direct_shrink_{weight:g}', f'residual_shrink_{weight:g}'])
    models = {name: {'subset_trial_mse': [np.ones(10).tolist()]} for name in model_names}
    group = {'budget': 15, 'policy': 'chronological', 'models': models}
    session = {'groups': [group], 'frozen_trial_mse': np.ones(10).tolist()}
    config = {'shrinkage_weights': [.1, .25, .5], 'primary_budget': 15,
              'bootstrap_draws': 100, 'bootstrap_block_trials': 5,
              'random_seed': 22, 'practical_relative_improvement': .05}
    decision = promotion_results([session] * 3, config)
    assert decision['selected_method'] is None
    assert len(decision['candidate_decisions']) == 7


def test_promotion_first_passing_priority_and_single_date_failure():
    names = ['direct_1', 'direct_100']
    for weight in (.1, .25, .5):
        names.extend([f'direct_shrink_{weight:g}', f'residual_shrink_{weight:g}'])
    sessions = []
    for index in range(3):
        models = {name: {'subset_trial_mse': [np.full(10, .8).tolist()]} for name in names}
        models['direct_1']['subset_trial_mse'] = [np.full(10, 1.2).tolist()]
        sessions.append({'groups': [{'budget': 15, 'policy': 'chronological', 'models': models}],
                         'frozen_trial_mse': np.ones(10).tolist()})
    config = {'shrinkage_weights': [.1, .25, .5], 'primary_budget': 15,
              'bootstrap_draws': 100, 'bootstrap_block_trials': 5,
              'random_seed': 22, 'practical_relative_improvement': .05}
    assert promotion_results(sessions, config)['selected_method'] == 'direct_shrink_0.1'
    sessions[0]['groups'][0]['models']['direct_shrink_0.1']['subset_trial_mse'] = [np.full(10, 1.01).tolist()]
    result = promotion_results(sessions, config)
    assert not result['candidate_decisions'][0]['passed']
    assert result['selected_method'] == 'residual_shrink_0.1'


def test_report_rejects_incompatible_scientific_narrative(tmp_path):
    report = {'config': json.loads(Path('configs/m022_calibration.json').read_text()),
              'sessions': [{'session': date} for date in ('20200130', '20200204', '20200205')],
              'source_training_bins': 21701, 'selected_source_alpha': 1000,
              'promotion': {'selected_method': 'different_outcome'}}
    path = tmp_path / 'results.json'
    path.write_text(json.dumps(report))
    render = runpy.run_path('tools/report_m022.py')['render']
    with pytest.raises(ValueError, match='only renders'):
        render(path, tmp_path)


@pytest.mark.data
def test_real_m022_lineage_decompositions_and_report_reproduction(tmp_path):
    results_path = Path('data/processed/m022_calibration_verified/results.json')
    if not results_path.exists():
        pytest.skip('Requires explicitly executed M022 development experiment')
    from cerebro.benchmark import array_digest
    from cerebro.dataset import verify_asset

    report = json.loads(results_path.read_text())
    arrays = np.load(results_path.parent / 'arrays.npz')
    for name, entry in report['arrays'].items():
        assert list(arrays[name].shape) == entry['shape']
        assert array_digest(arrays[name]) == entry['sha256']
    verify_asset(report['lineage']['source_manifest']['local_path'], report['lineage']['source_manifest'])
    assert len(report['lineage']['allocations']) == 369
    for session in report['sessions']:
        verify_asset(session['manifest']['local_path'], session['manifest'])
        assert len(session['pool_trial_ids']) == 45
        assert len(session['evaluation_trial_ids']) == 30
        assert not set(session['pool_trial_ids']) & set(session['evaluation_trial_ids'])
        for group in session['groups']:
            for model in group['models'].values():
                assert abs(model['bias_variance_identity_error']) < 1e-12
                total = model['mean_subset_offset_mse'] + model['mean_subset_centered_mse']
                assert total == pytest.approx(model['mean_subset_mse'], abs=1e-12)
    render = runpy.run_path('tools/report_m022.py')['render']
    regenerated = render(results_path, tmp_path)
    published = json.loads(Path('reports/m022_calibration_mechanisms.json').read_text())
    assert regenerated == published
    assert (tmp_path / 'figures/m022_mechanism_comparison.pdf').read_bytes() == Path('reports/figures/m022_mechanism_comparison.pdf').read_bytes()
