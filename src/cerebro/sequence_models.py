"""Small causal sequence baselines; software behavior is not scientific validation."""

import math

import torch
from torch import nn
from torch.nn import functional as functional


def _validate_input(values, input_units):
    if values.ndim != 3 or values.shape[2] != input_units:
        raise ValueError("Input must be trials × bins × input units.")
    if values.shape[0] < 1 or values.shape[1] < 1:
        raise ValueError("At least one trial and observation bin are required.")
    if not values.is_floating_point() or not torch.isfinite(values).all():
        raise ValueError("Input must contain finite floating-point observations.")


class BinMLP(nn.Module):
    def __init__(self, input_units, hidden, output_coordinates):
        super().__init__()
        self.input_units = input_units
        self.input_layer = nn.Linear(input_units, hidden)
        self.output_layer = nn.Linear(hidden, output_coordinates)

    def forward(self, values):
        _validate_input(values, self.input_units)
        hidden_activity = self.input_layer(values)
        activated_activity = functional.relu(hidden_activity)
        coordinates = self.output_layer(activated_activity)
        return coordinates


class RecurrentBaseline(nn.Module):
    def __init__(self, kind, input_units, hidden, output_coordinates):
        super().__init__()
        self.input_units = input_units
        recurrent_class = nn.GRU if kind == "gru" else nn.LSTM
        self.recurrent = recurrent_class(input_units, hidden, batch_first=True)
        self.output_layer = nn.Linear(hidden, output_coordinates)

    def forward(self, values):
        _validate_input(values, self.input_units)
        # Omitting initial state starts each independent trial from zero.
        hidden_activity, _ = self.recurrent(values)
        coordinates = self.output_layer(hidden_activity)
        return coordinates


class CausalTemporalCNN(nn.Module):
    def __init__(self, input_units, hidden, output_coordinates):
        super().__init__()
        self.input_units = input_units
        self.kernel_width = 3
        self.input_convolution = nn.Conv1d(input_units, hidden, self.kernel_width)
        self.hidden_convolution = nn.Conv1d(hidden, hidden, self.kernel_width)
        self.output_layer = nn.Linear(hidden, output_coordinates)

    def forward(self, values):
        _validate_input(values, self.input_units)
        channels_first = values.transpose(1, 2)
        padded_input = functional.pad(channels_first, (self.kernel_width - 1, 0))
        hidden_activity = self.input_convolution(padded_input)
        activated_activity = functional.relu(hidden_activity)
        padded_hidden = functional.pad(activated_activity, (self.kernel_width - 1, 0))
        second_hidden_activity = self.hidden_convolution(padded_hidden)
        second_activated_activity = functional.relu(second_hidden_activity)
        bins_first = second_activated_activity.transpose(1, 2)
        coordinates = self.output_layer(bins_first)
        return coordinates


class CausalTransformer(nn.Module):
    def __init__(self, input_units, hidden, output_coordinates):
        super().__init__()
        self.input_units = input_units
        self.hidden = hidden
        self.input_layer = nn.Linear(input_units, hidden)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden,
            nhead=1,
            dim_feedforward=hidden * 2,
            dropout=0.0,
            batch_first=True,
        )
        self.encoder = nn.TransformerEncoder(
            encoder_layer, num_layers=1, enable_nested_tensor=False
        )
        self.output_layer = nn.Linear(hidden, output_coordinates)

    def forward(self, values):
        _validate_input(values, self.input_units)
        bin_count = values.shape[1]
        positions = torch.arange(bin_count, device=values.device, dtype=values.dtype)
        even_coordinates = torch.arange(0, self.hidden, 2, device=values.device)
        logarithmic_scale = -math.log(10000.0) / self.hidden
        frequencies = torch.exp(even_coordinates.to(values.dtype) * logarithmic_scale)
        phases = positions[:, None] * frequencies[None, :]
        positional_encoding = torch.zeros(
            bin_count, self.hidden, device=values.device, dtype=values.dtype
        )
        positional_encoding[:, 0::2] = torch.sin(phases)
        odd_coordinate_count = self.hidden // 2
        positional_encoding[:, 1::2] = torch.cos(phases[:, :odd_coordinate_count])
        projected_activity = self.input_layer(values)
        positioned_activity = projected_activity + positional_encoding[None, :, :]
        mask_entries = torch.ones(bin_count, bin_count, device=values.device, dtype=torch.bool)
        future_mask = torch.triu(mask_entries, diagonal=1)
        hidden_activity = self.encoder(positioned_activity, mask=future_mask)
        coordinates = self.output_layer(hidden_activity)
        return coordinates


class DiagonalStateSpace(nn.Module):
    """Stable linear recurrence with fixed 20 ms exponential decay.

    State rates span 1–50 inverse seconds. Learned input/output projections
    provide a simple temporal baseline, not a Mamba or foundation model.
    """

    def __init__(self, input_units, hidden, output_coordinates):
        super().__init__()
        self.input_units = input_units
        self.input_layer = nn.Linear(input_units, hidden, bias=False)
        self.output_layer = nn.Linear(hidden, output_coordinates)
        rates_per_second = torch.logspace(0, math.log10(50), hidden)
        bin_width_seconds = 0.020
        decay = torch.exp(-rates_per_second * bin_width_seconds)
        self.register_buffer("decay", decay)

    def forward(self, values):
        _validate_input(values, self.input_units)
        projected_activity = self.input_layer(values)
        trial_count, bin_count, state_count = projected_activity.shape
        state = values.new_zeros(trial_count, state_count)
        input_fraction = 1 - self.decay
        outputs = []
        for bin_index in range(bin_count):
            decayed_state = state * self.decay
            current_input = projected_activity[:, bin_index, :] * input_fraction
            state = decayed_state + current_input
            current_coordinates = self.output_layer(state)
            outputs.append(current_coordinates)
        coordinates = torch.stack(outputs, dim=1)
        return coordinates


def make_sequence_model(kind, input_units, hidden=32, output_coordinates=2):
    """Return a model mapping trials × bins × units to aligned coordinates."""
    for dimension in (input_units, hidden, output_coordinates):
        if isinstance(dimension, bool) or not isinstance(dimension, int) or dimension < 1:
            raise ValueError("Model dimensions must be positive integers.")
    if kind == "mlp":
        model = BinMLP(input_units, hidden, output_coordinates)
    elif kind in ("gru", "lstm"):
        model = RecurrentBaseline(kind, input_units, hidden, output_coordinates)
    elif kind == "temporal_cnn":
        model = CausalTemporalCNN(input_units, hidden, output_coordinates)
    elif kind == "transformer":
        model = CausalTransformer(input_units, hidden, output_coordinates)
    elif kind == "state_space":
        model = DiagonalStateSpace(input_units, hidden, output_coordinates)
    else:
        raise ValueError("Unknown sequence model kind.")
    return model
