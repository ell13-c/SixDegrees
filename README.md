# SixDegrees

**Live app: https://six-degrees-omega.vercel.app**

A social networking app built around a 2D People Map. Users are plotted in space based on profile similarity and interaction history. The closer two people are on the map, the more similar they are. Matching uses UMAP dimensionality reduction over a combined profile distance + interaction distance matrix.

## Try It Out

Visit the live app at **https://six-degrees-omega.vercel.app**

> **Note:** The People Map may take 1-2 minutes to load on first use. This is due to Render's free-tier cold start limit (the backend spins down after inactivity), not the code itself. Run the app locally for seamless performance.

Want to explore without signing up? Use the demo account:

| Field | Value |
|-------|-------|
| Email | `aaaa@gmail.com` |
| Password | `AAAAaaaa1234!` |

The demo account is a pre-seeded user with friends, posts, and a People Map already built. Feel free to poke around: like posts, check the map, or use matching.

---

## How the People Map Works

The People Map places every user at a point in 2D space. The rule is simple: **the closer two people are on the map, the more similar they are** in interests, background, and how much they interact. This section explains exactly how that position is computed.

---

### Why a Global Coordinate System?

Computing similarity between two users requires comparing their profiles and interactions. That is an O(N²) operation (every pair). Rather than doing this on-demand each time someone opens the map (which would be slow and redundant), we run the full pipeline once per day for **all N users simultaneously**, producing a single shared coordinate space. Every user's (x, y) position is stored in `public.user_positions`.

When you open the map, the backend reads your position and those of your connections from the database. No recomputation needed. This is orders of magnitude faster than per-user, per-request matching.

---

### Step 1: Profile Distance Matrix

For every pair of users (i, j), we compute a **profile similarity score** from 0 to 1 across six fields:

| Field | Method | Weight |
|-------|--------|--------|
| Interests + Bio | **AI embedding similarity** (see below) | 0.40 |
| Location | Tiered: same city → 1.0 / same state → 0.5 / different → 0.0 | 0.20 |
| Languages | Jaccard similarity on language sets | 0.15 |
| Education (field of study) | Tiered categorical: exact match → 1.0 / same broad category → 0.5 | 0.10 |
| Industry | Tiered categorical: exact match → 1.0 / same broad category → 0.5 | 0.10 |
| Age | Inverse distance: 1 / (1 + \|age_a − age_b\|) | 0.05 |

#### AI Embedding Model (the core of interest matching)

Interests and bio are scored using a **pre-trained sentence-transformer model** (`all-MiniLM-L6-v2`, 384 dimensions). Each user's interests and bio are concatenated into a single text string and encoded into a 384-dimensional vector. Similarity between two users is then the **cosine similarity** between their vectors.

This means the system understands *semantic meaning*, not just exact keyword overlap. "Hiking" and "trail running" score high similarity even though they share no words. "Machine learning" and "AI" are treated as near-synonyms. Plain keyword matching (Jaccard) cannot do this. The embedding model is what makes interest matching intelligent.

The weighted sum across all fields gives a scalar **profile similarity** ∈ [0, 1]. We invert it to get **profile distance**:

```
profile_dist(i, j) = 1 − profile_similarity(i, j)
```

This produces an N×N symmetric matrix with zeros on the diagonal.

---

### Step 2: Interaction Distance Matrix

For every pair (i, j), we look up their interaction history:

```
raw_score(i, j) = likes_count × 0.5 + comments_count × 0.5
```

We normalize across all pairs by dividing by the maximum raw score observed, bringing every value into [0, 1]. More interaction means smaller distance:

```
interaction_dist(i, j) = 1 − (raw_score(i, j) / max_raw_score)
```

Users who have never interacted get `interaction_dist = 1.0` (maximum distance).

---

### Step 3: Combined Distance Matrix

The two N×N matrices are blended with fixed weights (α = 0.6, β = 0.4):

```
combined_dist(i, j) = 0.6 × profile_dist(i, j) + 0.4 × interaction_dist(i, j)
```

The result is clipped to [0, 1] and the diagonal is forced to 0 (every user is distance 0 from themselves). This single matrix encodes the full pairwise similarity of the entire user base.

---

### Step 4: UMAP Projection to 2D

UMAP (Uniform Manifold Approximation and Projection) takes the N×N precomputed distance matrix and projects every user to a point in 2D space, preserving the neighbourhood structure: users who are close in the high-dimensional distance space end up close on the map.

Key parameters:

| Parameter | Value | Effect |
|-----------|-------|--------|
| `metric` | `"precomputed"` | Uses our distance matrix directly |
| `n_neighbors` | 15 | How many nearby users each point considers when learning the manifold |
| `min_dist` | 0.1 | How tightly points are allowed to cluster together |

The output is an N×2 array of (x, y) coordinates, one point per user, all in the same global coordinate space.

---

### Step 5: Normalisation and Write

UMAP's raw output is unanchored. The coordinate scale, translation, and orientation can differ between runs even with the same random seed. Before storing, we normalise each axis to **[0, 1]**:

```
x_norm = (x − x_min) / (x_max − x_min)
y_norm = (y − y_min) / (y_max − y_min)
```

This keeps coordinates comparable across runs. The final coordinates are upserted into `public.user_positions` (one row per user).

---

### Step 6: Ego Map (What You See)

When you open the People Map, the backend calls `build_ego_map(your_id)`:

1. Reads **all** positions from `user_positions`.
2. Fetches your social graph up to 3 degrees via `extended_friends(3)`.
3. Translates every coordinate so **you are at (0, 0)**. Everyone else's position is relative to yours.
4. Assigns a tier to each person based on their friendship distance to you (tier 1 = Inner Circle, tier 2 = 2nd Degree, tier 3 = 3rd Degree).

The frontend receives this translated, tiered list and renders it as rings around you. You never see the raw global coordinates, only positions relative to your own.

---

### Pipeline Summary

```
All N user profiles + interactions
         │
         ▼
Step 1: Profile distance matrix        N×N  O(N²)
Step 2: Interaction distance matrix    N×N  O(N²)
Step 3: Combined distance matrix       N×N  O(N²)
         │
         ▼
Step 4: UMAP projection → N×2 coordinates
         │
         ▼
Step 5: Normalise to [0,1] → upsert to user_positions
         │
         ▼
Step 6: On map open → ego map (translate + tier)   O(1) DB reads
```

The expensive O(N²) work happens once per day at UTC 00:00. Every individual map load is a cheap database read.

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Vue 3 + Vite | SPA with reactive UI components |
| Frontend routing | Vue Router | Auth-guarded client-side routing |
| Backend | FastAPI (Python) | REST API for map, matching, and profile endpoints |
| Database | Supabase (PostgreSQL) | Hosted Postgres with Auth, RLS, and RPCs |
| ORM / client | supabase-py | Backend service-role DB access |
| Data modeling | Pydantic v2 | Request/response validation and coercion |
| Dimensionality reduction | umap-learn | UMAP 2D projection of the combined distance matrix |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) | Semantic similarity for interests and bio |
| Similarity math | NumPy, scikit-learn | Distance matrix construction and normalization |
| Scheduling | APScheduler | Daily UTC 00:00 pipeline trigger |
| Testing | pytest + pytest-cov | Unit and integration tests (138 tests, all mocked) |
| API docs | pdoc | Auto-generated HTML documentation |
| Frontend hosting | Vercel | Static SPA deployment |
| Backend hosting | Render (free tier) | FastAPI server deployment |

## Deployment

**Live app:** https://six-degrees-omega.vercel.app

### Cost and Performance Notes

The backend runs on Render's **free tier (512MB RAM)**. To stay within the memory limit:

- Heavy ML libraries (`umap-learn`, `sentence-transformers`) are **lazy-loaded**. They are not imported at startup, only when the pipeline actually runs.
- The map pipeline runs automatically once per day at **UTC 00:00** via APScheduler. This scheduled run recomputes positions for all users and writes them to `user_positions`. Individual map loads are always fast because they read precomputed positions from the database.

### Scheduled Pipeline (currently disabled on the live demo)

The automatic daily pipeline (`GLOBAL_COMPUTE_ENABLED`) is **turned off** on the live demo. Two reasons:

1. **Render free tier spins down** after 15 minutes of inactivity. A server that is asleep cannot run scheduled jobs reliably.
2. **Memory headroom.** The UMAP + sentence-transformer stack peaks above 512 MB on larger user sets, which can OOM-kill the free-tier instance.

When `GLOBAL_COMPUTE_ENABLED=true` is set in `backend/.env` and the server stays running, the pipeline fires every day at **UTC 00:00** and:

1. Fetches all user profiles and interaction counts from Supabase.
2. Builds an N×N combined distance matrix (profile similarity + interaction history).
3. Runs UMAP to project every user to a 2D coordinate.
4. Normalises coordinates to [0, 1] and upserts them into `public.user_positions`.
5. Logs the run (user count, duration, status) to `public.pipeline_runs`.

After each run, every user's map position updates automatically on their next map load — no manual trigger needed.

---

## Prerequisites

- Python 3.11+
- Node 18+
- A Supabase project (free tier works)

## Supabase Setup

1. Create a new Supabase project.

2. Enable the `private` schema. In the Supabase SQL editor:
   ```sql
   ALTER ROLE authenticator SET search_path TO public, private;
   ```

3. Create the `private.profiles` table (and related tables: `posts`, `likes`, `comments`, `friend_requests`, `reports`) in your Supabase project.

4. Run `backend/sql/02_schema.sql` in the SQL editor. This creates:
   - `public.profiles`: writable view over `private.profiles`
   - `public.interactions`: interaction counters
   - `public.user_positions`: UMAP map coordinates
   - `public.pipeline_runs`: pipeline diagnostics log

5. Create a Storage bucket named **`post-images`** with public read access:
   Dashboard → Storage → New bucket → Name: `post-images` → Public: on

6. Note your project's **URL**, **anon/public key**, and **service-role key** from:
   Dashboard → Settings → API

## Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env`:

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_KEY` | Service-role key (full DB access, keep secret) |
| `ALLOWED_ORIGINS` | Comma-separated frontend URLs for CORS. Defaults to `http://localhost:5173`. |
| `GLOBAL_COMPUTE_ENABLED` | Set to `true` to enable the scheduled UMAP pipeline. Default: `false`. |

Start the server:

```bash
# IMPORTANT: single worker only. APScheduler fires N times with N workers.
uvicorn app:app --reload
```

## Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env
```

Edit `frontend/.env`:

| Variable | Description |
|----------|-------------|
| `VITE_SUPABASE_URL` | Your Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | Anon/public key (safe to expose in frontend) |
| `VITE_API_URL` | FastAPI backend URL (e.g., `http://localhost:8000`) |

Start the dev server:

```bash
npm run dev   # http://localhost:5173
```

## Running Tests

```bash
cd backend
source venv/bin/activate
python -m pytest -q                          # all tests
python -m pytest -q tests/map/              # map pipeline only
python -m pytest --cov=. --cov-report=term-missing  # with coverage
```

## Friends and Degrees System

### Nicknames

Every user picks a unique nickname during onboarding. Nicknames are the primary way to find and connect with other people. Friend requests are sent by nickname, not by searching a name or email.

### How Friendship Works

Friendship on SixDegrees is **mutual and opt-in**:

1. User A sends a friend request to User B using B's nickname.
2. User B receives the request on their Home feed and chooses to **Accept** or **Reject** it.
3. Only after B accepts does the connection become active. Both users are then friends with each other simultaneously. There is no one-sided following; friendship is always a two-way bond.

If User A changes their mind before B responds, they can rescind the request. If B rejects it, no connection is created.

### Degrees of Separation (Tiers)

Connections are organised into tiers based on social distance:

| Tier | Label | Who it includes |
|------|-------|-----------------|
| 1 | **Inner Circle** | Your direct, mutual friends |
| 2 | **Extended Network** | Friends-of-friends, people connected to your Tier 1 friends |
| 3 | **Wider Community** | Two hops away, friends of your Tier 2 connections |

This mirrors the classic "six degrees of separation" idea: the further the tier, the more indirect the connection.

### What Tiers Affect

- **Posts** are tagged with a visibility tier (1, 2, or 3) when created. A Tier 1 post is only visible to your Inner Circle; a Tier 3 post reaches the Wider Community.
- **The People Map** plots all users in 2D space. Users closer to you on the map are more similar to you based on profile and interaction history, regardless of tier.
- **Matching** surfaces the most compatible users from across all tiers.

## Scheduled Jobs

**People Map recalculation:** The UMAP pipeline runs automatically every day at **UTC 00:00**, recomputing positions for all users. This requires `GLOBAL_COMPUTE_ENABLED=true` in `backend/.env` and the server running in single-worker mode. Results are written to `public.user_positions` and become visible immediately on the next map load.

## Key Constraints

**Single-worker only:** Never run `uvicorn --workers N`. APScheduler fires once per worker, causing duplicate pipeline runs. Always use `--reload`.

**Private schema architecture:** User-facing tables (`profiles`, `posts`, etc.) live in the `private` Supabase schema. The backend reads/writes profiles through a public view (`public.profiles`) with an INSTEAD OF trigger that routes writes back to `private.profiles`. Always use `sb.table("profiles")` and never bypass the view.

**Two data-flow paths:** Social features bypass FastAPI entirely. Map and matching go through FastAPI. Do not add social feature logic to the FastAPI backend.

## Project Structure

```
backend/
  app.py              # FastAPI app, CORS, lifespan (APScheduler)
  config/settings.py  # All config: Supabase client, weights, UMAP params
  routes/             # HTTP layer only, no business logic
  models/user.py      # UserProfile Pydantic model
  services/map/       # UMAP pipeline: fetcher → distance → projector → writer
  services/matching/  # Scoring, similarity, embedding (all-MiniLM-L6-v2)
  scripts/seed.py     # Seed 100 deterministic fake profiles
  sql/02_schema.sql   # Contributor DB setup script
  tests/              # 138 tests, all mocked (no live DB calls)

frontend/
  src/views/          # Page components (Home, Profile, PeopleMap, Match, etc.)
  src/components/     # Shared components (Post, CreatePost)
  src/router/         # Vue Router with auth guards
  src/lib/supabase.js # Supabase client init

demo/
  sixdegrees_demo.ipynb            # Eleanor/Brita two-case algorithm demo
  embedding_similarity_demo.ipynb  # Live embedding similarity demo

docs/
  api/                             # Auto-generated HTML API docs (pdoc)
```

## Architecture Overview

### High-Level Component Diagram

```
+-------------------+          +-----------------------+
|   Vue 3 Frontend  |          |  Supabase (Postgres)  |
|   (Vercel)        |          |  (hosted DB + Auth)   |
|                   |          |                       |
|  Social features  +--------->+  RPCs (posts, likes,  |
|  (posts, friends) |  direct  |  friends, comments)   |
|                   |  RPC     |                       |
|  Map + Matching   +----+     |  public.profiles      |
|                   |    |     |  public.interactions  |
+-------------------+    |     |  public.user_positions|
                         |     +-----------------------+
                         |                ^
                         v                |
              +--------------------+      |
              |  FastAPI Backend   +------+
              |  (Render)          |  service-role key
              |                    |
              |  GET /profile      |
              |  PUT /profile      |
              |  GET /map/:id      |
              |  POST /map/trigger |
              |  GET /match        |
              |  POST /interactions|
              +--------------------+
```

### Pipeline Sequence Diagram

```
Scheduler (00:00 UTC daily)
         |
         v
   fetcher.fetch()
         |
         | PipelineInput (N profiles + interactions)
         v
   distance.build_combined_distance()
         |
         | N x N distance matrix
         v
   projector.project()          <-- UMAP (metric="precomputed")
         |
         | (N, 2) raw coords
         v
   validation.validate_output()
         |
         v
   writer.write()               <-- normalise to [0,1], upsert user_positions
         |
         v
   diagnostics.record_run()     <-- log to pipeline_runs
```

### Database Schema

```
private schema (owned by frontend/DB team)
  private.profiles        -- canonical user rows
  private.posts           -- post content
  private.likes           -- post likes
  private.comments        -- post comments

public schema (managed by backend)
  public.profiles         -- writable VIEW over private.profiles
  public.interactions     -- (user_id_a, user_id_b, likes_count, comments_count)
  public.user_positions   -- (user_id, x, y, computed_at)  UMAP output
  public.pipeline_runs    -- diagnostics log per pipeline execution
```

## Usage Example

### Try the Live App

Visit **https://six-degrees-omega.vercel.app**, sign up with any email, complete onboarding, and click "People Map" to see your position relative to other users.

### Run Locally (Example Walkthrough)

After completing backend and frontend setup:

1. Start the backend:

```bash
cd backend
source venv/bin/activate
uvicorn app:app --reload
# Server running at http://localhost:8000
```

2. Start the frontend:

```bash
cd frontend
npm run dev
# Dev server at http://localhost:5173
```

3. Open `http://localhost:5173` in your browser, create an account, and finish onboarding.

4. Seed the database with 100 example users so the map has something to compute:

```bash
cd backend
source venv/bin/activate
python scripts/seed.py
```

5. Trigger the pipeline manually via the API (replace `<TOKEN>` with a valid Supabase JWT and `<USER_ID>` with your UUID):

```bash
curl -X POST http://localhost:8000/map/trigger/<USER_ID> \
  -H "Authorization: Bearer <TOKEN>"
# {"status":"ok","computed_at":"2026-04-27T00:00:00+00:00"}
```

6. Fetch your top matches:

```bash
curl http://localhost:8000/match \
  -H "Authorization: Bearer <TOKEN>"
# {"matches":[{"user_id":"...","nickname":"eleanor","similarity_score":0.8142},...]}
```

7. Open the People Map in the UI to see your position visualised alongside your connections.

## Team Members and Contributions

| Member | Role | Contributions |
|--------|------|---------------|
| HyangMok Baek | Backend and Algorithm | FastAPI application, UMAP pipeline, matching algorithm (sentence-transformer embeddings, similarity scoring), full test suite (138 tests) |
| Eleanor Colvin | Frontend and UI Design | Vue 3 SPA views, Vue Router with auth guards, Supabase JS client integration, post/like/comment/friend UI components, filter UI |
| Amanda Hsu | Frontend and Map Visualization | People Map component, closeness map rendering, map tier visualization, frontend map interactions |
| Joshua Kunnappilly | Backend and Database | Supabase schema design, private schema architecture, PostgreSQL RPCs and triggers, database migrations |

## Retrospective

**What went well:**

The split between a backend-owned REST API and a frontend that calls Supabase RPCs directly turned out to be a clean boundary. Each team member could work independently without stepping on the other's code. The pipeline architecture (one stage per module, all wired through contracts) made it easy to test each stage in isolation and to swap or extend any step without touching the others.

Using a pre-trained sentence-transformer model for interest similarity was a good decision early on. It gave the matching algorithm semantic understanding of interests (so "hiking" and "trail running" score close together) without writing any NLP code from scratch.

**What we would do differently:**

The Render free-tier cold start is a real usability problem. A user who opens the app after a period of inactivity waits over a minute for the backend to wake up before they can do anything. We would use a paid tier or a lightweight keep-alive ping in production.

The daily UMAP pipeline also ends up disabled on the live demo because the 512 MB memory cap on Render's free tier is not enough for the full `umap-learn` + `sentence-transformers` stack on a non-trivial user set. A production deployment would need either more memory or an offline worker process separate from the web server.

On the frontend side, the first version of the People Map filter was more complex than it needed to be. It was later simplified (see the filter expansion PR), but we would build that simplicity in from the start.

## API Documentation

Auto-generated HTML documentation for the backend modules is available in `docs/api/index.html`. Open it in any browser.

To regenerate after code changes:

```bash
cd backend
source venv/bin/activate
python -m pdoc \
  app config.settings models.user \
  routes.deps routes.profile routes.map routes.match routes.interactions \
  services.map.contracts services.map.fetcher services.map.distance \
  services.map.projector services.map.validation services.map.writer \
  services.map.ego services.map.pipeline services.map.scheduler \
  services.map.lock services.map.diagnostics \
  services.matching.embedder services.matching.similarity services.matching.scoring \
  --output-dir ../docs/api
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
