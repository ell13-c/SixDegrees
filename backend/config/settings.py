import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# --- Supabase ---
SUPABASE_URL: str = os.environ["SUPABASE_URL"]
SUPABASE_KEY: str = os.environ["SUPABASE_KEY"]
_client: Client | None = None

def get_supabase_client() -> Client:
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
    "like_count":    0.3,
    "comment_count": 0.5,
    "dm_count":      0.2,
}

# --- UMAP ---
UMAP_N_NEIGHBORS: int  = 15
UMAP_MIN_DIST: float   = 0.1
UMAP_RANDOM_STATE: int = 42

# --- Stability ---
MAX_POSITION_DELTA: float = 0.35

# --- Ego map tier thresholds ---
TIER1_K: int = 5
TIER2_K: int = 15
