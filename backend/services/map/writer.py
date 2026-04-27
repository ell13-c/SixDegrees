"""Normalises UMAP coordinates and writes them to ``public.user_positions``.

Normalisation maps each axis to ``[0, 1]`` so that coordinates remain
consistent across pipeline runs regardless of UMAP's unanchored output scale.
"""

from datetime import datetime, timezone
import numpy as np
from config.settings import get_supabase_client


def write(user_ids: list[str], new_coords: np.ndarray) -> None:
    """Normalise ``new_coords`` to ``[0, 1]`` and upsert into ``user_positions``.

    Each row is upserted (insert or update on ``user_id`` PK) with a shared
    ``computed_at`` timestamp set to UTC now.

    Args:
        user_ids: Ordered list of user UUIDs; index ``i`` corresponds to row
            ``i`` of ``new_coords``.
        new_coords: Raw ``(N, 2)`` UMAP output from ``project()``.
    """
    # Normalize to [0, 1] so coordinates are in a consistent space across runs.
    # UMAP's raw output is unanchored — scale, translation, and orientation can
    # differ between runs even with the same random seed.
    mn = new_coords.min(axis=0)
    mx = new_coords.max(axis=0)
    rng = np.where(mx - mn == 0, 1.0, mx - mn)
    new_coords = (new_coords - mn) / rng

    sb = get_supabase_client()
    rows = []
    now = datetime.now(timezone.utc).isoformat()
    for uid, (nx, ny) in zip(user_ids, new_coords):
        rows.append({"user_id": uid, "x": float(nx), "y": float(ny), "computed_at": now})
    sb.table("user_positions").upsert(rows).execute()
