"""Reject unsafe optimization settings before mutating a model."""

import pytest
import torch

from cerebro.sequence_benchmark import train_epoch


@pytest.mark.parametrize('gradient_clip', [-1., 0., float('nan'), float('inf')])
def test_invalid_gradient_clip_preserves_parameters(gradient_clip):
    model = torch.nn.Linear(1, 1)
    optimizer = torch.optim.SGD(model.parameters(), lr=.1)
    original_parameters = [parameter.detach().clone() for parameter in model.parameters()]
    observations = torch.ones(2, 1)
    targets = torch.zeros(2, 1)
    with pytest.raises(ValueError, match='finite and positive'):
        train_epoch(model, optimizer, observations, targets, gradient_clip)
    for original, parameter in zip(original_parameters, model.parameters()):
        torch.testing.assert_close(original, parameter)
