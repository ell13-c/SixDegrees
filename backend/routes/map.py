"""Map routes for retrieving and triggering the People Map pipeline.

All endpoints require a valid Supabase JWT in the ``Authorization: Bearer``
header. A user may only access their own map; attempting to read or trigger
another user's map returns 403.
"""

import dataclasses
from fastapi import APIRouter, Depends, HTTPException
from config.settings import get_supabase_client
from routes.deps import get_current_user
from services.map.ego import build_ego_map
from services.map.pipeline import run

router = APIRouter(prefix="/map", tags=["map"])


@router.get("/{user_id}")
async def get_map(
    user_id: str,
    acting_user_id: str = Depends(get_current_user),
):
    """Return the ego-centric map for ``user_id``.

    Args:
        user_id: UUID of the user whose map to retrieve.
        acting_user_id: UUID extracted from the JWT (injected by dependency).

    Returns:
        dict: Serialised ``EgoMapResponse`` with ``computed_at`` and
        ``coordinates`` fields.

    Raises:
        HTTPException 403: If ``acting_user_id != user_id``.
        HTTPException 404: If the user has no computed position yet.
    """
    if acting_user_id != user_id:
        raise HTTPException(status_code=403, detail="You may only view your own map")
    response = build_ego_map(user_id)
    return dataclasses.asdict(response)


@router.post("/trigger/{user_id}")
async def trigger_map(
    user_id: str,
    acting_user_id: str = Depends(get_current_user),
):
    """Manually trigger a full pipeline recompute for all users.

    Runs the global coordinate pipeline synchronously and returns the
    ``computed_at`` timestamp from the freshly written positions.

    Args:
        user_id: UUID of the requesting user (must match JWT subject).
        acting_user_id: UUID extracted from the JWT (injected by dependency).

    Returns:
        dict: ``{"status": "ok", "computed_at": "<ISO 8601 timestamp>"}``.

    Raises:
        HTTPException 403: If ``acting_user_id != user_id``.
        HTTPException 503: If the pipeline raises any exception.
    """
    if acting_user_id != user_id:
        raise HTTPException(status_code=403, detail="You may only trigger your own map")
    try:
        run()
    except Exception as e:
        print(f"Pipeline error: {e}")
        raise HTTPException(status_code=503, detail="Map computation failed. Check server logs.")
    sb = get_supabase_client()
    rows = sb.table("user_positions").select("computed_at").limit(1).execute().data
    computed_at = rows[0]["computed_at"] if rows else None
    return {"status": "ok", "computed_at": computed_at}
