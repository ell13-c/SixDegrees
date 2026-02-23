# Phase 4: API and Scheduler - Research

**Researched:** 2026-02-22
**Domain:** FastAPI route authoring, Supabase JWT validation, APScheduler 3.x AsyncIOScheduler, Supabase upsert/RPC patterns
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- Route files: `backend/routes/map.py`, `backend/routes/interactions.py`, `backend/routes/profile.py`; all registered in `app.py`
- JWT validation on all write endpoints via `supabase.auth.get_user(token)` from `Authorization: Bearer <token>` header
- Missing/invalid token → HTTP 401; user modifying another user's data → HTTP 403
- Existing `/match` routes remain unprotected this milestone
- `GET /map/{user_id}` reads `map_coordinates` table only — NO live computation at request time
- Response: `{ user_id, computed_at, coordinates: [{ user_id, x, y, tier, display_name }] }`
- No precomputed map → HTTP 404 with message `"Map not yet computed for this user"`
- `POST /map/trigger/{user_id}` — no JWT requirement; returns updated coordinates after recomputation
- Write endpoints upsert `interactions` in canonical pair order (user_id_a < user_id_b)
- `PUT /profile` — creates or updates authenticated user's own row in `user_profiles`; 403 if targeting another user
- APScheduler 3.x `AsyncIOScheduler` — NOT 4.x
- No Redis, no Celery, no PostgreSQL job store (MemoryJobStore only)
- Starts via `lifespan` context manager in `app.py`
- One CronTrigger per unique timezone in `user_profiles`, firing at 19:00 in that timezone
- Scheduler code lives in `backend/services/map_pipeline/scheduler.py`
- Single-worker constraint must be documented in code comments
- CORS stays hardcoded to `localhost:5173`

### Claude's Discretion

None specified.

### Deferred Ideas (OUT OF SCOPE)

- Redis, Celery, multi-worker support
- Frontend UI
- Fixing existing match route auth
- Procrustes alignment / animation
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| API-01 | `GET /map/{user_id}` returns precomputed coordinates from `map_coordinates` — no live computation | Supabase `.select("*").eq("center_user_id", ...).eq("is_current", True)` pattern confirmed |
| API-02 | Response format: `{ user_id, computed_at, coordinates: [{ user_id, x, y, tier, display_name }] }` | Pydantic response model; `display_name` requires join to `user_profiles` |
| API-03 | Requesting user always in coordinates at (0.0, 0.0) — guaranteed by coord_writer (Phase 3), query confirmed |  DB includes center user row with `other_user_id == center_user_id` |
| API-04 | No precomputed map → 404 with `"Map not yet computed for this user"` | `raise HTTPException(status_code=404, ...)` pattern |
| API-05 | `POST /map/trigger/{user_id}` — triggers recomputation, returns updated coordinates | Calls `run_pipeline_for_user()` from `services.map_pipeline`, then queries `map_coordinates` |
| SCHED-01 | APScheduler AsyncIOScheduler starts with FastAPI via lifespan context manager | `asynccontextmanager` + `scheduler.start()` / `scheduler.shutdown()` confirmed |
| SCHED-02 | One CronTrigger per unique timezone in `user_profiles`, firing at 19:00 | `CronTrigger(hour=19, minute=0, timezone=tz_string)` — APScheduler 3.x accepts timezone string |
| SCHED-03 | On trigger: group all users with that timezone, run pipeline for all | Query `user_profiles` by `timezone`, loop `run_pipeline_for_user()` per user |
| SCHED-04 | Single-worker constraint documented | Code comment in `scheduler.py` and `app.py` |
| AUTH-01 | All write endpoints validate Supabase JWT via `supabase.auth.get_user(token)`; 401 on fail | `HTTPBearer` dependency + `try/except AuthApiError` → 401; confirmed `get_user(jwt)` signature |
| WRITE-01 | `POST /interactions/like` — JWT → acting user → upsert interactions incrementing `likes_count` | Atomic upsert via Postgres RPC function (see Architecture Patterns) |
| WRITE-02 | `POST /interactions/comment` — same pattern, `comments_count` | Same RPC pattern, different column |
| WRITE-03 | `POST /interactions/dm` — same pattern, `dm_count` | Same RPC pattern, different column |
| WRITE-04 | `PUT /profile` — JWT → creates/updates authenticated user's own row in `user_profiles`; 403 on mismatch | `supabase.table("user_profiles").upsert({...}, on_conflict="user_id").execute()` |
</phase_requirements>

---

## Summary

Phase 4 connects the pipeline (Phase 3) to the outside world through FastAPI routes and an APScheduler-driven daily batch. All pieces are already in place from prior phases — this phase is purely wiring: new route files, a reusable JWT dependency, and a scheduler that reads timezones from the DB and fires CronTriggers.

The most subtle problem is the interaction counter increment. The `interactions` table uses a composite PK (`user_id_a`, `user_id_b`) and canonical pair ordering. Standard upsert replaces the full row — it cannot atomically increment a column. The correct pattern is a Postgres function called via `supabase.rpc()` that uses `INSERT ... ON CONFLICT DO UPDATE SET col = col + 1`. This is a one-time DDL step (create the function in Supabase, then call it from Python) that avoids race conditions and keeps all logic server-side.

The APScheduler integration is straightforward: APScheduler 3.11.x is the current stable 3.x release, uses `AsyncIOScheduler` from `apscheduler.schedulers.asyncio`, accepts timezone strings directly in `CronTrigger`, and starts/stops cleanly inside FastAPI's `lifespan` async context manager. No pytz import is needed in application code when passing IANA timezone strings (e.g., `"America/New_York"`).

**Primary recommendation:** Create a single reusable `get_current_user()` FastAPI dependency (using `HTTPBearer` + `supabase.auth.get_user(jwt)`) and inject it into all write endpoints. Create one Postgres RPC function `increment_interaction(uid_a, uid_b, column_name)` to handle all three interaction write endpoints atomically.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.109.0 (installed) | HTTP routing, dependency injection, Pydantic integration | Already in use in this project |
| APScheduler | 3.11.2 (latest 3.x — needs install) | AsyncIOScheduler + CronTrigger for timezone-grouped cron jobs | Project-locked to 3.x; 3.11.2 is current stable |
| supabase-py | 2.28.0 (installed) | Supabase client for DB reads/writes and JWT validation | Already in use; `auth.get_user(jwt)` is the validation method |
| pydantic | (installed with fastapi) | Request/response model validation | Already in use |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `fastapi.security.HTTPBearer` | (bundled with FastAPI) | Extract Bearer token from `Authorization` header | Use as the base for `get_current_user()` dependency |
| `supabase_auth.errors.AuthApiError` | (bundled with supabase-py 2.x) | Exception type raised by `auth.get_user()` on invalid JWT | Catch this specifically to return 401 |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| APScheduler 3.x `AsyncIOScheduler` | APScheduler 4.x `AsyncScheduler` | Project explicitly requires 3.x; 4.x has incompatible API (different imports, `add_schedule` not `add_job`) |
| Postgres RPC for increment | Two-step fetch+update in Python | RPC is atomic (no race condition); two-step risks double-counting under concurrent requests |
| `HTTPBearer` | `OAuth2PasswordBearer` | `HTTPBearer` is the correct choice for opaque token validation (not OAuth2 flow) |

**Installation:**
```bash
pip install "apscheduler>=3.10,<4"
```
Then add to `requirements.txt`:
```
apscheduler>=3.10,<4
```

---

## Architecture Patterns

### Recommended Project Structure (new files only)

```
backend/
├── routes/
│   ├── map.py              # GET /map/{user_id}, POST /map/trigger/{user_id}
│   ├── interactions.py     # POST /interactions/like, /comment, /dm
│   └── profile.py          # PUT /profile
├── services/
│   └── map_pipeline/
│       └── scheduler.py    # setup_scheduler() returns configured AsyncIOScheduler
└── app.py                  # updated: lifespan, include new routers
```

### Pattern 1: Reusable JWT Dependency

**What:** A FastAPI dependency function that extracts and validates the Supabase Bearer token. All write endpoints inject this dependency to get the authenticated user's ID.

**When to use:** Every write endpoint (interactions/*, profile).

```python
# Source: Verified from supabase-py 2.28.0 + FastAPI pattern
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase_auth.errors import AuthApiError
from config.supabase import get_supabase_client

_bearer = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> str:
    """Validate Supabase JWT and return the authenticated user's UUID.

    Returns:
        str: The authenticated user's UUID (user.user.id)

    Raises:
        HTTPException 401: If token is missing, expired, or invalid.
    """
    token = credentials.credentials
    sb = get_supabase_client()
    try:
        response = sb.auth.get_user(token)
        if response is None or response.user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return response.user.id
    except AuthApiError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
```

**Key facts confirmed:**
- `sb.auth.get_user(jwt: Optional[str]) -> Optional[UserResponse]` — confirmed via `inspect.signature`
- `supabase_auth.errors.AuthApiError` — confirmed importable from installed supabase-py 2.28.0
- `response.user.id` — standard Supabase user object field (UUID string matching `user_profiles.user_id`)

### Pattern 2: GET /map/{user_id} — Read Precomputed Coordinates

**What:** Query `map_coordinates` for `is_current=true` rows for the given `center_user_id`. Join `display_name` from `user_profiles`. Return 404 if no rows found.

**Important:** `map_coordinates` has no `display_name` column — it must come from `user_profiles`. The API response shape requires it. Use a separate Supabase query or a `user_id → display_name` lookup dict.

```python
# Source: Verified from actual map_coordinates schema
# Columns: id, center_user_id, other_user_id, x, y, tier, computed_at, is_current

@router.get("/map/{user_id}")
async def get_map(user_id: str):
    sb = get_supabase_client()
    rows = (
        sb.table("map_coordinates")
        .select("other_user_id, x, y, tier, computed_at")
        .eq("center_user_id", user_id)
        .eq("is_current", True)
        .execute()
    ).data

    if not rows:
        raise HTTPException(status_code=404, detail="Map not yet computed for this user")

    # Fetch display names for all other_user_ids
    other_ids = [r["other_user_id"] for r in rows]
    profiles = (
        sb.table("user_profiles")
        .select("user_id, display_name")
        .in_("user_id", other_ids)
        .execute()
    ).data
    name_map = {p["user_id"]: p["display_name"] for p in profiles}

    computed_at = rows[0]["computed_at"]
    coordinates = [
        {
            "user_id": r["other_user_id"],
            "x": r["x"],
            "y": r["y"],
            "tier": r["tier"],
            "display_name": name_map.get(r["other_user_id"], ""),
        }
        for r in rows
    ]
    return {"user_id": user_id, "computed_at": computed_at, "coordinates": coordinates}
```

### Pattern 3: Interaction Write — Atomic Upsert+Increment via RPC

**What:** The `interactions` table has a composite PK `(user_id_a, user_id_b)`. Standard `.upsert()` replaces the whole row — it cannot increment a column. The correct atomic approach is a Postgres function.

**DB schema confirmed:**
- PK: `(user_id_a, user_id_b)` — composite, enforced by UNIQUE index
- Defaults: `likes_count=0, comments_count=0, dm_count=0, last_updated=now()`
- Check constraint: `canonical_pair_order` enforces `user_id_a < user_id_b`

**Required DDL (one-time Supabase migration):**
```sql
CREATE OR REPLACE FUNCTION increment_interaction(
    p_user_id_a UUID,
    p_user_id_b UUID,
    p_column    TEXT   -- 'likes_count', 'comments_count', or 'dm_count'
) RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
    IF p_column NOT IN ('likes_count', 'comments_count', 'dm_count') THEN
        RAISE EXCEPTION 'Invalid column: %', p_column;
    END IF;

    INSERT INTO interactions (user_id_a, user_id_b, likes_count, comments_count, dm_count)
    VALUES (p_user_id_a, p_user_id_b, 0, 0, 0)
    ON CONFLICT (user_id_a, user_id_b)
    DO NOTHING;

    EXECUTE format(
        'UPDATE interactions SET %I = %I + 1, last_updated = now() WHERE user_id_a = $1 AND user_id_b = $2',
        p_column, p_column
    ) USING p_user_id_a, p_user_id_b;
END;
$$;
```

**Python call pattern (confirmed from supabase-py 2.x docs):**
```python
# Source: Context7 supabase-py + confirmed rpc() signature
sb.rpc("increment_interaction", {
    "p_user_id_a": uid_a,
    "p_user_id_b": uid_b,
    "p_column": "likes_count",
}).execute()
```

**Canonical pair ordering in Python:**
```python
# Always enforce before calling RPC
uid_a = min(acting_user_id, target_user_id)
uid_b = max(acting_user_id, target_user_id)
```

### Pattern 4: APScheduler 3.x Lifespan Integration

**What:** `AsyncIOScheduler` from APScheduler 3.x started and stopped inside FastAPI's `lifespan` async context manager. One `CronTrigger` per unique timezone from `user_profiles`. In-memory job store (default).

**Confirmed import paths for APScheduler 3.x:**
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
```

**scheduler.py pattern:**
```python
# Source: APScheduler 3.11.x official docs + FastAPI lifespan pattern
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from config.supabase import get_supabase_client
from services.map_pipeline import run_pipeline_for_user
import logging

logger = logging.getLogger(__name__)


def _run_pipeline_for_timezone(timezone: str) -> None:
    """Fetch all users for this timezone and run the pipeline for each."""
    sb = get_supabase_client()
    rows = (
        sb.table("user_profiles")
        .select("user_id")
        .eq("timezone", timezone)
        .execute()
    ).data
    for row in rows:
        try:
            run_pipeline_for_user(row["user_id"])
        except Exception as exc:
            logger.error("Pipeline failed for user %s: %s", row["user_id"], exc)


def setup_scheduler() -> AsyncIOScheduler:
    """Create and configure AsyncIOScheduler with per-timezone CronTriggers.

    IMPORTANT — SINGLE WORKER ONLY:
    APScheduler runs in-process. Running uvicorn with multiple workers
    (--workers N) will start N scheduler instances, causing each pipeline
    job to fire N times per trigger. Always run with:
        uvicorn app:app --reload
    Never use --workers > 1.

    Returns:
        Configured but not-yet-started AsyncIOScheduler.
    """
    scheduler = AsyncIOScheduler()

    sb = get_supabase_client()
    timezones = (
        sb.table("user_profiles")
        .select("timezone")
        .execute()
    ).data

    unique_timezones = {row["timezone"] for row in timezones if row.get("timezone")}

    for tz in unique_timezones:
        scheduler.add_job(
            _run_pipeline_for_timezone,
            trigger=CronTrigger(hour=19, minute=0, timezone=tz),
            args=[tz],
            id=f"pipeline_{tz.replace('/', '_')}",
            replace_existing=True,
        )
        logger.info("Registered CronTrigger at 19:00 %s", tz)

    return scheduler
```

**app.py lifespan update:**
```python
# Source: FastAPI lifespan pattern (verified from FastAPI docs)
from contextlib import asynccontextmanager
from fastapi import FastAPI
from services.map_pipeline.scheduler import setup_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = setup_scheduler()
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)
```

### Pattern 5: PUT /profile — Upsert User Profile

**What:** JWT-validated; acting user can only update their own profile. `supabase.table("user_profiles").upsert()` with `on_conflict="user_id"`.

```python
# on_conflict="user_id" — user_id is the PK; upsert on this column
# user_profiles.user_id is UUID type (confirmed from schema)
sb.table("user_profiles").upsert(
    {"user_id": acting_user_id, **profile_fields},
    on_conflict="user_id",
).execute()
```

**403 guard:**
```python
if body.user_id and body.user_id != acting_user_id:
    raise HTTPException(status_code=403, detail="Cannot update another user's profile")
```

### Anti-Patterns to Avoid

- **Do not use `.upsert()` for interaction increments.** Standard upsert replaces the row values — it will reset counts to whatever you pass, not increment. Use the Postgres RPC function.
- **Do not import `run_pipeline_for_user` at the module level inside scheduler.py if it causes circular imports.** Import inside the function body if needed.
- **Do not use APScheduler 4.x imports.** The API changed completely (`AsyncScheduler`, `add_schedule`, SQLAlchemy data stores). The project requires 3.x only.
- **Do not start the scheduler with `@app.on_event("startup")`.** These decorators are deprecated in FastAPI 0.93+. Use the `lifespan` context manager.
- **Do not query `user_profiles` for timezones inside the scheduler job.** Query at startup to register CronTriggers, not inside each job callback. The job callback queries users by timezone at fire time.
- **Do not return the raw `map_coordinates` row as the API response.** The `display_name` field must be fetched separately from `user_profiles` — it is not in `map_coordinates`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JWT token extraction from header | Manual header parsing | `fastapi.security.HTTPBearer` | Handles missing `Authorization` header, non-Bearer schemes, returns structured `HTTPAuthorizationCredentials` |
| Timezone-aware cron scheduling | Custom asyncio `sleep()` loop | `APScheduler 3.x CronTrigger(timezone=tz)` | DST transitions, missed fires, job overlap handling are all built in |
| Atomic counter increment on conflict | Fetch-then-update in Python | Postgres RPC with `INSERT ... ON CONFLICT DO UPDATE SET col = col + 1` | Python two-step has a race window — concurrent requests will double-count |

**Key insight:** The APScheduler MemoryJobStore is sufficient here. Jobs are recreated at startup (since timezones are re-queried). There is no need for a persistent job store.

---

## Common Pitfalls

### Pitfall 1: APScheduler 4.x vs 3.x API Confusion
**What goes wrong:** Importing `from apscheduler import AsyncScheduler` (4.x API) instead of `from apscheduler.schedulers.asyncio import AsyncIOScheduler` (3.x API). The package installs whichever major version PyPI resolves — if `apscheduler` is installed without a version pin, it may install 4.x.
**Why it happens:** PyPI serves the latest version by default; 4.x is a full rewrite with different imports.
**How to avoid:** Pin in requirements.txt: `apscheduler>=3.10,<4`. Verify: `pip show apscheduler` shows `Version: 3.x.x`.
**Warning signs:** `ImportError: cannot import name 'AsyncIOScheduler' from 'apscheduler'`

### Pitfall 2: CronTrigger Timezone String Not Recognized
**What goes wrong:** APScheduler 3.x raises `UnknownTimeZoneError` if the timezone string is invalid or unrecognized.
**Why it happens:** Seed data uses IANA strings (`"America/New_York"`) but typos or legacy timezone names (e.g., `"EST"`) can fail.
**How to avoid:** Wrap `add_job()` in a try/except during scheduler setup. Log the error and skip that timezone rather than crashing the entire app startup.
**Warning signs:** App fails to start; `pytz.exceptions.UnknownTimeZoneError` in logs.

### Pitfall 3: display_name Missing from /map Response
**What goes wrong:** `map_coordinates` has no `display_name` column. Returning rows directly from `map_coordinates` produces coordinates without display names.
**Why it happens:** The schema stores only `center_user_id, other_user_id, x, y, tier, computed_at, is_current`. The API contract requires `display_name` in each coordinate entry.
**How to avoid:** After fetching coordinates, fetch all `other_user_id` display names from `user_profiles` in a single `.in_()` query and build a lookup dict. Never make N individual lookups in a loop.
**Warning signs:** `display_name` is `null` or missing from the API response.

### Pitfall 4: Interaction Self-Loop
**What goes wrong:** A user sends a like to themselves. `min(uid, uid) == max(uid, uid)` produces `user_id_a == user_id_b`, which violates the `canonical_pair_order` CHECK constraint (which enforces `user_id_a < user_id_b`).
**Why it happens:** No guard in the Python endpoint.
**How to avoid:** Add a check in each interaction endpoint: `if acting_user_id == target_user_id: raise HTTPException(400, "Cannot interact with yourself")`.
**Warning signs:** Supabase returns a constraint violation error on the interactions upsert/RPC call.

### Pitfall 5: Scheduler Fires on Stale Timezone Set
**What goes wrong:** New users join after app startup. Their timezones are not registered as CronTriggers because the timezone query happens only at startup.
**Why it happens:** Timezones are read once at `setup_scheduler()` call time.
**How to avoid:** This is acceptable behavior for this milestone (SCHED-04 does not require dynamic re-registration). Document it. Each scheduler job re-queries users by timezone at fire time — new users in existing timezones are automatically picked up. Only new timezones added after startup are missed.
**Warning signs:** Users in a new timezone never get their map computed by the scheduler.

### Pitfall 6: run_pipeline_for_user Raises ValueError (N < 10)
**What goes wrong:** The scheduler calls `run_pipeline_for_user()` for a timezone group that happens to have fewer than 10 users visible in the combined dataset. The pipeline raises `ValueError`.
**Why it happens:** `tsne_projector.py` raises `ValueError` if N < 10 (documented). The orchestrator propagates it.
**How to avoid:** Wrap each `run_pipeline_for_user()` call in the scheduler job body with `try/except Exception` and log. Don't let one user's pipeline failure abort the rest of the batch. (See Pattern 4 above — `_run_pipeline_for_timezone` already shows this pattern.)
**Warning signs:** Scheduler job exits early; some users' maps are not updated.

---

## Code Examples

### Minimal Interaction Write Endpoint

```python
# Source: Verified pattern from CONTEXT.md + supabase-py 2.x + FastAPI
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from auth_deps import get_current_user  # the reusable dependency
from config.supabase import get_supabase_client

router = APIRouter(prefix="/interactions", tags=["interactions"])

class InteractionBody(BaseModel):
    target_user_id: str

@router.post("/like")
def record_like(
    body: InteractionBody,
    acting_user_id: str = Depends(get_current_user),
):
    if acting_user_id == body.target_user_id:
        raise HTTPException(status_code=400, detail="Cannot interact with yourself")

    uid_a = min(acting_user_id, body.target_user_id)
    uid_b = max(acting_user_id, body.target_user_id)

    get_supabase_client().rpc("increment_interaction", {
        "p_user_id_a": uid_a,
        "p_user_id_b": uid_b,
        "p_column": "likes_count",
    }).execute()

    return {"detail": "Like recorded"}
```

### Registering Routers in app.py

```python
# Source: FastAPI router include pattern; existing app.py already uses include_router
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.match import router as match_router
from routes.map import router as map_router
from routes.interactions import router as interactions_router
from routes.profile import router as profile_router
from services.map_pipeline.scheduler import setup_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = setup_scheduler()
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(match_router)
app.include_router(map_router)
app.include_router(interactions_router)
app.include_router(profile_router)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `@app.on_event("startup")` / `@app.on_event("shutdown")` | `lifespan` async context manager | FastAPI 0.93 (2023) | Old events are deprecated; lifespan is the canonical pattern |
| APScheduler 3.x (stable, maintenance mode) | APScheduler 4.x (new, breaking API) | APScheduler 4.0 (2024) | Project must stay on 3.x per constraints; version-pin is mandatory |
| `OAuth2PasswordBearer` for token extraction | `HTTPBearer` for opaque JWT validation | N/A — different use cases | `OAuth2PasswordBearer` implies OAuth2 flow; `HTTPBearer` is correct for validating third-party JWTs |

**Deprecated/outdated:**
- `@app.on_event("startup")` / `@app.on_event("shutdown")`: Deprecated since FastAPI 0.93. Use `lifespan`.
- APScheduler 4.x's `AsyncScheduler` / `add_schedule`: Not applicable to this project (wrong major version).

---

## Open Questions

1. **Where to place the `get_current_user` dependency?**
   - What we know: It will be used by all three route files (`interactions.py`, `profile.py`, and potentially `map.py` in future).
   - What's unclear: Should it live in `routes/deps.py`, `routes/auth_deps.py`, or directly in each router file?
   - Recommendation: Create `backend/routes/deps.py` with `get_current_user()`. All routers import from there. Avoids duplication, keeps auth logic in one place.

2. **Should `POST /map/trigger/{user_id}` return the full response or just 200 OK?**
   - What we know: CONTEXT.md says "returns updated coordinates after recomputation". API-05 says "manually triggers pipeline recomputation."
   - What's unclear: Return format — same shape as `GET /map/{user_id}`, or simpler `{"detail": "Pipeline complete"}`?
   - Recommendation: Return the same `{ user_id, computed_at, coordinates: [...] }` shape as `GET /map/{user_id}` — makes it immediately testable and the API feels complete.

3. **Scheduler job store — should timezones be re-registered if `user_profiles` changes?**
   - What we know: Jobs registered once at startup from DB query. New timezones added post-startup won't get a CronTrigger.
   - What's unclear: Whether this gap matters for the demo.
   - Recommendation: Document the limitation (SCHED-04). The scheduler job itself re-queries users at fire time, so all users in already-registered timezones are covered. New timezones require an app restart.

---

## Sources

### Primary (HIGH confidence)
- `supabase-py 2.28.0` installed in `/Users/BAEK/Code/sixDegrees/backend/venv` — `inspect.signature(SyncGoTrueClient.get_user)` confirmed `(self, jwt: Optional[str] = None) -> Optional[UserResponse]`
- `supabase_auth.errors.AuthApiError` — confirmed importable from installed package
- Supabase live DB — confirmed `interactions` schema: composite PK `(user_id_a, user_id_b)`, defaults `likes_count=0`
- Supabase live DB — confirmed `map_coordinates` schema: no `display_name` column
- Supabase live DB — confirmed `user_profiles` has `timezone TEXT` with 6 distinct IANA values
- Context7 `/supabase/supabase-py` — `rpc()` method signature and usage confirmed
- Context7 `/fastapi/fastapi` — lifespan pattern, `HTTPBearer`, `Security()` confirmed
- [APScheduler 3.x official docs](https://apscheduler.readthedocs.io/en/3.x/userguide.html) — `AsyncIOScheduler`, `CronTrigger(timezone=tz_string)`, MemoryJobStore default confirmed
- [APScheduler 3.x CronTrigger docs](https://apscheduler.readthedocs.io/en/3.x/modules/triggers/cron.html) — `hour`, `minute`, `timezone` parameter confirmed

### Secondary (MEDIUM confidence)
- [grokipedia.com Supabase Auth + FastAPI](https://grokipedia.com/page/Supabase_Auth_and_FastAPI_Integration) — `HTTPBearer` + `auth.get_user()` + `try/except` pattern; verified against supabase-py source
- APScheduler PyPI — version 3.11.2 is current stable 3.x as of December 2025

### Tertiary (LOW confidence)
- None.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — installed versions confirmed directly; APScheduler version confirmed from PyPI
- Architecture: HIGH — DB schemas confirmed from live Supabase; supabase-py API confirmed from installed package inspection; FastAPI patterns from Context7
- Pitfalls: HIGH for DB-constraint pitfalls (confirmed from live schema); MEDIUM for scheduler timing pitfalls (reasoning from documented behavior)

**Research date:** 2026-02-22
**Valid until:** 2026-03-22 (stable libraries; APScheduler 3.x and supabase-py 2.x are stable)
