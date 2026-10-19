"""Preparation must reproduce M025's saved dtype as well as count values."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

from cerebro.benchmark import array_digest


def test_preparation_preserves_original_float_counts_and_checks_cache(tmp_path, monkeypatch):
    path = Path('tools/m026_prepare.py')
    spec = importlib.util.spec_from_file_location('m026_prepare', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    data = {'counts': np.ones((2, 5, 3), dtype=np.int64),
            'velocity': np.zeros((2, 5, 2)), 'trial_ids': np.array([1, 2]),
            'unit_ids': np.arange(3), 'right_seconds': np.tile(np.arange(5), (2, 1)).astype(float),
            'exclusions': []}
    expected = {'counts': data['counts'][1:].astype(float), 'target': data['velocity'][1:],
                'trial_ids': data['trial_ids'][1:], 'unit_ids': data['unit_ids'],
                'right_seconds': data['right_seconds'][1:]}
    np.savez(tmp_path / 'predictions.npz', **expected)
    config = {'output': str(tmp_path), 'manifest': 'manifest', 'm025_report': 'original',
              'm025_directory': str(tmp_path), 'preprocessing': 'preprocessing', 'protocol': 'protocol'}
    manifest = {'local_path': 'unused'}
    original = {'asset': manifest, 'splits': {'source_validation': [2]}, 'exclusions': [],
                'arrays': {name: {'sha256': array_digest(values)} for name, values in expected.items()}}
    documents = {'configs/m026_neural_information.json': config, 'manifest': manifest,
                 'original': original, 'preprocessing': {}}
    monkeypatch.setattr(module, 'read_json', lambda name: documents[name])
    monkeypatch.setattr(module, 'check_committed_protocol', lambda *args: None)
    monkeypatch.setattr(module, 'verify_asset', lambda *args: None)
    monkeypatch.setattr(module, 'digest', lambda *args: 'fixture-checksum')
    trials = pd.DataFrame(index=[1, 2])
    monkeypatch.setattr(module, 'load_recording', lambda *args: SimpleNamespace(trials=trials))
    monkeypatch.setattr(module, 'prepare', lambda *args: data)
    monkeypatch.setattr(module, 'condition_keys', lambda *args: np.array(['a', 'a']))
    module.main()
    with np.load(tmp_path / 'inputs.npz', allow_pickle=False) as saved:
        assert saved['counts'].dtype == np.float64
        np.testing.assert_array_equal(saved['counts'], data['counts'])
    lineage = json.loads((tmp_path / 'inputs.json').read_text())
    assert lineage['m025_evaluation_arrays_exact']
    assert lineage['arrays']['counts']['shape'] == [2, 5, 3]
