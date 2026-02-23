# Phase 5 Context: Demo and Docs

*Derived from PROJECT.md, REQUIREMENTS.md, ROADMAP.md, CLAUDE.md, and existing backend code on 2026-02-22*

## Design Decisions

### scripts/test_map.py (DEMO-01, DEMO-03, DEMO-04)
- Standalone Python script — no external test framework
- Connects to real Supabase using `.env` credentials
- Workflow: reads seed users → runs full pipeline → plots 2D scatter with matplotlib
- Dots labeled by `display_name`
- Color-coded by tier: 3 colors (Tier 1 / Tier 2 / Tier 3)
- Must demonstrate sensitivity: seeding higher interaction count between two users makes them visibly closer on the scatter plot

### scripts/people_map_demo.ipynb (DEMO-02, DEMO-03, DEMO-04)
- Jupyter notebook with per-stage explanations and inline matplotlib plots
- One cell group per pipeline stage: data fetch → interaction scoring → combined distance → t-SNE → origin translation → visualization
- Runs end-to-end with a single "Run All Cells" command
- Also connects to real Supabase via `.env`
- Demonstrates sensitivity: same as test_map.py but interactively

### docs/API_CONTRACT.md (SPEC-01)
Complete frontend reference for:
- `GET /map/{user_id}` — full response JSON shape with field types
- `POST /map/trigger/{user_id}` — request/response
- `POST /interactions/like`, `/comment`, `/dm` — request body, auth header, response, error shapes (401, 403)
- `PUT /profile` — request body (all profile fields), auth header, response, 401/403 errors
- Auth header format: `Authorization: Bearer <supabase_jwt>`
- General error shape
Must be detailed enough that the frontend team can implement without asking follow-up questions.

### docs/DB_SCHEMA.md (SPEC-02)
Reference-only schema doc for:
- `user_profiles` — all fields, types, constraints
- `interactions` — canonical pair ordering explained, all count fields
- `map_coordinates` — is_current versioning explained, index note
Frontend does NOT write directly to any table. This is for reference only.

### .env requirement
Both scripts use `.env` files. A `.env.example` must exist in both `frontend/` and `backend/` (or at project root) with all required keys documented. Scripts should fail clearly if `.env` is missing rather than crashing with cryptic errors.

### No pytest suite
Full production test suite is out of scope. The demo scripts ARE the validation. If test_map.py runs and shows the correct scatter plot, the phase is complete.

### Sensitivity demonstration
The notebooks/scripts must show algorithm sensitivity — increasing interaction count between users A and B must produce a visibly closer position for those two users. This can be done by:
1. Running pipeline with current seed data
2. Manually bumping interaction counts for two specific users
3. Re-running and comparing plots side by side (or showing before/after in the notebook)

## Out of Scope for Phase 5
- Frontend UI rendering the People Map
- Production deployment
- pytest test suite
- Animation / Procrustes alignment
- Performance benchmarks
