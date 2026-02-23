# Phase 5: Demo and Docs - Research

**Researched:** 2026-02-23
**Domain:** Python demo scripts (matplotlib), Jupyter notebooks, API/DB documentation
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**scripts/test_map.py (DEMO-01, DEMO-03, DEMO-04)**
- Standalone Python script — no external test framework
- Connects to real Supabase using `.env` credentials
- Workflow: reads seed users → runs full pipeline → plots 2D scatter with matplotlib
- Dots labeled by `display_name`
- Color-coded by tier: 3 colors (Tier 1 / Tier 2 / Tier 3)
- Must demonstrate sensitivity: seeding higher interaction count between two users makes them visibly closer on the scatter plot

**scripts/people_map_demo.ipynb (DEMO-02, DEMO-03, DEMO-04)**
- Jupyter notebook with per-stage explanations and inline matplotlib plots
- One cell group per pipeline stage: data fetch → interaction scoring → combined distance → t-SNE → origin translation → visualization
- Runs end-to-end with a single "Run All Cells" command
- Also connects to real Supabase via `.env`
- Demonstrates sensitivity: same as test_map.py but interactively

**docs/API_CONTRACT.md (SPEC-01)**
Complete frontend reference for:
- `GET /map/{user_id}` — full response JSON shape with field types
- `POST /map/trigger/{user_id}` — request/response
- `POST /interactions/like`, `/comment`, `/dm` — request body, auth header, response, error shapes (401, 403)
- `PUT /profile` — request body (all profile fields), auth header, response, 401/403 errors
- Auth header format: `Authorization: Bearer <supabase_jwt>`
- General error shape
Must be detailed enough that the frontend team can implement without asking follow-up questions.

**docs/DB_SCHEMA.md (SPEC-02)**
Reference-only schema doc for:
- `user_profiles` — all fields, types, constraints
- `interactions` — canonical pair ordering explained, all count fields
- `map_coordinates` — is_current versioning explained, index note
Frontend does NOT write directly to any table. This is for reference only.

**.env requirement**
Both scripts use `.env` files. A `.env.example` must exist in both `frontend/` and `backend/` (or at project root) with all required keys documented. Scripts should fail clearly if `.env` is missing rather than crashing with cryptic errors.

**No pytest suite**
Full production test suite is out of scope. The demo scripts ARE the validation. If test_map.py runs and shows the correct scatter plot, the phase is complete.

**Sensitivity demonstration**
The notebooks/scripts must show algorithm sensitivity — increasing interaction count between users A and B must produce a visibly closer position for those two users. This can be done by:
1. Running pipeline with current seed data
2. Manually bumping interaction counts for two specific users
3. Re-running and comparing plots side by side (or showing before/after in the notebook)

### Claude's Discretion
(No explicit discretion items defined — all key decisions are locked above.)

### Deferred Ideas (OUT OF SCOPE)
- Frontend UI rendering the People Map
- Production deployment
- pytest test suite
- Animation / Procrustes alignment
- Performance benchmarks
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DEMO-01 | `scripts/test_map.py` is a standalone Python script that seeds mock data, runs the full pipeline, and plots a 2D scatter plot with matplotlib; dots labeled by display_name and color-coded by tier | Matplotlib scatter + annotate pattern; sys.path manipulation to import from backend/; run_pipeline_for_user() is the entry point |
| DEMO-02 | `scripts/people_map_demo.ipynb` is a Jupyter notebook with per-stage explanations and inline plots; runs end-to-end with a single "Run All" command | Jupyter install with ipykernel==6.30.1 workaround for Python 3.14; %matplotlib inline; per-stage cell groups calling pipeline sub-modules |
| DEMO-03 | Both scripts demonstrate sensitivity: increasing interaction count between two users moves them visibly closer; changing profile interests moves users relative to their interest cluster | Sensitivity demo via direct Supabase upsert of bumped interaction counts before second plot; matplotlib subplot side-by-side or sequential plots |
| DEMO-04 | Both scripts connect to the real Supabase instance (using `.env` credentials) and work with the seeded mock data | python-dotenv load_dotenv() with explicit dotenv_path pointing to backend/.env; Supabase service role client |
| SPEC-01 | `docs/API_CONTRACT.md` documents all endpoints: `GET /map/{user_id}` response format, all write endpoint request/response formats, auth header requirement, and error shapes | Full endpoint inventory from routes/map.py, routes/interactions.py, routes/profile.py; error shapes from deps.py; response shapes from _fetch_map_response() |
| SPEC-02 | `docs/DB_SCHEMA.md` documents the table schemas — for reference only; frontend does not write directly to any table | Table structure from setup_tables.sql logic; field names confirmed in data_fetcher.py, coord_writer.py, seed_db.py |
</phase_requirements>

---

## Summary

Phase 5 delivers two demo artifacts (a standalone script and a Jupyter notebook) plus two markdown documentation files. All backend pipeline code is already complete as of Phase 4. Phase 5 does not write any new Python logic — it wires together existing services (`run_pipeline_for_user`, `fetch_all`, individual pipeline stages) into runnable demos and documents what has already been built.

The key technical challenge is the Python 3.14 venv compatibility with Jupyter. The project venv uses Python 3.14, and Jupyter has a known kernel connectivity issue with Python 3.14 and ipykernel 7. The verified workaround is `pip install ipykernel==6.30.1`, which must be applied before the notebook will run. Matplotlib 3.10.x ships pre-built wheels for Python 3.14 and installs cleanly via pip.

The sensitivity demonstration (DEMO-03) is the trickiest requirement. The cleanest approach is for both scripts to: (1) run the pipeline and plot the baseline, (2) upsert bumped interaction counts for a specific pair directly via Supabase, (3) run the pipeline again and plot the result. For the notebook, show both plots side by side in one cell group; for the standalone script, show them sequentially in a single matplotlib figure with subplots.

**Primary recommendation:** Keep both demo artifacts as thin orchestrators that import from `backend/services/map_pipeline/` using `sys.path.insert`. Use `dotenv.find_dotenv()` to locate backend/.env regardless of working directory. Pin `ipykernel==6.30.1` in demo requirements when using Python 3.14.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| matplotlib | 3.10.x (latest stable) | Scatter plot rendering, annotating, subplots | Standard Python plotting library; confirmed wheel available for Python 3.14 |
| python-dotenv | 1.0.0 (already in requirements.txt) | Load .env credentials | Already installed in venv; `find_dotenv()` resolves path regardless of cwd |
| supabase (supabase-py) | already installed | Bump interaction counts for sensitivity demo | Already used in backend; same client pattern as seed_db.py |
| jupyter (notebook) | latest stable | Hosting people_map_demo.ipynb | Standard notebook environment |
| ipykernel | 6.30.1 (pinned) | Jupyter kernel for Python 3.14 | ipykernel 7 breaks Python 3.14 kernel; 6.30.1 is the verified fix |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| numpy | 2.4.2 (already installed) | Array operations in pipeline | Already present; imported by existing pipeline code |
| scikit-learn | 1.8.0 (already installed) | t-SNE via run_pipeline() | Already present; used inside existing pipeline |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| matplotlib scatter | plotly | Plotly gives interactive plots but adds a heavy dep not needed for demo; matplotlib is sufficient |
| ipykernel==6.30.1 | system Python (not 3.14) | Using a different Python avoids the issue but changing the venv is disruptive; pinning 6.30.1 is the minimal fix |
| load_dotenv(dotenv_path=...) | environment variables set externally | dotenv_path is more portable — no manual export needed before running |

**Installation (inside backend venv):**
```bash
cd /Users/BAEK/Code/sixDegrees/backend
source venv/bin/activate
pip install matplotlib jupyter ipykernel==6.30.1
```

These packages are NOT currently in requirements.txt (they are demo-only). Add them to requirements.txt or a separate `demo-requirements.txt`.

---

## Architecture Patterns

### Recommended Project Structure
```
sixDegrees/
├── scripts/
│   ├── test_map.py               # DEMO-01: standalone scatter script
│   └── people_map_demo.ipynb     # DEMO-02: Jupyter notebook
├── docs/
│   ├── API_CONTRACT.md           # SPEC-01
│   └── DB_SCHEMA.md              # SPEC-02
└── backend/
    └── services/map_pipeline/    # Existing — scripts import from here
```

Note: `scripts/` and `docs/` directories do not yet exist. Both must be created at the project root level (sibling to `backend/` and `frontend/`).

### Pattern 1: Standalone Script with sys.path manipulation

**What:** test_map.py sits at project root `scripts/`, but imports from `backend/`. It uses `sys.path.insert` to allow bare imports like `from services.map_pipeline import run_pipeline_for_user`.

**When to use:** Any standalone script outside the backend package that needs to call backend services.

**Example:**
```python
# scripts/test_map.py
import os
import sys

# Allow importing backend modules regardless of cwd
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, os.path.abspath(BACKEND_DIR))

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())  # finds backend/.env by traversing parent dirs

from services.map_pipeline import run_pipeline_for_user
from services.map_pipeline.data_fetcher import fetch_all
```

This exactly mirrors `backend/scripts/seed_db.py` which already uses `sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))`.

### Pattern 2: Matplotlib Scatter with Tier Colors and Point Labels

**What:** Three-color scatter plot (one color per tier), dots annotated with display_name.

**When to use:** DEMO-01 final plot; DEMO-02 visualization cell; sensitivity comparison subplots.

**Example:**
```python
import matplotlib
matplotlib.use("Agg")  # Use non-interactive backend for scripts (omit in notebook)
import matplotlib.pyplot as plt

TIER_COLORS = {1: "#e74c3c", 2: "#3498db", 3: "#95a5a6"}
TIER_LABELS = {1: "Tier 1", 2: "Tier 2", 3: "Tier 3"}

def plot_map(coordinates, title="People Map", ax=None):
    """Plot a list of coordinate dicts [{'user_id', 'x', 'y', 'tier', 'display_name'}]."""
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(10, 8))

    # Group by tier for legend
    for tier in [1, 2, 3]:
        pts = [c for c in coordinates if c["tier"] == tier]
        if not pts:
            continue
        ax.scatter(
            [p["x"] for p in pts],
            [p["y"] for p in pts],
            c=TIER_COLORS[tier],
            label=TIER_LABELS[tier],
            s=80,
            alpha=0.8,
        )
        for p in pts:
            ax.annotate(
                p["display_name"],
                (p["x"], p["y"]),
                textcoords="offset points",
                xytext=(5, 5),
                fontsize=7,
            )

    ax.scatter(0, 0, c="black", marker="*", s=200, label="You (center)", zorder=5)
    ax.axhline(0, color="gray", linewidth=0.5, linestyle="--", alpha=0.5)
    ax.axvline(0, color="gray", linewidth=0.5, linestyle="--", alpha=0.5)
    ax.legend()
    ax.set_title(title)
    ax.set_xlabel("t-SNE dim 1")
    ax.set_ylabel("t-SNE dim 2")

    if standalone:
        plt.tight_layout()
        plt.show()
```

Note: `matplotlib.use("Agg")` must be set BEFORE importing `matplotlib.pyplot` in a non-interactive script environment. In a Jupyter notebook, use `%matplotlib inline` magic instead and omit the `use()` call.

### Pattern 3: Sensitivity Demonstration (Before/After)

**What:** Run pipeline twice: once with seed data, once after bumping one pair's interaction counts. Show plots side by side.

**When to use:** DEMO-03 requirement in both test_map.py (side-by-side subplots) and notebook (separate cell groups with markdown explaining the change).

**Example (test_map.py):**
```python
from config.supabase import get_supabase_client

def bump_interaction(user_id_a: str, user_id_b: str, likes_increment: int = 20):
    """Bump likes_count for a specific pair to demonstrate sensitivity."""
    sb = get_supabase_client()
    uid_a, uid_b = min(user_id_a, user_id_b), max(user_id_a, user_id_b)
    # Use the existing RPC that was built in Phase 4
    for _ in range(likes_increment):
        sb.rpc(
            "increment_interaction",
            {"p_user_id_a": uid_a, "p_user_id_b": uid_b, "p_column": "likes_count"},
        ).execute()
```

Alternative: Direct upsert is simpler than looping the RPC.

**Better approach using direct upsert:**
```python
def set_interaction_count(user_id_a: str, user_id_b: str, likes: int):
    """Directly set likes_count to demonstrate sensitivity — no loop needed."""
    sb = get_supabase_client()
    uid_a, uid_b = min(user_id_a, user_id_b), max(user_id_a, user_id_b)
    sb.table("interactions").upsert(
        {"user_id_a": uid_a, "user_id_b": uid_b, "likes_count": likes},
        on_conflict="user_id_a,user_id_b",
    ).execute()
```

Then restore original value at the end of the script.

**Pair to use for sensitivity demo:** Alex Rivera (3561ceb0-...) and Skyler Thompson (af17902c-...) — they are in different clusters (Outdoors vs Tech) with only cross-cluster sparse interactions. Bumping their interaction count to 50+ should move them noticeably closer.

### Pattern 4: Jupyter Notebook Cell Group Structure

**What:** One cell group per pipeline stage. Each group = one markdown cell (explanation) + one code cell (execution) + one code cell (inline plot if applicable).

**When to use:** DEMO-02 — the notebook is the structured walkthrough.

**Cell group order:**
```
[Markdown] # Stage 1: Data Fetch
[Code]     profiles, interactions = fetch_all(); print summary
[Markdown] # Stage 2: Interaction Scoring
[Code]     interaction_matrix = compute_interaction_scores(...); plt.imshow(...)
[Markdown] # Stage 3: Combined Distance Matrix
[Code]     dist_matrix = build_combined_distance_matrix(...); plt.imshow(...)
[Markdown] # Stage 4: t-SNE Projection
[Code]     raw_coords = project_tsne(dist_matrix); plt.scatter(raw_coords[:,0], ...)
[Markdown] # Stage 5: Origin Translation + Tiers
[Code]     results = translate_and_assign_tiers(...); plot_map(results)
[Markdown] # Sensitivity Demonstration
[Code]     set_interaction_count(..., likes=50); run again; plot side by side
```

### Pattern 5: .env Loading in Scripts Outside backend/

**What:** `find_dotenv()` traverses parent directories to find `.env` files. This means `scripts/test_map.py` at project root will find `backend/.env` if the scripts/ directory is adjacent.

**Limitation:** `find_dotenv()` searches upward from the script's location but does NOT descend into sibling directories. If `backend/.env` is not an ancestor of `scripts/`, you must specify the path explicitly.

**Correct approach for this project (scripts/ is sibling of backend/):**
```python
from dotenv import load_dotenv
import os

BACKEND_ENV = os.path.join(os.path.dirname(__file__), "..", "backend", ".env")
load_dotenv(dotenv_path=os.path.abspath(BACKEND_ENV))
```

This is explicit and unambiguous — the safest pattern.

### Anti-Patterns to Avoid
- **`matplotlib.use("Agg")` called after `import matplotlib.pyplot`:** The backend call must come BEFORE pyplot import — once pyplot is imported, the backend is locked. Reordering causes a silent no-op or a warning.
- **`%matplotlib inline` in a .py file:** This magic only works in IPython/Jupyter contexts. In standalone scripts, call `plt.show()` at the end instead.
- **`matplotlib.use("TkAgg")` or `matplotlib.use("Qt5Agg")` in scripts:** These require GUI toolkits. On headless CI or macOS without tkinter, they crash. Use `"MacOSX"` on macOS or let matplotlib pick automatically — or just don't call `use()` in the script (matplotlib will pick a sensible default on macOS with a display).
- **Calling `run_pipeline_for_user()` without triggering a Supabase map computation first:** If map_coordinates has no rows for the demo user, `GET /map/{user_id}` returns 404. The demo scripts call `run_pipeline_for_user()` directly, which is the right pattern — they do NOT hit the HTTP API.
- **Modifying interaction counts without restoring them:** The sensitivity demo should restore original counts after the second run, to keep Supabase data consistent with seed state.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Pipeline execution | Custom pipeline wiring | `run_pipeline_for_user(requesting_user_id)` from `services.map_pipeline` | Already built and tested in Phases 2-4 |
| Per-stage inspection | Re-implement stages | Import `fetch_all`, `compute_interaction_scores`, `build_combined_distance_matrix`, `project_tsne`, `translate_and_assign_tiers` individually | All stages are importable pure functions |
| Color legend for scatter | Manual legend patches | `ax.scatter(..., label=...)` + `ax.legend()` | Matplotlib legend handles this automatically when label is set per scatter call |
| .env parsing | Custom file reader | `python-dotenv` `load_dotenv(dotenv_path=...)` | Already in requirements.txt; handles comments, quoting, variable interpolation |
| Supabase interaction bump | New RPC function | Direct upsert via `supabase.table("interactions").upsert(..., on_conflict="user_id_a,user_id_b")` | `increment_interaction` RPC exists but looping it is awkward; direct upsert is cleaner for demo |

**Key insight:** Phase 5 writes zero new business logic. Everything already exists. The scripts are thin orchestrators that call what's already built.

---

## Common Pitfalls

### Pitfall 1: Python 3.14 + Jupyter Kernel Timeout
**What goes wrong:** After `pip install jupyter notebook`, running the notebook produces "Waiting for kernel" timeout, and the kernel never connects. All cells remain unexecuted.
**Why it happens:** `ipykernel` 7.x (the latest) has a compatibility issue with Python 3.14's free-threaded build. The kernel fails to initialize the event loop properly.
**How to avoid:** Pin `ipykernel==6.30.1` explicitly when installing. `pip install jupyter ipykernel==6.30.1` — the version must be complete (not just `==6`).
**Warning signs:** The Jupyter UI shows "Starting kernel..." indefinitely. Console shows timeout errors in the kernel launcher.
**Source:** Confirmed workaround from Jupyter community forum (discourse.jupyter.org), verified Feb 2026.

### Pitfall 2: matplotlib backend crashes on macOS in scripts
**What goes wrong:** Script crashes at `plt.show()` with `RuntimeError: Invalid DISPLAY variable` or similar.
**Why it happens:** When running the script from a terminal that lacks a display connection, or when the default backend (usually TkAgg or MacOSX) isn't available.
**How to avoid:** On macOS, the `MacOSX` backend works in interactive terminal usage. If the script will be run headlessly, set `matplotlib.use("Agg")` before `import matplotlib.pyplot`. `Agg` saves to file instead of displaying. For demo purposes (where a human is watching), don't force `Agg` — let matplotlib pick the default.
**Warning signs:** Traceback mentioning `_tkinter`, `FigureCanvasAgg`, or display errors.

### Pitfall 3: sys.path order clobbering existing packages
**What goes wrong:** After `sys.path.insert(0, backend_dir)`, a module name in `backend/` shadows a stdlib or installed package of the same name.
**Why it happens:** Inserting at index 0 makes backend/ the first search path. If any backend module is named `logging`, `os`, etc., the stdlib version is shadowed.
**How to avoid:** Use `sys.path.insert(0, ...)` but verify no backend module names conflict with stdlib. All current backend modules (`app`, `config`, `models`, `routes`, `services`) are project-specific names — no conflict.

### Pitfall 4: t-SNE non-determinism masking the sensitivity effect
**What goes wrong:** Two runs of the pipeline, even after bumping interaction counts, look qualitatively similar but the bumped pair doesn't appear obviously closer, making the sensitivity demo unconvincing.
**Why it happens:** t-SNE uses `random_state=42` so coordinates are reproducible within a run, but the scale and orientation can differ across runs. Two plots on different coordinate systems look hard to compare.
**How to avoid:** In the sensitivity demo, display both plots on the same figure with the same axis limits. Or better: instead of visual comparison, print euclidean distances: "Before bump: distance(Alex, Skyler) = X.XX. After bump: distance = Y.YY". This makes the quantitative effect unambiguous. The scatter plot is still shown, but the text output proves sensitivity.
**Warning signs:** The two scatter plots look rotated or flipped relative to each other.

### Pitfall 5: Forgetting to restore bumped interaction counts
**What goes wrong:** After the demo runs and bumps counts for two users, Supabase retains the inflated counts. Future pipeline runs (including the scheduler) produce incorrect results for those users.
**Why it happens:** The demo script never restores the original values.
**How to avoid:** Save original counts before bumping, then restore at end of script using a `try/finally` block.
**Warning signs:** Running the demo twice produces increasingly extreme positions for the demo pair.

### Pitfall 6: Notebook import path depends on working directory
**What goes wrong:** Notebook cells fail with `ModuleNotFoundError: No module named 'services'` when the notebook is opened from a directory other than `scripts/`.
**Why it happens:** Jupyter sets the kernel's cwd to the notebook file's directory only sometimes. If Jupyter was launched from project root, cwd is project root, not `scripts/`.
**How to avoid:** Use `__file__` is not available in notebooks. Instead, use:
```python
import os
BACKEND_DIR = os.path.abspath(os.path.join(os.getcwd(), "..", "backend"))
sys.path.insert(0, BACKEND_DIR)
```
But this is fragile. The cleanest approach: add a setup cell at the top of the notebook that uses `pathlib` to resolve relative to a known anchor, and document "launch Jupyter from the project root: `cd /path/to/sixDegrees && jupyter notebook`".

---

## Code Examples

Verified patterns from codebase inspection and official matplotlib docs:

### Complete test_map.py Structure
```python
#!/usr/bin/env python3
"""
scripts/test_map.py
Demonstrates the People Map algorithm against live Supabase data.
Usage: cd /path/to/sixDegrees && python scripts/test_map.py
"""
import os
import sys

# Make backend modules importable
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, BACKEND_DIR)

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(BACKEND_DIR, ".env"))

import matplotlib
matplotlib.use("MacOSX")   # or omit; let matplotlib choose on macOS
import matplotlib.pyplot as plt

from services.map_pipeline import run_pipeline_for_user
from services.map_pipeline.data_fetcher import fetch_all
from config.supabase import get_supabase_client

DEMO_CENTER_USER = "3561ceb0-d433-437d-8a4f-08da002dff50"   # Alex Rivera
BUMP_USER_A = "3561ceb0-d433-437d-8a4f-08da002dff50"        # Alex Rivera (Outdoors)
BUMP_USER_B = "af17902c-723d-4a32-a5a1-93d9fb7777ee"        # Skyler Thompson (Tech)

TIER_COLORS = {1: "#e74c3c", 2: "#3498db", 3: "#95a5a6"}

def fetch_display_names() -> dict[str, str]:
    """Return {user_id: display_name} for all users."""
    sb = get_supabase_client()
    rows = sb.table("user_profiles").select("user_id, display_name").execute().data
    return {r["user_id"]: r["display_name"] for r in rows}

def run_and_get_coords(center_user_id: str) -> list[dict]:
    """Run the full pipeline and return translated coordinates with display_names."""
    run_pipeline_for_user(center_user_id)
    sb = get_supabase_client()
    rows = (
        sb.table("map_coordinates")
        .select("other_user_id, x, y, tier")
        .eq("center_user_id", center_user_id)
        .eq("is_current", True)
        .execute()
    ).data
    names = fetch_display_names()
    return [
        {**r, "user_id": r["other_user_id"], "display_name": names.get(r["other_user_id"], "")}
        for r in rows
    ]

def plot_map(coords, title, ax):
    """Plot coordinates on given axes."""
    for tier in [1, 2, 3]:
        pts = [c for c in coords if c["tier"] == tier]
        if pts:
            ax.scatter([p["x"] for p in pts], [p["y"] for p in pts],
                       c=TIER_COLORS[tier], label=f"Tier {tier}", s=80, alpha=0.8)
        for p in pts:
            ax.annotate(p["display_name"], (p["x"], p["y"]),
                        xytext=(5, 5), textcoords="offset points", fontsize=7)
    ax.scatter(0, 0, c="black", marker="*", s=200, label="Center (Alex)", zorder=5)
    ax.set_title(title)
    ax.legend(fontsize=8)

def get_interaction(uid_a, uid_b):
    uid_a, uid_b = min(uid_a, uid_b), max(uid_a, uid_b)
    sb = get_supabase_client()
    rows = (sb.table("interactions")
            .select("likes_count")
            .eq("user_id_a", uid_a).eq("user_id_b", uid_b)
            .execute()).data
    return rows[0]["likes_count"] if rows else 0

def set_likes(uid_a, uid_b, count):
    uid_a, uid_b = min(uid_a, uid_b), max(uid_a, uid_b)
    get_supabase_client().table("interactions").upsert(
        {"user_id_a": uid_a, "user_id_b": uid_b, "likes_count": count},
        on_conflict="user_id_a,user_id_b"
    ).execute()

if __name__ == "__main__":
    # ── Baseline plot ──────────────────────────────────────────────────────
    print("Running pipeline (baseline)...")
    baseline_coords = run_and_get_coords(DEMO_CENTER_USER)

    original_likes = get_interaction(BUMP_USER_A, BUMP_USER_B)
    print(f"Baseline likes(Alex, Skyler) = {original_likes}")

    # ── Bump interaction and re-run ────────────────────────────────────────
    print("Bumping interaction count between Alex and Skyler to 60...")
    set_likes(BUMP_USER_A, BUMP_USER_B, 60)

    try:
        print("Running pipeline (bumped)...")
        bumped_coords = run_and_get_coords(DEMO_CENTER_USER)

        # ── Side-by-side plot ──────────────────────────────────────────────
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))
        plot_map(baseline_coords, "Baseline: Alex's People Map", ax1)
        plot_map(bumped_coords, f"After bumping Alex–Skyler likes to 60", ax2)
        plt.suptitle("People Map: Sensitivity Demonstration", fontsize=14)
        plt.tight_layout()
        plt.show()

    finally:
        # Restore original counts
        print(f"Restoring likes to {original_likes}...")
        set_likes(BUMP_USER_A, BUMP_USER_B, original_likes)
        print("Done.")
```

### Notebook First Cell (Setup)
```python
# Cell 1 — Setup (run this first)
import os
import sys

# Resolve backend path relative to project root
# Assumption: Jupyter launched from project root (cd /path/to/sixDegrees && jupyter notebook)
BACKEND_DIR = os.path.abspath("backend")
sys.path.insert(0, BACKEND_DIR)

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(BACKEND_DIR, ".env"))

%matplotlib inline
import matplotlib.pyplot as plt
print(f"Backend path: {BACKEND_DIR}")
print(f"Environment loaded: {bool(os.getenv('SUPABASE_URL'))}")
```

### Heatmap for Distance Matrix (Notebook Stage 3)
```python
import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(combined_dist_matrix, cmap="viridis", vmin=0, vmax=1)
ax.set_title("Combined Distance Matrix (α=0.6, β=0.4)")
plt.colorbar(im, ax=ax)
plt.tight_layout()
plt.show()
```

### API_CONTRACT.md — Required Sections
The document must cover:
1. **Base URL** — `http://localhost:8000` (local dev)
2. **Authentication** — `Authorization: Bearer <supabase_jwt>` header; how to get the JWT (from Supabase Auth session)
3. **Endpoints (6 total):**
   - `GET /map/{user_id}` — response shape with nested coordinates array
   - `POST /map/trigger/{user_id}` — no body; returns same shape as GET
   - `POST /interactions/like` — `{"target_user_id": "uuid"}` body; JWT required
   - `POST /interactions/comment` — same body shape
   - `POST /interactions/dm` — same body shape
   - `PUT /profile` — all optional profile fields; JWT required; only own profile
4. **Error shapes** — 401 (missing/invalid JWT), 403 (wrong user), 404 (no map), 422 (N<10), 400 (self-interaction)
5. **Notes** — canonical pair ordering, single-worker constraint, map freshness

### DB_SCHEMA.md — Required Tables
Three tables from setup_tables.sql, confirmed against data_fetcher.py and seed_db.py:

**user_profiles:**
```
user_id         UUID PRIMARY KEY
display_name    TEXT
interests       TEXT[]
location_city   TEXT
location_state  TEXT
age             INTEGER
languages       TEXT[]
field_of_study  TEXT
industry        TEXT
education_level TEXT
timezone        TEXT
updated_at      TIMESTAMPTZ DEFAULT now()
```

**interactions:**
```
user_id_a       UUID NOT NULL  (canonical: user_id_a < user_id_b enforced by CHECK)
user_id_b       UUID NOT NULL
likes_count     INTEGER DEFAULT 0
comments_count  INTEGER DEFAULT 0
dm_count        INTEGER DEFAULT 0
last_updated    TIMESTAMPTZ DEFAULT now()
PRIMARY KEY     (user_id_a, user_id_b)
```

**map_coordinates:**
```
id              UUID DEFAULT gen_random_uuid() PRIMARY KEY
center_user_id  UUID NOT NULL
other_user_id   UUID NOT NULL
x               FLOAT
y               FLOAT
tier            INTEGER   (1, 2, or 3)
computed_at     TIMESTAMPTZ DEFAULT now()
is_current      BOOLEAN DEFAULT true
INDEX on        (center_user_id, is_current)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `%matplotlib notebook` (interactive) | `%matplotlib inline` (static) | Jupyter 6+ | Inline is simpler, no widget overhead, works in any Jupyter version |
| `plt.savefig()` for headless | `plt.show()` on macOS | N/A | On macOS with display, `plt.show()` opens an interactive window; no need to save |
| Manual `os.path.join()` for .env | `find_dotenv()` from python-dotenv | python-dotenv 1.0 | `find_dotenv()` walks parent dirs automatically |
| `n_iter` parameter in TSNE | `max_iter` | sklearn 1.5+ | `n_iter` causes DeprecationWarning in 1.8.0; already using `max_iter` in tsne_projector.py |

**Deprecated/outdated:**
- `%matplotlib notebook`: Creates interactive widget plots — heavier, not needed for this demo. Use `%matplotlib inline`.
- `ipykernel` 7.x with Python 3.14: Known broken. Use 6.30.1 specifically.

---

## Open Questions

1. **Does matplotlib `plt.show()` work interactively on this machine?**
   - What we know: macOS with a display and Python 3.14 — matplotlib 3.10 ships a wheel, should work.
   - What's unclear: Whether the MacOSX backend is properly configured in the venv. May need `pip install pyobjc-framework-cocoa` if the MacOSX backend is missing.
   - Recommendation: Test `import matplotlib; matplotlib.pyplot.plot([1]); matplotlib.pyplot.show()` immediately after installation. If it hangs, fall back to `matplotlib.use("Agg")` and save to PNG instead of displaying.

2. **Should demo packages go in requirements.txt or a separate demo-requirements.txt?**
   - What we know: `matplotlib`, `jupyter`, `ipykernel==6.30.1` are demo-only, not needed for the FastAPI server.
   - What's unclear: Team's preference for requirements file structure.
   - Recommendation: Add to `requirements.txt` under a `# Demo deliverables` comment. This keeps installation simple for the reviewer. The CLAUDE.md already documents `pip install -r requirements.txt` as the setup command.

3. **Does the sensitivity demo need to run a fresh `run_pipeline_for_user()` call?**
   - What we know: `map_coordinates` stores precomputed values; `run_pipeline_for_user()` triggers recomputation and writes fresh rows (marking old ones `is_current=false`).
   - What's unclear: Nothing — the answer is yes, the script must call `run_pipeline_for_user()` after bumping counts for the effect to appear in coordinates.
   - Recommendation: Always call `run_pipeline_for_user()` after any interaction count change. This is already the pattern.

---

## Sources

### Primary (HIGH confidence)
- Codebase direct inspection — `backend/services/map_pipeline/__init__.py`, `pipeline.py`, `data_fetcher.py`, `origin_translator.py`, `routes/map.py`, `routes/interactions.py`, `routes/profile.py`, `routes/deps.py`, `config/algorithm.py`, `config/supabase.py`, `models/user.py`, `scripts/seed_db.py` — complete understanding of existing API surface
- `backend/requirements.txt` and venv `site-packages/` — confirmed installed packages: numpy 2.4.2, scikit-learn 1.8.0, scipy 1.17.1; matplotlib and jupyter NOT yet installed
- `backend/.env.example` — confirmed env var names: `SUPABASE_URL`, `SUPABASE_KEY`
- [matplotlib 3.10 official docs](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.scatter.html) — scatter, annotate, legend patterns (HIGH — official docs)
- [matplotlib Python 3.14 wheel availability](https://pypi.org/project/matplotlib/) — confirmed wheel for Python 3.14 in matplotlib 3.10.x (HIGH — PyPI official)

### Secondary (MEDIUM confidence)
- [Jupyter community forum: Python 3.14 kernel issue](https://discourse.jupyter.org/t/notebook-for-python-3-14-0-wont-connect-to-kernel/38023) — ipykernel==6.30.1 workaround confirmed by multiple community members (MEDIUM — community, not official docs)
- [pyreadiness.org/3.14](http://pyreadiness.org/3.14/) — confirmed jupyter-core and notebook not yet declaring Python 3.14 support; matplotlib confirmed compatible (MEDIUM — tracking site, cross-refs PyPI classifiers)

### Tertiary (LOW confidence)
- WebSearch results for matplotlib annotation patterns — multiple sources agree on `ax.annotate()` with `textcoords="offset points"` (LOW → elevated to MEDIUM by consistency across sources)

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — directly verified against venv site-packages and PyPI
- Architecture patterns: HIGH — derived directly from existing codebase structure
- Jupyter Python 3.14 pitfall: MEDIUM — community-confirmed workaround, not official Jupyter docs
- matplotlib patterns: HIGH — official docs + direct code inspection of what the pipeline returns

**Research date:** 2026-02-23
**Valid until:** 2026-03-23 (stable libraries; ipykernel/Python 3.14 situation may improve sooner)
