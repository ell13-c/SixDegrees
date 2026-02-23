---
phase: 02-core-algorithm
plan: 01
subsystem: algorithm
tags: [tsne, scikit-learn, numpy, python, tdd]

# Dependency graph
requires:
  - phase: 01-database-foundation
    provides: user_profiles, interactions, map_coordinates tables — algorithm will read from these
provides:
  - backend/config/algorithm.py with ALPHA, BETA, INTERACTION_WEIGHTS, PROFILE_WEIGHTS constants
  - backend/services/map_pipeline/ package scaffold
  - backend/services/map_pipeline/tsne_projector.py — project_tsne() pure function
  - TDD test suite for t-SNE projector (8 tests)
affects: [02-02, 02-03, 02-04, 03-pipeline-integration, 04-api-and-scheduler]

# Tech tracking
tech-stack:
  added: [scikit-learn 1.8.0, numpy 2.4.2, scipy 1.17.1, pytest 9.0.2]
  patterns: [TDD red-green-refactor, pure-function pipeline modules, centralized algorithm constants]

key-files:
  created:
    - backend/config/algorithm.py
    - backend/services/map_pipeline/__init__.py
    - backend/services/map_pipeline/tsne_projector.py
    - backend/tests/__init__.py
    - backend/tests/map_pipeline/__init__.py
    - backend/tests/map_pipeline/test_tsne_projector.py
  modified: []

key-decisions:
  - "max_iter=1000 used (not n_iter) — renamed in sklearn 1.5; using old name causes DeprecationWarning"
  - "pytest installed separately since psycopg2-binary blocks full pip install -r requirements.txt on macOS arm64 + Python 3.14"
  - "perplexity = min(30, max(5, int(sqrt(N)))) — ensures perplexity < N at boundary (N=10 gives perplexity=5)"

patterns-established:
  - "Algorithm constants centralized in config/algorithm.py — no magic numbers in algorithm code"
  - "map_pipeline modules are pure functions — no side effects, take data in, return data out"
  - "TDD test files live in backend/tests/map_pipeline/ mirroring backend/services/map_pipeline/"

requirements-completed: [DIST-02, TSNE-01, TSNE-02, TSNE-03, TSNE-04]

# Metrics
duration: 2min
completed: 2026-02-22
---

# Phase 2 Plan 01: Algorithm Config and t-SNE Projector Summary

**Centralized algorithm constants (ALPHA=0.6, BETA=0.4) and scikit-learn TSNE projector with precomputed distance matrix, dynamic perplexity guard, and 8 TDD tests all green**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-02-22T07:26:44Z
- **Completed:** 2026-02-22T07:29:34Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Created `backend/config/algorithm.py` — single source of truth for ALPHA, BETA, INTERACTION_WEIGHTS (sum=1.0), PROFILE_WEIGHTS (sum=1.0)
- Created `backend/services/map_pipeline/` package with `tsne_projector.py` implementing `project_tsne()` — validates N>=10, computes dynamic perplexity, runs t-SNE with precomputed metric
- TDD test suite: 8 tests all green, covering ValueError for N<10, output shape, determinism, raw coordinate assertion, and perplexity boundary

## Task Commits

Each task was committed atomically:

1. **Task 1: Install deps and create algorithm config + map_pipeline package** - `489b140` (chore)
2. **Task 2: TDD RED — failing tests for t-SNE projector** - `8d798d0` (test)
3. **Task 2: TDD GREEN — implement t-SNE projector** - `1ac93e3` (feat)

_Note: TDD task has two commits — test (RED) and feat (GREEN). No REFACTOR commit needed — implementation was clean as written._

## Files Created/Modified
- `backend/config/algorithm.py` — All algorithm tuning constants; ALPHA=0.6, BETA=0.4, INTERACTION_WEIGHTS, PROFILE_WEIGHTS
- `backend/services/map_pipeline/__init__.py` — Package marker for map_pipeline module
- `backend/services/map_pipeline/tsne_projector.py` — `project_tsne()`: NxN precomputed distance matrix → (N,2) raw coordinates
- `backend/tests/__init__.py` — Test package marker
- `backend/tests/map_pipeline/__init__.py` — Test sub-package marker
- `backend/tests/map_pipeline/test_tsne_projector.py` — 8 TDD tests (all green)

## Decisions Made
- **max_iter=1000 (not n_iter):** Parameter was renamed in sklearn 1.5; using `n_iter` raises a DeprecationWarning in sklearn 1.8.0.
- **pytest installed separately:** `pip install -r requirements.txt` fails due to `psycopg2-binary` build failure on macOS arm64 + Python 3.14 (known pre-existing blocker in STATE.md). Installed `numpy`, `scikit-learn`, and `pytest` directly.
- **Perplexity formula uses int(sqrt(N)):** At N=10, `int(sqrt(10))` = 3, so `max(5, 3)` = 5, giving perplexity=5 which is safely below N=10.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed pytest separately due to psycopg2-binary build failure**
- **Found during:** Task 2 (TDD RED phase — running tests)
- **Issue:** `pip install -r requirements.txt` fails on macOS arm64 + Python 3.14 because psycopg2-binary cannot build from source. pytest was not installed.
- **Fix:** Ran `pip install pytest` directly (pre-existing known blocker; not introduced by this plan)
- **Files modified:** None (venv only)
- **Verification:** `python -m pytest tests/map_pipeline/ -v` runs successfully
- **Committed in:** Not committed (venv excluded from git)

---

**Total deviations:** 1 auto-fixed (blocking — pre-existing psycopg2 build issue)
**Impact on plan:** No scope creep. psycopg2 issue is pre-existing and tracked in STATE.md blockers.

## Issues Encountered
- `psycopg2-binary==2.9.9` in requirements.txt fails to build on macOS arm64 + Python 3.14 — pre-existing known issue. Not blocking for algorithm work (supabase-py uses HTTP). Workaround: install packages individually.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `config/algorithm.py` ready for import by all map_pipeline modules (scoring.py, interaction.py)
- `services/map_pipeline/` package scaffold in place — subsequent plans (02-02, 02-03, 02-04) add modules here
- `tsne_projector.project_tsne()` ready for integration in the full pipeline (Plan 02-04)
- sklearn version: 1.8.0 — `max_iter` is the correct parameter name

---
*Phase: 02-core-algorithm*
*Completed: 2026-02-22*

## Self-Check: PASSED

All created files verified present. All commits verified in git log.

- FOUND: backend/config/algorithm.py
- FOUND: backend/services/map_pipeline/__init__.py
- FOUND: backend/services/map_pipeline/tsne_projector.py
- FOUND: backend/tests/map_pipeline/test_tsne_projector.py
- FOUND: .planning/phases/02-core-algorithm/02-01-SUMMARY.md
- FOUND commit 489b140: chore(02-01)
- FOUND commit 8d798d0: test(02-01)
- FOUND commit 1ac93e3: feat(02-01)
- FOUND commit a58edcf: docs(02-01)
