import time
from fastapi import APIRouter, HTTPException
from config.supabase import get_supabase_client
from models.user import UserProfile, MatchResult
from services.matching.scoring import (
    build_similarity_matrix,
    apply_weights,
    similarity_to_distance,
    DEFAULT_WEIGHTS,
)
from services.matching.clustering import get_ranked_matches
from services.matching.visualization import project_to_2d

router = APIRouter(prefix="/match", tags=["matching"])

# Cache TTL in seconds — rebuild the distance matrix at most once every 5 minutes.
_CACHE_TTL = 300
_cache: dict = {"users": None, "matrix": None, "timestamp": 0.0}


def _fetch_all_users() -> list[UserProfile]:
    """Fetch all user profiles from Supabase and parse them into UserProfile objects."""
    client = get_supabase_client()
    response = client.table("users").select("*").execute()
    return [UserProfile(**row) for row in response.data]


def _build_distance_matrix(users: list[UserProfile]):
    sim_matrix = build_similarity_matrix(users)
    weighted = apply_weights(sim_matrix, DEFAULT_WEIGHTS)
    return similarity_to_distance(weighted)


def _get_cached_data() -> tuple[list[UserProfile], object]:
    """Return (users, distance_matrix), recomputing only when the cache is stale."""
    now = time.monotonic()
    if _cache["users"] is None or now - _cache["timestamp"] > _CACHE_TTL:
        users = _fetch_all_users()
        matrix = _build_distance_matrix(users)
        _cache["users"] = users
        _cache["matrix"] = matrix
        _cache["timestamp"] = now
    return _cache["users"], _cache["matrix"]


@router.post("/invalidate-cache", tags=["matching"])
async def invalidate_cache():
    """Force the distance matrix cache to rebuild on the next request.

    Call this after a user updates their profile so matches reflect the change
    without waiting for the TTL to expire.
    """
    _cache["timestamp"] = 0.0
    return {"detail": "Cache invalidated"}


@router.get("/users/{user_id}/matches", response_model=list[MatchResult])
async def get_matches(
    user_id: str,
    k1: int = 5,
    k2: int = 15,
    max_distance: float = 0.75,
):
    """Return ranked matches for a user, grouped into friendship tiers.

    - Tier 1: the k1 closest users (inner circle / first degree)
    - Tier 2: the next k2 - k1 closest users (second degree)
    - Tier 3: remaining users within max_distance

    Query params:
        k1: Number of tier-1 results (default 5)
        k2: Cumulative boundary for tier 2 (default 15, so tier 2 = ranks 6–15)
        max_distance: Users beyond this distance are excluded (default 0.75)
    """
    users, distance_matrix = _get_cached_data()
    if not any(u.id == user_id for u in users):
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")

    matches = get_ranked_matches(
        user_id=user_id,
        users=users,
        distance_matrix=distance_matrix,
        k1=k1,
        k2=k2,
        max_distance=max_distance,
    )
    return matches


@router.get("/graph")
async def get_graph():
    """Return 2D PCA coordinates for all users for the frontend social graph.

    Response format:
        [{"id": "user-uuid", "x": 0.42, "y": -0.17}, ...]

    The frontend should normalize x/y to its viewport dimensions.
    Users that cluster together share similar profiles.
    """
    users, _ = _get_cached_data()
    if len(users) == 0:
        return []
    return project_to_2d(users)
