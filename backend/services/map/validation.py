"""Validates UMAP output before it is written to the database.

Catches shape mismatches and NaN/Inf values that would corrupt stored
coordinates. Runs between the projector and writer stages in the pipeline.
"""

import numpy as np


def validate_output(coords: np.ndarray, user_ids: list[str]) -> None:
    """Validate that UMAP output coordinates are safe to persist.

    Args:
        coords: Shape ``(N, 2)`` ndarray produced by ``project()``.
        user_ids: List of N user UUIDs corresponding to coordinate rows.

    Raises:
        ValueError: If the array shape does not match ``(len(user_ids), 2)``,
            or if the array contains NaN or Inf values.
    """
    if coords.shape != (len(user_ids), 2):
        raise ValueError(f"Shape mismatch: {coords.shape} vs ({len(user_ids)}, 2)")
    if np.any(np.isnan(coords)) or np.any(np.isinf(coords)):
        raise ValueError("Coordinates contain NaN or Inf values")
