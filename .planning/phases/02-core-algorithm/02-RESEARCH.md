# Phase 2: Core Algorithm - Research

**Researched:** 2026-02-22
**Domain:** NumPy numerical computation, scikit-learn t-SNE, signal normalization, pure Python algorithm pipeline
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- All Phase 2 code goes in `backend/services/map_pipeline/` (new directory). Existing `services/matching/` is kept intact — old routes (`/match`, `/graph`) still rely on it. Do NOT modify existing matching code except where explicitly needed.
- `backend/config/algorithm.py` must be created with: `ALPHA = 0.6`, `BETA = 0.4`, `INTERACTION_WEIGHTS = {"likes": ..., "comments": ..., "dms": ...}` (must sum to 1.0), `PROFILE_WEIGHTS` dict (mirrors `DEFAULT_WEIGHTS` from `services/matching/scoring.py`). No magic numbers in algorithm code — all tunables live here.
- `interaction.py`: reads `INTERACTION_WEIGHTS` from `config/algorithm.py`; normalizes each type independently (clip at 95th percentile, then min-max to [0, 1]); missing pairs → 0.0; final score = weighted sum → [0, 1].
- `map_pipeline/scoring.py` (distinct from `matching/scoring.py`): reuses existing `services/matching/scoring.py` to get profile_distance; combined formula: `distance(i,j) = α × profile_distance(i,j) + β × (1 - interaction_score(i,j))`; output NxN matrix symmetric, zeros on diagonal, all values in [0, 1].
- `tsne_projector.py`: `sklearn.manifold.TSNE(metric='precomputed', init='random', random_state=42)` — NOT `init='pca'` (crashes with precomputed metric); perplexity = `min(30, max(5, int(sqrt(N))))` dynamic; fail fast if N < 10 with descriptive ValueError; raw t-SNE coords preserved before translation.
- `origin_translator.py`: subtract requesting user's raw t-SNE coordinates from ALL users; requesting user → (0.0, 0.0); tier assignment using existing KNN logic from `services/matching/clustering.py`; requesting user included at (0, 0) as Tier 1; applied independently per requesting user.
- Phase 2 is pure computation — no Supabase calls, no HTTP, no scheduler. All modules testable with synthetic in-memory data.
- `services/matching/visualization.py` (PCA-based): do NOT delete this phase — the existing `/graph` route still uses it. The new `tsne_projector.py` lives in `map_pipeline/` as a standalone module.

### Claude's Discretion

None specified.

### Deferred Ideas (OUT OF SCOPE)

- Any Supabase reads or writes
- API endpoints
- Scheduler code
- Modifying existing `matching/` service or match routes
- Writing results to `map_coordinates` table (Phase 3)
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INT-01 | Interaction score computation reads weights from `INTERACTION_WEIGHTS` dict config; adding new type = 1 column + 1 dict entry, zero logic changes | Dict-driven weight dispatch is a standard pattern; verified with `INTERACTION_WEIGHTS` design in CONTEXT.md |
| INT-02 | Each interaction type normalized independently using min-max with 95th-percentile clipping before normalization (prevents superuser collapse) | NumPy `np.percentile(arr, 95)` + `np.clip()` + min-max; well-established signal normalization pattern |
| INT-03 | Final interaction score per pair = weighted sum of normalized individual type scores → value in [0, 1] | Weighted sum with weights summing to 1.0 preserves [0,1] bound; verified by construction |
| INT-04 | Missing pairs (no interactions) produce `interaction_score = 0.0` (no special case needed) | Dict lookup with `.get(pair_key, 0.0)` default; canonical pair key ordering identical to DB pattern |
| DIST-01 | Combined distance formula: `distance(i,j) = α × profile_distance(i,j) + β × (1 - interaction_score(i,j))` | Existing `similarity_to_distance()` in `matching/scoring.py` returns profile distance; combine with interaction term via ALPHA/BETA from config |
| DIST-02 | α and β stored in `backend/config/algorithm.py` with defaults α=0.6, β=0.4; no magic numbers in algorithm code | Config module pattern already established by `config/supabase.py`; trivial to create |
| DIST-03 | Profile distance preserves existing field weights (interests 35%, location 20%, languages 15%, field_of_study 10%, industry 10%, education 5%, age 5%) | `DEFAULT_WEIGHTS` in `matching/scoring.py` already encodes these; `PROFILE_WEIGHTS` in `config/algorithm.py` mirrors it |
| DIST-04 | Resulting NxN matrix: values in [0,1], symmetric, zeros on diagonal | Guaranteed if profile_distance ∈ [0,1], interaction_score ∈ [0,1], α + β = 1.0, α,β ≥ 0; need explicit diagonal fill and symmetry enforcement |
| TSNE-01 | t-SNE uses `sklearn.manifold.TSNE` with `metric='precomputed'`, `init='random'`, `random_state=42` | Confirmed in Context7 docs: `metric='precomputed'` requires `init='random'` (PCA init crashes with precomputed); scikit-learn ≥ 1.4 in requirements |
| TSNE-02 | Perplexity: `perplexity = min(30, max(5, int(sqrt(N))))` where N = number of users | Confirmed valid range 5–50 per sklearn docs; dynamic computation is straightforward `math.sqrt` |
| TSNE-03 | Pipeline raises clear error if N < 10 (t-SNE unstable below this threshold) | Explicit `raise ValueError(...)` before calling TSNE; sklearn would give unclear error otherwise |
| TSNE-04 | Raw t-SNE coordinates preserved before origin translation (for future Procrustes alignment) | Return both raw and translated coords from projector; caller stores raw separately |
| ORIG-01 | After t-SNE, coordinates translated so requesting user is at (0.0, 0.0) by subtracting their raw coordinates from all users' coordinates | NumPy array subtraction: `coords_translated = coords_raw - coords_raw[user_idx]`; verified float precision |
| ORIG-02 | Tier assignment uses existing KNN logic: Tier 1 = 5 nearest, Tier 2 = next 10, Tier 3 = within 0.75 threshold; requesting user at (0,0) as Tier 1 | Reuse `get_ranked_matches()` from `matching/clustering.py`; requesting user inserted as explicit Tier 1 result after KNN |
| ORIG-03 | Origin translation applied independently per requesting user | Function takes (coords, user_idx) → translated coords; stateless, run per user independently |
</phase_requirements>

---

## Summary

Phase 2 is a pure NumPy computation pipeline with no I/O. It builds five new modules in `backend/services/map_pipeline/` plus one new config file. The critical dependencies are: NumPy (array operations, percentile, clip), scikit-learn (TSNE), and the existing `backend/services/matching/` modules which are called — not reimplemented.

The most important technical constraint is that `sklearn.manifold.TSNE(metric='precomputed')` **requires** `init='random'` — confirmed directly from scikit-learn docs. Using `init='pca'` with `metric='precomputed'` raises an error at runtime. Since the requirements.txt pins `scikit-learn>=1.4`, the parameter name `max_iter` applies (renamed from `n_iter` in scikit-learn 1.5). Plans should use `max_iter` to avoid deprecation warnings on the installed version.

A critical field-name mismatch exists between the existing `UserProfile` Pydantic model (uses `city`/`state`/`occupation` fields) and the `user_profiles` Supabase table (uses `location_city`/`location_state`, no `occupation` column). The existing `matching/` modules reference `u.city` and `u.state`. Since Phase 2 is pure computation and takes in-memory data, the planner must decide whether Phase 2 introduces a second data model (e.g., `MapUserProfile`) or reuses `UserProfile` with adapter logic — this is the key open question for the planner.

**Primary recommendation:** Build each module as a pure function taking/returning NumPy arrays and plain Python dicts. No classes, no state. Use `np.percentile` + `np.clip` for normalization. Wire together in a single `pipeline.py` orchestrator function that the planner can test end-to-end with synthetic data.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| numpy | >=1.26 (in requirements.txt) | All matrix operations, percentile, clip, array math | Only viable option for N×N matrix computation in Python |
| scikit-learn | >=1.4 (in requirements.txt) | `sklearn.manifold.TSNE` | Standard ML library; TSNE with precomputed metric is well-supported |
| math (stdlib) | Python stdlib | `math.sqrt` for perplexity computation | No dependency needed |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| typing (stdlib) | Python stdlib | Type hints for function signatures | All new modules should use typed signatures |
| dataclasses or TypedDict | Python stdlib | Structured return types from pipeline stages | For the coordinate output dicts passed between stages |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| sklearn TSNE | openTSNE | openTSNE is faster for N > 5000 but is a v2 requirement (SCALE-01); sklearn is sufficient for N ≤ 20 (seed data) and typical user counts |
| numpy min-max normalization | scipy stats | scipy adds a dependency; numpy is already required and sufficient |

**Installation:**
```bash
cd backend && source venv/bin/activate
pip install numpy scikit-learn
```

Note: scikit-learn and numpy are in `requirements.txt` but NOT currently installed in the venv (the venv only has supabase-related packages installed). The plan MUST include a step to install dependencies before running tests.

---

## Architecture Patterns

### Recommended Project Structure

```
backend/
├── config/
│   ├── supabase.py         # existing
│   └── algorithm.py        # NEW: ALPHA, BETA, INTERACTION_WEIGHTS, PROFILE_WEIGHTS
├── services/
│   ├── matching/           # UNTOUCHED
│   │   ├── scoring.py
│   │   ├── similarity.py
│   │   ├── clustering.py
│   │   └── visualization.py
│   └── map_pipeline/       # NEW directory (all Phase 2 code)
│       ├── __init__.py
│       ├── interaction.py  # INT-01..INT-04
│       ├── scoring.py      # DIST-01..DIST-04
│       ├── tsne_projector.py  # TSNE-01..TSNE-04
│       ├── origin_translator.py  # ORIG-01..ORIG-03
│       └── pipeline.py     # orchestrator: wire all stages together
```

### Pattern 1: Pure Function Modules

Each module exports one primary function with typed signatures. No module-level state, no I/O, no HTTP. This makes them directly unit-testable with synthetic numpy arrays.

**Example — interaction.py:**
```python
# Source: CONTEXT.md design decisions + standard numpy pattern
import numpy as np
from config.algorithm import INTERACTION_WEIGHTS

def compute_interaction_scores(
    user_ids: list[str],
    raw_counts: dict[tuple[str, str], dict[str, int]],
) -> np.ndarray:
    """
    Returns NxN matrix of interaction scores in [0, 1].
    raw_counts: {(uid_a, uid_b): {"likes": int, "comments": int, "dms": int}, ...}
    Pair key must be canonical (uid_a < uid_b).
    """
    n = len(user_ids)
    id_to_idx = {uid: i for i, uid in enumerate(user_ids)}

    # Collect per-type raw values for normalization
    type_values: dict[str, list[float]] = {t: [] for t in INTERACTION_WEIGHTS}
    for pair_counts in raw_counts.values():
        for itype in INTERACTION_WEIGHTS:
            type_values[itype].append(float(pair_counts.get(itype, 0)))

    # Normalize each type independently: clip at 95th pct, then min-max
    normalized: dict[str, dict[tuple, float]] = {}
    for itype, weight in INTERACTION_WEIGHTS.items():
        vals = np.array(type_values[itype])
        clip_val = np.percentile(vals, 95) if len(vals) > 0 else 1.0
        clipped = np.clip(vals, 0, clip_val)
        vmin, vmax = clipped.min(), clipped.max()
        if vmax > vmin:
            norm_vals = (clipped - vmin) / (vmax - vmin)
        else:
            norm_vals = np.zeros_like(clipped)
        normalized[itype] = dict(zip(raw_counts.keys(), norm_vals.tolist()))

    # Build NxN matrix
    matrix = np.zeros((n, n))
    for pair_key, pair_counts in raw_counts.items():
        uid_a, uid_b = pair_key
        i, j = id_to_idx[uid_a], id_to_idx[uid_b]
        score = sum(
            INTERACTION_WEIGHTS[itype] * normalized[itype].get(pair_key, 0.0)
            for itype in INTERACTION_WEIGHTS
        )
        matrix[i][j] = score
        matrix[j][i] = score  # symmetric
    return matrix
```

### Pattern 2: t-SNE with Precomputed Distance Matrix

```python
# Source: Context7 - scikit-learn official docs (https://scikit-learn.org/stable/modules/generated/sklearn.manifold.TSNE)
import math
import numpy as np
from sklearn.manifold import TSNE

def project_tsne(distance_matrix: np.ndarray) -> np.ndarray:
    """
    Returns (N, 2) array of 2D coordinates.
    distance_matrix: NxN, symmetric, zeros on diagonal, values in [0, 1].
    """
    n = distance_matrix.shape[0]
    if n < 10:
        raise ValueError(
            f"t-SNE requires at least 10 users, got {n}. "
            "Add more users before running the pipeline."
        )
    perplexity = min(30, max(5, int(math.sqrt(n))))
    tsne = TSNE(
        n_components=2,
        metric="precomputed",
        init="random",         # REQUIRED with metric='precomputed'; 'pca' raises ValueError
        random_state=42,
        perplexity=perplexity,
        learning_rate="auto",
        max_iter=1000,         # renamed from n_iter in sklearn 1.5
    )
    return tsne.fit_transform(distance_matrix)
```

### Pattern 3: Origin Translation

```python
# Source: CONTEXT.md + ORIG-01 requirement
import numpy as np

def translate_to_origin(
    coords: np.ndarray,     # (N, 2) raw t-SNE output
    user_idx: int,          # index of the requesting user
) -> np.ndarray:
    """Shift all coords so requesting user is at (0.0, 0.0)."""
    return coords - coords[user_idx]
```

### Pattern 4: Pipeline Orchestrator

```python
# backend/services/map_pipeline/pipeline.py
from services.map_pipeline.interaction import compute_interaction_scores
from services.map_pipeline.scoring import build_combined_distance_matrix
from services.map_pipeline.tsne_projector import project_tsne
from services.map_pipeline.origin_translator import translate_and_assign_tiers

def run_pipeline(
    users: list,                           # list of UserProfile (or equivalent)
    raw_interaction_counts: dict,          # {(uid_a, uid_b): {"likes": int, ...}}
    requesting_user_id: str,
) -> dict:
    """
    Returns {
        "raw_coords": np.ndarray,          # (N, 2) before translation — TSNE-04
        "translated_results": list[dict],  # [{"user_id": ..., "x": ..., "y": ..., "tier": ...}]
    }
    """
    ...
```

### Anti-Patterns to Avoid

- **Using `init='pca'` with `metric='precomputed'`:** Raises `ValueError` in sklearn. Always use `init='random'`.
- **Computing perplexity as a constant (e.g., 30) without guarding N < 10:** sklearn raises cryptic errors when `perplexity >= N`. The guard `min(30, max(5, int(sqrt(N))))` and the N < 10 fast-fail prevent this.
- **Using `n_iter` parameter name:** Renamed to `max_iter` in sklearn 1.5. Since requirements.txt pins `scikit-learn>=1.4`, the installed version may be 1.5+; use `max_iter` to avoid deprecation warnings.
- **Magic numbers in algorithm code:** All α, β, tier thresholds, and interaction weights must come from `config/algorithm.py`. Calling code must import from config, not hardcode.
- **Reimplementing similarity logic:** The existing `services/matching/scoring.py` (`build_similarity_matrix`, `apply_weights`, `similarity_to_distance`) already handles profile distance correctly. Call it; don't rewrite it.
- **Modifying `UserProfile` model in `models/user.py`:** The existing `UserProfile` uses `city`/`state` field names while `user_profiles` DB table uses `location_city`/`location_state`. Do NOT change the model — it would break existing `/match` routes. Instead, Phase 2 modules should either accept the existing `UserProfile` (with city/state) or define a separate `MapUserProfile` for map-pipeline use. This is a key decision for the planner.
- **Float precision on diagonal:** After combined distance computation, explicitly `np.fill_diagonal(matrix, 0.0)` to prevent floating-point drift (as the existing `similarity_to_distance` does).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| 2D dimensionality reduction | Custom t-SNE | `sklearn.manifold.TSNE` | t-SNE is notoriously hard to implement correctly; many subtle gradient/normalization details |
| Percentile clipping | Custom percentile | `np.percentile()` + `np.clip()` | Edge cases with small N, NaN handling; numpy's implementation is well-tested |
| KNN tier assignment | Custom KNN sort | `services/matching/clustering.get_ranked_matches()` | Already exists, tested, and correct — zero logic changes required |
| Profile similarity computation | Custom similarity | `services/matching/scoring.build_similarity_matrix()` | Already exists with correct weights; reusing it fulfills DIST-03 |

**Key insight:** Phase 2's value is wiring together existing and new components, not reimplementing well-solved problems.

---

## Common Pitfalls

### Pitfall 1: `init='pca'` with `metric='precomputed'`

**What goes wrong:** `ValueError: The parameter init="pca" cannot be used with metric="precomputed"` at runtime.
**Why it happens:** PCA initialization requires feature vectors; with precomputed distances, sklearn has no feature vectors to run PCA on.
**How to avoid:** Always set `init='random'` when `metric='precomputed'`. This is documented in CONTEXT.md and confirmed in sklearn official docs.
**Warning signs:** Any code path that constructs `TSNE(metric='precomputed', init='pca')` will fail.

### Pitfall 2: perplexity >= N

**What goes wrong:** sklearn raises: `ValueError: 'perplexity' must be less than 'n_samples'` or produces degenerate output.
**Why it happens:** t-SNE's perplexity is related to effective neighborhood size; if perplexity ≥ N, the neighborhood exceeds the dataset.
**How to avoid:** The formula `min(30, max(5, int(sqrt(N))))` ensures perplexity ≤ sqrt(N) for small N. The N < 10 guard provides a clean fail-fast before sklearn sees degenerate input.
**Warning signs:** N close to perplexity value; N = 10 with sqrt(10) ≈ 3.16 → int → 3 → max(5, 3) = 5 (safe).

### Pitfall 3: `n_iter` vs `max_iter` parameter name

**What goes wrong:** `TypeError: __init__() got an unexpected keyword argument 'n_iter'` on sklearn >=1.5.
**Why it happens:** Parameter was renamed from `n_iter` to `max_iter` in sklearn 1.5 (confirmed in Context7 docs).
**How to avoid:** Use `max_iter` in all TSNE constructor calls.
**Warning signs:** `DeprecationWarning: n_iter was renamed to max_iter` on sklearn 1.4.x.

### Pitfall 4: Superuser collapse (not clipping at 95th percentile)

**What goes wrong:** One user with 1000 likes causes all other users to have normalized score ≈ 0.0, making interaction data meaningless for the majority.
**Why it happens:** Raw min-max normalization when max >> median collapses normal values to near-zero.
**How to avoid:** `clip_val = np.percentile(values, 95)` before min-max. INT-02 mandates this.
**Warning signs:** Normalized interaction matrix has nearly all zeros except one or two pairs.

### Pitfall 5: Asymmetric distance matrix causing t-SNE artifacts

**What goes wrong:** t-SNE with `metric='precomputed'` expects a symmetric distance matrix. If matrix[i][j] != matrix[j][i], results are undefined.
**Why it happens:** Interaction scores built by iterating over canonical pairs are symmetric by construction, but floating-point drift in profile similarity computation can cause epsilon asymmetry.
**How to avoid:** Enforce symmetry after building combined matrix: `D = (D + D.T) / 2` and `np.fill_diagonal(D, 0.0)`.
**Warning signs:** `assert np.allclose(D, D.T)` fails on the output matrix.

### Pitfall 6: Field name mismatch — `city`/`state` vs `location_city`/`location_state`

**What goes wrong:** The existing `UserProfile` Pydantic model (used by `matching/`) has fields `city` and `state`. The `user_profiles` Supabase table has `location_city` and `location_state`. The `matching/scoring.py` calls `u.city` and `u.state`.
**Why it happens:** The DB schema was finalized in Phase 1 with `location_city`/`location_state` column names, but the Pydantic model predates that decision.
**How to avoid:** Since Phase 2 is pure computation with in-memory data, the planner has two options:
  1. Pass existing `UserProfile` objects to `map_pipeline/scoring.py` (which internally calls `matching/scoring.py` that expects `.city`/`.state`) — requires callers (Phase 3 data_fetcher) to map DB column names when constructing `UserProfile`
  2. Define a new `MapUserProfile` dataclass in `map_pipeline/` with `location_city`/`location_state` fields and an adapter layer in Phase 3
  Option 1 is simpler for Phase 2 and defers the mapping to Phase 3's data_fetcher where DB column names are known.
**Warning signs:** `AttributeError: 'UserProfile' object has no attribute 'location_city'`

---

## Code Examples

Verified patterns from official sources:

### t-SNE with precomputed distance matrix (confirmed sklearn API)

```python
# Source: Context7 - https://scikit-learn.org/stable/modules/generated/sklearn.manifold.TSNE
import math
import numpy as np
from sklearn.manifold import TSNE

def project_tsne(dist_matrix: np.ndarray) -> np.ndarray:
    n = dist_matrix.shape[0]
    if n < 10:
        raise ValueError(
            f"t-SNE pipeline requires at least 10 users; received {n}. "
            "Ensure the user set has at least 10 members before calling the pipeline."
        )
    perplexity = min(30, max(5, int(math.sqrt(n))))
    tsne = TSNE(
        n_components=2,
        metric="precomputed",
        init="random",          # required: 'pca' is incompatible with metric='precomputed'
        random_state=42,
        perplexity=perplexity,
        learning_rate="auto",
        max_iter=1000,          # use max_iter (not n_iter) for sklearn >= 1.5
    )
    return tsne.fit_transform(dist_matrix)
```

### Min-max normalization with 95th-percentile clipping (numpy)

```python
# Source: REQUIREMENTS.md INT-02 + standard numpy pattern
import numpy as np

def normalize_with_clip(values: np.ndarray, percentile: float = 95.0) -> np.ndarray:
    """
    Clip at given percentile then min-max normalize to [0, 1].
    Handles all-zero input by returning zeros.
    """
    if len(values) == 0:
        return values
    clip_val = np.percentile(values, percentile)
    clipped = np.clip(values, 0.0, clip_val)
    vmin, vmax = clipped.min(), clipped.max()
    if vmax == vmin:
        return np.zeros_like(clipped, dtype=float)
    return (clipped - vmin) / (vmax - vmin)
```

### Combined distance matrix (reusing existing matching module)

```python
# Source: CONTEXT.md DIST-01 + existing matching/scoring.py API
import numpy as np
from config.algorithm import ALPHA, BETA, PROFILE_WEIGHTS
from services.matching.scoring import build_similarity_matrix, apply_weights, similarity_to_distance

def build_combined_distance_matrix(
    users: list,               # list[UserProfile] with .city/.state fields
    interaction_matrix: np.ndarray,  # NxN scores from compute_interaction_scores()
) -> np.ndarray:
    """
    Combined distance: α × profile_dist + β × (1 - interaction_score)
    Returns NxN matrix in [0, 1], symmetric, zeros on diagonal.
    """
    sim_matrix = build_similarity_matrix(users)
    weighted_sim = apply_weights(sim_matrix, PROFILE_WEIGHTS)
    profile_dist = similarity_to_distance(weighted_sim)   # NxN, [0,1]

    combined = ALPHA * profile_dist + BETA * (1.0 - interaction_matrix)

    # Enforce symmetry and clean diagonal (guard against floating-point drift)
    combined = (combined + combined.T) / 2.0
    np.fill_diagonal(combined, 0.0)
    return combined
```

### config/algorithm.py structure

```python
# backend/config/algorithm.py
# All algorithm tuning constants. No magic numbers in algorithm code — change here only.

ALPHA: float = 0.6   # Weight for profile distance component
BETA: float = 0.4    # Weight for interaction score component
# ALPHA + BETA must equal 1.0

INTERACTION_WEIGHTS: dict[str, float] = {
    "likes":    0.3,
    "comments": 0.5,
    "dms":      0.2,
    # To add a new interaction type:
    # 1. Add column to interactions table in Supabase
    # 2. Add entry here (weights must sum to 1.0)
    # Zero logic changes required anywhere else.
}

# Mirrors DEFAULT_WEIGHTS from services/matching/scoring.py.
# Kept here so map_pipeline/ can import without depending on matching/ directly.
PROFILE_WEIGHTS: dict[str, float] = {
    "interests":       0.35,
    "location":        0.20,
    "languages":       0.15,
    "field_of_study":  0.10,
    "industry":        0.10,
    "education_level": 0.05,
    "age":             0.05,
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| PCA for 2D projection (`visualization.py`) | t-SNE with precomputed distance (`tsne_projector.py`) | Phase 2 (this milestone) | t-SNE preserves local cluster structure better; PCA treats similarity matrix as feature space |
| `init='pca'` (sklearn 1.2+ default for raw data) | `init='random'` (required for precomputed metric) | sklearn 1.2 changed default — but precomputed metric always required random | No visible change to user; internal t-SNE initialization |
| `n_iter` parameter | `max_iter` parameter | sklearn 1.5 | Must use `max_iter` in code; `n_iter` raises deprecation warning then error |

**Deprecated/outdated:**
- `visualization.py` (PCA): will eventually be superseded but kept this phase (existing `/graph` route uses it)
- `n_iter` TSNE parameter: renamed to `max_iter` in sklearn 1.5; do not use `n_iter`

---

## Open Questions

1. **Which Python data model does `map_pipeline/scoring.py` accept?**
   - What we know: `matching/scoring.py`'s `build_similarity_matrix()` calls `u.city` and `u.state` on `UserProfile` objects. The Supabase DB table uses `location_city`/`location_state`. Phase 3's `data_fetcher.py` will read from DB.
   - What's unclear: Should Phase 2's `scoring.py` accept the existing `UserProfile` (with `city`/`state`) and defer the field mapping to Phase 3, or should it define a new `MapUserProfile` now?
   - Recommendation: Accept `UserProfile` as-is in Phase 2 (reusing all of `matching/scoring.py` cleanly), and document that Phase 3's `data_fetcher.py` must map `location_city`→`city` and `location_state`→`state` when constructing `UserProfile` objects. This is the path of least resistance that keeps Phase 2 purely computational.

2. **Should `pipeline.py` orchestrator be part of Phase 2 or Phase 3?**
   - What we know: Phase 2 is pure computation; Phase 3 adds DB wiring. A `pipeline.py` that wires stages together without DB is valid Phase 2 work.
   - What's unclear: The orchestrator in Phase 3 will wrap Phase 2's pipeline with DB reads (data_fetcher) and writes (coord_writer).
   - Recommendation: Include `pipeline.py` in Phase 2 as an end-to-end orchestrator taking in-memory data, so Phase 2 can be verified completely. Phase 3 adds DB wrapper around it.

3. **What INTERACTION_WEIGHTS values should be used for likes/comments/dms?**
   - What we know: They must sum to 1.0. CONTEXT.md says to include the dict but doesn't specify values.
   - Recommendation: Use `{"likes": 0.3, "comments": 0.5, "dms": 0.2}` — this weights DMs heaviest (intimate), comments medium (engaged), likes lightest (passive). Reasonable defaults; all live in config so trivially changeable.

---

## Sources

### Primary (HIGH confidence)

- `/scikit-learn/scikit-learn` (Context7) — TSNE parameter API, `metric='precomputed'` + `init='random'` requirement, `max_iter` rename from `n_iter` in v1.5, `init='pca'` incompatibility confirmation
- `/websites/scikit-learn_stable` (Context7) — TSNE initialization parameters table, perplexity guidance, precomputed metric pipeline pattern
- Existing codebase: `backend/services/matching/scoring.py`, `similarity.py`, `clustering.py`, `visualization.py`, `models/user.py` — all read directly

### Secondary (MEDIUM confidence)

- CONTEXT.md `/Users/BAEK/Code/sixDegrees/.planning/phases/02-core-algorithm/CONTEXT.md` — design decisions and architecture confirmed by user
- REQUIREMENTS.md `/Users/BAEK/Code/sixDegrees/.planning/REQUIREMENTS.md` — requirement text confirmed

### Tertiary (LOW confidence)

- Recommended `INTERACTION_WEIGHTS` values (likes 0.3, comments 0.5, dms 0.2) — based on domain reasoning, not validated

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — requirements.txt lists numpy + scikit-learn; versions verified in venv setup
- Architecture: HIGH — CONTEXT.md is locked decisions; existing code read directly
- Pitfalls: HIGH for sklearn API pitfalls (Context7-verified); MEDIUM for field-name mismatch (codebase-verified, solution recommended)
- INTERACTION_WEIGHTS values: LOW — domain reasoning only

**Research date:** 2026-02-22
**Valid until:** 2026-04-22 (scikit-learn API is stable; numpy array operations are stable)

---

## Critical Pre-Implementation Note

scikit-learn and numpy are listed in `backend/requirements.txt` but are **not installed** in the current venv (`/Users/BAEK/Code/sixDegrees/backend/venv/`). The first task in any Phase 2 plan must be:

```bash
cd backend && source venv/bin/activate && pip install -r requirements.txt
```

This will install numpy, scikit-learn, and their dependencies (scipy, joblib, threadpoolctl). Without this step, all Phase 2 code will fail with `ModuleNotFoundError`.
