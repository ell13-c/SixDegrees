from __future__ import annotations

from math import hypot
from typing import Iterable

from services.map_pipeline.contracts import EgoCoordinateRow, EgoMapNode, EgoProfileRow

# Tier thresholds (matching origin_translator.py)
_K1 = 5   # Tier 1: 5 nearest
_K2 = 15  # Tier 2: ranks 6-15


def _normalize_coordinate_rows(rows: Iterable[EgoCoordinateRow | dict]) -> list[EgoCoordinateRow]:
    normalized: list[EgoCoordinateRow] = []
    for row in rows:
        if isinstance(row, EgoCoordinateRow):
            normalized.append(row)
            continue
        normalized.append(
            EgoCoordinateRow(
                user_id=str(row["user_id"]),
                x=float(row["x"]),
                y=float(row["y"]),
                computed_at=str(row.get("computed_at", "")),
                version_date=str(row.get("version_date", "")),
            )
        )
    return normalized


def _normalize_profile_rows(rows: Iterable[EgoProfileRow | dict]) -> list[EgoProfileRow]:
    normalized: list[EgoProfileRow] = []
    for row in rows:
        if isinstance(row, EgoProfileRow):
            normalized.append(row)
            continue
        normalized.append(
            EgoProfileRow(
                id=str(row["id"]),
                nickname=str(row.get("nickname", "")),
                friends=[str(f) for f in (row.get("friends") or [])],
            )
        )
    return normalized


def build_ego_map(
    requesting_user_id: str,
    coordinate_rows: Iterable[EgoCoordinateRow | dict],
    profile_rows: Iterable[EgoProfileRow | dict],
) -> list[EgoMapNode]:
    normalized_coordinates = _normalize_coordinate_rows(coordinate_rows)
    normalized_profiles = _normalize_profile_rows(profile_rows)

    if not normalized_coordinates:
        raise ValueError("coordinate rows are required")

    coordinate_map = {row.user_id: row for row in normalized_coordinates}
    if requesting_user_id not in coordinate_map:
        raise ValueError("requesting user coordinate row is missing")

    profile_map = {row.id: row for row in normalized_profiles}
    requester_profile = profile_map.get(requesting_user_id)
    requester_coord = coordinate_map[requesting_user_id]

    # Translate all to ego-centric and sort others by distance
    others: list[tuple[float, str]] = []
    for user_id, row in coordinate_map.items():
        if user_id == requesting_user_id:
            continue
        dx = row.x - requester_coord.x
        dy = row.y - requester_coord.y
        others.append((hypot(dx, dy), user_id))

    others.sort(key=lambda t: (t[0], t[1]))

    nodes: list[EgoMapNode] = [
        EgoMapNode(
            user_id=requesting_user_id,
            x=0.0,
            y=0.0,
            tier=1,
            nickname=requester_profile.nickname if requester_profile else "",
            is_suggestion=False,
        )
    ]

    for rank, (_, user_id) in enumerate(others, start=1):
        row = coordinate_map[user_id]
        profile = profile_map.get(user_id)
        if rank <= _K1:
            tier = 1
        elif rank <= _K2:
            tier = 2
        else:
            tier = 3
        nodes.append(
            EgoMapNode(
                user_id=user_id,
                x=row.x - requester_coord.x,
                y=row.y - requester_coord.y,
                tier=tier,
                nickname=profile.nickname if profile else "",
                is_suggestion=False,
            )
        )

    return nodes
