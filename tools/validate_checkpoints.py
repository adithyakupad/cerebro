"""Audit recorded artifact integrity and replay historical CPU predictions without fitting."""
import json
from pathlib import Path

import numpy as np
import torch

from cerebro.benchmark import array_digest, restore_prediction
from cerebro.link import load_link
from cerebro.registry import file_digest
from cerebro.representation_benchmark import RepresentationGRU, VelocityGRU
from cerebro.representation_transfer import prepare_sessions
from cerebro.sequence_models import make_sequence_model


def read_json(path):
    return json.loads(Path(path).read_text())


def archive(path):
    with np.load(path, allow_pickle=False) as saved:
        return {name: saved[name] for name in saved.files}


def features(counts, normalization):
    mean = np.asarray(normalization['feature_mean'])
    scale = np.asarray(normalization['feature_scale'])
    assert np.isfinite(counts).all() and (counts >= 0).all()
    assert np.isfinite(mean).all() and np.isfinite(scale).all() and (scale > 0).all()
    normalized = (counts.astype(float) - mean) / scale
    return torch.tensor(normalized, dtype=torch.float32)


def encoder(checkpoint):
    model = RepresentationGRU(checkpoint['input_units'], checkpoint['hidden'])
    model.load_state_dict(checkpoint['state_dict'])
    return model.eval()


def supervised(checkpoint, counts):
    initial = RepresentationGRU(checkpoint['input_units'], checkpoint['hidden'])
    model = VelocityGRU(initial.encoder, checkpoint['hidden'])
    model.load_state_dict(checkpoint['state_dict'])
    model.eval()
    normalization = checkpoint['normalization']
    with torch.no_grad():
        normalized_prediction = model(features(counts, normalization)).numpy()
    return normalized_prediction * normalization['target_scale'].numpy() + normalization['target_mean'].numpy()


def main():
    root = Path(__file__).resolve().parents[1]
    # Historical paths are repository relative; run from the recorded root.
    import os
    os.chdir(root)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    registry = read_json('data/processed/registry.json')
    integrity = []
    for item in registry['checkpoints_and_arrays']:
        actual = file_digest(Path(item['path']))
        assert actual == item['sha256'], item['path']
        integrity.append({'path': item['path'], 'sha256': actual, 'passed': True})
    verified = {item['path'] for item in integrity}
    arrays_checked = 0
    reports = {}
    saved_arrays = {}
    for experiment in registry['experiments']:
        path = Path(experiment['path'])
        assert file_digest(path) == experiment['sha256'], str(path)
        report = read_json(path)
        arrays = {}
        for candidate in sorted(path.parent.glob('*.npz')):
            assert str(candidate) in verified, str(candidate)
            arrays.update(archive(candidate))
        for name, metadata in report.get('arrays', {}).items():
            assert name in arrays, (str(path), name)
            assert array_digest(arrays[name]) == metadata['sha256'], (str(path), name)
            arrays_checked += 1
        reports[path.parent.name] = report
        saved_arrays[path.parent.name] = arrays
    replay = []

    def check(name, prediction, expected, dependency='self-contained parameters'):
        assert prediction.shape == expected.shape, name
        assert np.isfinite(prediction).all(), name
        exact = np.array_equal(prediction, expected)
        np.testing.assert_allclose(prediction, expected, rtol=1e-7, atol=1e-9, err_msg=name)
        replay.append({'artifact': name, 'passed': True, 'exact': exact,
                       'maximum_absolute_error': float(np.max(np.abs(prediction - expected))),
                       'dependency': dependency})

    def checkpoint(path):
        assert str(path) in verified, str(path)
        return torch.load(path, map_location='cpu', weights_only=True)

    classical = reports['classical_05']
    raw = saved_arrays['classical_05']
    validation = np.isin(raw['trial_ids'], classical['splits']['source_validation'])
    counts = raw['counts'][validation]
    for kind in classical['metrics']:
        prediction = restore_prediction(raw, kind, counts)
        check('classical_05/' + kind, prediction, raw[kind + '_prediction_m_s'])
    sequence = saved_arrays['sequence_06']
    assert np.array_equal(sequence['evaluation_trial_ids'], raw['trial_ids'][validation])
    for path in sorted(Path('data/processed/sequence_06').glob('*.pt')):
        state = checkpoint(path)
        model = make_sequence_model(state['kind'], state['input_units'], state['hidden'], state['output_coordinates'])
        model.load_state_dict(state['state_dict'])
        model.eval()
        normalization = state['normalization']
        with torch.no_grad():
            prediction = model(features(counts, normalization)).numpy()
        prediction = prediction * normalization['target_scale'].numpy() + normalization['target_mean'].numpy()
        check(str(path), prediction, sequence[path.stem + '_prediction_m_s'])
    representation = reports['representation_07']
    architecture_digest = file_digest(Path('src/cerebro/representation_benchmark.py'))
    assert architecture_digest == representation['source_sha256'], 'Representation07 architecture changed'
    saved = saved_arrays['representation_07']
    assert np.array_equal(saved['evaluation_trial_ids'], raw['trial_ids'][validation])
    for row in representation['results']:
        identifier = row['control'] + '_seed_' + str(row['seed']) + '_budget_' + str(row['label_budget_trials'])
        expected = saved[identifier + '_prediction_m_s']
        base = Path('data/processed/representation_07')
        if 'frozen_ridge' in row['control']:
            state = checkpoint(base / ('pretrained_seed_' + str(row['seed']) + '.pt'))
            if row['control'].startswith('random'):
                torch.manual_seed(row['seed'])
                model = RepresentationGRU(state['input_units'], state['hidden']).eval()
                dependency = 'probe NPZ + saved normalization + seeded initial encoder; architecture/PyTorch dependency'
            else:
                model = encoder(state)
                dependency = 'probe NPZ + pretrained encoder PT and its saved normalization'
            with torch.no_grad():
                latent = model.encode(features(counts, state['normalization'])).numpy()
            probe = archive(base / (identifier + '.npz'))
            prediction = latent.reshape(-1, state['hidden']) @ probe['coefficients'].T + probe['intercept']
            prediction = prediction.reshape(expected.shape)
        else:
            prediction = supervised(checkpoint(base / (identifier + '.pt')), counts)
            dependency = 'saved encoder/readout and normalization'
        check('representation_07/' + identifier, prediction, expected, dependency)
    transfer = reports['representation_09']
    config = transfer['config']
    recordings = [load_link(read_json(path)) for path in config['source_manifests'] + [config['target_manifest']]]
    sessions, mappings, _ = prepare_sessions(recordings, config)
    assert mappings == transfer['channel_column_mappings']
    saved = saved_arrays['representation_09']
    number = config['target_evaluation_trials']
    target = sessions[2]
    assert np.array_equal(target['trial_ids'][-number:], saved['evaluation_trial_ids'])
    assert np.array_equal(target['timestamps'][-number:], saved['evaluation_native_timestamps_seconds'])
    assert np.array_equal(target['position'][-number:], saved['evaluation_position_native_units'])
    counts = target['counts'][-number:]
    for path in sorted(Path('data/processed/representation_09').glob('*.pt')):
        if path.stem not in saved:
            continue
        state = checkpoint(path)
        if 'ridge_coefficients' in state:
            model = encoder(state)
            with torch.no_grad():
                latent = model.encode(features(counts, state['normalization'])).numpy()
            prediction = latent.reshape(-1, state['hidden']) @ state['ridge_coefficients'].numpy().T
            prediction = prediction + state['ridge_intercept'].numpy()
            prediction = prediction.reshape(saved[path.stem].shape)
        else:
            prediction = supervised(state, counts)
        check(str(path), prediction, saved[path.stem])
    report = {'schema_version': 1, 'device': 'CPU', 'torch_version': str(torch.__version__),
              'validator_sha256': file_digest(Path(__file__)),
              'representation07_architecture_sha256_verified': architecture_digest,
              'tolerance': {'rtol': 1e-7, 'atol': 1e-9}, 'file_integrity': integrity,
              'report_array_digests_checked': arrays_checked, 'prediction_replays': replay,
              'limitations': ['Integrity alone does not validate predictions for unsupported historical formats.',
                             'Representation07 frozen probes are components; random encoder recreation depends on recorded seed, architecture and PyTorch initialization.',
                             'Representation09 pretraining/session-identity components have integrity checks only.',
                             'No training; no independent scientific validation; physical velocity/native position outputs retain historical interpretation.']}
    output = Path('data/processed/mission_014/checkpoints.json')
    output.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'files_verified': len(integrity), 'array_digests_verified': arrays_checked,
                      'predictions_replayed': len(replay), 'exact': sum(row['exact'] for row in replay)}))


if __name__ == '__main__':
    main()
