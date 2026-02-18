import numpy as np
from sklearn.decomposition import PCA
from models.user import UserProfile
from services.matching.scoring import build_similarity_matrix, apply_weights, DEFAULT_WEIGHTS


def project_to_2d(
    users: list[UserProfile],
    weights: dict[str, float] = DEFAULT_WEIGHTS,
) -> list[dict]:
    """Project all users into 2D space using PCA for the frontend social graph.

    Builds the weighted similarity matrix, then applies PCA(n_components=2)
    to reduce the per-user feature representation to x/y coordinates.

    Args:
        users: Full list of user profiles.
        weights: Feature weights (uses DEFAULT_WEIGHTS if not provided).

    Returns:
        List of dicts: [{"id": "...", "x": float, "y": float}, ...]
        Coordinates are not on a fixed scale — the frontend should normalize
        them to its viewport dimensions.
    """
    if len(users) < 2:
        # PCA requires at least 2 samples
        return [{"id": u.id, "x": 0.0, "y": 0.0} for u in users]

    sim_matrix = build_similarity_matrix(users)
    weighted_scores = apply_weights(sim_matrix, weights)

    # Each row of weighted_scores is a user's similarity profile against all others.
    # This N x N matrix is a valid feature representation for PCA.
    n_components = min(2, len(users) - 1)
    pca = PCA(n_components=n_components)
    coords_2d = pca.fit_transform(weighted_scores)

    result = []
    for i, user in enumerate(users):
        x = float(coords_2d[i, 0])
        y = float(coords_2d[i, 1]) if n_components > 1 else 0.0
        result.append({"id": user.id, "x": x, "y": y})

    return result
