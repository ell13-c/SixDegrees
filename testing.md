# Testing

## Backend

### Where Tests Live
All backend tests are in `backend/tests/`. The suite is organized by domain:

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

### What Is Covered

| Area | Coverage | Notes |
|------|----------|-------|
| `app.py` | 100% | Lifespan, CORS, router registration |
| `config/settings.py` | 100% | Config constants and Supabase client factory |
| `models/user.py` | 100% | Field validation and coercion |
| `routes/` | 94-100% | All endpoints tested for happy path and auth failures |
| `services/map/` | 77-100% | Full pipeline stages, scheduler, lock, diagnostics |
| `services/matching/` | 98-100% | Embedder, similarity functions, scoring |

The scheduler job branches for `GLOBAL_COMPUTE_ENABLED=True` are not exercised by the unit tests (77% on `scheduler.py`). These require a live process and APScheduler clock, so they are verified through manual integration testing.

### How to Run

#### Prerequisites
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

No `.env` file and no live database are needed. All Supabase calls are mocked via
`unittest.mock.MagicMock`, and the module-level settings use safe empty-string defaults
when `SUPABASE_URL` and `SUPABASE_KEY` are not set.

#### Run All Tests
```bash
cd backend
source venv/bin/activate
python -m pytest -q
```

#### Run a Specific Directory
```bash
python -m pytest tests/map/
python -m pytest tests/matching/
python -m pytest tests/routes/
```

#### Run a Single File or Test
```bash
python -m pytest tests/routes/test_profile.py
python -m pytest tests/routes/test_profile.py::test_get_profile_success
```

#### Stop at First Failure
```bash
python -m pytest -x
```

#### Run with Coverage Report
```bash
python -m pytest --cov=. --cov-report=term-missing
```

## Frontend

### Where Tests Live
All frontend tests are in `frontend/src/tests/`. The suite is organized by Vue components and views:

```
frontend/src/tests/
  admin.test.js       # Admin page rendering, Auth redirects, and post management
  createpost.test.js  # Post creation including tier selection and image handling
  friends.test.js     # Friends list rendering, friend management, profile redirection
  home.test.js        # Home page rendering, Auth redirects, friend requests, post tier filtering, post deletion
  map.test.js         # People map rendering, backend connections, mobile advisements
  posts.test.js       # Post component rendering, user-relevant buttons, delete and report events
  profile.test.js     # Profile page rendering, edit options for user's own profile
  signup.test.js      # Signup page rendering, database availability checks, completion redirects
```

**Total: 181 tests, all passing.**

### What Is Covered
| Area | Coverage | Notes |
|------|----------|-------|
| `Admin.vue` | 95% | Displays single reported post for deletion or resolvement |
| `ClosenessMap.vue` | 84% | Renders coordinates accurately from backend data |
| `CreatePost.vue` | 100% | Post creation and Supabase insertion |
| `Friends.vue` | 98% | Friend list rendering and interaction |
| `Home.vue` | 96% | Primary directory, rendering, redirects, event handling |
| `PeopleMap.vue` | 86% | Contains ClosenessMap, handles errors and mobile warnings |
| `Post.vue` | 96% | Dynamic buttons, event emissions |
| `Profile.vue` | 65% | Limited testing of client-side input validation, database data validation is primary |
| `SignUp.vue` | 95% | Basic nickname validation, Supabase insertion |

### How To Run

#### Prerequisites
```bash
cd frontend
npm install
```

#### Run All Tests
```bash
cd backend
npm test
```

No live database is needed, but the `.env` file is required with a VITE_API_URL for the PeopleMap tests. All Supabase calls are mocked via `vi.mock()`, which bypasses the need for a real `SUPABASE_URL` and `SUPABASE_KEY` to be set.

#### Run a Specific Test Batch
```bash
npm test src/tests/admin.test.js
npm test src/tests/createpost.test.js
npm test src/tests/home.test.js
```

#### Run a Single Test
```bash
npm test -- src/tests/admin.test.js -t "renders the page header with "Reported Post""
npm test -- src/tests/home.test.js -t "renders the page header with "Your Feed""
```

#### Stop at First Failure
```bash
npm test -- --bail=1
```

#### Run with Coverage Report 
```bash
npm test -- --coverage
```

## Important Limitations

- **No live database calls.** The Supabase client is replaced in every test, for both backend and frontend. Real RPC behaviour (Postgres functions, RLS policies, triggers) is not tested here.
- **UMAP is called in pipeline regression tests.** `test_pipeline_regression.py` runs the real UMAP algorithm on a small synthetic dataset. This takes a few seconds and requires `umap-learn` to be installed. The snapshot embedded in `tests/fixtures/` pins the expected coordinate output; if UMAP's random state changes between versions the snapshot may need regenerating.
- **Sentence-transformer model is mocked.** `embed_profiles` is patched in most tests. The model is only exercised in the live demo notebooks, not in the unit suite.
- **APScheduler job fires are not tested end-to-end.** The `_run_job` coroutine is called directly in tests; actual cron scheduling is not verified.
