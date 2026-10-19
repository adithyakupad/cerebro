"""Reproduce the synthetic precision diagnosis; never read validation targets."""
import hashlib
import json
from pathlib import Path

import numpy as np
import torch

from cerebro.sequence_models import make_sequence_model


def main():
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    checkpoint_path = Path('data/processed/m025_final/cnn_200_seed_0.pt')
    saved = torch.load(checkpoint_path, weights_only=True, map_location='cpu')
    model = make_sequence_model(saved['kind'], saved['input_units'], saved['hidden'], saved['output_coordinates'])
    model.load_state_dict(saved['state_dict'])
    model.eval()
    mean = saved['normalization']['feature_mean'].numpy()
    scale = saved['normalization']['feature_scale'].numpy()
    generator = np.random.default_rng(2525)
    counts = generator.poisson(mean, size=(574, 70, saved['input_units'])).astype(float)
    normalized_counts = (counts - mean) / scale
    features = torch.tensor(normalized_counts, dtype=torch.float32)
    results = {}
    for dtype in (torch.float32, torch.float64):
        model = model.to(dtype=dtype)
        values = features.to(dtype=dtype)
        changed = values.clone()
        changed[:, 35:] = torch.flip(changed[:, 35:], dims=[1]) + 3
        with torch.no_grad():
            complete = model(values)[:, :35]
            prefix = model(values[:, :35])
            counterfactual = model(changed)[:, :35]
        results[str(dtype)] = {
            'cross_length_maximum_difference': float((prefix - complete).abs().max()),
            'same_shape_future_maximum_difference': float((counterfactual - complete).abs().max()),
        }
        if dtype == torch.float64:
            torch.testing.assert_close(prefix, complete, rtol=1e-12, atol=1e-12)
            torch.testing.assert_close(counterfactual, complete, rtol=1e-12, atol=1e-12)
    report = {'fixture': 'Synthetic Poisson counts with training feature means; no native evaluation values',
              'seed': 2525, 'shape': list(counts.shape), 'checkpoint_sha256': hashlib.sha256(checkpoint_path.read_bytes()).hexdigest(),
              'torch_version': str(torch.__version__), 'results': results,
              'limitations': 'Float32 discrepancies are diagnostics, not biological evidence or a demand for bitwise invariance across kernels/platforms.'}
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
