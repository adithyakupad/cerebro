import numpy as np
import pytest

from cerebro.population import (
    covariance_similarity,
    fit_decoder,
    fit_population,
    principal_angles,
    reconstruction,
)


@pytest.mark.parametrize("kind", ["pca", "fa"])
def test_training_mean_and_reconstruction(kind):
    random_generator = np.random.default_rng(8)
    training = random_generator.normal(size=(30, 3)) + [10, 20, 30]
    model = fit_population(training, 2, kind=kind, seed=4)
    heldout = training[:5] + 100
    expected_mean = training.mean(axis=0)
    np.testing.assert_allclose(model.mean_, expected_mean)
    latent = model.transform(heldout)
    expected = latent @ model.components_ + expected_mean
    np.testing.assert_allclose(reconstruction(model, heldout), expected)
    np.testing.assert_allclose(model.mean_, expected_mean)


def test_full_pca_reconstructs():
    training = np.array([[1, 2], [2, 5], [4, 1], [3, 3]], dtype=float)
    model = fit_population(training, 2)
    np.testing.assert_allclose(reconstruction(model, training), training)


@pytest.mark.parametrize("values", [[], [[1]], [[1, np.nan], [2, 3]], [1, 2]])
def test_population_rejects_invalid_observations(values):
    with pytest.raises(ValueError):
        fit_population(values, 1)


@pytest.mark.parametrize("components", [0, 3, 1.5, True])
def test_population_dimension_validation(components):
    with pytest.raises(ValueError):
        fit_population(np.ones((3, 2)), components)


def test_reconstruction_validation():
    model = fit_population(np.array([[1, 2], [3, 4], [4, 2]]), 1)
    with pytest.raises(ValueError):
        reconstruction(model, np.ones((2, 3)))
    with pytest.raises(ValueError):
        fit_population(np.ones((3, 2)), 1, kind="unknown")


def test_angles_rotation_and_orthogonality():
    basis = np.eye(4)[:, :2]
    rotated = basis @ np.array([[0, -2], [3, 0]])
    np.testing.assert_allclose(principal_angles(basis, rotated), 0, atol=1e-14)
    orthogonal = np.eye(4)[:, 2:]
    np.testing.assert_allclose(principal_angles(basis, orthogonal), np.pi / 2)


def test_angles_reject_rank_or_space_mismatch():
    with pytest.raises(ValueError):
        principal_angles(np.ones((4, 2)), np.eye(4)[:, :2])
    with pytest.raises(ValueError):
        principal_angles(np.eye(3), np.eye(4))


def test_covariance_cosine_and_degeneracy():
    covariance = np.array([[2, 1], [1, 3]], dtype=float)
    assert covariance_similarity(covariance, covariance * 4) == pytest.approx(1)
    assert np.isnan(covariance_similarity(covariance, np.zeros((2, 2))))
    with pytest.raises(ValueError):
        covariance_similarity(covariance, np.eye(3))
    with pytest.raises(ValueError):
        covariance_similarity(covariance, [[1, 2], [0, 1]])


@pytest.mark.parametrize("alpha", [None, 0, 0.001])
def test_linear_decoder_prediction(alpha):
    features = np.arange(20, dtype=float).reshape(10, 2)
    targets = features[:, 0] * 2 + 3
    model = fit_decoder(features, targets, alpha=alpha)
    predictions = model.predict(features)
    predicted_values = predictions.reshape(-1)
    np.testing.assert_allclose(predicted_values, targets, atol=1e-4)


@pytest.mark.parametrize("alpha", [-1, np.nan, [1], True])
def test_decoder_rejects_invalid_penalty(alpha):
    with pytest.raises(ValueError):
        fit_decoder(np.ones((3, 2)), np.ones((3, 1)), alpha=alpha)


def test_decoder_rejects_mismatched_rows_and_nonfinite_targets():
    with pytest.raises(ValueError):
        fit_decoder(np.ones((3, 2)), np.ones((2, 1)))
    with pytest.raises(ValueError):
        fit_decoder(np.ones((3, 2)), [1, np.inf, 3])
