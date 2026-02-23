---
phase: 03-pipeline-integration
plan: "01"
subsystem: database
tags: [supabase, supabase-py, fastapi, postgresql, data-fetcher, coord-writer]

# Dependency graph
requires:
  - phase: 01-database-foundation
    provides: user_profiles, interactions, and map_coordinates tables with service role key access
  - phase: 02-core-algorithm
    provides: run_pipeline() orchestrator that defines the input/output contract for these modules

provides:
  - fetch_all() function reading user_profiles + interactions from Supabase (data_fetcher.py)
  - write_coordinates() function implementing two-step write to map_coordinates (coord_writer.py)
  - DB read/write boundary wrappers that connect Phase 2 pure computation to live Supabase data

affects:
  - 03-pipeline-integration (plan 02 — scheduler will call both modules)
  - 04-api-and-scheduler (routes will call run_pipeline() which depends on these boundaries)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Two-step write pattern: UPDATE is_current=False then INSERT new rows — never DELETE"
    - "Field mapping at DB boundary: location_city→city, location_state→state"
    - "Hardcode missing DB fields at boundary (occupation='') rather than changing the model"
    - "Tuple keys for interaction pairs: (user_id_a, user_id_b) where a < b"

key-files:
  created:
    - backend/services/map_pipeline/data_fetcher.py
    - backend/services/map_pipeline/coord_writer.py
  modified: []

key-decisions:
  - "Smoke test for coord_writer used nil-UUID (00000000-0000-0000-0000-000000000001) not 'test-center-000' — map_coordinates.center_user_id is UUID type, string literal fails DB validation"
  - "occupation hardcoded to '' at the DB boundary — user_profiles table has no occupation column; UserProfile model requires the field; boundary absorbs the mismatch"
  - "write_coordinates() includes center user entry (other_user_id==center_user_id, x=0,y=0) in every write — caller (run_pipeline) produces it, writer does not filter"

patterns-established:
  - "DB boundary modules are stateless functions only — no retry logic, no algorithm logic"
  - "Never delete old map_coordinates rows — mark is_current=False for animation delta retention"

requirements-completed: [DATA-01, DATA-02, DATA-03, STORE-01, STORE-02, STORE-03]

# Metrics
duration: 2min
completed: 2026-02-23
---

# Phase 3 Plan 01: Pipeline DB Wiring Summary

**Supabase read/write boundary for map pipeline: fetch_all() maps location_city/state→city/state, write_coordinates() implements two-step mark-then-insert pattern retaining old rows for animation delta**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-02-23T03:24:44Z
- **Completed:** 2026-02-23T03:26:22Z
- **Tasks:** 2
- **Files modified:** 2 (both new)

## Accomplishments

- Implemented data_fetcher.py with fetch_all() that reads 20 user profiles and 35 interactions from live Supabase, mapping DB column names (location_city/location_state) to UserProfile fields (city/state) and hardcoding occupation="" for the absent DB column
- Implemented coord_writer.py with write_coordinates() that performs the mandatory two-step write: UPDATE is_current=False on existing rows then INSERT new rows — never DELETE (STORE-02 animation delta retention)
- Verified round-trip smoke test: two sequential writes produce exactly 1 is_current=True row and 1 retained is_current=False row

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement data_fetcher.py** - `b4e8b7d` (feat)
2. **Task 2: Implement coord_writer.py** - `101974c` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `backend/services/map_pipeline/data_fetcher.py` - fetch_all() reads user_profiles + interactions; maps location_city→city, location_state→state; hardcodes occupation=""; returns tuple-keyed interaction dict matching INTERACTION_WEIGHTS keys
- `backend/services/map_pipeline/coord_writer.py` - write_coordinates() implements two-step write pattern; marks old is_current=True rows as False; inserts new rows including center user at (0,0)

## Decisions Made

- Smoke test UUID: plan used "test-center-000" but map_coordinates.center_user_id is a UUID column; used nil-UUID `00000000-0000-0000-0000-000000000001` instead — same functional test, passes DB type validation
- occupation hardcoded to "" at the boundary: user_profiles table has no occupation column but UserProfile Pydantic model requires the field; absorbing the mismatch at the DB boundary is cleaner than modifying the model (matches Phase 2 plan decision)
- write_coordinates() includes center user row verbatim from translated_results without filtering — the caller (origin_translator) already includes it

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Smoke test used invalid UUID string for center_user_id**
- **Found during:** Task 2 (coord_writer.py verification)
- **Issue:** Plan's verify block used "test-center-000" as center_user_id; map_coordinates.center_user_id is UUID type — DB rejected the string with `invalid input syntax for type uuid`
- **Fix:** Used nil-UUID `00000000-0000-0000-0000-000000000001` — valid UUID format, won't conflict with real seed data, functionally equivalent test
- **Files modified:** None (smoke test was a CLI one-liner, not a file)
- **Verification:** Smoke test passed; two-step write pattern confirmed
- **Committed in:** 101974c (Task 2 commit — implementation unchanged)

---

**Total deviations:** 1 auto-fixed (test input format issue, not an implementation bug)
**Impact on plan:** Smoke test ran with a valid UUID. Production coord_writer.py unchanged. No scope creep.

## Issues Encountered

None beyond the UUID type mismatch in the verify block (documented above).

## User Setup Required

None — no new external service configuration required. Uses existing Supabase service role key from backend/.env.

## Next Phase Readiness

- Both DB boundary modules ready: fetch_all() and write_coordinates() are stateless, importable, and verified against live Supabase
- Phase 3 Plan 02 (scheduler.py) can now wire: fetch_all() → run_pipeline() → write_coordinates() for each user's daily map update
- No blockers

---
*Phase: 03-pipeline-integration*
*Completed: 2026-02-23*

## Self-Check: PASSED

- FOUND: backend/services/map_pipeline/data_fetcher.py
- FOUND: backend/services/map_pipeline/coord_writer.py
- FOUND: .planning/phases/03-pipeline-integration/03-01-SUMMARY.md
- FOUND: commit b4e8b7d (feat(03-01): implement data_fetcher.py)
- FOUND: commit 101974c (feat(03-01): implement coord_writer.py)
