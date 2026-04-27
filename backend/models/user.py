"""Pydantic models for user profile data.

Defines the canonical ``UserProfile`` model used throughout the backend.
"""

from pydantic import BaseModel, ConfigDict, field_validator


class UserProfile(BaseModel):
    """Pydantic model representing a user's profile row from ``public.profiles``.

    The model is configured with ``extra="ignore"`` so unknown columns returned
    by Supabase are silently dropped rather than raising a validation error.
    ``id`` and ``nickname`` are required; all other fields are optional.

    Attributes:
        id: UUID of the user (matches ``auth.users.id``).
        nickname: Unique display handle chosen during onboarding.
        bio: Free-text biography.
        avatar_url: Public URL to the user's avatar image.
        age: Age in years.
        city: City of residence.
        state: State or province of residence.
        education: Field of study (used in tiered categorical similarity).
        occupation: Job title or role.
        industry: Industry sector (used in tiered categorical similarity).
        interests: List of interest tags, lowercased and deduplicated on write.
        languages: List of languages spoken, lowercased and deduplicated on write.
        profile_tier: Visibility tier of the profile (1 to 6).
        is_admin: Whether the user has admin privileges.
    """
    model_config = ConfigDict(extra="ignore")

    id: str
    nickname: str
    bio: str | None = None
    avatar_url: str | None = None
    age: int | None = None
    city: str | None = None
    state: str | None = None
    education: str | None = None
    occupation: str | None = None
    industry: str | None = None
    interests: list[str] = []
    languages: list[str] = []
    profile_tier: int = 6
    is_admin: bool = False

    @field_validator("interests", "languages", mode="before")
    @classmethod
    def coerce_none_to_empty_list(cls, v) -> list:
        """Coerce ``None`` to an empty list so callers never receive ``None`` for list fields."""
        return v if v is not None else []
