-- =============================================================================
-- SixDegrees — Backend Schema Setup
-- =============================================================================
-- Run this entire file in the Supabase SQL editor to set up the backend tables.
--
-- IMPORTANT: This script sets up ONLY the backend-owned tables. The frontend
-- team's tables (profiles, posts, likes, comments, friend_requests, reports)
-- live in the `private` schema and are managed separately via Supabase RPCs
-- and dashboard configuration.
--
-- Architecture:
--   private.profiles      — canonical profile table (not created here)
--   public.profiles       — writable VIEW over private.profiles (created here)
--   public.interactions   — backend interaction counters (created here)
--   public.user_positions — UMAP coordinates per user (created here)
--   public.pipeline_runs  — pipeline diagnostics log (created here)
--
-- Prerequisites:
--   1. Enable the `private` schema in your Supabase project
--      (Dashboard → Settings → API → Exposed schemas, or via SQL:
--       ALTER ROLE authenticator SET search_path TO public, private;)
--   2. The private.profiles table must already exist with columns:
--      id, nickname, bio, avatar_url, age, city, state, education,
--      occupation, industry, interests, languages, profile_tier,
--      is_admin, timezone, is_onboarded, created_at
-- =============================================================================


-- =============================================================================
-- 1. Public view over private.profiles (writable via INSTEAD OF trigger)
-- =============================================================================

CREATE OR REPLACE VIEW public.profiles AS
SELECT id, nickname, bio, avatar_url, age, city, state,
       education, occupation, industry, interests, languages,
       profile_tier, is_admin, timezone, is_onboarded, created_at
FROM private.profiles;

CREATE OR REPLACE FUNCTION public.profiles_view_upsert()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO private.profiles (
    id, nickname, bio, avatar_url, age, city, state,
    education, occupation, industry, interests, languages,
    profile_tier, is_admin, timezone
  )
  VALUES (
    NEW.id, NEW.nickname, NEW.bio, NEW.avatar_url, NEW.age,
    NEW.city, NEW.state, NEW.education, NEW.occupation, NEW.industry,
    NEW.interests, NEW.languages,
    COALESCE(NEW.profile_tier, 6),
    COALESCE(NEW.is_admin, false),
    COALESCE(NEW.timezone, 'UTC')
  )
  ON CONFLICT (id) DO UPDATE SET
    nickname     = EXCLUDED.nickname,
    bio          = EXCLUDED.bio,
    avatar_url   = EXCLUDED.avatar_url,
    age          = EXCLUDED.age,
    city         = EXCLUDED.city,
    state        = EXCLUDED.state,
    education    = EXCLUDED.education,
    occupation   = EXCLUDED.occupation,
    industry     = EXCLUDED.industry,
    interests    = EXCLUDED.interests,
    languages    = EXCLUDED.languages,
    profile_tier = EXCLUDED.profile_tier,
    is_admin     = EXCLUDED.is_admin,
    timezone     = EXCLUDED.timezone;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Drop existing triggers before recreating (idempotent)
DROP TRIGGER IF EXISTS profiles_view_insert_trigger ON public.profiles;
CREATE TRIGGER profiles_view_insert_trigger
INSTEAD OF INSERT ON public.profiles
FOR EACH ROW EXECUTE FUNCTION public.profiles_view_upsert();

DROP TRIGGER IF EXISTS profiles_view_update_trigger ON public.profiles;
CREATE TRIGGER profiles_view_update_trigger
INSTEAD OF UPDATE ON public.profiles
FOR EACH ROW EXECUTE FUNCTION public.profiles_view_upsert();


-- =============================================================================
-- 2. Interactions table
--    Stores aggregated interaction counts between user pairs.
--    Canonical ordering: user_id_a < user_id_b (enforced by CHECK constraint).
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.interactions (
  user_id_a      UUID NOT NULL REFERENCES private.profiles(id) ON DELETE CASCADE,
  user_id_b      UUID NOT NULL REFERENCES private.profiles(id) ON DELETE CASCADE,
  likes_count    INTEGER DEFAULT 0 CHECK (likes_count >= 0),
  comments_count INTEGER DEFAULT 0 CHECK (comments_count >= 0),
  dm_count       INTEGER DEFAULT 0 CHECK (dm_count >= 0),
  last_updated   TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (user_id_a, user_id_b),
  CHECK (user_id_a < user_id_b)   -- enforces canonical pair ordering
);

-- Index for fast lookups by either user
CREATE INDEX IF NOT EXISTS interactions_user_id_a_idx ON public.interactions(user_id_a);
CREATE INDEX IF NOT EXISTS interactions_user_id_b_idx ON public.interactions(user_id_b);

-- RLS: backend uses service-role key (bypasses RLS). Frontend reads via RPC only.
ALTER TABLE public.interactions ENABLE ROW LEVEL SECURITY;


-- =============================================================================
-- 3. User positions table
--    Stores 2D UMAP coordinates for each user (one row per user, not per pair).
--    FK references auth.users so positions persist even if profile is deleted.
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.user_positions (
  user_id     UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  x           FLOAT NOT NULL,
  y           FLOAT NOT NULL,
  computed_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE public.user_positions ENABLE ROW LEVEL SECURITY;


-- =============================================================================
-- 4. Pipeline runs table
--    Diagnostics log for each UMAP pipeline execution.
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.pipeline_runs (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  status      TEXT NOT NULL CHECK (status IN ('success', 'failed', 'skipped')),
  user_count  INTEGER,
  edge_count  INTEGER,
  duration_ms INTEGER,
  error       TEXT,
  created_at  TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE public.pipeline_runs ENABLE ROW LEVEL SECURITY;


-- =============================================================================
-- Done. Next steps:
--   - Set up Supabase Storage: create a bucket named `post-images` with
--     public read access (Dashboard → Storage → New bucket).
--   - Configure backend/.env with SUPABASE_URL and SUPABASE_KEY
--     (service-role key — this key bypasses RLS, keep it secret).
-- =============================================================================
