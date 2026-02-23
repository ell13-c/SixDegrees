# Phase 1 Context: Database Foundation

*Derived from PROJECT.md, REQUIREMENTS.md, ROADMAP.md, and CLAUDE.md on 2026-02-22*

## Design Decisions

### Table schemas
- `user_profiles`: user_id (UUID), display_name, interests (text[]), location_city, location_state, age, languages (text[]), field_of_study, industry, education_level, timezone, updated_at
- `interactions`: user_id_a (UUID), user_id_b (UUID), likes_count (int), comments_count (int), dm_count (int), last_updated; canonical pair order enforced (user_id_a < user_id_b)
- `map_coordinates`: id, center_user_id (UUID), other_user_id (UUID), x (float), y (float), tier (1/2/3), computed_at, is_current (boolean)

### Canonical pair ordering
Interactions stored with user_id_a < user_id_b (lexicographic UUID comparison). Prevents duplicate rows. All query/write code must enforce this ordering.

### `is_current` versioning
`map_coordinates` table stores both old and new rows — old rows marked `is_current=false`, new rows `is_current=true`. Do NOT delete old rows; they support future animation delta computation.

### Index requirement
`map_coordinates` needs a composite index on `(center_user_id, is_current)` for fast API reads. This is critical for serving precomputed maps.

### Seed data quantity and diversity
At least 15 users required (t-SNE is unstable below 10). Users must have:
- Varied interests (the algorithm's heaviest-weighted field at 35%)
- Different timezones (scheduler groups by timezone)
- Mixed ages, locations, languages
- Seeded interaction counts that are non-trivial (to verify algorithm sensitivity)

### RLS / service role key
Backend must use the Supabase **service role key** (not anon key) to bypass RLS. Verify after table creation that reads work without RLS errors.

### No Supabase migrations file required
This project doesn't use a migrations directory. Tables are created directly via the Supabase dashboard SQL editor or a one-time setup script.

## Out of Scope for Phase 1
- Any algorithm code
- Any API endpoints
- Any scheduler code
- Frontend changes
