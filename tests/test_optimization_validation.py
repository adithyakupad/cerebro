"""Synthetic causality checks distinguish future access from float32 rounding."""

import pytest
import torch

from cerebro.optimization_validation import validate_causality
from cerebro.sequence_models import make_sequence_model


def test_cnn_causality_preserves_production_state_inputs_and_random_state():
    torch.manual_seed(25)
    model = make_sequence_model('temporal_cnn', 4, hidden=8)
    model.eval()
    features = torch.randn(2, 70, 4)
    original_features = features.clone()
    original_state = {name: value.clone() for name, value in model.state_dict().items()}
    random_state = torch.get_rng_state()
    result = validate_causality(model, features)
    assert result['passed']
    assert result['float64_cross_length_max_difference'] <= 1e-12
    assert result['float64_future_perturbation_max_difference'] <= 1e-12
    assert not model.training
    assert torch.equal(features, original_features)
    assert torch.equal(random_state, torch.get_rng_state())
    for name, value in model.state_dict().items():
        assert value.dtype == original_state[name].dtype
        assert torch.equal(value, original_state[name])


class FutureReadingModel(torch.nn.Module):
    def forward(self, features):
        future_mean = features.mean(dim=1, keepdim=True)
        return features[:, :, :2] + future_mean[:, :, :2]


def test_future_reading_model_is_rejected():
    model = FutureReadingModel().eval()
    features = torch.zeros(2, 70, 4)
    random_state = torch.get_rng_state()
    with pytest.raises(AssertionError):
        validate_causality(model, features)
    assert torch.equal(random_state, torch.get_rng_state())


class RoundingFixture(torch.nn.Module):
    def forward(self, features):
        prediction = features[:, :, :2].clone()
        if features.dtype == torch.float32 and features.shape[1] > 35:
            prediction += 2e-6
        return prediction


def test_float32_length_discrepancy_is_a_diagnostic_not_structural_failure():
    model = RoundingFixture().eval()
    features = torch.zeros(2, 70, 4)
    result = validate_causality(model, features)
    assert result['passed']
    assert result['float32_cross_length_max_difference'] > 1e-6
    assert result['float64_cross_length_max_difference'] == 0
    assert result['float64_future_perturbation_max_difference'] == 0


def test_requires_evaluation_mode_and_sufficient_finite_production_inputs():
    model = make_sequence_model('temporal_cnn', 4, hidden=8)
    with pytest.raises(ValueError, match='evaluation mode'):
        validate_causality(model, torch.zeros(2, 70, 4))
    model.eval()
    with pytest.raises(ValueError, match='35 bins'):
        validate_causality(model, torch.zeros(2, 35, 4))
    with pytest.raises(ValueError, match='finite float32'):
        validate_causality(model, torch.full((2, 70, 4), float('nan')))
