"""Training-only classical estimators and descriptive population comparisons."""

import numpy as np
from scipy.linalg import subspace_angles
from sklearn.decomposition import FactorAnalysis, PCA
from sklearn.linear_model import LinearRegression, Ridge


def _observations(values, minimum_rows=1):
    observations = np.asarray(values, dtype=float)
    if observations.ndim != 2:
        raise ValueError("Observations must be samples × features.")
    row_count, feature_count = observations.shape
    if row_count < minimum_rows or feature_count < 1:
        raise ValueError("Insufficient observation rows or features.")
    if not np.all(np.isfinite(observations)):
        raise ValueError("Observations must be finite.")
    return observations


def fit_population(training, n_components, kind="pca", seed=0):
    """Fit PCA or FA using only supplied training samples × neural units."""
    observations = _observations(training, minimum_rows=2)
    row_count, unit_count = observations.shape
    maximum_components = min(row_count - 1, unit_count)
    integer_components = isinstance(n_components, (int, np.integer))
    if isinstance(n_components, (bool, np.bool_)) or not integer_components:
        raise ValueError("n_components must be an integer.")
    if n_components < 1 or n_components > maximum_components:
        raise ValueError("n_components exceeds the centered-data dimensions.")
    if kind == "pca":
        model = PCA(n_components=n_components, svd_solver="full")
    elif kind == "fa":
        model = FactorAnalysis(n_components=n_components, random_state=seed)
    else:
        raise ValueError("kind must be 'pca' or 'fa'.")
    model.fit(observations)
    return model


def reconstruction(model, values):
    """Return samples × units reconstruction using the fitted training mean."""
    observations = _observations(values)
    if not isinstance(model, (PCA, FactorAnalysis)):
        raise ValueError("Expected a fitted PCA or FactorAnalysis estimator.")
    if not hasattr(model, "components_"):
        raise ValueError("Population estimator is not fitted.")
    if observations.shape[1] != model.components_.shape[1]:
        raise ValueError("Observation unit count differs from fitted model.")
    latent_coordinates = model.transform(observations)
    reconstructed_centered = latent_coordinates @ model.components_
    reconstructed_observations = reconstructed_centered + model.mean_
    return reconstructed_observations


def principal_angles(left_basis, right_basis):
    """Return radians between full-column-rank bases in one feature space.

    Each input is features × directions. QR removes basis scale and rotations;
    this does not establish cross-session neuron identity.
    """
    left = _observations(left_basis)
    right = _observations(right_basis)
    if left.shape[0] != right.shape[0]:
        raise ValueError("Bases must share the same feature space.")
    for basis in (left, right):
        direction_count = basis.shape[1]
        basis_rank = np.linalg.matrix_rank(basis)
        if direction_count > basis.shape[0] or basis_rank != direction_count:
            raise ValueError("Basis directions must be linearly independent.")
    left_orthonormal, _ = np.linalg.qr(left, mode="reduced")
    right_orthonormal, _ = np.linalg.qr(right, mode="reduced")
    angles_radians = subspace_angles(left_orthonormal, right_orthonormal)
    return angles_radians


def covariance_similarity(left_covariance, right_covariance):
    """Frobenius cosine of covariance matrices from centered observations.

    Covariance entries are not centered again. Zero covariance has undefined
    cosine (NaN); matching feature order and units are caller responsibilities.
    """
    left = _observations(left_covariance)
    right = _observations(right_covariance)
    if left.shape != right.shape or left.shape[0] != left.shape[1]:
        raise ValueError("Covariances must be matching square matrices.")
    if not np.allclose(left, left.T) or not np.allclose(right, right.T):
        raise ValueError("Covariances must be symmetric.")
    left_norm = np.linalg.norm(left, ord="fro")
    right_norm = np.linalg.norm(right, ord="fro")
    norm_product = left_norm * right_norm
    if norm_product == 0:
        return float("nan")
    inner_product = np.sum(left * right)
    covariance_cosine = inner_product / norm_product
    bounded_cosine = np.clip(covariance_cosine, -1.0, 1.0)
    return float(bounded_cosine)


def fit_decoder(training_features, training_targets, alpha=None):
    """Fit OLS or ridge to supplied training rows; alpha uses feature units."""
    features = _observations(training_features, minimum_rows=2)
    targets = np.asarray(training_targets, dtype=float)
    if targets.ndim == 1:
        targets = targets[:, None]
    targets = _observations(targets, minimum_rows=2)
    if features.shape[0] != targets.shape[0]:
        raise ValueError("Features and targets must have matching sample rows.")
    if alpha is None:
        model = LinearRegression()
    else:
        if not np.isscalar(alpha) or isinstance(alpha, (bool, np.bool_)):
            raise ValueError("Ridge alpha must be a finite nonnegative scalar.")
        if not np.isfinite(alpha) or alpha < 0:
            raise ValueError("Ridge alpha must be a finite nonnegative scalar.")
        model = Ridge(alpha=alpha)
    model.fit(features, targets)
    return model
