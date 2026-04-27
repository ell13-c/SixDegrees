"""Projects the precomputed distance matrix to 2D coordinates using UMAP.

UMAP is imported lazily on first call to keep it out of startup memory
so the Render free-tier instance does not OOM during cold start.
"""

import numpy as np
from config.settings import UMAP_N_NEIGHBORS, UMAP_MIN_DIST, UMAP_RANDOM_STATE


def project(distance_matrix: np.ndarray) -> np.ndarray:
    """Run UMAP on a precomputed symmetric distance matrix and return 2D coords.

    Args:
        distance_matrix: Square symmetric ``(N, N)`` ndarray with values in
            ``[0, 1]`` and zeros on the diagonal.

    Returns:
        np.ndarray: Shape ``(N, 2)`` array of raw (unscaled) UMAP coordinates.

    Raises:
        ValueError: If ``N < 2`` (UMAP requires at least two points).
    """
    import umap  # lazy import — keeps umap out of startup memory
    n = len(distance_matrix)
    if n < 2:
        raise ValueError(f"Cannot project fewer than 2 users (got {n})")
    n_neighbors = min(UMAP_N_NEIGHBORS, n - 1)
    return umap.UMAP(
        n_components=2,
        metric="precomputed",
        n_neighbors=n_neighbors,
        min_dist=UMAP_MIN_DIST,
        random_state=UMAP_RANDOM_STATE,
    ).fit_transform(distance_matrix)
