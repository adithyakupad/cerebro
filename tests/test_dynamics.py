import numpy as np
import pytest

from cerebro.dynamics import transition_rows, validate_bin_clock


def test_transitions_never_cross_trial_boundaries():
    latent = np.array([[[1.], [2.], [3.]], [[100.], [200.], [300.]]])
    previous, following = transition_rows(latent)
    np.testing.assert_array_equal(previous[:, 0], [1, 2, 100, 200])
    np.testing.assert_array_equal(following[:, 0], [2, 3, 200, 300])
    with pytest.raises(ValueError):
        transition_rows(latent[:, :1])


def test_dynamics_rejects_wrong_width_or_irregular_trial_clock():
    timestamps = np.array([[1., 1.02, 1.04], [10., 10.02, 10.04]])
    validate_bin_clock(timestamps, .02)
    with pytest.raises(ValueError, match='20 ms'):
        validate_bin_clock(timestamps, .05)
    timestamps[1, 2] += .001
    with pytest.raises(ValueError, match='disagree'):
        validate_bin_clock(timestamps, .02)
