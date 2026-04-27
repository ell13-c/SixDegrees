"""Data contracts (dataclasses) for the map pipeline.

All inter-module data structures are defined here so individual pipeline
stages depend only on these contracts rather than on each other directly.
"""

from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from models.user import UserProfile


@dataclass
class PipelineInput:
    """Input bundle for the global coordinate pipeline.

    Attributes:
        profiles: All user profiles fetched from ``public.profiles``.
        interactions: All rows from ``public.interactions`` as raw dicts.
    """

    profiles: list[UserProfile]
    interactions: list[dict]

    @property
    def user_ids(self) -> list[str]:
        """Return profile IDs in the same order as ``profiles``."""
        return [p.id for p in self.profiles]


@dataclass
class PipelineResult:
    """Output bundle produced by a successful pipeline run.

    Attributes:
        user_ids: Ordered list of user UUIDs; index matches rows of ``coords``.
        coords: Shape ``(N, 2)`` array of normalised UMAP coordinates.
        edge_count: Number of user pairs with at least one interaction.
        duration_ms: Wall-clock time for the full pipeline run in milliseconds.
    """

    user_ids: list[str]
    coords: np.ndarray
    edge_count: int
    duration_ms: int


@dataclass
class EgoMapNode:
    """A single node in the ego-centric map sent to the frontend.

    Coordinates are relative to the requesting user who sits at (0, 0).

    Attributes:
        user_id: UUID of the represented user.
        nickname: Unique handle of the represented user.
        display_name: Alias for ``nickname``; used by the ClosenessMap component.
        avatar_url: Public URL to the user's avatar, or ``None``.
        x: Horizontal position relative to the requester.
        y: Vertical position relative to the requester.
        tier: Social distance tier (0 = self, 1 = direct friend, 2 = friend-of-friend, 3 = wider).
    """

    user_id: str
    nickname: str
    display_name: str
    avatar_url: str | None
    x: float
    y: float
    tier: int


@dataclass
class EgoMapResponse:
    """Full ego-map response returned by ``GET /map/{user_id}``.

    Attributes:
        coordinates: List of all visible nodes including the requester at (0, 0).
        computed_at: ISO 8601 timestamp of the most recent pipeline run.
    """

    coordinates: list[EgoMapNode]
    computed_at: str | None    # ISO 8601 timestamp; None if positions table is empty
