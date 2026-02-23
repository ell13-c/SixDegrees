# Phase 3 Context: Pipeline Integration

*Derived from PROJECT.md, REQUIREMENTS.md, ROADMAP.md, CLAUDE.md, and existing backend code on 2026-02-22*

## Design Decisions

### New files in map_pipeline/
Phase 3 adds the DB-connected layer to the Phase 2 computation modules:
- `data_fetcher.py` — reads user_profiles + interactions from Supabase
- `coord_writer.py` — writes computed coordinates to map_coordinates

### data_fetcher.py (DATA-01, DATA-02, DATA-03)
- Uses the Supabase Python client from `config/supabase.py` (service role key, bypasses RLS)
- Reads all rows from `user_profiles` and `interactions`
- Returns structured Python objects suitable for passing to Phase 2 algorithm modules
- No anon key usage — service role key is mandatory

### coord_writer.py (STORE-01, STORE-02, STORE-03)
Write pattern (always in this order):
1. Mark all existing rows for this `center_user_id` where `is_current=true` → set `is_current=false`
2. Insert new rows with `is_current=true`
3. Do NOT delete old rows — they're kept for future animation delta computation

Every write includes the requesting user themselves at (0.0, 0.0) plus all other users in the coordinate set.

### Pipeline orchestrator
A top-level function (e.g. in `map_pipeline/__init__.py` or `pipeline.py`) chains:
1. `data_fetcher.fetch_all()` → profiles + interactions
2. Phase 2 algorithm modules (interaction scoring → combined distance → t-SNE → origin translation)
3. `coord_writer.write_coordinates(center_user_id, results)`

This is the function the Phase 4 scheduler and trigger endpoint will call.

### Column names
User profile fields in Supabase: `location_city`, `location_state` (not `city`/`state`). Must match exactly — this was corrected in Phase 1.

### Canonical pair ordering
When reading interactions, the pair order `user_id_a < user_id_b` is enforced in the DB. When looking up interaction data for a given (i, j) pair, code must handle both orderings (query by either direction).

### No FK from user_profiles to auth.users
The seed users don't exist in auth.users. `data_fetcher.py` reads directly from `user_profiles` — no auth.users join needed.

### N < 10 guard
The pipeline must propagate the t-SNE error clearly if fewer than 10 users are in the DB. Fail fast with a descriptive error before calling t-SNE.

## Out of Scope for Phase 3
- API endpoints (Phase 4)
- Scheduler (Phase 4)
- JWT validation
- Modifying existing matching/ routes
