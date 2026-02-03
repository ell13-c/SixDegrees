# Supabase Setup for SixDegrees

Complete guide to setting up Supabase for the SixDegrees project.

## 📋 Prerequisites

- Supabase account (free at [supabase.com](https://supabase.com))
- Node.js & npm (for frontend)
- Python 3.8+ (for backend)

---

## 🚀 Quick Start

### 1. Create Supabase Project

1. Go to [https://app.supabase.com](https://app.supabase.com)
2. Click "New Project"
3. Fill in:
    - **Name**: `sixdegrees` (or your choice)
    - **Database Password**: Create a strong password (save this!)
    - **Region**: Choose closest to you
4. Click "Create new project" (takes ~2 minutes)

---

### 2. Get Your Credentials

Once project is created:

1. Go to **Settings** (gear icon) → **API**
2. Copy these values:
    - **Project URL**: `https://xxxxx.supabase.co`
    - **anon public key**: Long string starting with `eyJ...`
    - **service_role key**: Another long string (⚠️ keep secret!)

---

### 3. Set Up Environment Variables

#### Frontend:

```bash
cd frontend
cp .env.example .env
# Edit .env and paste:
# VITE_SUPABASE_URL=your-project-url
# VITE_SUPABASE_ANON_KEY=your-anon-key
```

#### Backend:

```bash
cd backend
cp .env.example .env
# Edit .env and paste:
# SUPABASE_URL=your-project-url
# SUPABASE_KEY=your-service-role-key
```

---

### 4. Run Database Schema

1. In Supabase dashboard, go to **SQL Editor**
2. Click "New Query"
3. Paste and run this SQL:

```sql
-- Enable Row Level Security on auth.users
ALTER TABLE auth.users ENABLE ROW LEVEL SECURITY;

-- Create users table (extends Supabase auth)
CREATE TABLE public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    bio TEXT,
    profile_picture_url VARCHAR(500),
    work VARCHAR(255),
    location VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    compatibility_opt_in BOOLEAN DEFAULT FALSE
);

-- Indexes for performance
CREATE INDEX idx_users_username ON public.users(username);
CREATE INDEX idx_users_email ON public.users(email);

-- Enable RLS on users table
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- RLS Policies: Users can only read/write their own data
CREATE POLICY "Users can read own profile"
    ON public.users FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON public.users FOR UPDATE
    USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile on signup"
    ON public.users FOR INSERT
    WITH CHECK (auth.uid() = id);

-- Function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON public.users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

4. Click "Run" (or press F5)
5. You should see "Success. No rows returned"

---

### 5. Verify Setup

#### Test in Supabase Dashboard:

1. Go to **Table Editor**
2. You should see `users` table
3. Try inserting a test row (will fail due to RLS - that's good!)

#### Test in Code:

```bash
# Frontend
cd frontend
npm install
npm run dev

# Backend
cd backend
pip install -r requirements.txt
python app.py
```

If no errors appear, you're set up! ✅

---

## 📊 Database Schema

### Current Tables

#### `public.users`

Extends Supabase's built-in `auth.users` with additional profile data.

| Column                 | Type         | Description                         |
| ---------------------- | ------------ | ----------------------------------- |
| `id`                   | UUID         | Primary key (references auth.users) |
| `username`             | VARCHAR(50)  | Unique username                     |
| `email`                | VARCHAR(255) | User email (synced with auth.users) |
| `bio`                  | TEXT         | User bio/description                |
| `profile_picture_url`  | VARCHAR(500) | Profile picture URL                 |
| `work`                 | VARCHAR(255) | Current job/work                    |
| `location`             | VARCHAR(255) | User location                       |
| `created_at`           | TIMESTAMP    | Account creation time               |
| `updated_at`           | TIMESTAMP    | Last profile update                 |
| `compatibility_opt_in` | BOOLEAN      | Opted into compatibility scoring    |

---

## 🔐 Security Notes

### Frontend (.env)

- ✅ Uses `anon` key - safe to expose in browser
- ✅ Row Level Security protects data
- ⚠️ Still add `.env` to `.gitignore`

### Backend (.env)

- ⚠️ Uses `service_role` key - bypasses RLS
- 🔒 NEVER commit this to Git
- 🔒 NEVER expose in frontend

---

## 🛠️ Troubleshooting

### "Missing Supabase environment variables"

- Check that `.env` file exists in `frontend/` and `backend/`
- Verify variable names match `.env.example`
- Restart dev servers after changing `.env`

### "Failed to fetch" errors

- Check Supabase project is running (not paused)
- Verify `SUPABASE_URL` is correct
- Check internet connection

### RLS policy errors

- Make sure you ran the SQL schema
- Verify user is authenticated before queries
- Check policies exist: `SELECT * FROM pg_policies WHERE tablename = 'users';`

---

## 📚 Next Steps

1. ✅ Supabase is set up
2. → Integrate login/signup with Supabase auth
3. → Add more tables (friendships, posts, etc.)
4. → Build People Map feature