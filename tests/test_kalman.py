import numpy as np
import pytest

from cerebro.kalman import fit_kalman, predict_kalman


def fixture():
    random_generator = np.random.default_rng(11)
    targets = random_generator.normal(size=(8, 12, 2))
    observation = np.array([[2, 0], [0, 3], [1, 1]], dtype=float)
    features = targets @ observation.T + [10, 20, 30]
    return features, targets


def test_controlled_observation_and_filter():
    features, targets = fixture()
    model = fit_kalman(features, targets, ridge_alpha=0, covariance_floor=1e-8)
    np.testing.assert_allclose(model["H"], [[2, 0], [0, 3], [1, 1]], atol=1e-12)
    np.testing.assert_allclose(model["observation_offset"], [10, 20, 30], atol=1e-12)
    predictions = predict_kalman(model, features)
    np.testing.assert_allclose(predictions, targets, atol=1e-7)


def test_transition_fit_excludes_trial_boundaries():
    initial_states = np.array([[1, 0], [0, 1], [2, 3], [-4, 2]], dtype=float)
    targets = np.stack([initial_states, initial_states * 0.5, initial_states * 0.25], axis=1)
    features = targets.copy()
    model = fit_kalman(features, targets, ridge_alpha=0)
    np.testing.assert_allclose(model["A"], np.eye(2) * 0.5, atol=1e-12)
    np.testing.assert_allclose(model["transition_offset"], 0, atol=1e-12)


def test_prefix_causality_and_trial_reset():
    features, targets = fixture()
    model = fit_kalman(features, targets)
    complete = predict_kalman(model, features)
    prefix = predict_kalman(model, features[:, :5])
    np.testing.assert_allclose(complete[:, :5], prefix)
    single_trial = predict_kalman(model, features[3:4])
    np.testing.assert_allclose(complete[3:4], single_trial)
    repeated = predict_kalman(model, features)
    np.testing.assert_array_equal(complete, repeated)


def test_parameter_npz_roundtrip(tmp_path):
    features, targets = fixture()
    model = fit_kalman(features, targets)
    path = tmp_path / "parameters.npz"
    np.savez(path, **model)
    with np.load(path, allow_pickle=False) as archive:
        restored = dict(archive)
    np.testing.assert_array_equal(predict_kalman(model, features), predict_kalman(restored, features))


def test_state_space_gain_matches_observation_space_solve():
    features, targets = fixture()
    model = fit_kalman(features, targets)
    prior_mean = model["initial_mean"]
    prior_covariance = model["initial_covariance"]
    observation = model["H"]
    cross_covariance = prior_covariance @ observation.T
    innovation_covariance = observation @ cross_covariance + model["R"]
    gain = np.linalg.solve(innovation_covariance, cross_covariance.T).T
    expected_observation = observation @ prior_mean + model["observation_offset"]
    innovation = features[0, 0] - expected_observation
    expected_state = prior_mean + gain @ innovation
    predicted = predict_kalman(model, features[0:1, 0:1])
    np.testing.assert_allclose(predicted[0, 0], expected_state, atol=1e-10)


def test_constant_states_remain_finite():
    features = np.full((1, 30, 3), 2.0)
    targets = np.broadcast_to([3.0, -4.0], (1, 30, 2)).copy()
    model = fit_kalman(features, targets)
    predictions = predict_kalman(model, features)
    np.testing.assert_allclose(predictions, targets)
    for name in ("Q", "R", "initial_covariance"):
        assert np.linalg.eigvalsh(model[name]).min() > 0


def test_invalid_data_and_parameters():
    features, targets = fixture()
    for bad_features in (features[:, :1], features[0], np.full(features.shape, np.nan)):
        with pytest.raises(ValueError):
            fit_kalman(bad_features, targets)
    with pytest.raises(ValueError):
        fit_kalman(features, targets[:, :, :1])
    for arguments in ({"ridge_alpha": -1}, {"ridge_alpha": np.nan}, {"covariance_floor": 0}):
        with pytest.raises(ValueError):
            fit_kalman(features, targets, **arguments)
    model = fit_kalman(features, targets)
    with pytest.raises(ValueError):
        predict_kalman(model, np.full(features.shape, np.nan))
    model["R"][0, 0] = -1
    with pytest.raises(ValueError):
        predict_kalman(model, features)


def test_missing_and_shape_invalid_restored_parameters():
    features, targets = fixture()
    model = fit_kalman(features, targets)
    del model["A"]
    with pytest.raises(ValueError):
        predict_kalman(model, features)
    model = fit_kalman(features, targets)
    model["initial_mean"] = np.ones(3)
    with pytest.raises(ValueError):
        predict_kalman(model, features)
