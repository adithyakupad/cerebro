"""Separate finite-precision diagnostics from structural temporal leakage tests."""

import copy

import torch


def validate_causality(model, features):
    """Check a copied model in double precision without altering production state.

    Float32 convolution kernels can accumulate differently across input lengths.
    Their discrepancy is recorded, while both double-precision prefix tests
    retain a fixed 1e-12 absolute and relative tolerance.
    """
    if model.training:
        raise ValueError('Causality validation requires evaluation mode')
    if features.ndim != 3 or features.shape[1] <= 35:
        raise ValueError('Features require trials × more than 35 bins × units')
    if features.dtype != torch.float32 or not torch.isfinite(features).all():
        raise ValueError('Production features must be finite float32 values')
    diagnostic_model = copy.deepcopy(model)
    double_model = copy.deepcopy(model).double()
    double_features = features.double()
    changed_features = double_features.clone()
    changed_features[:, 35:, :] = 1000.
    devices = []
    if features.device.type == 'cuda':
        devices = [features.device.index]
    with torch.random.fork_rng(devices=devices), torch.no_grad():
        production_prefix = diagnostic_model(features[:, :35])
        production_full_prefix = diagnostic_model(features)[:, :35]
        float32_difference = production_prefix - production_full_prefix
        double_prefix = double_model(double_features[:, :35])
        double_full_prefix = double_model(double_features)[:, :35]
        double_changed_prefix = double_model(changed_features)[:, :35]
        torch.testing.assert_close(double_prefix, double_full_prefix, rtol=1e-12, atol=1e-12)
        torch.testing.assert_close(double_changed_prefix, double_full_prefix, rtol=1e-12, atol=1e-12)
        double_length_difference = double_prefix - double_full_prefix
        double_future_difference = double_changed_prefix - double_full_prefix
        return {
            'float32_cross_length_max_difference': float(float32_difference.abs().max()),
            'float64_cross_length_max_difference': float(double_length_difference.abs().max()),
            'float64_future_perturbation_max_difference': float(double_future_difference.abs().max()),
            'passed': True,
        }
