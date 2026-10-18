"""Explicitly acquired data checks; public CI collects but does not run these."""

import json
from pathlib import Path
import runpy

import numpy as np
import pytest

from cerebro.benchmark import array_digest
from cerebro.link import align_channel_keys, load_link
from cerebro.reliability import MODELS


@pytest.mark.data
@pytest.mark.parametrize('date', ['20200224', '20200225', '20200626'])
def test_new_native_eligibility_without_model_outcomes(date):
    manifest = json.loads(Path(f'configs/link_{date}.json').read_text())
    if not Path(manifest['local_path']).exists():
        pytest.skip('Requires explicitly acquired native LINK asset')
    recording = load_link(manifest)
    source = load_link(json.loads(Path('configs/link_20200127.json').read_text()))
    assert len(recording['trials']) == 375
    assert recording['subject_id'] == source['subject_id']
    assert recording['metadata']['position_units'] == source['metadata']['position_units']
    np.testing.assert_array_equal(align_channel_keys(source['channel_keys'], recording['channel_keys']), np.arange(96))
    for trial in recording['trials']:
        assert len(trial['timestamps']) == len(trial['counts']) == len(trial['position'])
        assert trial['counts'].shape[1] == 96
        assert np.isfinite(trial['position']).all()


@pytest.mark.data
def test_m023_risk_checkpoint_lineage_and_report_reproduction(tmp_path):
    path = Path('data/processed/m023_reliability_verified/results.json')
    if not path.exists():
        pytest.skip('Requires explicitly executed M023 reliability development study')
    report = json.loads(path.read_text())
    arrays = np.load(path.parent / 'arrays.npz')
    for name, entry in report['arrays'].items():
        assert array_digest(arrays[name]) == entry['sha256']
    assert len(report['rows']) == 369
    for row in report['rows']:
        selected = row['pool_indices']
        assert len(set(selected)) == row['budget']
        assert max(selected) < 45
        for indices in row['within_selected_trial_indices']:
            assert len(indices) == row['budget']
            assert min(indices) >= 0 and max(indices) < row['budget']
    for budget in report['config']['budgets']:
        features = arrays[f'b{budget}_features']
        for fold in report['evaluation']['budgets'][str(budget)]['folds']:
            session = fold['held_out_session']
            testing = np.asarray(fold['testing_rows'])
            for name, columns in MODELS.items():
                prefix = f'b{budget}_{session}_{name}'
                normalized = (features[testing][:, columns] - arrays[prefix + '_mean']) / arrays[prefix + '_scale']
                restored = normalized @ arrays[prefix + '_coef'].T + arrays[prefix + '_intercept']
                expected = arrays[f'b{budget}_{name}_predictions'][testing]
                np.testing.assert_allclose(restored.reshape(-1), expected, atol=1e-15, rtol=1e-12)
    regenerated = runpy.run_path('tools/report_m023.py')['render'](str(path), str(tmp_path))
    assert regenerated == json.loads(Path('reports/m023_reliability.json').read_text())
    assert (tmp_path / 'figures/m023_reliability.pdf').read_bytes() == Path('reports/figures/m023_reliability.pdf').read_bytes()


@pytest.mark.data
def test_m023_population_parameter_integrity_and_manuscript_values():
    path = Path('data/processed/m023_dynamics/parameters.npz')
    if not path.exists():
        pytest.skip('Requires explicitly executed M023 dynamics development study')
    report = json.loads(Path('reports/m023_dynamics.json').read_text())
    arrays = np.load(path)
    for name, entry in report['arrays'].items():
        assert array_digest(arrays[name]) == entry['sha256']
    assert not report['temporal_gate']['passed']
    assert sum(len(session['comparisons']) for session in report['sessions']) == 60
    manuscript = Path('reports/m023_manuscript.md').read_text()
    risk = json.loads(Path('reports/m023_reliability.json').read_text())
    primary = risk['evaluation']['budgets']['15']['models']
    for name in ('constant', 'combined', 'label_only', 'permuted_combined'):
        mantissa = f"{primary[name]['risk_mse_flexion4']:.8e}".split('e')[0]
        assert mantissa in manuscript
    for contrast in report['temporal_gate']['comparisons']:
        improvement = 100 * contrast['equal_date_mean_relative_improvement']
        assert f'{improvement:.3f}%' in manuscript
