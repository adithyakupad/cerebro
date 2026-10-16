import pytest
import torch

from cerebro.sequence_models import make_sequence_model


KINDS = ["mlp", "gru", "lstm", "temporal_cnn", "transformer", "state_space"]


@pytest.mark.parametrize("kind", KINDS)
def test_shapes_gradients_and_finite_output(kind):
    torch.manual_seed(3)
    model = make_sequence_model(kind, input_units=4, hidden=7)
    inputs = torch.randn(3, 9, 4, requires_grad=True)
    output = model(inputs)
    assert output.shape == (3, 9, 2)
    assert torch.isfinite(output).all()
    loss = output.square().mean()
    loss.backward()
    assert torch.isfinite(inputs.grad).all()
    for parameter in model.parameters():
        assert parameter.grad is not None
        assert torch.isfinite(parameter.grad).all()


@pytest.mark.parametrize("kind", KINDS)
def test_prefix_invariance(kind):
    torch.manual_seed(4)
    model = make_sequence_model(kind, 4, hidden=8)
    model.eval()
    inputs = torch.randn(2, 11, 4)
    altered_inputs = inputs.clone()
    altered_inputs[:, 6:, :] += 100
    with torch.no_grad():
        complete_output = model(inputs)
        prefix_output = model(inputs[:, :6, :])
        altered_output = model(altered_inputs)
    torch.testing.assert_close(complete_output[:, :6, :], prefix_output, atol=1e-6, rtol=1e-5)
    torch.testing.assert_close(complete_output[:, :6, :], altered_output[:, :6, :])


@pytest.mark.parametrize("kind", KINDS)
def test_trials_are_independent_and_state_resets(kind):
    torch.manual_seed(5)
    model = make_sequence_model(kind, 3, hidden=8)
    model.eval()
    inputs = torch.randn(2, 7, 3)
    with torch.no_grad():
        batched_output = model(inputs)
        single_trial_output = model(inputs[1:2])
        model(inputs + 100)
        repeated_output = model(inputs)
    torch.testing.assert_close(batched_output[1:2], single_trial_output, atol=1e-6, rtol=1e-5)
    torch.testing.assert_close(batched_output, repeated_output)


@pytest.mark.parametrize("kind", KINDS)
def test_seed_determinism(kind):
    inputs = torch.ones(2, 4, 3)
    torch.manual_seed(6)
    first_model = make_sequence_model(kind, 3, hidden=8)
    torch.manual_seed(6)
    second_model = make_sequence_model(kind, 3, hidden=8)
    torch.testing.assert_close(first_model(inputs), second_model(inputs))


def test_diagonal_recurrence_is_stable_and_matches_rule():
    model = make_sequence_model("state_space", 1, hidden=1, output_coordinates=1)
    with torch.no_grad():
        model.input_layer.weight.fill_(1)
        model.output_layer.weight.fill_(1)
        model.output_layer.bias.zero_()
    assert torch.all((model.decay > 0) & (model.decay < 1))
    inputs = torch.ones(1, 4, 1)
    observed = model(inputs)
    steps = torch.arange(1, 5)
    expected = 1 - model.decay[0] ** steps
    torch.testing.assert_close(observed[0, :, 0], expected)


@pytest.mark.parametrize("kind", KINDS)
def test_missing_and_invalid_inputs(kind):
    model = make_sequence_model(kind, 3)
    for inputs in (torch.ones(2, 3), torch.ones(1, 0, 3), torch.ones(2, 3, 4)):
        with pytest.raises(ValueError):
            model(inputs)
    with pytest.raises(ValueError):
        model(torch.full((1, 2, 3), float("nan")))


def test_factory_rejects_invalid_dimensions_and_unknown_kind():
    with pytest.raises(ValueError):
        make_sequence_model("unknown", 2)
    for dimension in (0, -1, True, 1.2):
        with pytest.raises(ValueError):
            make_sequence_model("mlp", dimension)
