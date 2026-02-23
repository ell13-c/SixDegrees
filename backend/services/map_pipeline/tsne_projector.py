"""t-SNE projection module for the map pipeline.

Takes a precomputed NxN distance matrix and returns raw 2D coordinates.
IMPORTANT: Returns RAW coordinates before origin translation (TSNE-04).
Origin translation is the responsibility of origin_translator.py.
"""
import math
import numpy as np
from sklearn.manifold import TSNE


def project_tsne(distance_matrix: np.ndarray) -> np.ndarray:
    """Project users into 2D space using t-SNE with a precomputed distance matrix.

    Args:
        distance_matrix: NxN symmetric distance matrix with zeros on diagonal
                         and values in [0, 1]. Must have N >= 10.

    Returns:
        (N, 2) ndarray of raw 2D coordinates. NOT origin-translated — the
        requesting user will NOT be at (0, 0). Use origin_translator.py for that.

    Raises:
        ValueError: If N < 10 (t-SNE is unstable below this threshold).
    """
    n = distance_matrix.shape[0]
    if n < 10:
        raise ValueError(
            f"t-SNE pipeline requires at least 10 users; received {n}. "
            "Ensure the user set has at least 10 members before calling the pipeline."
        )

    # TSNE-02: dynamic perplexity, never exceeds sqrt(N) for small N
    perplexity = min(30, max(5, int(math.sqrt(n))))

    # TSNE-01: metric='precomputed' REQUIRES init='random' — 'pca' raises ValueError
    # max_iter: use this name (renamed from n_iter in sklearn 1.5)
    tsne = TSNE(
        n_components=2,
        metric="precomputed",
        init="random",          # required: 'pca' is incompatible with metric='precomputed'
        random_state=42,
        perplexity=perplexity,
        learning_rate="auto",
        max_iter=1000,          # use max_iter (not n_iter) — renamed in sklearn 1.5
    )
    return tsne.fit_transform(distance_matrix)
