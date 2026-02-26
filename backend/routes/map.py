from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException
from config.supabase import get_supabase_client
from routes.deps import get_current_user
from services.map_pipeline import run_pipeline_for_user

router = APIRouter(prefix="/map", tags=["map"])


def _fetch_map_response(user_id: str) -> dict:
    """Shared helper: fetch global map_coordinates + nicknames for map response."""
    sb = get_supabase_client()
    rows = cast(
        list[dict[str, Any]],
        sb.rpc(
            "get_global_map_coordinates",
            {"p_user_ids": None, "p_version_date": None},
        ).execute().data
        or [],
    )

    required_fields = {"user_id", "x", "y", "computed_at", "version_date"}
    valid_rows = [r for r in rows if required_fields.issubset(r)]

    if not valid_rows:
        raise HTTPException(status_code=404, detail="Map not yet computed for this user")

    profile_ids = [r["user_id"] for r in valid_rows]
    profiles = cast(
        list[dict[str, Any]],
        sb.rpc("get_profile_nicknames", {"p_ids": profile_ids}).execute().data or [],
    )
    name_map = {p["id"]: p["nickname"] for p in profiles}

    return {
        "user_id": user_id,
        "version_date": valid_rows[0]["version_date"],
        "computed_at": valid_rows[0]["computed_at"],
        "coordinates": [
            {
                "user_id": r["user_id"],
                "x": r["x"],
                "y": r["y"],
                "tier": 1,
                "nickname": name_map.get(r["user_id"], ""),
            }
            for r in valid_rows
        ],
    }


@router.get("/{user_id}")
async def get_map(
    user_id: str,
    acting_user_id: str = Depends(get_current_user),
):
    return _fetch_map_response(user_id)


@router.post("/trigger/{user_id}")
async def trigger_map(
    user_id: str,
    acting_user_id: str = Depends(get_current_user),
):
    if acting_user_id != user_id:
        raise HTTPException(status_code=403, detail="You may only trigger your own map")
    try:
        run_pipeline_for_user(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return _fetch_map_response(user_id)
