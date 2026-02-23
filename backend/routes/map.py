from fastapi import APIRouter, HTTPException
from config.supabase import get_supabase_client
from services.map_pipeline import run_pipeline_for_user

router = APIRouter(prefix="/map", tags=["map"])


def _fetch_map_response(user_id: str) -> dict:
    """Shared helper: fetch current map_coordinates + display_names for a user."""
    sb = get_supabase_client()
    rows = (
        sb.table("map_coordinates")
        .select("other_user_id, x, y, tier, computed_at")
        .eq("center_user_id", user_id)
        .eq("is_current", True)
        .execute()
    ).data

    if not rows:
        raise HTTPException(status_code=404, detail="Map not yet computed for this user")

    other_ids = [r["other_user_id"] for r in rows]
    profiles = (
        sb.table("user_profiles")
        .select("user_id, display_name")
        .in_("user_id", other_ids)
        .execute()
    ).data
    name_map = {p["user_id"]: p["display_name"] for p in profiles}

    return {
        "user_id": user_id,
        "computed_at": rows[0]["computed_at"],
        "coordinates": [
            {
                "user_id": r["other_user_id"],
                "x": r["x"],
                "y": r["y"],
                "tier": r["tier"],
                "display_name": name_map.get(r["other_user_id"], ""),
            }
            for r in rows
        ],
    }


@router.get("/{user_id}")
async def get_map(user_id: str):
    return _fetch_map_response(user_id)


@router.post("/trigger/{user_id}")
async def trigger_map(user_id: str):
    try:
        run_pipeline_for_user(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return _fetch_map_response(user_id)
