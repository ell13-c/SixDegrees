---
phase: 02-core-algorithm
plan: 02
subsystem: algorithm
tags: [numpy, interaction-scoring, normalization, tdd, map-pipeline]

# Dependency graph
requires:
  - phase: 02-01
    provides: tsne_projector.py, config/algorithm.py with INTERACTION_WEIGHTS dict

provides:
  - compute_interaction_scores(): pure function converting raw pairwise interaction counts → NxN interaction score matrix in [0, 1]
  - 95th-pct clip normalization with method='lower' to prevent superuser collapse
  - Dict-driven weight dispatch via INTERACTION_WEIGHTS (zero logic changes to add new types)

affects:
  - 02-03 (combined distance scoring — consumes interaction score matrix as input)
  - 02-04 (end-to-end pipeline — depends on interaction module)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "95th-pct clip using method='lower' to pick an actual observed data value as the cap, preventing interpolated-pct from inflating the threshold near outliers"
    - "Normalize from 0 → clip_val (not min → max) so 0 interactions always scores 0.0"
    - "Dict-driven weight dispatch: INTERACTION_WEIGHTS drives all computation, no hardcoded type names"

key-files:
  created:
    - backend/services/map_pipeline/interaction.py
    - backend/tests/map_pipeline/test_interaction.py
  modified: []

key-decisions:
  - "Use np.percentile(method='lower') for 95th-pct clip: picks actual observed data point as cap, avoids interpolated value inflating threshold near outlier (discovered via test failure on 6-pair sample)"
  - "Normalize by dividing by clip_val (not clipped range): anchors 0 at 0.0 so missing pairs and zero-count pairs produce identical 0.0 score without special-case code"
  - "INTERACTION_WEIGHTS dict dispatch: all interaction type logic flows through config dict — adding new type requires only 1 column + 1 dict entry, verified by extensibility test"

patterns-established:
  - "Pure function pattern for algorithm modules: inputs only (user_ids + raw_counts), returns ndarray — no side effects, no DB calls"
  - "Canonical pair key ordering (a < b) enforced by callers, not by the scoring module itself"

requirements-completed: [INT-01, INT-02, INT-03, INT-04]

# Metrics
duration: 6min
completed: 2026-02-23
---

# Phase 2 Plan 02: Interaction Scoring Module Summary

**95th-pct clipped interaction normalizer: pure `compute_interaction_scores()` function that converts raw pairwise interaction counts into a symmetric NxN [0,1] score matrix using dict-driven weight dispatch from INTERACTION_WEIGHTS**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-02-23T00:31:52Z
- **Completed:** 2026-02-23T00:37:30Z
- **Tasks:** 1 (TDD: RED → GREEN → REFACTOR)
- **Files modified:** 2

## Accomplishments

- `compute_interaction_scores()` implemented as a pure function: `user_ids + raw_counts → NxN ndarray`
- 8 TDD tests covering all requirements: zero matrix (INT-04), superuser clipping (INT-02), [0,1] range (INT-03), dict-driven weights (INT-01), symmetry, zero diagonal
- INT-01 extensibility verified: adding `reactions` to `INTERACTION_WEIGHTS` flows through automatically with zero logic changes

## Task Commits

1. **Task 1: TDD interaction scoring module (RED → GREEN → REFACTOR)** - `ce3740a` (feat)

## Files Created/Modified

- `backend/services/map_pipeline/interaction.py` — Pure function computing NxN interaction score matrix; 95th-pct clip normalization; dict-driven weight dispatch via INTERACTION_WEIGHTS
- `backend/tests/map_pipeline/test_interaction.py` — 8 TDD tests covering INT-01 through INT-04, symmetry, and zero diagonal

## Decisions Made

1. **`np.percentile(method='lower')` for 95th-pct clip** — discovered via test failure: with 6 pairs [1000, 5, 5, 5, 5, 5], numpy's default linear interpolation gives a clip value of ~751 (close to the outlier), making normal pair scores ~0.002. Using `method='lower'` picks the actual 95th-pct data point (5 in this case), which is what the algorithm intends: clip outliers to the value that represents the top of the normal distribution.

2. **Normalize by `clip_val` not `clipped.max()`** — anchors the normalization at 0 (not at the minimum clipped value). This ensures that 0 interactions = 0.0 score without any special-case code, satisfying INT-04 elegantly: missing pairs produce 0.0 purely because they are absent from `raw_counts`, no conditional required.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed normalization producing 0.0 for non-zero interaction counts**
- **Found during:** Task 1 GREEN phase (running tests after first implementation attempt)
- **Issue:** Two tests failed: (1) `test_uses_interaction_weights_from_config` — single pair with equal counts normalized to 0.0 because vmin==vmax with min-max. (2) `test_superuser_clipping` — normal scores of 0.002 fell below the 0.01 threshold because numpy's default interpolated 95th-pct set the cap near the outlier (751), making normal pair counts (5/751) negligibly small.
- **Fix:** Changed to `np.percentile(method='lower')` to pick an actual observed data point as the clip threshold; changed normalization denominator from `clipped.max()` to `clip_val` (anchors at 0).
- **Files modified:** `backend/services/map_pipeline/interaction.py`
- **Verification:** All 8 tests green; scores are in [0,1], superuser clipping test passes with normal scores ~0.3
- **Committed in:** `ce3740a` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug in normalization logic)
**Impact on plan:** Fix was essential for correctness — the normalization edge cases would have made the module silently produce wrong results in production. The fix aligns with the stated algorithmic intent (95th-pct clip to prevent superuser collapse).

## Issues Encountered

- Initial `min-max` normalization implementation failed on edge cases: (a) single pair with all-equal values, (b) small sample where 95th-pct interpolation places cap near the outlier value. Both resolved by switching to `method='lower'` percentile and normalizing against the clip value directly.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `compute_interaction_scores()` ready to be consumed by Plan 02-03 (combined distance scoring: `distance = α × profile_dist + β × (1 - interaction_score)`)
- Module is a pure function with no I/O dependencies — easy to integrate and test in the pipeline
- INT-01 extensibility confirmed: adding future interaction types (reactions, shares, views) requires only 1 dict entry in `config/algorithm.py`

---
*Phase: 02-core-algorithm*
*Completed: 2026-02-23*
