"""Tests for GET /match endpoint."""

import pytest
from unittest.mock import MagicMock, patch
from starlette.testclient import TestClient

from tests.conftest import TEST_USER_ID

# Two extra users that will appear in the profiles table alongside the acting user
OTHER_USER_ID_1 = "other-user-uuid-1"
OTHER_USER_ID_2 = "other-user-uuid-2"

_FULL_PROFILE_ROWS = [
    {
        "id": TEST_USER_ID,
        "nickname": "Test User",
        "age": 25,
        "city": "SF",
        "state": "CA",
        "interests": ["coding", "music"],
        "languages": ["English"],
        "education": "CS",
        "industry": "Tech",
        "occupation": "Engineer",
        "bio": None,
        "avatar_url": None,
        "profile_tier": 1,
        "is_admin": False,
    },
    {
        "id": OTHER_USER_ID_1,
        "nickname": "Alice",
        "age": 27,
        "city": "SF",
        "state": "CA",
        "interests": ["coding", "gaming"],
        "languages": ["English"],
        "education": "CS",
        "industry": "Tech",
        "occupation": "Designer",
        "bio": None,
        "avatar_url": None,
        "profile_tier": 1,
        "is_admin": False,
    },
    {
        "id": OTHER_USER_ID_2,
        "nickname": "Bob",
        "age": 40,
        "city": "NYC",
        "state": "NY",
        "interests": ["sports"],
        "languages": ["Spanish"],
        "education": "Biology",
        "industry": "Healthcare",
        "occupation": "Doctor",
        "bio": None,
        "avatar_url": None,
        "profile_tier": 2,
        "is_admin": False,
    },
]


def _make_client_with_profiles(rows: list[dict]):
    """Build a TestClient whose profiles table mock returns the given rows."""
    from app import app
    from routes.deps import get_current_user

    mock_sb = MagicMock()

    profiles_tbl = MagicMock()
    profiles_tbl.select.return_value.execute.return_value.data = rows

    def _table_side_effect(table_name):
        if table_name == "profiles":
            return profiles_tbl
        tbl = MagicMock()
        tbl.select.return_value.execute.return_value.data = []
        return tbl

    mock_sb.table.side_effect = _table_side_effect

    with patch("config.settings._client", mock_sb):
        with patch("services.map.scheduler.setup_scheduler", return_value=MagicMock()):
            app.dependency_overrides[get_current_user] = lambda: TEST_USER_ID
            with TestClient(app, raise_server_exceptions=False) as tc:
                yield tc
            app.dependency_overrides.clear()


# --- Tests ---

def test_match_happy_path():
    """Returns 200 with matches list; each item has the required keys."""
    for tc in _make_client_with_profiles(_FULL_PROFILE_ROWS):
        resp = tc.get("/match")
    assert resp.status_code == 200
    body = resp.json()
    assert "matches" in body
    matches = body["matches"]
    assert len(matches) >= 1
    for m in matches:
        assert "user_id" in m
        assert "nickname" in m
        assert "similarity_score" in m
        assert isinstance(m["similarity_score"], float)


def test_match_self_excluded():
    """The acting user must not appear in the matches list."""
    for tc in _make_client_with_profiles(_FULL_PROFILE_ROWS):
        resp = tc.get("/match")
    assert resp.status_code == 200
    user_ids = [m["user_id"] for m in resp.json()["matches"]]
    assert TEST_USER_ID not in user_ids


def test_match_404_no_profiles():
    """Returns 404 when the profiles table is empty."""
    for tc in _make_client_with_profiles([]):
        resp = tc.get("/match")
    assert resp.status_code == 404
    assert "No profiles found" in resp.json()["detail"]


def test_match_404_profile_not_found():
    """Returns 404 when profiles exist but the acting user is absent."""
    rows_without_current = [r for r in _FULL_PROFILE_ROWS if r["id"] != TEST_USER_ID]
    for tc in _make_client_with_profiles(rows_without_current):
        resp = tc.get("/match")
    assert resp.status_code == 404
    assert "profile was not found" in resp.json()["detail"]


def test_match_401_no_auth(client_no_auth):
    """Returns 401 when no JWT is supplied."""
    resp = client_no_auth.get("/match")
    assert resp.status_code == 401


def test_match_top_n_negative_returns_422():
    """GET /match?top_n=-1 must return 422 (FastAPI query validation)."""
    for tc in _make_client_with_profiles(_FULL_PROFILE_ROWS):
        resp = tc.get("/match?top_n=-1")
    assert resp.status_code == 422
