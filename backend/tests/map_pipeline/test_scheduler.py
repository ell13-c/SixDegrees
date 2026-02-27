from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from services.map_pipeline import scheduler_lock
from services.map_pipeline.scheduler_lock import (
    DEFAULT_LOCK_TTL_SECONDS,
    acquire_global_compute_lock,
    release_global_compute_lock,
)


def _build_mock_supabase_with_payload(payload):
    mock_sb = MagicMock()
    mock_sb.rpc.return_value.execute.return_value = SimpleNamespace(data=payload)
    return mock_sb


def test_lock_acquire_success(monkeypatch):
    mock_sb = _build_mock_supabase_with_payload({"acquired": True})
    monkeypatch.setattr(
        "services.map_pipeline.scheduler_lock.get_supabase_client",
        lambda: mock_sb,
    )

    acquired, owner_token = acquire_global_compute_lock(owner_token="owner-1")

    assert acquired is True
    assert owner_token == "owner-1"
    mock_sb.rpc.assert_called_once_with(
        "acquire_global_compute_lock",
        {
            "p_lock_key": "map_pipeline_global_compute",
            "p_owner_token": "owner-1",
            "p_ttl_seconds": DEFAULT_LOCK_TTL_SECONDS,
        },
    )


def test_lock_contention_returns_false(monkeypatch):
    mock_sb = _build_mock_supabase_with_payload({"acquired": False})
    monkeypatch.setattr(
        "services.map_pipeline.scheduler_lock.get_supabase_client",
        lambda: mock_sb,
    )

    acquired, owner_token = acquire_global_compute_lock(owner_token="owner-2")

    assert acquired is False
    assert owner_token == "owner-2"


def test_lock_release_happens_on_success_and_error(monkeypatch):
    monkeypatch.setattr(
        "services.map_pipeline.scheduler_lock.acquire_global_compute_lock",
        lambda owner_token=None, ttl_seconds=DEFAULT_LOCK_TTL_SECONDS: (True, "owner-3"),
    )

    release_calls = []

    def fake_release(owner_token):
        release_calls.append(owner_token)
        return True

    monkeypatch.setattr(
        "services.map_pipeline.scheduler_lock.release_global_compute_lock",
        fake_release,
    )

    def run_with_lock(work):
        acquired, owner_token = scheduler_lock.acquire_global_compute_lock()
        if not acquired:
            return
        try:
            work()
        finally:
            scheduler_lock.release_global_compute_lock(owner_token)

    run_with_lock(lambda: None)

    with pytest.raises(RuntimeError, match="boom"):
        run_with_lock(lambda: (_ for _ in ()).throw(RuntimeError("boom")))

    assert release_calls == ["owner-3", "owner-3"]


def test_release_global_compute_lock_success(monkeypatch):
    mock_sb = _build_mock_supabase_with_payload({"released": True})
    monkeypatch.setattr(
        "services.map_pipeline.scheduler_lock.get_supabase_client",
        lambda: mock_sb,
    )

    released = release_global_compute_lock("owner-4")

    assert released is True
    mock_sb.rpc.assert_called_once_with(
        "release_global_compute_lock",
        {
            "p_lock_key": "map_pipeline_global_compute",
            "p_owner_token": "owner-4",
        },
    )
