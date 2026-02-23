---
phase: 04-api-and-scheduler
plan: 04
subsystem: scheduler-and-wiring
tags: [scheduler, apscheduler, lifespan, fastapi, integration]
dependency_graph:
  requires: [04-01, 04-02, 04-03]
  provides: [scheduler-and-app-wiring]
  affects: [backend/app.py, backend/services/map_pipeline/scheduler.py, backend/requirements.txt]
tech_stack:
  added: [apscheduler==3.11.2, tzlocal==5.3.1]
  patterns: [asynccontextmanager-lifespan, cron-trigger-per-timezone, per-user-error-isolation]
key_files:
  created: [backend/services/map_pipeline/scheduler.py]
  modified: [backend/app.py, backend/requirements.txt]
decisions:
  - "AsyncIOScheduler with CronTrigger per unique timezone — one DB query at startup, re-query at fire time for current user list"
  - "replace_existing=True on add_job — safe for future app restarts without duplicate jobs"
  - "Per-user and per-timezone try/except — one user's ValueError (N<10) does not abort the batch"
  - "asynccontextmanager lifespan replaces deprecated @app.on_event — modern FastAPI pattern"
  - "apscheduler pinned to >=3.10,<4 in requirements.txt — prevents accidental 4.x upgrade (breaking API)"
metrics:
  duration: "~3 min"
  completed_date: "2026-02-23"
  tasks_completed: 2
  tasks_total: 2
  files_created: 1
  files_modified: 2
---

# Phase 4 Plan 4: Scheduler and App Wiring Summary

**One-liner:** APScheduler 3.x with per-timezone CronTriggers wired into FastAPI lifespan, all Phase 4 routers registered and server starting cleanly.

## What Was Built

### Task 1: scheduler.py with setup_scheduler()

Created `backend/services/map_pipeline/scheduler.py` providing:

- `setup_scheduler()` — queries `user_profiles` for unique timezone strings, registers one `CronTrigger(hour=19, minute=0, timezone=tz)` per unique timezone, returns a configured-but-not-started `AsyncIOScheduler`
- `_run_pipeline_for_timezone(timezone)` — re-queries users in that timezone at fire time, calls `run_pipeline_for_user()` per user with per-user try/except so one failure does not abort the batch
- Invalid timezone strings caught at `add_job()` — log and skip rather than crashing startup
- Single-worker constraint documented in module docstring

### Task 2: app.py lifespan + routers; requirements.txt pin

Updated `backend/app.py`:
- Replaced bare `FastAPI()` + no lifecycle with `@asynccontextmanager async def lifespan(app)` pattern
- Calls `setup_scheduler().start()` on startup, `scheduler.shutdown()` on teardown
- Registered all four Phase 4 routers: match, map, interactions, profile
- Single-worker constraint documented in top-of-file comment

Updated `backend/requirements.txt`:
- Added `apscheduler>=3.10,<4` version pin

## Verification Results

All checks passed:
1. `from services.map_pipeline.scheduler import setup_scheduler` — OK
2. `pip show apscheduler | grep Version` — Version: 3.11.2
3. All required routes present: `/map/{user_id}`, `/interactions/like`, `/interactions/comment`, `/interactions/dm`, `/profile`
4. `apscheduler>=3.10,<4` in requirements.txt — confirmed
5. `uvicorn app:app --reload` — "Application startup complete" with no errors

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 | accd433 | feat(04-04): implement scheduler.py with setup_scheduler() |
| Task 2 | e916297 | feat(04-04): update app.py with lifespan + new routers; pin apscheduler in requirements.txt |

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED
