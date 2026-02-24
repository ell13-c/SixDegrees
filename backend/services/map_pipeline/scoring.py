"""Combined distance matrix module for the map pipeline.

Combines profile distance (from existing matching module) and interaction score
using the formula from DIST-01:
    distance(i, j) = α × profile_distance(i, j) + β × (1 - interaction_score(i, j))

NOTE on data model (field name mapping):
    This module accepts the existing UserProfile model (fields: .city, .state).
    The Supabase DB uses location_city/location_state. Phase 3's data_fetcher.py
    is responsible for mapping DB column names to UserProfile fields when constructing
    UserProfile objects. Do NOT change UserProfile here — it would break existing /match routes.
"""
import numpy as np
from models.user import UserProfile
from config.algorithm import ALPHA, BETA, PROFILE_WEIGHTS
from services.matching.scoring import (
    build_similarity_matrix,
    apply_weights,
    similarity_to_distance,
)


def build_combined_distance_matrix(
    users: list[UserProfile],
    interaction_matrix: np.ndarray,
) -> np.ndarray:
    """Build the NxN combined distance matrix for t-SNE input.

    Args:
        users: Ordered list of UserProfile objects. Must use .city/.state fields
               (matching the existing UserProfile model). Phase 3 data_fetcher maps
               location_city → city and location_state → state before passing here.
        interaction_matrix: NxN float array of interaction scores in [0, 1],
                            symmetric, zeros on diagonal. From compute_interaction_scores().

    Returns:
        NxN numpy ndarray of combined distances in [0, 1].
        Symmetric, zeros on diagonal. Suitable as input to project_tsne().
    """
    # DIST-03: reuse existing profile similarity computation — do NOT reimplement
    sim_matrix = build_similarity_matrix(users)                  # (N, N, F)
    weighted_sim = apply_weights(sim_matrix, PROFILE_WEIGHTS)    # (N, N)
    profile_dist = similarity_to_distance(weighted_sim)          # (N, N), [0,1]

    # DIST-01: combined distance formula
    combined = ALPHA * profile_dist + BETA * (1.0 - interaction_matrix)

    # DIST-04: enforce symmetry and clean diagonal (guard against floating-point drift)
    combined = (combined + combined.T) / 2.0
    np.fill_diagonal(combined, 0.0)

    return combined
