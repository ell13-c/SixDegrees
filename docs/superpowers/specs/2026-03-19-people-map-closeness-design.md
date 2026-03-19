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

---

## Architecture

### Components

**`PeopleMap.vue`** — minimal changes only:
- Add toggle UI: `[ Connections ] [ Closeness ]` below the title, above the legend
- Conditionally render existing SVG (Connections) or `<ClosenessMap>` (Closeness)
- Hide tier legend when Closeness is active
- Pass `rawCoordinates` and `computedAt` as props to `ClosenessMap`
- All existing logic (fetchMap, triggerAndReload, resize, stars, mock data) untouched

**`ClosenessMap.vue`** — new component:
- Props: `nodes` (array of `{user_id, x, y, tier, nickname, display_name}`), `computedAt`
- Plots nodes at real scaled `x, y` positions
- Same SVG canvas dimensions and starfield background as existing map

### API wiring
The existing real API call is already written but commented out in `PeopleMap.vue`. Uncomment and wire it up:
- `GET /map/{user_id}` with Supabase auth token on mount
- 404 response → auto-trigger `POST /map/trigger/{user_id}` then reload
- "Refresh Map" button → `POST /map/trigger/{user_id}` → reload
- Both views share the single fetched `rawCoordinates` array — no extra fetch

---

## Closeness Map: Node Positioning

### Coordinate scaling
t-SNE values are small floats (roughly `-1` to `1`). Scale to SVG canvas:
```
maxMagnitude = max(sqrt(x² + y²)) across all nodes
screenX = centerX + (x / maxMagnitude) * maxRadius
screenY = centerY + (y / maxMagnitude) * maxRadius
```
The furthest node sits near the canvas edge. The closest node sits near center. YOU always at `(centerX, centerY)`.

### Node coloring
Distance from origin = `sqrt(x² + y²)`, normalized 0→1 across all nodes.
- Distance 0 (closest) → `#60d4f7` (bright cyan — same as existing map's inner tier)
- Distance 1 (furthest) → `#1e3a5f` (dim blue)
- Interpolated linearly between the two

### Lines
Draw a line from YOU to each node, colored by that node's distance color, low opacity (matching existing map's line style).

---

## Interactions

| Action | Behavior |
|--------|----------|
| Hover node | Show tooltip: name only (same style as existing map) |
| Click node | `router.push(/profile/${user_id})` |
| YOU node | Fixed center, glowing white circle (identical to existing map) |
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
            └─ 404 → POST /map/trigger/{user_id} → reload
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

### Backend tests
No new backend tests needed — `ego_map.py` and `interaction_refinement.py` are already well covered by existing test suites.

---

## What is NOT changing

- `PeopleMap.vue` existing ring visualization — untouched
- Backend pipeline, API, ego_map — untouched
- Tier legend (hidden on Closeness view, visible on Connections view)
- All existing mock data (retained for Connections view until backend is confirmed stable)
