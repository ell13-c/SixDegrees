import numpy as np
from models.user import UserProfile, MatchResult

# KNN tier thresholds.
# Tier 1: the k1 closest users (inner circle / first degree).
# Tier 2: next k2 closest users (second degree).
# Tier 3: anyone else within the distance cutoff.
DEFAULT_K1 = 5
DEFAULT_K2 = 15
DEFAULT_MAX_DISTANCE = 0.75  # Users beyond this distance are not returned


def get_ranked_matches(
    user_id: str,
    users: list[UserProfile],
    distance_matrix: np.ndarray,
    k1: int = DEFAULT_K1,
    k2: int = DEFAULT_K2,
    max_distance: float = DEFAULT_MAX_DISTANCE,
) -> list[MatchResult]:
    """Return ranked matches for a given user with tier labels.

    Args:
        user_id: ID of the target user.
        users: Full list of UserProfile objects (same order as distance_matrix rows).
        distance_matrix: (N x N) distance matrix from scoring.similarity_to_distance().
        k1: Number of tier-1 (closest) matches.
        k2: Cumulative count for tier-2 boundary (so tier 2 = ranks k1+1 to k2).
        max_distance: Users with distance > this value are excluded.

    Returns:
        List of MatchResult sorted by ascending distance (closest first).
    """
    # Find the row index for this user
    id_to_idx = {u.id: i for i, u in enumerate(users)}
    if user_id not in id_to_idx:
        raise ValueError(f"User {user_id} not found in user list")

    idx = id_to_idx[user_id]
    distances = distance_matrix[idx]

    # Sort all other users by distance (ascending), exclude self
    sorted_indices = np.argsort(distances)
    results: list[MatchResult] = []

    rank = 0
    for other_idx in sorted_indices:
        if other_idx == idx:
            continue
        dist = float(distances[other_idx])
        if dist > max_distance:
            break

        rank += 1
        if rank <= k1:
            tier = 1
        elif rank <= k2:
            tier = 2
        else:
            tier = 3

        results.append(
            MatchResult(
                user=users[other_idx],
                score=round(1.0 - dist, 4),  # convert distance back to similarity
                tier=tier,
            )
        )

    return results
