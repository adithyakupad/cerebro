"""Build portable local data, experiment and checkpoint registries."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from cerebro.dataset import verify_asset


def file_digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def build_registry(root):
    root = Path(root).resolve()
    datasets = []
    configurations = []
    experiments = []
    checkpoints = []
    for path in sorted((root / 'configs').glob('*.json')):
        config = json.loads(path.read_text())
        entry = {'path': str(path.relative_to(root)), 'sha256': file_digest(path)}
        if 'asset_id' in config:
            raw_path = Path(config['local_path'])
            if raw_path.is_absolute() or '..' in raw_path.parts:
                raise ValueError('Dataset registry requires repository-relative local paths')
            asset_path = root / raw_path
            entry['asset_id'] = config['asset_id']
            entry['published_sha256'] = config['sha256']
            entry['source_version'] = config['version']
            entry['license'] = config['license']
            entry['status'] = 'missing'
            if asset_path.exists():
                verify_asset(asset_path, config)
                entry['status'] = 'verified'
            datasets.append(entry)
        else:
            configurations.append(entry)
    processed = root / 'data/processed'
    for path in sorted(processed.glob('*/results.json')):
        result = json.loads(path.read_text())
        experiments.append({
            'path': str(path.relative_to(root)), 'sha256': file_digest(path),
            'schema_version': result.get('schema_version'),
            'revision': result.get('git_revision'),
            'source_sha256': result.get('source_sha256'),
            'config': result.get('config'),
        })
    for suffix in ('*.pt', '*.npz'):
        for path in sorted(processed.glob('*/' + suffix)):
            entry = {'path': str(path.relative_to(root)), 'sha256': file_digest(path)}
            if path.suffix == '.npz':
                with np.load(path, allow_pickle=False) as archive:
                    entry['array_shapes'] = {name: list(archive[name].shape) for name in archive.files}
                entry['format'] = 'numerical NPZ; no pickle'
            else:
                entry['format'] = 'PyTorch checkpoint; load trusted files with weights_only=True'
            checkpoints.append(entry)
    return {
        'schema_version': 1, 'datasets': datasets, 'configurations': configurations,
        'experiments': experiments, 'checkpoints_and_arrays': checkpoints,
        'limitations': 'Archive byte digests identify saved artifacts, not numerical reproducibility across ZIP/PyTorch serializers. Registries do not infer scientific validity.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--output', default='data/processed/registry.json')
    arguments = parser.parse_args()
    result = build_registry(arguments.root)
    output = Path(arguments.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({key: len(result[key]) for key in ('datasets', 'experiments', 'checkpoints_and_arrays')}))


if __name__ == '__main__':
    main()
