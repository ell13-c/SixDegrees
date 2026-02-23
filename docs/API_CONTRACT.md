# SixDegrees API Contract

**Version:** 1.0 (Phase 4 complete — 2026-02-23)
**Base URL:** `http://localhost:8000` (local development)
**Purpose:** Frontend API reference. The frontend reads map coordinates directly from Supabase; all writes go through these endpoints.

---

## Authentication

All write endpoints require a Supabase JWT in the `Authorization` header.

**Header format:**
```
Authorization: Bearer <supabase_jwt>
```

**How to obtain the token:** After the user logs in via Supabase Auth (`supabase.auth.signIn`), the session includes `session.access_token`. Pass this value as the Bearer token on every write request.

**Token errors:**

| Code | Detail string | Meaning |
|------|--------------|---------|
| 401 | `"Authorization header missing"` | `Authorization` header is absent from the request |
| 401 | `"Invalid or expired token"` | Token present but expired, revoked, or malformed |
| 403 | `"Cannot update another user's profile"` | Token valid but the `user_id` field in the body belongs to a different user |

The `WWW-Authenticate: Bearer` response header is included on all 401 responses.

---

## Read Endpoints

These endpoints do not require authentication. The frontend may also read `map_coordinates` directly from Supabase using the anon key — see [Notes for Frontend Implementation](#notes-for-frontend-implementation).

---

### GET /map/{user_id}

Returns the precomputed People Map for the given user.

**Path parameter:** `user_id` — UUID of the center user

**No request body. No authentication required.**

**Success response (200):**
```json
{
  "user_id": "3561ceb0-d433-437d-8a4f-08da002dff50",
  "computed_at": "2026-02-23T19:00:00+00:00",
  "coordinates": [
    {
      "user_id": "3561ceb0-d433-437d-8a4f-08da002dff50",
      "x": 0.0,
      "y": 0.0,
      "tier": 1,
      "display_name": "Alex Rivera"
    },
    {
      "user_id": "af17902c-723d-4a32-a5a1-93d9fb7777ee",
      "x": 12.34,
      "y": -5.67,
      "tier": 2,
      "display_name": "Skyler Thompson"
    }
  ]
}
```

**Response field descriptions:**

| Field | Type | Description |
|-------|------|-------------|
| `user_id` | string (UUID) | The center user — echoes the path parameter |
| `computed_at` | ISO 8601 timestamp | When this coordinate set was last computed |
| `coordinates` | array | All users on the map, including the center user |
| `coordinates[].user_id` | string (UUID) | The user this coordinate belongs to |
| `coordinates[].x` | float | Horizontal position (center user is always 0.0) |
| `coordinates[].y` | float | Vertical position (center user is always 0.0) |
| `coordinates[].tier` | integer | 1 = closest 5, 2 = next 10, 3 = outer ring |
| `coordinates[].display_name` | string | The user's display name (empty string if not set) |

**Notes:**
- The center user always appears in `coordinates` at `x: 0.0, y: 0.0` with `tier: 1`
- Coordinates are updated daily at 19:00 in the center user's local timezone via batch scheduler
- `computed_at` is sourced from the `map_coordinates` table row, not the current time

**Error responses:**

| Code | Body | When |
|------|------|------|
| 404 | `{"detail": "Map not yet computed for this user"}` | No precomputed map exists yet for this `user_id` — run `POST /map/trigger/{user_id}` first |

---

### POST /map/trigger/{user_id}

Manually triggers the full pipeline recomputation for a single user and returns the freshly computed coordinates immediately. Used for testing and demos.

**Path parameter:** `user_id` — UUID of the user to recompute

**No request body. No authentication required.**

**Success response (200):** Same shape as `GET /map/{user_id}`.

**Error responses:**

| Code | Body | When |
|------|------|------|
| 422 | `{"detail": "Pipeline failed: N=<n> users is below the minimum of 10 required for t-SNE. Seed more users."}` | Fewer than 10 users exist in `user_profiles` (t-SNE minimum) |
| 422 | `{"detail": "Pipeline failed: ..."}` | Any other `ValueError` raised by the pipeline (e.g. user not found) |

---

## Write Endpoints

All write endpoints require `Authorization: Bearer <supabase_jwt>` header. The backend validates the JWT by calling `supabase.auth.get_user(token)` — the user ID is extracted from the validated token, not from the request body.

---

### POST /interactions/like

Records a "like" interaction from the authenticated user to a target user. Atomically increments `likes_count` in the `interactions` table using a Postgres RPC (`increment_interaction`).

**Request body:**
```json
{
  "target_user_id": "af17902c-723d-4a32-a5a1-93d9fb7777ee"
}
```

**Request fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `target_user_id` | string (UUID) | Yes | UUID of the user being liked |

**Success response (200):**
```json
{
  "detail": "likes recorded"
}
```

**Error responses:**

| Code | Body | When |
|------|------|------|
| 400 | `{"detail": "Cannot interact with yourself"}` | `target_user_id` equals the authenticated user's own ID |
| 401 | `{"detail": "Authorization header missing"}` | No `Authorization` header |
| 401 | `{"detail": "Invalid or expired token"}` | Token present but invalid or expired |

---

### POST /interactions/comment

Records a "comment" interaction. Atomically increments `comments_count` in the `interactions` table.

**Request body:**
```json
{
  "target_user_id": "af17902c-723d-4a32-a5a1-93d9fb7777ee"
}
```

**Success response (200):**
```json
{
  "detail": "comments recorded"
}
```

**Error responses:** Same as `POST /interactions/like`.

---

### POST /interactions/dm

Records a direct message interaction. Atomically increments `dm_count` in the `interactions` table.

**Request body:**
```json
{
  "target_user_id": "af17902c-723d-4a32-a5a1-93d9fb7777ee"
}
```

**Success response (200):**
```json
{
  "detail": "dms recorded"
}
```

**Error responses:** Same as `POST /interactions/like`.

---

### PUT /profile

Creates or updates the authenticated user's profile in `user_profiles`. All fields are optional — only provided fields are written (existing fields not in the request body are preserved, because the backend builds the upsert payload from non-null fields only).

The `user_id` is always taken from the JWT — the backend sets it from the validated token. If `user_id` is included in the request body, it must match the authenticated user's ID or the request will be rejected with 403.

**Request body (all fields optional):**
```json
{
  "display_name": "Alex Rivera",
  "interests": ["hiking", "photography"],
  "location_city": "Denver",
  "location_state": "CO",
  "age": 28,
  "languages": ["English", "Spanish"],
  "field_of_study": "Environmental Science",
  "industry": "Outdoor Recreation",
  "education_level": "Bachelor's",
  "timezone": "America/Denver"
}
```

**Field types:**

| Field | Type | Notes |
|-------|------|-------|
| `display_name` | string | Public display name shown on the People Map |
| `interests` | string[] | Array of interest tags (e.g. `["hiking", "photography"]`) |
| `location_city` | string | City name |
| `location_state` | string | State or region code (empty string for international users) |
| `age` | integer | Age in years |
| `languages` | string[] | Languages spoken (e.g. `["English", "Spanish"]`) |
| `field_of_study` | string | Academic discipline |
| `industry` | string | Professional industry |
| `education_level` | string | Highest degree (e.g. `"bachelors"`, `"masters"`, `"phd"`) |
| `timezone` | string | IANA timezone string (e.g. `"America/New_York"`) — controls when the daily map recomputation fires for this user |

**Success response (200):**
```json
{
  "detail": "Profile updated"
}
```

**Error responses:**

| Code | Body | When |
|------|------|------|
| 401 | `{"detail": "Authorization header missing"}` | No `Authorization` header |
| 401 | `{"detail": "Invalid or expired token"}` | Token present but invalid or expired |
| 403 | `{"detail": "Cannot update another user's profile"}` | `user_id` in request body does not match authenticated user's ID |

---

## General Error Shape

All error responses follow FastAPI's default format:
```json
{
  "detail": "Error message string"
}
```

Validation errors (e.g. missing required field, wrong type) return HTTP 422 with a structured `detail` array from FastAPI/Pydantic.

---

## Notes for Frontend Implementation

1. **Direct Supabase reads:** Frontend should read `map_coordinates` and `user_profiles` directly from Supabase (not via this API) for display purposes. The Supabase anon key is safe for reads — RLS allows it. Example:
   ```javascript
   const { data } = await supabase
     .from('map_coordinates')
     .select('other_user_id, x, y, tier')
     .eq('center_user_id', userId)
     .eq('is_current', true)
   ```

2. **Write pattern:** All interaction events and profile updates MUST go through this API (not direct Supabase writes). Supabase RLS blocks anon key writes to `interactions` and `user_profiles`.

3. **Map freshness:** Coordinates are batch-updated at 19:00 in each user's timezone. After calling `POST /interactions/*`, the map does not update immediately — the interaction will be reflected at the next scheduled run or on manual trigger via `POST /map/trigger/{user_id}`.

4. **Canonical pair ordering:** The backend enforces canonical pair ordering internally (`user_id_a < user_id_b`). The frontend does not need to worry about this — just send `target_user_id` in the request body and the backend handles ordering before writing to the database.

5. **Single-worker constraint:** The backend must run as a single uvicorn worker (`uvicorn app:app --reload`). Multi-worker deployments cause the APScheduler to fire jobs multiple times per user.

6. **Profile upsert vs update:** `PUT /profile` is an upsert — it creates the profile row if it does not exist yet, or updates it if it does. Only the fields included in the request body are written; omitted fields retain their existing database values.
