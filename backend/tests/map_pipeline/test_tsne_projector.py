"""Tests for tsne_projector.project_tsne()"""
import math
import numpy as np
import pytest
from services.map_pipeline.tsne_projector import project_tsne


def make_distance_matrix(n: int) -> np.ndarray:
    """Create a valid symmetric NxN distance matrix with zeros on diagonal."""
    rng = np.random.default_rng(0)
    raw = rng.random((n, n))
    d = (raw + raw.T) / 2.0
    np.fill_diagonal(d, 0.0)
    # Normalize to [0, 1]
    d = d / d.max()
    np.fill_diagonal(d, 0.0)
    return d


def test_raises_on_fewer_than_10_users():
    """TSNE-03: N < 10 raises ValueError with descriptive message."""
    d = make_distance_matrix(9)
    with pytest.raises(ValueError, match="10"):
        project_tsne(d)


def test_raises_on_exact_9_users():
    """TSNE-03: Boundary check — 9 users still raises."""
    d = make_distance_matrix(9)
    with pytest.raises(ValueError):
        project_tsne(d)


def test_output_shape_10_users():
    """TSNE-01: Returns (N, 2) array for N=10."""
    d = make_distance_matrix(10)
    coords = project_tsne(d)
    assert coords.shape == (10, 2), f"Expected (10, 2), got {coords.shape}"


def test_output_shape_20_users():
    """TSNE-01: Returns (N, 2) array for N=20."""
    d = make_distance_matrix(20)
    coords = project_tsne(d)
    assert coords.shape == (20, 2), f"Expected (20, 2), got {coords.shape}"


def test_output_is_ndarray():
    """TSNE-01: Output is numpy ndarray."""
    d = make_distance_matrix(10)
    coords = project_tsne(d)
    assert isinstance(coords, np.ndarray)


def test_perplexity_guard_at_10_users():
    """TSNE-02: perplexity = min(30, max(5, int(sqrt(10)))) = min(30, max(5, 3)) = 5 — must not crash."""
    d = make_distance_matrix(10)
    # Should not raise — perplexity=5 < N=10
    coords = project_tsne(d)
    assert coords.shape == (10, 2)


def test_deterministic_with_random_state():
    """TSNE-01: random_state=42 produces same output on repeated calls."""
    d = make_distance_matrix(15)
    coords1 = project_tsne(d)
    coords2 = project_tsne(d)
    np.testing.assert_array_equal(coords1, coords2)


def test_returns_raw_coordinates():
    """TSNE-04: Returned coordinates are raw (before any translation).
    The requesting user is NOT at (0,0) — that's origin_translator's job."""
    d = make_distance_matrix(12)
    coords = project_tsne(d)
    # No guarantee any row is at (0,0) — raw output
    assert coords.shape == (12, 2)
    # Verify at least one row is NOT at origin (raw, untranslated)
    any_nonzero = any(abs(coords[i, 0]) > 1e-6 or abs(coords[i, 1]) > 1e-6 for i in range(len(coords)))
    assert any_nonzero, "All coords at origin — translation was applied (should not be in projector)"
