"""Seed bot accounts for aaaa@gmail.com's friend network.

Creates:
  - 5 tier-1 friends (direct friends of aaaa)
  - 25 tier-2 friends (5 friends of each tier-1)
  - 125 tier-3 friends (5 friends of each tier-2)
  Total: 155 new bot users

Also seeds posts, likes, comments, and interactions.

Run with:
    cd backend && source venv/bin/activate
    python -m scripts.seed_bots
"""
import random
import uuid
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import get_supabase_client

AAAA_ID = "e6c58cdc-767a-4ccf-a840-6901941c30fc"
CHUNK = 500

_NS = uuid.UUID("aaaabbbb-cccc-dddd-eeee-ffffaaaabbbb")

def _uid(label: str) -> str:
    return str(uuid.uuid5(_NS, f"bot-{label}"))

_INTEREST_POOL = [
    "art", "music", "film", "sports", "finance", "cooking", "coding",
    "hiking", "travel", "gaming", "reading", "yoga", "photography",
    "fashion", "design", "science", "politics", "history", "animals", "gardening",
]
_CITIES = ["NYC", "LA", "Austin", "Chicago", "Seattle", "Boston", "Denver", "Miami"]
_STATES = ["NY", "CA", "TX", "IL", "WA", "MA", "CO", "FL"]
_EDUCATIONS = ["bachelor", "master", "phd", "associate", "high school"]
_INDUSTRIES = ["tech", "media", "health", "finance", "education", "retail", "government"]
_LANGUAGES = ["english", "spanish", "french", "german", "mandarin", "japanese", "portuguese"]
_OCCUPATIONS = ["engineer", "designer", "manager", "analyst", "teacher", "doctor", "artist", "writer"]

_POST_CONTENTS = [
    "Just had the best coffee of my life ☕",
    "Working on something exciting — can't wait to share!",
    "Long walk today cleared my head 🌿",
    "Anyone else obsessed with the new album?",
    "Finished reading an incredible book. Mind = blown.",
    "Cooked a new recipe tonight. Total success 🍜",
    "So grateful for the people in my life right now.",
    "Hot take: mornings are actually underrated.",
    "Just discovered a hidden gem of a restaurant downtown.",
    "Finally started that side project I've been putting off.",
    "Nothing beats a good sunset view 🌅",
    "This city never gets old.",
    "Thinking about picking up a new hobby. Any suggestions?",
    "Today was tough but I'm still here 💪",
    "Weekend plans: absolutely nothing. Perfect.",
    "Some days you just need a reset.",
    "Learning something new every day.",
    "The small wins matter too.",
    "Random act of kindness made my whole day.",
    "Summer can't come fast enough.",
]

_COMMENT_CONTENTS = [
    "Love this!", "So true!", "Miss you!", "Same!", "Haha yes 😂",
    "This is so you 😄", "Proud of you!", "We need to catch up!",
    "Amazing!", "Can't wait to hear more!", "Tell me everything.",
    "You're the best!", "This made me smile 😊", "Iconic.",
    "Totally agree!", "Goals!", "Sending love ❤️", "lowkey jealous",
    "omg same", "needed to hear this today",
]


def _make_profile(uid: str, nickname: str, seed: int) -> dict:
    rng = random.Random(seed)
    city_idx = rng.randint(0, len(_CITIES) - 1)
    return {
        "id": uid,
        "nickname": nickname,
        "age": rng.randint(20, 45),
        "city": _CITIES[city_idx],
        "state": _STATES[city_idx],
        "interests": rng.sample(_INTEREST_POOL, k=rng.randint(2, 5)),
        "education": rng.choice(_EDUCATIONS),
        "industry": rng.choice(_INDUSTRIES),
        "languages": rng.sample(_LANGUAGES, k=rng.randint(1, 3)),
        "occupation": rng.choice(_OCCUPATIONS),
        "profile_tier": 6,
        "is_onboarded": True,
        "is_admin": False,
        "bio": f"Bot account #{seed} — seeded for testing.",
    }


def seed_bots():
    sb = get_supabase_client()
    rng = random.Random(999)

    # ── 1. Build user graph ──────────────────────────────────────────────────
    # tier1: 5 direct friends of aaaa
    tier1_ids = [_uid(f"t1_{i}") for i in range(5)]
    tier1_nicknames = [f"bot_t1_{i:02d}" for i in range(5)]

    # tier2: 5 friends for each tier1 (25 total)
    tier2_ids = [[_uid(f"t2_{i}_{j}") for j in range(5)] for i in range(5)]
    tier2_nicknames = [[f"bot_t2_{i}{j}" for j in range(5)] for i in range(5)]

    # tier3: 5 friends for each tier2 (125 total)
    tier3_ids = [[[_uid(f"t3_{i}_{j}_{k}") for k in range(5)] for j in range(5)] for i in range(5)]
    tier3_nicknames = [[[f"bt3{i}{j}{k}" for k in range(5)] for j in range(5)] for i in range(5)]

    all_bot_ids: list[str] = []
    all_profiles: list[dict] = []
    seed_counter = 1000

    for i, (uid, nick) in enumerate(zip(tier1_ids, tier1_nicknames)):
        all_bot_ids.append(uid)
        all_profiles.append(_make_profile(uid, nick, seed_counter)); seed_counter += 1

    for i in range(5):
        for j in range(5):
            uid = tier2_ids[i][j]; nick = tier2_nicknames[i][j]
            all_bot_ids.append(uid)
            all_profiles.append(_make_profile(uid, nick, seed_counter)); seed_counter += 1

    for i in range(5):
        for j in range(5):
            for k in range(5):
                uid = tier3_ids[i][j][k]; nick = tier3_nicknames[i][j][k]
                all_bot_ids.append(uid)
                all_profiles.append(_make_profile(uid, nick, seed_counter)); seed_counter += 1

    print(f"Creating {len(all_profiles)} bot profiles...")

    # ── 2. Create auth users (so profiles FK is satisfied) ───────────────────
    existing_auth = {
        r["id"]
        for r in (sb.table("profiles").select("id").execute().data or [])
    }
    created_auth = 0
    for p in all_profiles:
        if p["id"] in existing_auth:
            continue
        try:
            sb.auth.admin.create_user({
                "user_id": p["id"],
                "email": f"{p['nickname']}@botmail.dev",
                "password": "Bot$ecure123!",
                "email_confirm": True,
            })
            created_auth += 1
        except Exception as e:
            print(f"  Auth user {p['nickname']} may already exist: {e}")
    print(f"  Created {created_auth} auth users")

    # ── 3. Upsert profiles ───────────────────────────────────────────────────
    # Build SQL for bulk insert into private.profiles
    rows = []
    for p in all_profiles:
        interests = "{" + ",".join(p.get("interests") or []) + "}"
        languages = "{" + ",".join(p.get("languages") or []) + "}"
        rows.append(
            f"('{p['id']}', '{p['nickname']}', {p['age']}, '{p['city']}', '{p['state']}', "
            f"'{interests}', '{p['education']}', '{p['industry']}', '{languages}', "
            f"'{p['occupation']}', {p['profile_tier']}, true, false, '{p['bio']}')"
        )
    values_sql = ",\n".join(rows)
    sql = f"""
        INSERT INTO private.profiles
          (id, nickname, age, city, state, interests, education, industry, languages,
           occupation, profile_tier, is_onboarded, is_admin, bio)
        VALUES {values_sql}
        ON CONFLICT (id) DO UPDATE SET
          nickname = EXCLUDED.nickname,
          age = EXCLUDED.age,
          city = EXCLUDED.city,
          state = EXCLUDED.state,
          interests = EXCLUDED.interests,
          education = EXCLUDED.education,
          industry = EXCLUDED.industry,
          languages = EXCLUDED.languages,
          occupation = EXCLUDED.occupation,
          profile_tier = EXCLUDED.profile_tier,
          is_onboarded = EXCLUDED.is_onboarded,
          bio = EXCLUDED.bio
    """
    # Write SQL to a temp file for MCP tool to execute
    import tempfile, pathlib
    out_path = pathlib.Path(__file__).parent / "_bot_seed.sql"
    out_path.write_text(sql)
    print(f"  Wrote profile SQL to {out_path} — run via MCP execute_sql or psql")
    print(f"  (profile count: {len(all_profiles)})")

    # ── 4. Build friendship graph (bidirectional via friends array) ──────────
    # friendship_map[uid] = set of friend uids
    friendship_map: dict[str, set] = {uid: set() for uid in all_bot_ids}
    friendship_map[AAAA_ID] = set()

    # aaaa ↔ each tier1
    for uid in tier1_ids:
        friendship_map[AAAA_ID].add(uid)
        friendship_map[uid].add(AAAA_ID)

    # tier1[i] ↔ each tier2[i][j]
    for i in range(5):
        for j in range(5):
            t1 = tier1_ids[i]; t2 = tier2_ids[i][j]
            friendship_map[t1].add(t2)
            friendship_map[t2].add(t1)

    # tier2[i][j] ↔ each tier3[i][j][k]
    for i in range(5):
        for j in range(5):
            for k in range(5):
                t2 = tier2_ids[i][j]; t3 = tier3_ids[i][j][k]
                friendship_map[t2].add(t3)
                friendship_map[t3].add(t2)

    # Apply: update each user's friends array
    print("  Writing friendships...")

    # Get aaaa's current friends so we don't overwrite them
    aaaa_current = sb.table("profiles").select("friends").eq("id", AAAA_ID).execute().data
    existing_friends = set(aaaa_current[0].get("friends") or []) if aaaa_current else set()
    friendship_map[AAAA_ID].update(existing_friends)

    all_friend_updates = [(uid, list(friends)) for uid, friends in friendship_map.items()]
    for uid, friends in all_friend_updates:
        sb.table("profiles").update({"friends": friends}).eq("id", uid).execute()
    print(f"  Updated friends arrays for {len(all_friend_updates)} users")

    # ── 5. Create posts ──────────────────────────────────────────────────────
    posts = []
    post_id_map: dict[str, list[str]] = {}  # uid → list of post ids
    tiers_cycle = ["inner_circle", "second_degree", "third_degree"]
    tier_nums_cycle = [1, 2, 3]

    for idx, uid in enumerate(all_bot_ids):
        user_rng = random.Random(idx + 5000)
        num_posts = user_rng.randint(1, 3)
        post_id_map[uid] = []
        for p in range(num_posts):
            pid = str(uuid.uuid5(_NS, f"post-{uid}-{p}"))
            tier_idx = (idx + p) % 3
            posts.append({
                "id": pid,
                "user_id": uid,
                "content": user_rng.choice(_POST_CONTENTS),
                "tier": tiers_cycle[tier_idx],
                "tier_num": tier_nums_cycle[tier_idx],
            })
            post_id_map[uid].append(pid)

    for i in range(0, len(posts), CHUNK):
        sb.table("posts").upsert(posts[i:i+CHUNK], on_conflict="id").execute()
    print(f"  Upserted {len(posts)} posts")

    # ── 6. Likes ─────────────────────────────────────────────────────────────
    likes = []
    likes_seen: set[tuple] = set()

    def _add_like(liker_id: str, post_id: str):
        key = (liker_id, post_id)
        if key not in likes_seen:
            likes_seen.add(key)
            likes.append({
                "id": str(uuid.uuid5(_NS, f"like-{liker_id}-{post_id}")),
                "user_id": liker_id,
                "post_id": post_id,
            })

    # Friends like each other's posts
    for i in range(5):
        t1 = tier1_ids[i]
        for pid in post_id_map.get(t1, []):
            _add_like(AAAA_ID, pid)
        for pid in post_id_map.get(AAAA_ID, []):
            _add_like(t1, pid)
        for j in range(5):
            t2 = tier2_ids[i][j]
            for pid in post_id_map.get(t2, []):
                _add_like(t1, pid)
            for pid in post_id_map.get(t1, []):
                _add_like(t2, pid)
            for k in range(5):
                t3 = tier3_ids[i][j][k]
                for pid in post_id_map.get(t3, []):
                    _add_like(t2, pid)
                for pid in post_id_map.get(t2, []):
                    _add_like(t3, pid)

    for i in range(0, len(likes), CHUNK):
        sb.table("likes").upsert(likes[i:i+CHUNK], on_conflict="id").execute()
    print(f"  Upserted {len(likes)} likes")

    # ── 7. Comments ──────────────────────────────────────────────────────────
    comments = []

    def _add_comment(commenter_id: str, post_id: str, seed: int):
        c_rng = random.Random(seed)
        comments.append({
            "id": str(uuid.uuid5(_NS, f"comment-{commenter_id}-{post_id}")),
            "user_id": commenter_id,
            "post_id": post_id,
            "content": c_rng.choice(_COMMENT_CONTENTS),
        })

    comment_seed = 0
    for i in range(5):
        t1 = tier1_ids[i]
        for pid in post_id_map.get(t1, []):
            _add_comment(AAAA_ID, pid, comment_seed); comment_seed += 1
        for j in range(5):
            t2 = tier2_ids[i][j]
            for pid in post_id_map.get(t1, []):
                if rng.random() < 0.5:
                    _add_comment(t2, pid, comment_seed); comment_seed += 1

    for i in range(0, len(comments), CHUNK):
        sb.table("comments").upsert(comments[i:i+CHUNK], on_conflict="id").execute()
    print(f"  Upserted {len(comments)} comments")

    # ── 8. Interactions table ─────────────────────────────────────────────────
    interactions = []
    interactions_seen: set[tuple] = set()

    def _add_interaction(a: str, b: str, lk: int, cm: int):
        uid_a, uid_b = (a, b) if a < b else (b, a)
        key = (uid_a, uid_b)
        if key not in interactions_seen:
            interactions_seen.add(key)
            interactions.append({
                "user_id_a": uid_a,
                "user_id_b": uid_b,
                "likes_count": lk,
                "comments_count": cm,
            })

    for i in range(5):
        t1 = tier1_ids[i]
        _add_interaction(AAAA_ID, t1, 15, 10)
        for j in range(5):
            t2 = tier2_ids[i][j]
            _add_interaction(t1, t2, 8, 5)
            for k in range(5):
                t3 = tier3_ids[i][j][k]
                _add_interaction(t2, t3, 4, 2)

    for i in range(0, len(interactions), CHUNK):
        sb.table("interactions").upsert(
            interactions[i:i+CHUNK], on_conflict="user_id_a,user_id_b"
        ).execute()
    print(f"  Upserted {len(interactions)} interactions")

    print("\nDone! Summary:")
    print(f"  Bot profiles : {len(all_profiles)}")
    print(f"  Posts        : {len(posts)}")
    print(f"  Likes        : {len(likes)}")
    print(f"  Comments     : {len(comments)}")
    print(f"  Interactions : {len(interactions)}")


if __name__ == "__main__":
    seed_bots()
