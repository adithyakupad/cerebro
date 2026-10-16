import hashlib
import json

import numpy as np
import pytest

from cerebro.registry import build_registry


def test_registry_validates_identity_and_uses_portable_paths(tmp_path):
    config_dir = tmp_path / 'configs'
    config_dir.mkdir()
    raw = tmp_path / 'data/raw'
    raw.mkdir(parents=True)
    asset = raw / 'fixture'
    asset.write_bytes(b'fixture')
    manifest = {
        'asset_id': 'fixture', 'sha256': hashlib.sha256(b'fixture').hexdigest(),
        'size_bytes': 7, 'local_path': 'data/raw/fixture', 'version': 'fixture',
        'license': 'test fixture only',
    }
    (config_dir / 'asset.json').write_text(json.dumps(manifest))
    processed = tmp_path / 'data/processed/experiment'
    processed.mkdir(parents=True)
    np.savez(processed / 'parameters.npz', coefficients=np.eye(2))
    (processed / 'results.json').write_text(json.dumps({'schema_version': 1, 'source_sha256': 'fixture'}))
    result = build_registry(tmp_path)
    assert result['datasets'][0]['status'] == 'verified'
    assert result['checkpoints_and_arrays'][0]['array_shapes'] == {'coefficients': [2, 2]}
    assert result == build_registry(tmp_path)
    asset.write_bytes(b'changed')
    with pytest.raises(ValueError, match='checksum'):
        build_registry(tmp_path)
