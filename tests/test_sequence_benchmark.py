"""Reject unsafe optimization settings before mutating a model."""

import copy

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


def test_broadcast_compatible_targets_rejected_before_parameter_update():
    model = torch.nn.Linear(3, 2)
    optimizer = torch.optim.Adam(model.parameters(), lr=.1)
    original_parameters = [parameter.detach().clone() for parameter in model.parameters()]
    observations = torch.ones(2, 4, 3)
    targets = torch.zeros(2, 4, 1)
    with pytest.raises(ValueError, match='matching shapes'):
        train_epoch(model, optimizer, observations, targets, 1.)
    for original, parameter in zip(original_parameters, model.parameters()):
        assert torch.equal(original, parameter)
        assert parameter.grad is None
    assert not optimizer.state


def test_matching_shapes_preserve_numerical_update_and_random_state():
    torch.manual_seed(25)
    model = torch.nn.Sequential(
        torch.nn.Linear(3, 4),
        torch.nn.Dropout(.2),
        torch.nn.Linear(4, 2),
    )
    reference = copy.deepcopy(model)
    optimizer = torch.optim.SGD(model.parameters(), lr=.1)
    reference_optimizer = torch.optim.SGD(reference.parameters(), lr=.1)
    observations = torch.ones(2, 4, 3)
    targets = torch.zeros(2, 4, 2)
    random_state = torch.get_rng_state()
    actual_loss = train_epoch(model, optimizer, observations, targets, 1.)
    actual_random_state = torch.get_rng_state()

    torch.set_rng_state(random_state)
    reference.train()
    reference_optimizer.zero_grad()
    prediction = reference(observations)
    differences = prediction - targets
    expected_loss = torch.mean(differences ** 2)
    expected_loss.backward()
    torch.nn.utils.clip_grad_norm_(reference.parameters(), 1.)
    reference_optimizer.step()

    assert actual_loss == float(expected_loss.detach())
    assert torch.equal(actual_random_state, torch.get_rng_state())
    for expected, actual in zip(reference.parameters(), model.parameters()):
        assert torch.equal(expected, actual)
