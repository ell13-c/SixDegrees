"""Compatibility shim for ego_map."""
from dataclasses import dataclass


@dataclass
class _EgoMapNode:
    user_id: str
    nickname: str
    x: float
    y: float
    tier: int
    is_suggestion: bool = False


def build_ego_map(requesting_user_id, coordinate_rows, profile_rows):
    raise NotImplementedError("Ego map not yet implemented in new layout")
