"""Tests for services/map/ego.py — friends-only map."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from services.map.ego import build_ego_map

REQUESTER_ID = "user-a"
USER_B = "user-b"
USER_C = "user-c"
USER_D = "user-d"
USER_E = "user-e"  # not a friend, should be excluded
COMPUTED_AT = "2026-03-27T00:00:00Z"

POSITIONS = [
    {"user_id": REQUESTER_ID, "x": 10.0, "y": 10.0, "computed_at": COMPUTED_AT},
    {"user_id": USER_B,       "x": 11.0, "y": 10.0, "computed_at": COMPUTED_AT},
    {"user_id": USER_C,       "x": 10.0, "y": 15.0, "computed_at": COMPUTED_AT},
    {"user_id": USER_D,       "x": 20.0, "y": 20.0, "computed_at": COMPUTED_AT},
    {"user_id": USER_E,       "x": 99.0, "y": 99.0, "computed_at": COMPUTED_AT},
]

# extended_friends(max_tier=1) returns only the requester (depth=0) and direct friends (depth=1)
FRIENDS_DATA = [
    {"id": REQUESTER_ID, "nickname": "Alpha",   "avatar_url": "https://example.com/a.png", "tier": 0},
    {"id": USER_B,       "nickname": "Bravo",   "avatar_url": "https://example.com/b.png", "tier": 1},
    {"id": USER_C,       "nickname": "Charlie", "avatar_url": None,                         "tier": 1},
    {"id": USER_D,       "nickname": "Delta",   "avatar_url": "https://example.com/d.png", "tier": 1},
    # USER_E is not a friend — not in FRIENDS_DATA
]


def _make_mock_sb(positions=POSITIONS, friends_data=FRIENDS_DATA):
    mock_sb = MagicMock()

    mock_sb.table.return_value.select.return_value.execute.return_value.data = positions
    mock_sb.rpc.return_value.execute.return_value.data = friends_data

    return mock_sb


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_only_friends_appear():
    """Non-friends (USER_E) must be excluded even if they have a position."""
    mock_sb = _make_mock_sb()
    with patch("config.settings._client", mock_sb):
        response = build_ego_map(REQUESTER_ID)

    ids = {node.user_id for node in response.coordinates}
    assert USER_E not in ids
    assert ids == {REQUESTER_ID, USER_B, USER_C, USER_D}


def test_requester_included_at_origin():
    """The requester is included at (0, 0, tier=0) so the frontend length-1 count is correct."""
    mock_sb = _make_mock_sb()
    with patch("config.settings._client", mock_sb):
        response = build_ego_map(REQUESTER_ID)

    requester_node = next(n for n in response.coordinates if n.user_id == REQUESTER_ID)
    assert requester_node.x == 0.0
    assert requester_node.y == 0.0
    assert requester_node.tier == 0


def test_coordinate_translation():
    """user_b at (11,10) should be translated to (1.0, 0.0) relative to requester at (10,10)."""
    mock_sb = _make_mock_sb()
    with patch("config.settings._client", mock_sb):
        response = build_ego_map(REQUESTER_ID)

    node_b = next(n for n in response.coordinates if n.user_id == USER_B)
    assert node_b.x == pytest.approx(1.0)
    assert node_b.y == pytest.approx(0.0)


def test_tier_from_friendship_not_distance():
    """Tier should come from extended_friends depth (all 1 = direct friends), not UMAP distance rank."""
    mock_sb = _make_mock_sb()
    with patch("config.settings._client", mock_sb):
        response = build_ego_map(REQUESTER_ID)

    tier_map = {n.user_id: n.tier for n in response.coordinates}
    assert tier_map[USER_B] == 1
    assert tier_map[USER_C] == 1
    assert tier_map[USER_D] == 1


def test_nickname_display_name_and_avatar_from_friends_data():
    """nickname, display_name, and avatar_url should come from extended_friends result."""
    mock_sb = _make_mock_sb()
    with patch("config.settings._client", mock_sb):
        response = build_ego_map(REQUESTER_ID)

    node_b = next(n for n in response.coordinates if n.user_id == USER_B)
    assert node_b.nickname == "Bravo"
    assert node_b.display_name == "Bravo"
    assert node_b.avatar_url == "https://example.com/b.png"


def test_missing_avatar_url_is_none():
    """When a friend has avatar_url=None, EgoMapNode.avatar_url should be None."""
    mock_sb = _make_mock_sb()
    with patch("config.settings._client", mock_sb):
        response = build_ego_map(REQUESTER_ID)

    node_c = next(n for n in response.coordinates if n.user_id == USER_C)
    assert node_c.avatar_url is None


def test_computed_at():
    """result.computed_at should match the requester's row in user_positions."""
    mock_sb = _make_mock_sb()
    with patch("config.settings._client", mock_sb):
        response = build_ego_map(REQUESTER_ID)

    assert response.computed_at == COMPUTED_AT


def test_404_when_requester_not_in_positions():
    """build_ego_map should raise HTTPException(404) if requester has no position row."""
    mock_sb = _make_mock_sb()
    with patch("config.settings._client", mock_sb):
        with pytest.raises(HTTPException) as exc_info:
            build_ego_map("nonexistent-user-id")

    assert exc_info.value.status_code == 404


def test_zero_friends_returns_only_requester_node():
    """A user with no friends gets only their own (0,0) node, so the frontend shows 0 connections."""
    no_friends_data = [
        {"id": REQUESTER_ID, "nickname": "Alpha", "avatar_url": None, "tier": 0},
    ]
    mock_sb = _make_mock_sb(friends_data=no_friends_data)
    with patch("config.settings._client", mock_sb):
        response = build_ego_map(REQUESTER_ID)

    assert len(response.coordinates) == 1
    assert response.coordinates[0].user_id == REQUESTER_ID


def test_friend_without_position_is_skipped():
    """A friend who has no entry in user_positions is silently skipped."""
    # USER_D is a friend but has no position row
    positions_without_d = [p for p in POSITIONS if p["user_id"] != USER_D]
    mock_sb = _make_mock_sb(positions=positions_without_d)
    with patch("config.settings._client", mock_sb):
        response = build_ego_map(REQUESTER_ID)

    ids = {n.user_id for n in response.coordinates}
    assert USER_D not in ids
    assert USER_B in ids
    assert USER_C in ids
