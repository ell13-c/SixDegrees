"""Application-wide configuration.

All runtime constants live here: Supabase client factory, algorithm weights,
UMAP hyper-parameters, and embedding model settings. Import from this module
rather than accessing environment variables directly in route or service code.

Environment variables (set in ``backend/.env``):

- ``SUPABASE_URL``: Supabase project URL.
- ``SUPABASE_KEY``: Service-role key (full DB access -- keep secret).
- ``ALLOWED_ORIGINS``: Comma-separated CORS origins (default ``http://localhost:5173``).
- ``GLOBAL_COMPUTE_ENABLED``: Set to ``true`` to run the scheduled UMAP pipeline.
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# --- Supabase ---
# os.getenv() with empty-string fallback allows the test suite to import this
# module without a .env file. The real client is lazy-loaded in get_supabase_client()
# and is never constructed during tests because conftest.py patches _client directly.
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
_client: Client | None = None

def get_supabase_client() -> Client:
    """Return the singleton Supabase client, creating it on first call."""
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client

# --- Scheduler ---
GLOBAL_COMPUTE_ENABLED: bool = os.getenv("GLOBAL_COMPUTE_ENABLED", "false").lower() == "true"

# --- Algorithm ---
ALPHA: float = 0.6
BETA: float = 0.4

PROFILE_WEIGHTS: dict[str, float] = {
    "interests":  0.40,
    "location":   0.20,
    "languages":  0.15,
    "education":  0.10,
    "industry":   0.10,
    "age":        0.05,
}

INTERACTION_WEIGHTS: dict[str, float] = {
    "likes_count":    0.5,
    "comments_count": 0.5,
}

# --- UMAP ---
UMAP_N_NEIGHBORS: int  = 15
UMAP_MIN_DIST: float   = 0.1
UMAP_RANDOM_STATE: int = 42

# --- Stability ---
# --- Ego map tier thresholds ---
TIER1_K: int = 5
TIER2_K: int = 15

# --- Embeddings ---
# Fields whose similarity is computed via sentence-transformer embeddings.
# Replaces hand-crafted counterparts in the weighted profile score.
# Set to [] to disable embeddings and fall back to hand-crafted methods.
EMBEDDING_FIELDS: list[str] = ["interests", "bio"]

# Sentence-transformers model — downloads once on first run (~90MB)
EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
