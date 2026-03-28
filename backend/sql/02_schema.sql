CREATE TABLE profiles (
  id            UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  nickname      TEXT UNIQUE NOT NULL,
  bio           TEXT,
  avatar_url    TEXT,
  age           INTEGER,
  city          TEXT,
  state         TEXT,
  education     TEXT,
  occupation    TEXT,
  industry      TEXT,
  interests     TEXT[],
  languages     TEXT[],
  profile_tier  INTEGER DEFAULT 6,
  is_admin      BOOLEAN DEFAULT false,
  created_at    TIMESTAMPTZ DEFAULT now(),
  updated_at    TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE interactions (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id_a           UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  user_id_b           UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  like_count          INTEGER DEFAULT 0,
  comment_count       INTEGER DEFAULT 0,
  dm_count            INTEGER DEFAULT 0,
  last_interaction_at TIMESTAMPTZ,
  UNIQUE(user_id_a, user_id_b),
  CHECK (user_id_a < user_id_b)
);

CREATE TABLE user_positions (
  user_id     UUID PRIMARY KEY REFERENCES profiles(id) ON DELETE CASCADE,
  x           FLOAT NOT NULL,
  y           FLOAT NOT NULL,
  computed_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE posts (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  content    TEXT NOT NULL,
  tier       INTEGER NOT NULL CHECK (tier BETWEEN 1 AND 3),
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE likes (
  id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  post_id UUID NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  UNIQUE(post_id, user_id)
);

CREATE TABLE comments (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  post_id    UUID NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
  user_id    UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  content    TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE friend_requests (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sender_id   UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  receiver_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  status      TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'accepted', 'rejected')),
  created_at  TIMESTAMPTZ DEFAULT now(),
  UNIQUE(sender_id, receiver_id)
);

CREATE TABLE reports (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  post_id    UUID NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
  user_id    UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(post_id, user_id)
);

CREATE TABLE pipeline_runs (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  status      TEXT NOT NULL CHECK (status IN ('success', 'failed', 'skipped')),
  user_count  INTEGER,
  edge_count  INTEGER,
  duration_ms INTEGER,
  error       TEXT,
  created_at  TIMESTAMPTZ DEFAULT now()
);
