# SixDegrees — Backend & DB Quick Reference 🗺️

**For:** DB team, Frontend team, anyone who needs to understand how everything connects.
**Last updated:** 2026-02-23

---

## 🧭 What Is This App, In One Paragraph

SixDegrees shows you a **People Map** — a 2D scatter plot where every other user is placed at some (x, y) position relative to you. You are always at the center (0, 0). The closer someone is to you on the map, the more similar your profiles are AND the more you've interacted with each other. The map is recomputed every day at 7:00 PM in your local timezone.

---

## ⚠️ The Most Important Thing To Know

**There are TWO separate profile tables.** This is the #1 source of confusion:

| Table | Who uses it | What it's for |
|---|---|---|
| `profiles` | Frontend (direct Supabase read/write) | Social features — nickname, friends list, friend requests, visibility settings |
| `user_profiles` | Backend algorithm only | People Map input — the numbers and tags the algorithm crunches |

**Right now, `ProfileSetup.vue` only writes to `profiles`.** The backend algorithm reads from `user_profiles`. That means **profile data filled in at signup does NOT reach the algorithm yet.** See [What Frontend Needs To Fix](#-what-frontend-needs-to-fix) below.

---

## 🗄️ All 7 Tables Explained

---

### 1. `profiles` — The Social Graph Table

> **Who writes it:** Frontend directly (Supabase anon key via upsert)
> **Who reads it:** Frontend

This is the table for everything social — who you're friends with, what your nickname is, who has sent you friend requests. The algorithm does NOT use this table.

| Column | Type | What it means |
|---|---|---|
| `id` | UUID | **Must equal the Supabase Auth user ID** — this is how auth and profile are linked |
| `nickname` | TEXT (unique) | Public username. Letters, numbers, underscores only (enforced by DB). |
| `friends` | UUID[] | Array of user IDs you are friends with |
| `pending_friend_requests` | UUID[] | Array of user IDs who have sent YOU a friend request (not yet accepted) |
| `rejected_friends` | UUID[] | User IDs whose requests you've declined (so they don't show up again) |
| `profile_tier` | smallint (1–6) | Which friend tier can see your profile (1 = only closest friends, 6 = everyone) |
| `is_onboarded` | boolean | `false` until the user completes profile setup. Used to redirect to `/profile-setup`. |
| `interests` | TEXT[] | Tags like `["hiking", "coding"]` |
| `city`, `state` | TEXT | Location (free text) |
| `age` | smallint | Age in years |
| `education` | TEXT | School name (e.g. "University of Toronto") |
| `occupation` | TEXT | Job title |
| `industry` | TEXT | Industry name |
| `languages` | TEXT[] | Languages spoken |

**8 rows live today.** RLS is enabled. Frontend can read and write using the anon key.

---

### 2. `user_profiles` — The Algorithm Input Table

> **Who writes it:** Backend only, via `PUT /profile` endpoint
> **Who reads it:** Backend algorithm

This is what the People Map algorithm actually uses. It has slightly different column names than `profiles` (e.g. `location_city` not `city`). **Do not confuse the two.**

| Column | Type | What it means |
|---|---|---|
| `user_id` | UUID | Primary key. Same as Supabase Auth user ID. |
| `display_name` | TEXT | Name shown on the map |
| `interests` | TEXT[] | Interest tags — **35% weight in similarity score** |
| `location_city` | TEXT | ⚠️ Column is `location_city`, NOT `city` |
| `location_state` | TEXT | ⚠️ Column is `location_state`, NOT `state` |
| `age` | INTEGER | **5% weight** |
| `languages` | TEXT[] | **15% weight** |
| `field_of_study` | TEXT | e.g. `"Computer Science"` — **10% weight** |
| `industry` | TEXT | e.g. `"Healthcare"` — **10% weight** |
| `education_level` | TEXT | `"bachelors"` / `"masters"` / `"phd"` / `"highschool"` — **5% weight** |
| `timezone` | TEXT | IANA timezone string, e.g. `"America/New_York"` — **controls when the daily map update fires for this user** |
| `updated_at` | TIMESTAMPTZ | Auto-set to now() on every update |

**20 rows live today** (seed data). RLS enabled. Frontend uses anon key to **read** — but must use the backend API (`PUT /profile`) to **write**.

---

### 3. `interactions` — How Much Two People Have Interacted

> **Who writes it:** Backend only, via `/interactions/like` and `/interactions/comment` endpoints
> **Who reads it:** Backend algorithm

Each row represents **a pair of users** and counts every interaction between them. There is exactly **one row per pair** — no duplicates.

| Column | Type | What it means |
|---|---|---|
| `user_id_a` | UUID | Always the lexicographically **smaller** UUID of the pair |
| `user_id_b` | UUID | Always the **larger** UUID of the pair |
| `likes_count` | INTEGER | Total likes between this pair (bidirectional — A→B and B→A both count here) |
| `comments_count` | INTEGER | Total comments between this pair |
| `last_updated` | TIMESTAMPTZ | When the last interaction happened |

**36 rows live today** (seed data).

> 🔑 **Canonical pair ordering:** The backend always stores pairs so that `user_id_a < user_id_b` (alphabetical UUID comparison). A DB `CHECK` constraint enforces this. Frontend doesn't need to think about this — just send `target_user_id` to the API and the backend sorts it out.

> ⚠️ **`dm_count` is missing from the DB.** The API docs mention a `POST /interactions/dm` endpoint and a `dm_count` column — but that column does not exist in the live DB yet. The DB team needs to add it: `ALTER TABLE interactions ADD COLUMN dm_count INTEGER DEFAULT 0;`

---

### 4. `map_coordinates` — The Precomputed People Map

> **Who writes it:** Backend algorithm pipeline (never the frontend)
> **Who reads it:** Frontend directly from Supabase

This is the output of the algorithm. Every time the pipeline runs for a user, it writes a fresh set of rows here.

| Column | Type | What it means |
|---|---|---|
| `id` | UUID | Row ID (auto-generated) |
| `center_user_id` | UUID | Whose map this is (the user at (0, 0)) |
| `other_user_id` | UUID | A user appearing on that map |
| `x`, `y` | FLOAT | 2D position. Center user is always `(0.0, 0.0)`. |
| `tier` | smallint (1/2/3) | **1** = 5 closest people, **2** = next 10, **3** = outer ring |
| `computed_at` | TIMESTAMPTZ | When this batch ran |
| `is_current` | BOOLEAN | `true` = today's map, `false` = historical (kept for future animation) |

**762 rows live today.** To read the current map for a user:
```javascript
const { data } = await supabase
  .from('map_coordinates')
  .select('other_user_id, x, y, tier')
  .eq('center_user_id', userId)
  .eq('is_current', true)
```

> 📝 Old rows are **never deleted** — they're kept with `is_current = false` so we can animate smooth transitions in a future update.

---

### 5. `posts`, `likes`, `comments` — The Feed Tables

> **Status:** Tables exist in the DB, but **no rows yet and frontend is not wired up.**

These tables exist and have the right structure (with RLS), but the home feed currently shows hardcoded mock data. Wiring these up is a future milestone — nothing to do here yet.

---

## 🔧 How The Algorithm Pipeline Works

Here is the full flow from raw data to map coordinates, step by step:

```
user_profiles table           interactions table
       │                              │
       ▼                              ▼
  data_fetcher.py  ←──────── reads both tables
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
  map_coordinates table  ◄──── frontend reads from here
```

**Profile similarity weights** (how much each field affects closeness):

| Field | Weight |
|---|---|
| interests | 35% |
| location (city + state) | 20% |
| languages | 15% |
| field_of_study | 10% |
| industry | 10% |
| education_level | 5% |
| age | 5% |

**When does it run?** Every day at 7:00 PM in each user's local timezone (set by the `timezone` field in `user_profiles`). You can also manually trigger a recompute:
```
POST http://localhost:8000/map/trigger/{user_id}
```

---

## 🌐 Frontend Data Flow

Here is how data moves through the system:

```
User fills in ProfileSetup form
         │
         ├──► Direct Supabase write ──► profiles table
         │    (social features — nickname, friends, is_onboarded)
         │
         └──► PUT /profile (backend API) ──► user_profiles table
              (algorithm input — field_of_study, timezone, etc.)
              ⚠️ THIS SECOND WRITE IS NOT HAPPENING YET — see below

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

> ⚠️ **Known gap:** The existing `/match` routes do **not** have JWT validation yet. Do not expose these to real users until auth is added.

---

## 🚨 What Frontend Needs To Fix

### Problem 1: Profile data never reaches the algorithm

`ProfileSetup.vue` currently writes to `profiles` only. The backend algorithm reads from `user_profiles`. **A user who completes the profile setup will have zero effect on the People Map** because their data doesn't exist in `user_profiles`.

**Fix:** After writing to `profiles`, also call `PUT /profile` with the user's JWT:
```javascript
// After the existing supabase.from('profiles').upsert(...) call, ADD:
const { data: { session } } = await supabase.auth.getSession()

await axios.put('http://localhost:8000/profile', {
  display_name: form.value.nickname,       // or whatever name field you have
  location_city: form.value.city,          // ⚠️ must be location_city, not city
  location_state: form.value.state,        // ⚠️ must be location_state, not state
  age: parseInt(form.value.age),
  interests: interestsArray,
  languages: languagesArray,
  industry: form.value.industry,
  // field_of_study, education_level, timezone — see Problem 2
}, {
  headers: { Authorization: `Bearer ${session.access_token}` }
})
```

### Problem 2: Missing fields in ProfileSetup form

The current ProfileSetup form collects `education` (free text school name) but the algorithm needs two separate fields — **`field_of_study`** (e.g. "Computer Science") and **`education_level`** (e.g. "bachelors" / "masters" / "phd"). It also collects nothing about **`timezone`**.

**Fields to add to the form:**

| Field to add | What to collect | Where it goes |
|---|---|---|
| `field_of_study` | Dropdown or free text (e.g. "Computer Science", "Biology") | `user_profiles` only |
| `education_level` | Dropdown: bachelors / masters / phd / highschool | `user_profiles` only |
| `timezone` | Auto-detect from browser: `Intl.DateTimeFormat().resolvedOptions().timeZone` | `user_profiles` only |

`timezone` can be auto-detected — no user input needed:
```javascript
const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone // e.g. "America/Toronto"
```

### Problem 3: Column name mismatch

`profiles` table uses `city` and `state`. `user_profiles` table uses `location_city` and `location_state`. When calling `PUT /profile`, make sure to use the right names.

### Problem 4: handleLogout() is defined inside loadPosts()

In `Home.vue`, `handleLogout` is defined inside the `loadPosts` function. This means the logout button crashes the app because `handleLogout` is out of scope when the button calls it. Move `handleLogout` to the top level of the `<script setup>` block.

---

## 🔒 Write Rules — What Goes Where

This is a hard rule. **Frontend must never write directly to these tables:**

| Table | Frontend READ | Frontend WRITE | How frontend writes |
|---|---|---|---|
| `profiles` | ✅ Direct Supabase | ✅ Direct Supabase | `supabase.from('profiles').upsert(...)` |
| `user_profiles` | ✅ Direct Supabase | ❌ Blocked by RLS | `PUT /profile` (backend API) |
| `interactions` | ✅ Direct Supabase | ❌ Blocked by RLS | `POST /interactions/like` or `/comment` |
| `map_coordinates` | ✅ Direct Supabase | ❌ Pipeline only | No frontend write ever |
| `posts` | ✅ Direct Supabase | 🔜 Not wired yet | TBD |

---

## 🗂️ What The DB Team Needs To Do

1. **Add `dm_count` column to `interactions`:**
   ```sql
   ALTER TABLE interactions ADD COLUMN dm_count INTEGER DEFAULT 0;
   ```
   Once added, also add `"dm_count": 1` to `INTERACTION_WEIGHTS` in `backend/config/algorithm.py` — that's all that's needed for the algorithm to pick it up automatically.

2. **Verify `user_profiles` has a FK to `auth.users`** (or intentionally skip it for seed data support — currently there is no FK, which is intentional to allow demo users who don't have real auth accounts).

3. **`profiles` and `user_profiles` will eventually need to be reconciled** — right now they are separate tables with overlapping fields. This is a planned cleanup for a future milestone.

---

## 🏃 Quick Start Cheatsheet

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

> ⚠️ **Doc typo:** `docs/DB_SCHEMA.md` incorrectly lists the backend env var as `SUPABASE_SERVICE_ROLE_KEY` — the correct name is `SUPABASE_KEY`.

---

## 📚 More Detail

| Document | What's in it |
|---|---|
| `docs/DB_SCHEMA.md` | Full column definitions for all algorithm tables |
| `docs/API_CONTRACT.md` | Full API reference — all endpoints, request/response shapes, error codes |
