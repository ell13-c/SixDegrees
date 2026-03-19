import pytest

from services.map_pipeline.contracts import EgoCoordinateRow, EgoProfileRow
from services.map_pipeline.ego_map import build_ego_map


def _coordinate_rows() -> list[EgoCoordinateRow]:
    return [
        EgoCoordinateRow(
            user_id="requester",
            x=10.0,
            y=5.0,
            computed_at="2026-02-26T00:00:00Z",
            version_date="2026-02-26",
        ),
        EgoCoordinateRow(
            user_id="mutual-a",
            x=14.0,
            y=11.0,
            computed_at="2026-02-26T00:00:00Z",
            version_date="2026-02-26",
        ),
        EgoCoordinateRow(
            user_id="mutual-b",
            x=7.0,
            y=9.0,
            computed_at="2026-02-26T00:00:00Z",
            version_date="2026-02-26",
        ),
        EgoCoordinateRow(
            user_id="one-way",
            x=20.0,
            y=8.0,
            computed_at="2026-02-26T00:00:00Z",
            version_date="2026-02-26",
        ),
        EgoCoordinateRow(
            user_id="suggestion-a",
            x=11.0,
            y=6.0,
            computed_at="2026-02-26T00:00:00Z",
            version_date="2026-02-26",
        ),
        EgoCoordinateRow(
            user_id="suggestion-b",
            x=9.5,
            y=5.5,
            computed_at="2026-02-26T00:00:00Z",
            version_date="2026-02-26",
        ),
    ]


def _profile_rows() -> list[EgoProfileRow]:
    return [
        EgoProfileRow(id="requester", nickname="Requester", friends=["mutual-a", "mutual-b"]),
        EgoProfileRow(id="mutual-a", nickname="Mutual A", friends=["requester"]),
        EgoProfileRow(id="mutual-b", nickname="Mutual B", friends=["requester"]),
        EgoProfileRow(id="one-way", nickname="One Way", friends=[]),
        EgoProfileRow(id="suggestion-a", nickname="Suggestion A", friends=[]),
        EgoProfileRow(id="suggestion-b", nickname="Suggestion B", friends=[]),
    ]


def test_requester_is_forced_to_origin():
    nodes = build_ego_map("requester", _coordinate_rows(), _profile_rows())

    requester = next(node for node in nodes if node.user_id == "requester")
    assert requester.x == pytest.approx(0.0, abs=1e-12)
    assert requester.y == pytest.approx(0.0, abs=1e-12)
    assert requester.is_suggestion is False


def test_returns_all_users():
    nodes = build_ego_map("requester", _coordinate_rows(), _profile_rows())

    included_ids = {node.user_id for node in nodes}
    assert included_ids == {"requester", "mutual-a", "mutual-b", "one-way", "suggestion-a", "suggestion-b"}


def test_coordinates_are_translated_relative_to_requester():
    nodes = build_ego_map("requester", _coordinate_rows(), _profile_rows())
    node_map = {node.user_id: node for node in nodes}

    assert node_map["mutual-a"].x == pytest.approx(4.0)
    assert node_map["mutual-a"].y == pytest.approx(6.0)
    assert node_map["mutual-b"].x == pytest.approx(-3.0)
    assert node_map["mutual-b"].y == pytest.approx(4.0)


def test_no_users_have_is_suggestion_true():
    nodes = build_ego_map("requester", _coordinate_rows(), _profile_rows())
    assert all(node.is_suggestion is False for node in nodes)


def test_tiers_assigned_by_distance_rank():
    nodes = build_ego_map("requester", _coordinate_rows(), _profile_rows())
    node_map = {node.user_id: node for node in nodes}

    # suggestion-b is closest (sqrt(0.25+0.25)≈0.71), suggestion-a next (sqrt(1+1)≈1.41)
    # Both should be tier 1 (K1=5, only 5 others total)
    assert node_map["suggestion-b"].tier == 1
    assert node_map["suggestion-a"].tier == 1
    assert node_map["requester"].tier == 1


def test_nodes_ordered_requester_first_then_by_distance():
    nodes = build_ego_map("requester", _coordinate_rows(), _profile_rows())

    assert nodes[0].user_id == "requester"
    # remaining nodes sorted by distance
    distances = []
    requester_coord = (10.0, 5.0)
    for node in nodes[1:]:
        dx = (node.x)  # already translated
        dy = (node.y)
        distances.append((dx**2 + dy**2) ** 0.5)
    assert all(a <= b + 1e-9 for a, b in zip(distances, distances[1:]))


def test_raises_when_requester_coordinate_missing():
    with pytest.raises(ValueError, match="requesting user coordinate row is missing"):
        build_ego_map("missing", _coordinate_rows(), _profile_rows())


def test_handles_absent_friend_lists_and_empty_profile_rows():
    coordinates = _coordinate_rows()
    profile_dicts = [{"id": "requester", "nickname": "Requester", "friends": None}]

    nodes = build_ego_map("requester", coordinates, profile_dicts)

    assert nodes[0].user_id == "requester"
    assert nodes[0].is_suggestion is False
    # All coordinate row users are returned even without profile rows
    assert len(nodes) == len(coordinates)


def test_raises_when_coordinate_rows_empty():
    with pytest.raises(ValueError, match="coordinate rows are required"):
        build_ego_map("requester", [], _profile_rows())
