import numpy as np
import umap
from config.settings import UMAP_N_NEIGHBORS, UMAP_MIN_DIST, UMAP_RANDOM_STATE


def project(distance_matrix: np.ndarray) -> np.ndarray:
    return umap.UMAP(
        n_components=2,
        metric="precomputed",
        n_neighbors=UMAP_N_NEIGHBORS,
        min_dist=UMAP_MIN_DIST,
        random_state=UMAP_RANDOM_STATE,
    ).fit_transform(distance_matrix)
