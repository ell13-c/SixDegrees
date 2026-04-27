from fastapi import HTTPException
from config.settings import get_supabase_client
from services.map.contracts import EgoMapNode, EgoMapResponse


def build_ego_map(requester_id: str) -> EgoMapResponse:
    sb = get_supabase_client()

    positions = {
        r["user_id"]: r
        for r in sb.table("user_positions").select("*").execute().data
    }

    if requester_id not in positions:
        raise HTTPException(status_code=404, detail="Map not yet computed for this user")

    # extended_friends includes the requester at depth 0; exclude them from friend_tiers.
    friends_data = sb.rpc("extended_friends", {"max_tier": 3, "target_user_id": requester_id}).execute().data or []
    friend_tiers: dict[str, int] = {
        r["id"]: r["tier"]
        for r in friends_data
        if r["id"] != requester_id
    }

    rx, ry = positions[requester_id]["x"], positions[requester_id]["y"]
    computed_at = positions[requester_id]["computed_at"]

    friends_lookup: dict[str, dict] = {r["id"]: r for r in friends_data}

    # Requester placed at (0, 0); all other coordinates are relative to them.
    requester_profile = friends_lookup.get(requester_id, {})
    result: list[EgoMapNode] = [EgoMapNode(
        user_id=requester_id,
        nickname=requester_profile.get("nickname", ""),
        display_name=requester_profile.get("nickname", ""),
        avatar_url=requester_profile.get("avatar_url"),
        x=0.0,
        y=0.0,
        tier=0,
    )]

    for uid, friendship_tier in friend_tiers.items():
        pos = positions.get(uid)
        if pos is None:
            continue
        f = friends_lookup.get(uid, {})
        name = f.get("nickname", "")
        result.append(EgoMapNode(
            user_id=uid,
            nickname=name,
            display_name=name,
            avatar_url=f.get("avatar_url"),
            x=pos["x"] - rx,
            y=pos["y"] - ry,
            tier=friendship_tier,
        ))

    return EgoMapResponse(coordinates=result, computed_at=computed_at)
