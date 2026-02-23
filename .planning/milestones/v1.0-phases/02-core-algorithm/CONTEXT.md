# Phase 2 Context: Core Algorithm

*Derived from PROJECT.md, REQUIREMENTS.md, ROADMAP.md, CLAUDE.md, and existing backend code on 2026-02-22*

## Design Decisions

### New module location
All Phase 2 code goes in `backend/services/map_pipeline/` (new directory). Existing `services/matching/` is kept intact — the old routes (`/match`, `/graph`) still rely on it. Do NOT modify existing matching code except where explicitly needed.

### config/algorithm.py
This file must be created in `backend/config/algorithm.py` with:
- `ALPHA = 0.6` (profile distance weight)
- `BETA = 0.4` (interaction weight)
- `INTERACTION_WEIGHTS = {"likes": ..., "comments": ..., "dms": ...}` (must sum to 1.0)
- `PROFILE_WEIGHTS` dict (mirrors DEFAULT_WEIGHTS from services/matching/scoring.py)
No magic numbers allowed in algorithm code — all tunables live here.

### interaction.py (INT-01 through INT-04)
- Reads `INTERACTION_WEIGHTS` from `config/algorithm.py` — the dict drives everything
- Normalizes each interaction type independently: clip at 95th percentile, then min-max to [0, 1]
- Missing pairs (no interactions) → interaction_score = 0.0
- Final score per pair = weighted sum of normalized per-type scores → value in [0, 1]
- Adding a new interaction type = add column to DB + add entry to INTERACTION_WEIGHTS dict, zero logic changes

### scoring.py in map_pipeline (DIST-01 through DIST-04)
New file `map_pipeline/scoring.py` (distinct from existing `matching/scoring.py`):
- Reuses existing `services/matching/scoring.py` to get profile_distance (1 - similarity)
- Combined distance formula: `distance(i,j) = α × profile_distance(i,j) + β × (1 - interaction_score(i,j))`
- Output NxN matrix: symmetric, zeros on diagonal, all values in [0, 1]
- ALPHA and BETA come from `config/algorithm.py`

### tsne_projector.py (TSNE-01 through TSNE-04)
- `sklearn.manifold.TSNE(metric='precomputed', init='random', random_state=42)` — NOT `init='pca'` (crashes with precomputed metric)
- Perplexity: `min(30, max(5, int(sqrt(N))))` — computed dynamically at call time
- Fail fast with clear error if N < 10: raise ValueError with descriptive message (not sklearn crash)
- Raw t-SNE coordinates preserved before origin translation (for future Procrustes alignment)

### origin_translator.py (ORIG-01 through ORIG-03)
- Subtracts requesting user's raw t-SNE coordinates from ALL users' coordinates
- Result: requesting user is at exactly (0.0, 0.0)
- Tier assignment computed from 2D Euclidean distances in translated coordinate space:
  - Tier 1 = 5 nearest, Tier 2 = next 10 (ranks 6-15), Tier 3 = all remaining users
  - Requesting user is included in output at (0, 0) as Tier 1
  - **Decision:** `get_ranked_matches()` from `services/matching/clustering.py` is NOT used
    here because it operates on the precomputed NxN distance matrix (not 2D coords) and
    has a hard 0.75 cutoff that would silently drop distant users from the map.
    Tier assignment is implemented directly from 2D Euclidean distances — same thresholds
    (K1=5, K2=15), no user exclusion. clustering.py constants are mirrored for consistency.
- Origin translation applied independently per requesting user (stateless pure function)

### Phase 2 is pure computation — no DB
Phase 2 modules take in-memory data structures (lists, numpy arrays). No Supabase calls, no HTTP, no scheduler. All modules are testable with synthetic data. DB wiring happens in Phase 3.

### visualization.py (PCA) replacement
`services/matching/visualization.py` (PCA-based) is being replaced by the t-SNE pipeline, but do NOT delete it this phase — the existing `/graph` route still uses it. The new tsne_projector.py lives in map_pipeline/ as a standalone module.

## Out of Scope for Phase 2
- Any Supabase reads or writes
- API endpoints
- Scheduler code
- Modifying existing matching/ service or match routes
- Writing results to map_coordinates table (Phase 3)
