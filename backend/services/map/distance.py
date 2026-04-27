"""Builds the combined N x N distance matrix for the global pipeline.

Combines profile-similarity distance (weighted cosine + field similarity)
with interaction distance (normalised like and comment counts) using fixed
weights ALPHA and BETA from ``config.settings``.
"""

import numpy as np

from config.settings import ALPHA, BETA, INTERACTION_WEIGHTS
from services.map.contracts import PipelineInput
from services.matching.scoring import build_similarity_matrix, apply_weights, similarity_to_distance


def build_combined_distance(data: PipelineInput) -> np.ndarray:
    """Build a combined N×N distance matrix from profile similarity and interaction data.

    Algorithm:
      1. Profile distance: build_similarity_matrix → apply_weights → similarity_to_distance
      2. Interaction distance: normalize raw interaction scores then invert
      3. Combined: ALPHA * profile_dist + BETA * interaction_dist, clipped to [0, 1]

    Returns:
        np.ndarray: shape (N, N), symmetric, diagonal = 0, values in [0, 1]
    """
    profiles = data.profiles
    n = len(profiles)

    profile_dist = similarity_to_distance(apply_weights(build_similarity_matrix(profiles)))

    # Canonical-pair lookup: (uid_a, uid_b) where uid_a < uid_b
    interaction_map: dict[tuple[str, str], dict] = {
        (r["user_id_a"], r["user_id_b"]): r for r in data.interactions
    }

    raw_scores = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            uid_i = profiles[i].id
            uid_j = profiles[j].id
            key = (min(uid_i, uid_j), max(uid_i, uid_j))
            row = interaction_map.get(key)
            if row is not None:
                score = (
                    (row.get("likes_count") or 0) * INTERACTION_WEIGHTS["likes_count"]
                    + (row.get("comments_count") or 0) * INTERACTION_WEIGHTS["comments_count"]
                )
                raw_scores[i][j] = score
                raw_scores[j][i] = score

    max_score = raw_scores.max()
    normalized = raw_scores / max_score if max_score > 0 else raw_scores

    # More interaction → lower distance
    interaction_dist = 1.0 - normalized
    np.fill_diagonal(interaction_dist, 0.0)

    combined = np.clip(ALPHA * profile_dist + BETA * interaction_dist, 0.0, 1.0)
    np.fill_diagonal(combined, 0.0)
    return combined
