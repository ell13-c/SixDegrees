import numpy as np
from models.user import UserProfile
from config.settings import PROFILE_WEIGHTS
from services.matching.similarity import (
    jaccard,
    tiered_location,
    tiered_categorical,
    inverse_distance_age,
    FIELD_OF_STUDY_CATEGORIES,
    INDUSTRY_CATEGORIES,
)

# Tunable weights. Must sum to 1.0.
# Interests are the highest-signal field, so they get the most weight.
DEFAULT_WEIGHTS: dict[str, float] = {
    "interests":  0.40,
    "location":   0.20,
    "languages":  0.15,
    "education":  0.10,
    "industry":   0.10,
    "age":        0.05,
}

# Column index for each feature dimension
FEATURE_COLS = list(DEFAULT_WEIGHTS.keys())


def _similarity_vector(u1: UserProfile, u2: UserProfile) -> list[float]:
    """Compute the raw [0,1] similarity score per field for a pair of users."""
    return [
        jaccard(u1.interests, u2.interests, stem=True),
        tiered_location(u1.city, u1.state, u2.city, u2.state),
        jaccard(u1.languages, u2.languages),
        tiered_categorical(u1.education, u2.education, FIELD_OF_STUDY_CATEGORIES),
        tiered_categorical(u1.industry, u2.industry, INDUSTRY_CATEGORIES),
        inverse_distance_age(u1.age, u2.age),
    ]


def _profile_similarity(u1: UserProfile, u2: UserProfile) -> float:
    """Weighted similarity score in [0, 1] between two users."""
    scores = [
        jaccard(u1.interests, u2.interests, stem=True),
        tiered_location(u1.city, u1.state, u2.city, u2.state),
        jaccard(u1.languages, u2.languages),
        tiered_categorical(u1.education, u2.education, FIELD_OF_STUDY_CATEGORIES),
        tiered_categorical(u1.industry, u2.industry, INDUSTRY_CATEGORIES),
        inverse_distance_age(u1.age, u2.age),
    ]
    weights = [
        PROFILE_WEIGHTS["interests"],
        PROFILE_WEIGHTS["location"],
        PROFILE_WEIGHTS["languages"],
        PROFILE_WEIGHTS["education"],
        PROFILE_WEIGHTS["industry"],
        PROFILE_WEIGHTS["age"],
    ]
    return sum(s * w for s, w in zip(scores, weights))


def get_top_matches(
    current_user: UserProfile,
    all_users: list[UserProfile],
    top_n: int = 10,
) -> list[dict]:
    """Return top_n most similar users sorted by descending similarity score.

    all_users must NOT include current_user.
    Returns list of {"user": UserProfile, "similarity_score": float}.
    """
    scored = [
        {"user": u, "similarity_score": round(_profile_similarity(current_user, u), 4)}
        for u in all_users
    ]
    scored.sort(key=lambda x: x["similarity_score"], reverse=True)
    return scored[:top_n]


def build_similarity_matrix(users: list[UserProfile]) -> np.ndarray:
    """Build an (N x N x F) matrix of per-field similarity scores.

    Returns shape (N, N, F) where F = number of feature dimensions.
    sim[i][j] is a vector of similarity scores between users[i] and users[j].
    """
    n = len(users)
    f = len(FEATURE_COLS)
    matrix = np.zeros((n, n, f))
    for i in range(n):
        for j in range(i + 1, n):
            vec = _similarity_vector(users[i], users[j])
            matrix[i][j] = vec
            matrix[j][i] = vec  # symmetric
    return matrix


def apply_weights(
    sim_matrix: np.ndarray,
    weights: dict[str, float] = DEFAULT_WEIGHTS,
) -> np.ndarray:
    """Dot-multiply each feature dimension by its weight.

    Returns a (N, N) matrix of weighted similarity scores in [0, 1].
    Higher score = more similar.
    """
    weight_vec = np.array([weights[col] for col in FEATURE_COLS])
    # sim_matrix shape: (N, N, F) — dot product along the last axis
    return np.dot(sim_matrix, weight_vec)


def similarity_to_distance(weighted_scores: np.ndarray) -> np.ndarray:
    """Convert similarity scores to distances: distance = 1 - similarity.

    Returns a (N, N) distance matrix where 0 = identical, 1 = maximally different.
    """
    dist = 1.0 - weighted_scores
    np.fill_diagonal(dist, 0.0)
    return dist
