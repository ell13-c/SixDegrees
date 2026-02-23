---
phase: 05-demo-and-docs
plan: "02"
subsystem: demo
tags: [jupyter, notebook, matplotlib, tsne, pipeline, visualization]

# Dependency graph
requires:
  - phase: 03-pipeline-integration
    provides: run_pipeline_for_user, data_fetcher.fetch_all, map_pipeline modules
  - phase: 04-api-and-scheduler
    provides: map_coordinates table populated by scheduler and trigger endpoints

provides:
  - scripts/people_map_demo.ipynb — interactive Jupyter notebook walking through all 5 pipeline stages with inline matplotlib heatmaps and scatter plots
  - jupyter and ipykernel==6.30.1 declared in backend/requirements.txt
affects: [05-demo-and-docs]

# Tech tracking
tech-stack:
  added: [jupyter, ipykernel==6.30.1, notebook, nbconvert]
  patterns: [sys.path.insert for notebook backend imports, names_lookup dict for display_name not in UserProfile model]

key-files:
  created:
    - scripts/people_map_demo.ipynb
  modified:
    - backend/requirements.txt

key-decisions:
  - "Fetch display_name from Supabase separately in notebook setup — UserProfile model omits display_name; added names_lookup dict via get_supabase_client()"
  - "Use p.id (not p.user_id) for UserProfile access — actual model field is 'id' not 'user_id'"
  - "Use interaction keys 'likes'/'comments'/'dms' (not 'likes_count') — data_fetcher.py maps DB column names to these shorter keys"
  - "ipykernel pinned at 6.30.1 — ipykernel 7.x has kernel connect issue with Python 3.14 free-threaded build"

patterns-established:
  - "Notebook path resolution: os.path.abspath('backend') from project root, not __file__ (undefined in Jupyter cells)"
  - "Sensitivity demo pattern: run pipeline, record baseline, bump interaction count, re-run, compare side-by-side, restore in finally block"

requirements-completed: [DEMO-02, DEMO-03, DEMO-04]

# Metrics
duration: 3min
completed: 2026-02-23
---

# Phase 5 Plan 02: Jupyter Demo Notebook Summary

**Jupyter notebook walking through all 5 pipeline stages — data fetch to origin-translated People Map — with per-stage matplotlib heatmaps, 3-color tier scatter plot, and Alex-Skyler sensitivity demonstration**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-02-23T20:23:19Z
- **Completed:** 2026-02-23T20:26:34Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Installed jupyter and ipykernel==6.30.1 into backend venv; added both to requirements.txt Demo section
- Created 14-cell Jupyter notebook (7 markdown + 7 code) covering: setup, data fetch with display_name lookup, interaction scoring heatmap, combined distance heatmap, t-SNE raw scatter, origin-translated People Map with 3-color tiers, and sensitivity demo
- Sensitivity cell bumps Alex-Skyler likes_count to 60, re-runs full pipeline via run_pipeline_for_user(), shows side-by-side plots, restores original count in try/finally

## Task Commits

1. **Task 1: Install Jupyter dependencies and update requirements.txt** - `b053b17` (chore)
2. **Task 2: Create people_map_demo.ipynb** - `9a3077a` (feat)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified
- `scripts/people_map_demo.ipynb` — 14-cell interactive Jupyter notebook demo
- `backend/requirements.txt` — Added `jupyter` and `ipykernel==6.30.1` under Demo deliverables section

## Decisions Made
- **display_name not in UserProfile:** The `UserProfile` Pydantic model has no `display_name` field (it stores `id`, `city`, `state`, etc.). The notebook fetches display names from Supabase directly via `get_supabase_client()` and stores in `names_lookup` dict used throughout.
- **Field name correction:** Plan code used `p.user_id` and `p.display_name` — actual model uses `p.id`. All cells corrected to use `p.id`.
- **Interaction key names:** Plan code used `counts.get('likes_count', 0)` — `data_fetcher.py` maps DB column names `likes_count/comments_count/dm_count` to short keys `likes/comments/dms`. All cells use the short keys.
- **ipykernel 6.30.1 pinned:** Prevents accidental upgrade to 7.x which has kernel connectivity issue on Python 3.14.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed UserProfile field name references (p.user_id → p.id, p.display_name lookup)**
- **Found during:** Task 2 (notebook creation)
- **Issue:** Plan code referenced `p.user_id` and `p.display_name`, but the actual `UserProfile` Pydantic model uses `p.id` and has no `display_name` field
- **Fix:** Used `p.id` for user ID access; added a separate Supabase query in the Data Fetch cell to build `names_lookup = {user_id: display_name}` dict; replaced all `p.display_name` references with `names_lookup.get(p.id, ...)`
- **Files modified:** scripts/people_map_demo.ipynb
- **Verification:** Notebook JSON is structurally valid; all required function names present; plan assertions pass
- **Committed in:** 9a3077a (Task 2 commit)

**2. [Rule 1 - Bug] Fixed interaction dict key names (likes_count → likes)**
- **Found during:** Task 2 (notebook creation)
- **Issue:** Plan code used `counts.get('likes_count', 0)` etc., but `data_fetcher.py` returns dicts with keys `"likes"`, `"comments"`, `"dms"` (not `"likes_count"`, `"comments_count"`, `"dm_count"`)
- **Fix:** Changed all interaction count lookups in Stage 1 display to use the correct short key names matching data_fetcher output
- **Files modified:** scripts/people_map_demo.ipynb
- **Verification:** Key names match INTERACTION_WEIGHTS dict in config/algorithm.py
- **Committed in:** 9a3077a (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (both Rule 1 - Bug, field name mismatches between plan pseudocode and actual implementation)
**Impact on plan:** Both fixes necessary for notebook to run without AttributeError/KeyError. No scope creep.

## Issues Encountered
- Plan 05-01 (test_map.py) had already run before this plan: `scripts/test_map.py` existed, `matplotlib>=3.10` was in requirements.txt, but no 05-01-SUMMARY.md was present. Added `jupyter` and `ipykernel==6.30.1` to the existing Demo deliverables section in requirements.txt.

## User Setup Required
None - no additional external service configuration required beyond existing `backend/.env` with Supabase credentials.

## Next Phase Readiness
- `scripts/people_map_demo.ipynb` ready for stakeholder review — launch with `jupyter notebook` from project root
- Plan 05-03 (API contract + DB schema docs) can proceed independently
- Note: notebook requires seeded Supabase database (run `python scripts/seed_db.py` from backend/) to execute all cells

## Self-Check: PASSED

- FOUND: scripts/people_map_demo.ipynb
- FOUND: .planning/phases/05-demo-and-docs/05-02-SUMMARY.md
- FOUND: backend/requirements.txt
- FOUND commit b053b17 (Task 1 — chore: jupyter dependencies)
- FOUND commit 9a3077a (Task 2 — feat: notebook creation)
- Notebook validation: 7 code cells, 7 markdown cells, all required imports present, try/finally present

---
*Phase: 05-demo-and-docs*
*Completed: 2026-02-23*
