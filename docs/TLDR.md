# SixDegrees — Backend & DB Quick Reference

**For:** DB team, Frontend team, anyone who needs to understand how everything connects.
**Last updated:** 2026-02-25 (v1.2 migration complete)

---

## What Is This App, In One Paragraph

SixDegrees shows you a **People Map** — a 2D scatter plot where every other user is placed at some (x, y) position relative to you. You are always at the center (0, 0). The closer someone is to you on the map, the more similar your profiles are AND the more you've interacted with each other. The map is recomputed every day at 7:00 PM in your local timezone.

---

## The Profile Table

Since v1.2 there is one canonical profile table: **`profiles`**. This table is used by both the frontend (direct Supabase writes) and the backend algorithm.

The old `user_profiles` table was the previous algorithm input table. It has been **dropped in v1.2** — do not reference it in new code.

---

## All Active Tables Explained

---

### 1. `profiles` — The Canonical Profile Table

> **Who writes it:** Frontend (direct Supabase upsert) + Backend (`PUT /profile` endpoint)
> **Who reads it:** Frontend + Backend algorithm

This is the table for everything — profile data, social features, and algorithm input.

| Column | Type | What it means |
|---|---|---|
| `id` | UUID | **Must equal the Supabase Auth user ID** — this is how auth and profile are linked |
| `nickname` | TEXT (unique) | Public username. Letters, numbers, underscores only (enforced by DB). |
| `interests` | TEXT[] | Tags like `["hiking", "coding"]` — **40% weight in similarity score** |
| `city` | TEXT | City name |
| `state` | TEXT | State or region code |
| `age` | SMALLINT | Age in years — **5% weight** |
| `languages` | TEXT[] | Languages spoken — **15% weight** |
| `education` | TEXT | Academic discipline (e.g. "Computer Science") — **10% weight** |
| `occupation` | TEXT | Job title (nullable) |
| `industry` | TEXT | Industry name — **10% weight** |
| `timezone` | TEXT | IANA timezone string, e.g. `"America/New_York"` — **controls when the daily map update fires for this user** |
| `is_onboarded` | BOOLEAN | `false` until the user completes profile setup. Used to redirect to `/profile-setup`. |
| `profile_tier` | SMALLINT (1–6) | Which friend tier can see your profile (1 = only closest friends, 6 = everyone) |
| `friends` | UUID[] | Array of user IDs you are friends with |
| `pending_friend_requests` | UUID[] | Array of user IDs who have sent YOU a friend request (not yet accepted) |
| `rejected_friends` | UUID[] | User IDs whose requests you've declined (so they don't show up again) |

**RLS is enabled.** Frontend can read and write using the anon key. Backend uses service role key.

---

### 2. `interactions` — How Much Two People Have Interacted

> **Who writes it:** Backend only, via `/interactions/like` and `/interactions/comment` endpoints
> **Who reads it:** Backend algorithm

Each row represents **a pair of users** and counts every interaction between them. There is exactly **one row per pair** — no duplicates.

| Column | Type | What it means |
|---|---|---|
| `user_id_a` | UUID | Always the lexicographically **smaller** UUID of the pair |
| `user_id_b` | UUID | Always the **larger** UUID of the pair |
| `likes_count` | INTEGER | Total likes between this pair (bidirectional — A→B and B→A both count here) |
| `comments_count` | INTEGER | Total comments between this pair |
| `dm_count` | INTEGER | Total direct messages between this pair |
| `last_updated` | TIMESTAMPTZ | When the last interaction happened |

> **Canonical pair ordering:** The backend always stores pairs so that `user_id_a < user_id_b` (alphabetical UUID comparison). A DB `CHECK` constraint enforces this. Frontend doesn't need to think about this — just send `target_user_id` to the API and the backend sorts it out.

---

### 3. `map_coordinates` — The Precomputed People Map

> **Who writes it:** Backend algorithm pipeline (never the frontend)
> **Who reads it:** Frontend directly from Supabase

This is the output of the algorithm. Every time the pipeline runs for a user, it writes a fresh set of rows here.

| Column | Type | What it means |
|---|---|---|
| `id` | UUID | Row ID (auto-generated) |
| `center_user_id` | UUID | Whose map this is (the user at (0, 0)) |
| `other_user_id` | UUID | A user appearing on that map |
| `x`, `y` | FLOAT | 2D position. Center user is always `(0.0, 0.0)`. |
| `tier` | SMALLINT (1/2/3) | **1** = 5 closest people, **2** = next 10, **3** = outer ring |
| `computed_at` | TIMESTAMPTZ | When this batch ran |
| `is_current` | BOOLEAN | `true` = today's map, `false` = historical (kept for future animation) |

To read the current map for a user:
```javascript
const { data } = await supabase
  .from('map_coordinates')
  .select('other_user_id, x, y, tier')
  .eq('center_user_id', userId)
  .eq('is_current', true)
```

> Old rows are **never deleted** — they're kept with `is_current = false` so we can animate smooth transitions in a future update.

---

### 4. `posts`, `likes`, `comments` — The Feed Tables

> **Status:** Tables exist in the DB. Frontend writes directly to Supabase. FKs point to `profiles.id`.

These tables store social feed content. RLS is enabled with appropriate policies.

---

## How The Algorithm Pipeline Works

Here is the full flow from raw data to map coordinates, step by step:

```
profiles table                interactions table
       │                              │
       ▼                              ▼
  data_fetcher.py  <──────── reads both tables
       │
       ▼
  scoring.py  ──── computes distance between every pair of users
  │
  │   Formula:  distance = 0.6 × profile_distance + 0.4 × (1 - interaction_score)
  │   (closer profiles + more interactions = smaller distance = closer on map)
  │
  ▼
  tsne_projector.py  ──── converts distances to 2D (x, y) coordinates
  │                        (needs at least 10 users to work)
  │
  ▼
  origin_translator.py  ──── shifts all coordinates so YOU are at (0, 0)
  │
  ▼
  coord_writer.py  ──── marks old rows is_current=false, inserts new rows
       │
       ▼
  map_coordinates table  <──── frontend reads from here
```

**Profile similarity weights** (how much each field affects closeness):

| Feature | Weight |
|---------|--------|
| interests | 0.40 |
| location (city + state) | 0.20 |
| languages | 0.15 |
| education | 0.10 |
| industry | 0.10 |
| age | 0.05 |

**When does it run?** Every day at 7:00 PM in each user's local timezone (set by the `timezone` field in `profiles`). You can also manually trigger a recompute:
```
POST http://localhost:8000/map/trigger/{user_id}
```

---

## Frontend Data Flow

Here is how data moves through the system:

```
User fills in ProfileSetup form
         │
         ├──► PUT /profile (backend API) ──► profiles table
         │    (algorithm input — education, timezone, etc.)
         │
         └──► Direct Supabase upsert ──► profiles table
              (social features — nickname, friends, is_onboarded)

User likes someone's post
         │
         └──► POST /interactions/like (backend API) ──► interactions table
              (frontend cannot write here directly — RLS blocks it)

User opens the People Map
         │
         └──► Direct Supabase read ──► map_coordinates table
              .eq('center_user_id', userId).eq('is_current', true)
```

### Auth flow

1. User signs up / logs in via **Supabase Auth** (frontend handles this directly — no backend involved)
2. After login, Supabase gives you a **JWT token** (stored in `localStorage` as `supabase_token`)
3. For every backend write (profile update, interactions), pass the JWT in the header:
   ```
   Authorization: Bearer <token from supabase.auth.getSession()>
   ```
4. The backend validates the token and refuses the request if it's missing or expired

---

## Write Rules — What Goes Where

| Table | Frontend READ | Frontend WRITE | How frontend writes |
|---|---|---|---|
| `profiles` | Yes | Yes | `supabase.from('profiles').upsert(...)` or `PUT /profile` |
| `interactions` | Yes | No (RLS blocks) | `POST /interactions/like` or `/comment` |
| `map_coordinates` | Yes | No (pipeline only) | No frontend write ever |
| `posts` | Yes | Yes | `supabase.from('posts').insert(...)` |
| `likes` | Yes | Yes | `supabase.from('likes').insert(...)` |
| `comments` | Yes | Yes | `supabase.from('comments').insert(...)` |

---

## Quick Start Cheatsheet

```bash
# Backend
cd backend
source venv/bin/activate
uvicorn app:app --reload          # ALWAYS single worker — never --workers 2+

# Frontend
cd frontend
npm run dev                       # http://localhost:5173

# Manually trigger map recompute for a user (for testing)
curl -X POST http://localhost:8000/map/trigger/<user_id>

# Check what endpoints exist
curl http://localhost:8000/openapi.json
```

**Environment files needed:**
- `backend/.env` — needs `SUPABASE_URL` and `SUPABASE_KEY` (service role, not anon)
- `frontend/.env` — needs `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` (anon key is fine)

---

## More Detail

| Document | What's in it |
|---|---|
| `docs/DB_SCHEMA.md` | Full column definitions for all tables |
| `docs/API_CONTRACT.md` | Full API reference — all endpoints, request/response shapes, error codes |
