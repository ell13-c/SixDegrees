# Supabase Setup for SixDegrees


### 1. Create Supabase Project (DONE)

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