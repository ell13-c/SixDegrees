# People Map — Closeness View Design

**Date:** 2026-03-19
**Status:** Approved

---

## Overview

Add a "Closeness" view to the existing People Map page that plots users at their real t-SNE coordinates — encoding actual profile similarity and interaction counts — rather than forcing them onto fixed tier rings. The existing "Connections" view is left completely untouched.

---

## Background

### Existing "Connections" map
The current `PeopleMap.vue` (built by a teammate) renders a ring-based visualization: YOU at center, other users placed on fixed concentric rings by tier rank. The `x, y` from the backend are used only to determine the angle of each node around its ring. The radial distance — the most meaningful signal from the algorithm — is discarded.

### Why this matters
The backend pipeline does significant work:
- **t-SNE** places users with similar profiles close together in a shared 2D space
- **Interaction refinement** pulls frequently-interacting pairs closer (weighted by recency)
- The result: `x, y` coordinates that genuinely encode closeness

The Connections map ignores this. The Closeness map will use it directly.

### How the coordinate system works
1. **Nightly pipeline** — t-SNE runs on all users together → one global `x, y` row per user written to `map_coordinates` (N rows, not N²)
2. **At request time** — `ego_map.py` subtracts the requesting user's coordinates from all others → requesting user lands at `(0, 0)`, everyone else's `x, y` is relative to them
3. **What the API returns** — ego-centered coordinates already. YOU = `(0, 0)`. Nearby users = small magnitude. Distant users = large magnitude.

### Tier values in real API data
The real API (`ego_map.py`) assigns tiers 1, 2, and 3 only — never 0. Tier 0 ("Inner Circle") exists only in the existing mock data in `PeopleMap.vue` and does not appear in production API responses. The Closeness map does not use tiers for positioning or coloring — it uses Euclidean distance from origin exclusively.

---

## Architecture

### Components

**`PeopleMap.vue`** — minimal changes only:
- Add toggle UI: `[ Connections ] [ Closeness ]` — placed on the same row as the existing "Refresh Map" button, right-aligned or centered together
- Conditionally render existing SVG (Connections) or `<ClosenessMap>` (Closeness)
- Hide tier legend when Closeness is active
- Pass `rawCoordinates` and `computedAt` as props to `ClosenessMap` (use `rawCoordinates` — the array directly from the API response — not the projected `nodes` computed property which has `px/py` ring positions injected)
- All existing logic (fetchMap, triggerAndReload, resize, stars, mock data) untouched

**`ClosenessMap.vue`** — new component:
- Props: `rawCoordinates` (array of `{user_id, x, y, tier, nickname, display_name}`), `computedAt`
- Computes its own screen positions from `x, y` — does not use `px/py` from the parent
- Plots nodes at real scaled `x, y` positions
- Same SVG canvas dimensions and starfield background as existing map
- YOU node identified by coordinates `(0, 0)` (the requester is always at origin in the API response)

### API wiring
The existing real API call is already written but commented out in `PeopleMap.vue`. Uncomment and wire it up:
- `GET /map/{user_id}` with Supabase auth token on mount
- 404 response → auto-trigger `POST /map/trigger/{user_id}`; the trigger endpoint returns the full map payload directly — consume it immediately, do not fire a second GET
- "Refresh Map" button → `POST /map/trigger/{user_id}` → consume response directly (same pattern)
- Both views share the single fetched `rawCoordinates` array — no extra fetch

---

## Closeness Map: Node Positioning

### Coordinate scaling
t-SNE output magnitude is data-dependent and not bounded to any fixed range. Scale to SVG canvas using the actual data:
```
maxMagnitude = max(sqrt(x² + y²)) across all non-YOU nodes
             = max(1e-9, maxMagnitude)  ← guard against all-zero edge case
screenX = centerX + (x / maxMagnitude) * maxRadius
screenY = centerY + (y / maxMagnitude) * maxRadius
```
The furthest node sits near the canvas edge. The closest node sits near center. YOU always at `(centerX, centerY)`. The `1e-9` floor prevents division by zero when all nodes are at the origin (e.g., sparse early-stage data).

### Node coloring
Distance from origin = `sqrt(x² + y²)`, normalized 0→1 across all nodes.
- Distance 0 (closest) → `#60d4f7` (bright cyan — same as existing map's inner tier color)
- Distance 1 (furthest) → `#1e3a5f` (dim blue)
- Interpolated linearly between the two

### Lines
Draw a line from YOU to each node, colored by that node's distance color, low opacity (matching existing map's line style).

---

## Interactions

| Action | Behavior |
|--------|----------|
| Hover node | Show tooltip: `display_name` field (same style as existing map) |
| Click node | `router.push(/profile/${user_id})` |
| YOU node | Fixed center at origin `(0,0)`, glowing white circle (identical to existing map) |
| Toggle | Switch between Connections and Closeness views instantly |

---

## Visual Style

- Same dark background (`#0a0c18`), starfield, monospace font as existing map
- Same SVG border, shadow, rounded corners
- Toggle buttons: same pill/monospace style as existing UI elements
- Active tab highlighted, inactive dimmed
- Footer: connection count + last updated timestamp (same as existing)
- Demo badge removed from Closeness view once real API is wired up

---

## Data Flow

```
mount
  └─ fetchMap()
       └─ GET /map/{user_id}
            ├─ 200 → rawCoordinates = data.coordinates
            │         computedAt = data.computed_at
            │         ├─ Connections view: ring layout (existing)
            │         └─ Closeness view: x,y scaled layout (new)
            └─ 404 → POST /map/trigger/{user_id}
                       └─ 200 → rawCoordinates = response.coordinates
                                 computedAt = response.computed_at
                                 (no second GET needed — trigger returns full payload)

"Refresh Map" button
  └─ POST /map/trigger/{user_id}
       └─ 200 → rawCoordinates = response.coordinates  (consume directly)
```

---

## Testing

### Visual regression test (manual)
1. Pick two users, create heavy interactions between them (likes, comments, DMs)
2. Click "Refresh Map" to trigger pipeline recompute
3. Open Closeness map — confirm those two nodes are visually closer than before
4. Capture before/after screenshots as evidence

### Frontend component tests
- `ClosenessMap.vue`: given mock `rawCoordinates`, assert nodes render at scaled `x, y` positions (not fixed ring radii)
- `PeopleMap.vue`: toggling between Connections and Closeness renders the correct child component
- `PeopleMap.vue`: when `fetchMap` receives a 404, assert that `triggerAndReload` is called and `rawCoordinates` is populated from the trigger response (not a second GET)

### Backend tests
No new backend tests needed — `ego_map.py` and `interaction_refinement.py` are already well covered by existing test suites.

---

## What is NOT changing

- `PeopleMap.vue` existing ring visualization — untouched
- Backend pipeline, API, ego_map — untouched
- Tier legend (hidden on Closeness view, visible on Connections view)
- All existing mock data (retained for Connections view until backend is confirmed stable)
