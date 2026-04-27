"""Profile write endpoint.

Requires a valid Supabase JWT. User can only update their own profile row.
Creates the row if it does not exist (upsert on id PK).
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from routes.deps import get_current_user
from config.settings import get_supabase_client

router = APIRouter(prefix="/profile", tags=["profile"])


class ProfileBody(BaseModel):
    """Request body for ``PUT /profile``. All fields are optional; ``None`` fields are ignored."""

    nickname: str | None = None
    city: str | None = None
    state: str | None = None
    education: str | None = None
    occupation: str | None = None
    interests: list[str] | None = None
    languages: list[str] | None = None
    industry: str | None = None
    age: int | None = None


@router.get("")
def get_profile(
    acting_user_id: str = Depends(get_current_user),
):
    """Return the authenticated user's profile row.

    Returns:
        dict: The first result row from the ``get_profile`` Supabase RPC.

    Raises:
        HTTPException 404: If no profile row exists for the user.
    """
    result = get_supabase_client().rpc("get_profile", {"p_id": acting_user_id}).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Profile not found")
    return result.data[0]


@router.put("")
def update_profile(
    body: ProfileBody,
    acting_user_id: str = Depends(get_current_user),
):
    """Create or update the authenticated user's profile.

    ``interests`` values are lowercased and deduplicated before writing.
    The ``is_onboarded`` flag is always set to ``True`` on a successful update.

    Args:
        body: Partial profile fields to write. ``None`` fields are ignored.
        acting_user_id: UUID extracted from the JWT (injected by dependency).

    Returns:
        dict: ``{"detail": "Profile updated"}``.
    """
    payload = {"id": acting_user_id}
    raw = body.model_dump()
    for list_field in ("interests", "languages"):
        if raw.get(list_field) is not None:
            seen: set[str] = set()
            normalized: list[str] = []
            for item in raw[list_field]:
                key = item.lower().strip()
                if key and key not in seen:
                    seen.add(key)
                    normalized.append(key)
            raw[list_field] = normalized
    payload.update({k: v for k, v in raw.items() if v is not None})
    payload["is_onboarded"] = True

    p_data = {k: v for k, v in payload.items() if k != "id"}
    get_supabase_client().rpc("upsert_profile", {"p_id": acting_user_id, "p_data": p_data}).execute()

    return {"detail": "Profile updated"}
