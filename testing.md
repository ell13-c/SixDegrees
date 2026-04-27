# Testing

## Where Tests Live

All tests are in `backend/tests/`. The suite is organized by domain:

```
backend/tests/
  conftest.py          # Shared fixtures (mock Supabase client, FastAPI TestClient)
  core/
    test_models.py     # UserProfile validation and field coercion
  map/
    test_fetcher.py    # Supabase data fetch and PipelineInput construction
    test_distance.py   # Combined N x N distance matrix (shape, symmetry, values)
    test_projector.py  # UMAP 2D projection (shape, dtype, determinism)
    test_validation.py # Coordinate validation (NaN, Inf, shape mismatch)
    test_writer.py     # Normalisation to [0, 1] and upsert logic
    test_ego.py        # Ego-centric map building (translation, tiers, 404)
    test_pipeline.py   # Full pipeline orchestration (happy path, failure paths)
    test_pipeline_regression.py  # Snapshot regression test for UMAP output
    test_diagnostics.py          # pipeline_runs insert (success, failed, skipped)
    test_scheduler.py            # APScheduler job (skip when disabled, lock held)
    test_lock.py                 # File-based dedup lock (acquire, stale, release)
  matching/
    test_embedder.py             # Profile text builder, cosine sim, embed_profiles
    test_embedder_property.py    # Property-based tests for cosine_sim bounds
    test_match.py                # get_top_matches (ordering, exclusion, top_n)
    test_similarity_none.py      # Similarity functions when fields are None
  routes/
    test_contracts.py            # Interactions, profile, and match contract tests
    test_deps.py                 # JWT auth dependency (missing header, invalid token)
    test_interactions.py         # POST /interactions/like and /comment endpoints
    test_map_route.py            # GET /map/:id and POST /map/trigger/:id endpoints
    test_profile.py              # GET /profile and PUT /profile endpoints
```

**Total: 138 tests, all passing.**

## What Is Covered

| Area | Coverage | Notes |
|------|----------|-------|
| `app.py` | 100% | Lifespan, CORS, router registration |
| `config/settings.py` | 100% | Config constants and Supabase client factory |
| `models/user.py` | 100% | Field validation and coercion |
| `routes/` | 94-100% | All endpoints tested for happy path and auth failures |
| `services/map/` | 77-100% | Full pipeline stages, scheduler, lock, diagnostics |
| `services/matching/` | 98-100% | Embedder, similarity functions, scoring |

The scheduler job branches for `GLOBAL_COMPUTE_ENABLED=True` are not exercised by the unit tests (77% on `scheduler.py`). These require a live process and APScheduler clock, so they are verified through manual integration testing.

## How to Run

### Prerequisites

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

No `.env` file and no live database are needed. All Supabase calls are mocked via
`unittest.mock.MagicMock`, and the module-level settings use safe empty-string defaults
when `SUPABASE_URL` and `SUPABASE_KEY` are not set.

### Run All Tests

```bash
cd backend
source venv/bin/activate
python -m pytest -q
```

### Run a Specific Directory

```bash
python -m pytest tests/map/
python -m pytest tests/matching/
python -m pytest tests/routes/
```

### Run a Single File or Test

```bash
python -m pytest tests/routes/test_profile.py
python -m pytest tests/routes/test_profile.py::test_get_profile_success
```

### Stop at First Failure

```bash
python -m pytest -x
```

### Run with Coverage Report

```bash
python -m pytest --cov=. --cov-report=term-missing
```

## Important Limitations

- **No live database calls.** The Supabase client is replaced by a `MagicMock` in every test. Real RPC behaviour (Postgres functions, RLS policies, triggers) is not tested here.
- **UMAP is called in pipeline regression tests.** `test_pipeline_regression.py` runs the real UMAP algorithm on a small synthetic dataset. This takes a few seconds and requires `umap-learn` to be installed. The snapshot embedded in `tests/fixtures/` pins the expected coordinate output; if UMAP's random state changes between versions the snapshot may need regenerating.
- **Sentence-transformer model is mocked.** `embed_profiles` is patched in most tests. The model is only exercised in the live demo notebooks, not in the unit suite.
- **APScheduler job fires are not tested end-to-end.** The `_run_job` coroutine is called directly in tests; actual cron scheduling is not verified.
