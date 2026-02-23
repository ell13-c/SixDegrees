---
phase: 05-demo-and-docs
verified: 2026-02-23T21:00:00Z
status: passed
score: 6/6 must-haves verified
re_verification: false
---

# Phase 5: Demo and Docs Verification Report

**Phase Goal:** The algorithm's correctness is demonstrable through runnable scripts, and the frontend team has a complete written contract for what to read and write
**Verified:** 2026-02-23T21:00:00Z
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `scripts/test_map.py` exists, is substantive (193 lines), and runs the full pipeline end-to-end with baseline + bumped coordinates | VERIFIED | File exists, 193 lines, imports `run_pipeline_for_user`, calls pipeline twice |
| 2 | Scatter plot is color-coded by tier (3 colors) and labeled by `display_name` | VERIFIED | `TIER_COLORS` dict with all 3 hex values present; `ax.annotate(p["display_name"])` in `plot_map()` |
| 3 | Sensitivity structure is correct: baseline computed, interaction bumped to 60, re-run, distance delta compared, counts restored in `try/finally` | VERIFIED | Execution order verified — `baseline_coords` before `set_likes`, `original_likes` saved before bump, `finally` restores |
| 4 | `scripts/people_map_demo.ipynb` is a valid Jupyter notebook (nbformat 4) with 7 code cells covering all 5 pipeline stages plus sensitivity demo | VERIFIED | JSON valid, nbformat=4, 14 cells (7 code + 7 markdown), all stage imports confirmed present |
| 5 | `docs/API_CONTRACT.md` documents all 6 endpoints with request/response shapes, auth header format, and 401/403 error detail strings | VERIFIED | 285 lines; all 6 endpoints present; actual response shapes verified from code (e.g. `{"detail": "likes recorded"}` not `{"status": "ok"}`) |
| 6 | `docs/DB_SCHEMA.md` documents all 3 tables with canonical pair ordering explanation and `is_current` versioning pattern | VERIFIED | 137 lines; all 3 tables; canonical pair ordering section present; `is_current` versioning 3-step pattern documented |

**Score:** 6/6 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `scripts/test_map.py` | Standalone scatter plot demo with sensitivity comparison; min 80 lines | VERIFIED | Exists, 193 lines, substantive implementation |
| `backend/requirements.txt` | Contains `matplotlib>=3.10`, `jupyter`, `ipykernel==6.30.1` under `# Demo deliverables` | VERIFIED | All three present under correct section comment |
| `scripts/people_map_demo.ipynb` | Valid Jupyter notebook with per-stage inline plots; min 50 lines | VERIFIED | Valid JSON, nbformat 4, 14 cells |
| `docs/API_CONTRACT.md` | Complete frontend API reference; min 120 lines; contains `Authorization: Bearer` | VERIFIED | 285 lines; all required content present |
| `docs/DB_SCHEMA.md` | Database schema reference; min 60 lines; contains `is_current` | VERIFIED | 137 lines; all required content present |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `scripts/test_map.py` | `backend/services/map_pipeline/__init__.py` | `sys.path.insert` + `from services.map_pipeline import run_pipeline_for_user` | WIRED | Both `sys.path.insert(0, BACKEND_DIR)` and the import are present |
| `scripts/test_map.py` | `backend/.env` | `load_dotenv(dotenv_path=os.path.join(BACKEND_DIR, ".env"))` | WIRED | Pattern confirmed in file |
| `scripts/test_map.py` | `supabase interactions table` | `set_likes()` upsert + `try/finally` restore | WIRED | `upsert` call present; `finally` block restores `original_likes` |
| `scripts/people_map_demo.ipynb` | `data_fetcher.py` | `from services.map_pipeline.data_fetcher import fetch_all` | WIRED | `fetch_all` present in notebook source; function exists in module |
| `scripts/people_map_demo.ipynb` | `interaction.py` | `from services.map_pipeline.interaction import compute_interaction_scores` | WIRED | Present in notebook; `compute_interaction_scores` is the only function in `interaction.py` |
| `scripts/people_map_demo.ipynb` | `scoring.py` | `from services.map_pipeline.scoring import build_combined_distance_matrix` | WIRED | Present in notebook; function confirmed in `scoring.py` |
| `scripts/people_map_demo.ipynb` | `tsne_projector.py` | `from services.map_pipeline.tsne_projector import project_tsne` | WIRED | Present in notebook; function confirmed in `tsne_projector.py` |
| `scripts/people_map_demo.ipynb` | `origin_translator.py` | `from services.map_pipeline.origin_translator import translate_and_assign_tiers` | WIRED | Present in notebook; function confirmed in `origin_translator.py` |
| `docs/API_CONTRACT.md` | `backend/routes/map.py` | Documents `GET /map/{user_id}` and `POST /map/trigger/{user_id}` response shapes | WIRED | Both routes confirmed in `map.py`; response shapes documented with actual field names |
| `docs/API_CONTRACT.md` | `backend/routes/interactions.py` | Documents `POST /interactions/*` request/response shapes | WIRED | All 3 interaction routes confirmed; actual response `{"detail": "likes recorded"}` documented (not assumed `{"status": "ok"}`) |
| `docs/API_CONTRACT.md` | `backend/routes/profile.py` | Documents `PUT /profile` request/response shape | WIRED | Route confirmed; `{"detail": "Profile updated"}` response documented |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|---------|
| DEMO-01 | 05-01 | `scripts/test_map.py` runs full pipeline, produces scatter plot with tier color-coding and `display_name` labels | SATISFIED | File exists 193 lines; 3 tier colors hardcoded; `annotate(p["display_name"])` in plot function |
| DEMO-02 | 05-02 | `scripts/people_map_demo.ipynb` runs end-to-end with per-stage explanations and inline plots | SATISFIED | Valid nbformat 4 notebook, 7 code cells + 7 markdown cells; `imshow` heatmaps for stages 3-4; scatter for stage 5 |
| DEMO-03 | 05-01, 05-02 | Both scripts demonstrate sensitivity — bumping interaction count moves users closer | SATISFIED | Sensitivity structure verified in both files: baseline before bump, re-run after, distance delta printed; `BUMP_LIKES = 60` in both |
| DEMO-04 | 05-01, 05-02 | Both scripts connect to real Supabase via `.env` credentials | SATISFIED | Both load `backend/.env`; both use `get_supabase_client()` or `supabase.auth`; env guard raises/exits if missing |
| SPEC-01 | 05-03 | `docs/API_CONTRACT.md` documents all endpoints: response formats, auth header, error shapes | SATISFIED | 285 lines; all 6 endpoints; actual 401 detail strings from `deps.py` documented; 401/403/404/422 all covered |
| SPEC-02 | 05-03 | `docs/DB_SCHEMA.md` documents table schemas for frontend reference | SATISFIED | 137 lines; all 3 tables; canonical pair ordering explanation; `is_current` 3-step versioning pattern; frontend `Cannot write` summary table |

**Orphaned requirements:** None. REQUIREMENTS.md maps exactly DEMO-01, DEMO-02, DEMO-03, DEMO-04, SPEC-01, SPEC-02 to Phase 5 — all 6 are claimed by plans and verified above.

---

### Anti-Patterns Found

| File | Pattern | Severity | Notes |
|------|---------|----------|-------|
| — | None found | — | All four artifacts clean; no TODO/FIXME/placeholder/stub patterns detected |

---

### Human Verification Required

#### 1. Sensitivity Result Direction

**Test:** With seeded Supabase data, run `python scripts/test_map.py`
**Expected:** Printed output shows `Distance(Alex, Skyler)` is lower after the bump than before — i.e., `delta > 0` and "CLOSER" is printed
**Why human:** t-SNE is stochastic and the direction of the distance change depends on runtime data. The code structure is correct (baseline before, bump, re-run, compare) but the actual numeric result requires live Supabase + seeded data to confirm. The algorithm *should* produce this but the code cannot guarantee it without execution.

#### 2. Matplotlib Window Renders Correctly

**Test:** Run `python scripts/test_map.py` with seeded Supabase data; observe the matplotlib window
**Expected:** Two side-by-side scatter plots appear — left labeled "Baseline: Alex's People Map", right labeled "After bumping Alex-Skyler likes to 60"; dots are 3 colors (red/blue/gray for tiers 1/2/3); display names annotate each dot
**Why human:** Visual rendering cannot be verified programmatically.

#### 3. Jupyter Notebook Executes All Cells Without Error

**Test:** From project root, `source backend/venv/bin/activate && jupyter notebook scripts/people_map_demo.ipynb`, then "Run All Cells"
**Expected:** All 7 code cells complete without exception; stages 2-3 render inline heatmaps; stage 4 renders raw t-SNE scatter; stage 5 renders final People Map with tier colors; sensitivity cell shows side-by-side plots and prints counts restored
**Why human:** Notebook execution requires Jupyter kernel + live Supabase; cannot run headlessly in this context.

#### 4. API_CONTRACT.md Response Shapes Are Live-Accurate

**Test:** Call each of the 6 endpoints against the running backend and compare actual responses to `docs/API_CONTRACT.md`
**Expected:** All response shapes, status codes, and error detail strings match exactly as documented
**Why human:** Docs were written by reading route code (verified), but actual HTTP response format depends on runtime FastAPI serialization and middleware not statically verifiable.

---

### Gaps Summary

No gaps. All 6 observable truths are verified. All 5 artifacts pass all three levels (exists, substantive, wired). All 11 key links are wired. All 6 requirements are satisfied. No anti-patterns detected.

The 4 human verification items are routine runtime/visual checks — they cannot be confirmed programmatically but the code structure fully supports the expected outcomes.

---

## Notable Implementation Decisions (Verified in Code)

1. **Actual response shapes differ from plan template:** Interaction endpoints return `{"detail": "likes recorded"}` (not `{"status": "ok"}`). Profile endpoint returns `{"detail": "Profile updated"}`. API_CONTRACT.md correctly documents the actual shapes (verified from route code).

2. **UserProfile model field correction:** The `UserProfile` Pydantic model uses `.id` (not `.user_id`) and has no `.display_name` field. The notebook fetches display names separately from Supabase. This deviation from the plan template was correctly fixed in the implementation (documented in 05-02-SUMMARY.md deviations).

3. **Interaction dict keys:** `data_fetcher.py` returns keys `"likes"`, `"comments"`, `"dms"` (not `"likes_count"` etc.). The notebook uses the correct short keys (verified present in notebook source).

4. **Commits verified:** All 6 commits referenced in SUMMARY files (`b78a2f7`, `313f9a4`, `b053b17`, `9a3077a`, `cb4a212`, `d2e7919`) exist in git history.

---

_Verified: 2026-02-23T21:00:00Z_
_Verifier: Claude (gsd-verifier)_
