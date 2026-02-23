# Phase 4 Context: API and Scheduler

*Derived from PROJECT.md, REQUIREMENTS.md, ROADMAP.md, CLAUDE.md, and existing backend code on 2026-02-22*

## Design Decisions

### New route files
- `backend/routes/map.py` — GET /map/{user_id}, POST /map/trigger/{user_id}
- `backend/routes/interactions.py` — POST /interactions/like, /interactions/comment, /interactions/dm
- `backend/routes/profile.py` — PUT /profile
All registered in `app.py`.

### JWT validation pattern (AUTH-01)
All write endpoints validate the Supabase JWT from `Authorization: Bearer <token>` header:
```python
user = supabase.auth.get_user(token)
```
- Missing/invalid token → HTTP 401
- User attempting to modify another user's data → HTTP 403
- Existing `/match` routes remain unprotected (not in scope to fix this milestone)

### GET /map/{user_id} (API-01 through API-04)
- Reads from `map_coordinates` table only — NO live computation at request time
- Response: `{ user_id, computed_at, coordinates: [{ user_id, x, y, tier, display_name }] }`
- If no precomputed map: returns HTTP 404 with message "Map not yet computed for this user"
- Requesting user always appears in list at (0.0, 0.0)

### POST /map/trigger/{user_id} (API-05)
- Manually triggers the pipeline orchestrator for a single user_id
- Used for testing and demo; no JWT requirement (or minimal auth — keep simple)
- Returns updated coordinates after recomputation

### Write endpoints (WRITE-01 through WRITE-04)
All write endpoints upsert to the `interactions` table in canonical pair order (user_id_a < user_id_b). Each endpoint:
- Extracts acting user from validated JWT
- Accepts `{ target_user_id }` in request body
- Upserts the interactions row, incrementing the relevant count
- `PUT /profile`: creates or updates the authenticated user's row in `user_profiles`; 403 if attempting to write another user's profile

### APScheduler (SCHED-01 through SCHED-04)
- APScheduler 3.x (NOT 4.x) — `AsyncIOScheduler`
- No Redis, no Celery, no PostgreSQL job store
- Starts via `lifespan` context manager in `app.py` (already partially stubbed there)
- At startup: query unique timezones from `user_profiles`, register one CronTrigger per timezone firing at 19:00
- On trigger: group all users with that timezone and run pipeline for all of them
- **Single worker constraint**: multi-worker uvicorn causes APScheduler to fire jobs N times. Must document this in code comments. Run only with `uvicorn app:app --reload`.
- `backend/services/map_pipeline/scheduler.py` — the scheduler setup lives here

### CORS
CORS is hardcoded to `localhost:5173` only (existing constraint, not changed this phase).

### Write pattern reminder
All application data writes go through the FastAPI backend. Frontend reads directly from Supabase (map_coordinates, user_profiles for display). Frontend writes go through backend API with JWT.

## Out of Scope for Phase 4
- Redis, Celery, multi-worker support
- Frontend UI
- Fixing existing match route auth
- Procrustes alignment / animation
