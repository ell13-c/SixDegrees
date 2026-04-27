"""File-based deduplication lock to prevent multiple scheduler fires."""

import os
import tempfile
import time

LOCK_FILE = os.path.join(tempfile.gettempdir(), "sixdegrees_global_compute.lock")
LOCK_TTL_SECONDS = 3600  # 1 hour


def acquire_lock() -> bool:
    """Return True if lock acquired, False if already held."""
    if os.path.exists(LOCK_FILE):
        if time.time() - os.path.getmtime(LOCK_FILE) < LOCK_TTL_SECONDS:
            return False
    with open(LOCK_FILE, "w") as f:
        f.write(str(time.time()))
    return True


def release_lock() -> None:
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)
