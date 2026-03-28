import numpy as np
import pytest
from unittest.mock import patch


def _make_distance_matrix(n: int, seed: int = 42) -> np.ndarray:
    rng = np.random.default_rng(seed)
    m = rng.random((n, n))
    m = (m + m.T) / 2
    np.fill_diagonal(m, 0.0)
    return np.clip(m, 0.0, 1.0)


N = 20


@patch("services.map.projector.UMAP_N_NEIGHBORS", 3)
def test_output_shape() -> None:
    from services.map.projector import project

    dist = _make_distance_matrix(N)
    coords = project(dist)
    assert coords.shape == (N, 2)


@patch("services.map.projector.UMAP_N_NEIGHBORS", 3)
def test_determinism() -> None:
    from services.map.projector import project

    dist = _make_distance_matrix(N)
    coords1 = project(dist)
    coords2 = project(dist)
    np.testing.assert_array_equal(coords1, coords2)


@patch("services.map.projector.UMAP_N_NEIGHBORS", 3)
def test_output_dtype() -> None:
    from services.map.projector import project

    dist = _make_distance_matrix(N)
    coords = project(dist)
    assert np.issubdtype(coords.dtype, np.floating)
