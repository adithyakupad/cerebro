"""Rebuild unchanged M025 tensors into a new, checked M026 cache."""
import json
from pathlib import Path
import time

import numpy as np

from cerebro.benchmark import array_digest, prepare
from cerebro.dataset import verify_asset
from cerebro.optimization_study import check_committed_protocol, digest, read_json
from cerebro.sense import load_recording
from cerebro.event_audit import condition_keys


def main():
    config = read_json('configs/m026_neural_information.json')
    check_committed_protocol('configs/m026_neural_information.json', config)
    output = Path(config['output'])
    cache_path = output / 'inputs.npz'
    if cache_path.exists():
        raise ValueError('Prepared cache already exists; never overwrite')
    manifest = read_json(config['manifest'])
    original = read_json(config['m025_report'])
    if manifest != original['asset']:
        raise ValueError('Native asset differs from M025')
    verify_asset(Path(manifest['local_path']), manifest)
    started = time.perf_counter()
    recording = load_recording(manifest['local_path'])
    data = prepare(recording, read_json(config['preprocessing']))
    keys = condition_keys(recording.trials.loc[data['trial_ids']])
    evaluation = np.isin(data['trial_ids'], original['splits']['source_validation'])
    with np.load(Path(config['m025_directory']) / 'predictions.npz', allow_pickle=False) as old:
        for name, values in [('counts', data['counts'][evaluation]), ('target', data['velocity'][evaluation]), ('trial_ids', data['trial_ids'][evaluation]), ('unit_ids', data['unit_ids']), ('right_seconds', data['right_seconds'][evaluation])]:
            np.testing.assert_array_equal(values, old[name])
            if array_digest(values) != original['arrays'][name]['sha256']:
                raise ValueError('M025 digest differs: ' + name)
    if data['exclusions'] != original['exclusions']:
        raise ValueError('Coverage exclusions differ')
    arrays = {name: data[name] for name in ('counts', 'velocity', 'trial_ids', 'unit_ids', 'right_seconds')}
    arrays['conditions'] = keys
    np.savez_compressed(cache_path, **arrays)
    lineage = {'asset': manifest, 'm025_report_sha256': digest(config['m025_report']),
               'preprocessing_sha256': digest(config['preprocessing']), 'protocol_sha256': digest(config['protocol']),
               'cache_sha256': digest(cache_path), 'seconds': time.perf_counter() - started,
               'arrays': {name: {'shape': list(value.shape), 'sha256': array_digest(value)} for name, value in arrays.items()},
               'm025_evaluation_arrays_exact': True, 'exclusions': data['exclusions']}
    (output / 'inputs.json').write_text(json.dumps(lineage, indent=2) + '\n')
    print(json.dumps({'prepared': True, 'shape': list(data['counts'].shape), 'seconds': lineage['seconds']}))


if __name__ == '__main__':
    main()
