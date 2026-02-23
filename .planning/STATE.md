# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-22)

**Core value:** The People Map — every user is always at (0,0), all others positioned by profile similarity + interaction intensity, updated daily
**Current focus:** Phase 2 — Algorithm Pipeline

## Current Position

Phase: 2 of 5 (Algorithm Pipeline) — IN PROGRESS
Current Plan: 02-02 complete
Next: Phase 2 Plan 03 — Combined Distance Scoring (02-03)
Status: Plan 02-02 complete — interaction scoring module built and tested (8 TDD tests green)
Last activity: 2026-02-23 — Plan 02-02 complete; compute_interaction_scores() implemented with 95th-pct clip normalization

Progress: [█████░░░░░] 28%

## Performance Metrics

**Velocity:**
- Total plans completed: 4
- Average duration: ~14min (01-01: ~45min including checkpoint, 01-02: ~4min, 02-01: ~2min, 02-02: ~6min)
- Total execution time: ~0.95 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-database-foundation | 2 complete / 2 total | ~49min | ~24min |
| 02-core-algorithm | 2 complete / 4 total | ~8min | ~4min |

**Recent Trend:**
- Last 5 plans: 01-01 (~45min, includes human checkpoint), 01-02 (~4min), 02-01 (~2min), 02-02 (~6min)
- Trend: Fast execution for pure coding tasks

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- t-SNE over PCA: `metric='precomputed'` requires `init='random'` — NOT 'pca' (crashes)
- α=0.6, β=0.4 defaults in `backend/config/algorithm.py` — no magic numbers in algorithm code
- Dict-driven INTERACTION_WEIGHTS: adding new type = 1 column + 1 dict entry, zero logic changes
- Canonical pair ordering in interactions table (user_id_a < user_id_b) — prevents duplicate rows
- Batch precompute + store: t-SNE is expensive; precompute at 7pm, serve from DB
- No FK from user_profiles.user_id to auth.users — seed users won't exist in auth.users, FK would block inserts
- FK constraints on interactions wrapped in DO $$ block for idempotency (plan 01-01)
- RLS enabled on all 3 tables; service role key used in all backend DB access (plan 01-01)
- Column names in user_profiles are location_city/location_state (not city/state) — matches DDL from plan 01-01
- Hardcoded UUIDs in seed script for idempotent upserts — same PKs on every re-run
- max_iter=1000 (not n_iter) — parameter renamed in sklearn 1.5; old name causes DeprecationWarning in 1.8.0 (plan 02-01)
- perplexity = min(30, max(5, int(sqrt(N)))) — at N=10 gives perplexity=5, safely < N (plan 02-01)
- scikit-learn 1.8.0, numpy 2.4.2 installed in backend venv (plan 02-01)
- np.percentile(method='lower') for 95th-pct clip: picks actual observed data point as cap, avoids interpolated threshold near outlier (plan 02-02)
- Normalize by clip_val not clipped.max(): anchors at 0 so missing pairs always score 0.0 without special-case code (plan 02-02)

### Pending Todos

None.

### Blockers/Concerns

- Known bug: `handleLogout()` in `Home.vue` scoped inside `loadPosts()` — crashes on logout. Out of scope this milestone but worth noting.
- APScheduler single-worker constraint: multi-worker uvicorn causes double-firing. Must document clearly.
- Supabase RLS: verify service role key is used for all backend DB reads (not anon key). Verified for algorithm tables; existing match routes not yet validated.
- `psycopg2-binary` fails to build on macOS arm64 + Python 3.14. Not blocking for seed script (supabase-py uses HTTP). May need resolution before SQLAlchemy usage in later phases.

## Session Continuity

Last session: 2026-02-23
Stopped at: Plan 02-02 complete. Next: Phase 2 Plan 03 — Combined Distance Scoring (02-03).
