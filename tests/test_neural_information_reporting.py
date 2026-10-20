"""Synthetic report fixtures test rendering/replay, never scientific findings."""
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

from cerebro.neural_information import summarize


def test_reporting_is_deterministic_and_explicitly_retrospective(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location('m026_report', Path('tools/m026_report.py').resolve())
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)
    target = np.zeros((3, 7, 2))
    keys = np.array(['a', 'b', 'a'])
    predictions = {}
    names = ['neural_200', 'neural_20', 'clock', 'zero', 'permuted', 'permuted_real',
             'condition_template', 'go_time_template', 'history_ridge', 'kalman', 'mean']
    for index, name in enumerate(names):
        predictions[name] = target + .1 * (index + 1)
    predictions['history_ridge'][:, :4] = np.nan
    config = {'score_start_bin': 4, 'bootstrap_draws': 20, 'bootstrap_seed': 26, 'descriptive_reduction': .05}
    summary = summarize(target, predictions, keys, config)
    models = []
    for mode in ('zero', 'clock', 'permuted'):
        for seed in (0, 1, 2):
            models.append({'name': mode + '_seed_' + str(seed), 'mode': mode, 'seed': seed,
                           'selected_epoch': 1, 'history': [{'epoch': 1, 'inner_physical_mse': .1}],
                           'fit_seconds': .01, 'evaluation_forward_seconds': .001,
                           'mapping': {'source_training': {'unchanged': 0}}, 'parameters': 16354,
                           'restoration_exact': True})
    report = {'evidence_status': 'RETROSPECTIVE_SINGLE_SESSION_DIAGNOSTIC', 'models': models,
              'summary': summary, 'condition_template_fallback_trials': 0,
              'seconds_total': 1., 'lineage': {'seconds': .1}}
    monkeypatch.chdir(tmp_path)
    Path('reports/figures').mkdir(parents=True)
    Path('reports/m026_neural_information.json').write_text(json.dumps(report))
    renderer.main()
    artifacts = ['reports/m026_neural_information.md', 'reports/m026_artifacts.json',
                 'reports/figures/m026_neural_information.pdf', 'reports/figures/m026_training_curves.pdf',
                 'reports/figures/m026_error_strata.pdf']
    first = {name: hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in artifacts}
    renderer.main()
    second = {name: hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in artifacts}
    assert first == second
    markdown = Path(artifacts[0]).read_text()
    assert 'Retrospective diagnostic analysis' in markdown
    assert 'not a second independent confirmation' in markdown
