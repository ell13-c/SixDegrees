# People Map — Closeness View Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "Closeness" tab to the existing People Map page that plots users at their real t-SNE coordinates (encoding profile similarity + interaction counts), alongside the existing ring-based "Connections" view.

**Architecture:** A new `ClosenessMap.vue` component receives `rawCoordinates` as a prop and scales `x, y` values to SVG canvas coordinates — the closest users appear near center, the furthest near the edge. `PeopleMap.vue` gets a two-tab toggle ("Connections" / "Closeness") and has its mock `fetchMap` replaced with the real API call. Both views share one fetch.

**Tech Stack:** Vue 3 Composition API, Vitest + @vue/test-utils, SVG, Supabase JS client (`supabase.auth`), FastAPI backend at `GET /map/{user_id}` and `POST /map/trigger/{user_id}`.

**Spec:** `docs/superpowers/specs/2026-03-19-people-map-closeness-design.md`

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `frontend/src/components/ClosenessMap.vue` | New Closeness view — scales x,y → screen coords, renders nodes by distance color |
| Modify | `frontend/src/views/PeopleMap.vue` | Add toggle, wire real API, pass `rawCoordinates` + `svgW`/`svgH` to ClosenessMap |
| Create | `frontend/src/tests/map.test.js` | Tests for ClosenessMap rendering and PeopleMap toggle + API wiring |

---

## Task 1: Build ClosenessMap.vue

**Files:**
- Create: `frontend/src/components/ClosenessMap.vue`
- Create: `frontend/src/tests/map.test.js`

### Background
The component receives `rawCoordinates` — the array from `GET /map/{user_id}` response. Each entry is `{user_id, x, y, tier, nickname, display_name}`. The requesting user is always at `x=0, y=0`. All other nodes have ego-centered coordinates whose magnitude encodes real closeness (t-SNE + interaction refinement).

Key formula:
```
maxMagnitude = max(1e-9, max of sqrt(x²+y²) across all non-YOU nodes)
px = centerX + (x / maxMagnitude) * maxRadius
py = centerY + (y / maxMagnitude) * maxRadius
```

Color interpolation by normalized distance (0=closest, 1=furthest):
- 0 → `rgb(96, 212, 247)` (bright cyan)
- 1 → `rgb(30, 58, 95)` (dim blue)

- [ ] **Step 1.1: Create the test file with a failing test for node count**

Create `frontend/src/tests/map.test.js` with this exact content:

```js
import { describe, it, expect, vi, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'

// vi.mock is hoisted by Vitest before imports — safe to place here
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn() }),
  useRoute: () => ({ params: {} }),
}))

vi.mock('../lib/supabase', () => ({
  supabase: {
    auth: {
      getUser: vi.fn().mockResolvedValue({ data: { user: { id: 'user-1' } } }),
      getSession: vi.fn().mockResolvedValue({ data: { session: { access_token: 'tok' } } }),
    },
  },
}))

import ClosenessMap from '../components/ClosenessMap.vue'

const MOCK_COORDS = [
  { user_id: 'you',   x: 0.0,  y: 0.0,  tier: 1, nickname: 'You',   display_name: 'You'   },
  { user_id: 'alice', x: 0.3,  y: 0.2,  tier: 1, nickname: 'Alice', display_name: 'Alice' },
  { user_id: 'bob',   x: -0.8, y: 0.6,  tier: 2, nickname: 'Bob',   display_name: 'Bob'   },
  { user_id: 'carol', x: 0.1,  y: -0.9, tier: 3, nickname: 'Carol', display_name: 'Carol' },
]

describe('ClosenessMap', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('renders one node-group per non-YOU coordinate', () => {
    const wrapper = mount(ClosenessMap, {
      props: { rawCoordinates: MOCK_COORDS, svgW: 800, svgH: 560 },
    })
    expect(wrapper.findAll('.cl-node-group')).toHaveLength(3)
  })
  // more tests added in Step 1.4
})
```

- [ ] **Step 1.2: Run the test — expect FAIL (component doesn't exist yet)**

```bash
cd frontend && npm test -- map.test.js
```
Expected: `Cannot find module '../components/ClosenessMap.vue'`

- [ ] **Step 1.3: Create ClosenessMap.vue**

Create `frontend/src/components/ClosenessMap.vue`:

```vue
<template>
  <svg class="map-svg" :viewBox="`0 0 ${svgW} ${svgH}`" :width="svgW" :height="svgH">
    <defs>
      <filter id="cl-glow-center" x="-80%" y="-80%" width="260%" height="260%">
        <feGaussianBlur stdDeviation="10" result="blur" />
        <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
      </filter>
      <radialGradient id="cl-bg-grad" cx="50%" cy="50%" r="60%">
        <stop offset="0%" stop-color="#1a1f3a" />
        <stop offset="100%" stop-color="#0a0c18" />
      </radialGradient>
    </defs>

    <rect width="100%" height="100%" fill="url(#cl-bg-grad)" rx="16" />

    <circle
      v-for="s in stars" :key="s.id"
      :cx="s.x * svgW" :cy="s.y * svgH" :r="s.r"
      :fill="`rgba(255,255,255,${s.o})`"
    />

    <line
      v-for="n in scaledNodes" :key="'cl-edge-'+n.user_id"
      :x1="cx" :y1="cy" :x2="n.px" :y2="n.py"
      :stroke="n.color"
      :stroke-opacity="hoveredId && hoveredId !== n.user_id ? 0.05 : 0.25"
      :stroke-width="hoveredId === n.user_id ? 1.8 : 0.8"
      stroke-linecap="round"
    />

    <g
      v-for="n in scaledNodes" :key="'cl-node-'+n.user_id"
      :transform="`translate(${n.px}, ${n.py}) scale(${hoveredId === n.user_id ? 1.3 : 1})`"
      class="cl-node-group"
      @mouseenter="hoveredId = n.user_id"
      @mouseleave="hoveredId = null"
      @click="goToProfile(n.user_id)"
      style="cursor:pointer"
    >
      <circle r="8" :fill="n.color" :fill-opacity="hoveredId === n.user_id ? 1 : 0.85" />
      <text
        text-anchor="middle" dominant-baseline="central"
        font-size="7" fill="white" font-weight="700" font-family="monospace"
        style="pointer-events:none;user-select:none"
      >{{ initials(n.display_name) }}</text>
    </g>

    <g
      v-if="hoveredNode"
      style="pointer-events: none"
      :transform="`translate(${tooltipX(hoveredNode)}, ${tooltipY(hoveredNode)})`"
    >
      <rect :x="-70" y="-40" width="140" height="36" rx="8" fill="#1e2540" stroke="#ffffff20" stroke-width="1" />
      <text text-anchor="middle" y="-26" font-size="11" fill="white" font-family="monospace" font-weight="600">
        {{ hoveredNode.display_name || 'Unknown' }}
      </text>
    </g>

    <g :transform="`translate(${cx}, ${cy})`">
      <circle r="34" fill="#ffffff" fill-opacity="0.03" filter="url(#cl-glow-center)" class="cl-pulse-node" />
      <circle r="22" fill="#e8f4ff" filter="url(#cl-glow-center)" />
      <circle r="17" fill="#c5e4ff" />
      <text
        text-anchor="middle" dominant-baseline="central"
        font-size="8" fill="#0a1628" font-weight="800" font-family="monospace"
        style="pointer-events:none"
      >YOU</text>
    </g>
  </svg>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  rawCoordinates: { type: Array, required: true },
  svgW: { type: Number, default: 800 },
  svgH: { type: Number, default: 560 },
})

const router = useRouter()
const hoveredId = ref(null)

const cx = computed(() => props.svgW / 2)
const cy = computed(() => props.svgH / 2)
const maxRadius = computed(() => Math.min(props.svgW, props.svgH) / 2 - 52)

const stars = Array.from({ length: 130 }, (_, i) => ({
  id: i,
  x: Math.sin(i * 7.3) * 0.5 + 0.5,
  y: Math.cos(i * 3.7) * 0.5 + 0.5,
  r: Math.sin(i) * 0.5 + 0.7,
  o: Math.cos(i * 2.1) * 0.2 + 0.25,
}))

const scaledNodes = computed(() => {
  const others = props.rawCoordinates.filter(c => !(c.x === 0 && c.y === 0))
  if (!others.length) return []
  const magnitudes = others.map(c => Math.sqrt(c.x * c.x + c.y * c.y))
  const maxMag = Math.max(1e-9, ...magnitudes)
  return others.map((c, i) => ({
    ...c,
    px: cx.value + (c.x / maxMag) * maxRadius.value,
    py: cy.value + (c.y / maxMag) * maxRadius.value,
    color: distanceColor(magnitudes[i] / maxMag),
  }))
})

const hoveredNode = computed(() =>
  hoveredId.value ? scaledNodes.value.find(n => n.user_id === hoveredId.value) : null
)

function distanceColor(t) {
  const r = Math.round(96 + (30 - 96) * t)
  const g = Math.round(212 + (58 - 212) * t)
  const b = Math.round(247 + (95 - 247) * t)
  return `rgb(${r},${g},${b})`
}

function initials(name) {
  if (!name) return '?'
  return name.trim().split(/\s+/).map(w => w[0]).join('').toUpperCase().slice(0, 2)
}

function tooltipX(node) { return Math.min(Math.max(node.px, 70), props.svgW - 70) }
function tooltipY(node) { return node.py < 100 ? node.py + 60 : node.py - 60 }
function goToProfile(userId) { router.push(`/profile/${userId}`) }
</script>

<style scoped>
.map-svg {
  width: 100%;
  height: auto;
  border-radius: 16px;
  border: 1px solid #181e38;
  box-shadow:
    0 0 0 1px #0d1124,
    0 0 80px rgba(96, 212, 247, 0.04),
    0 8px 60px rgba(0, 0, 0, 0.7);
  display: block;
}
.cl-node-group {
  transition: transform 0.15s ease;
  transform-box: fill-box;
  transform-origin: center;
}
@keyframes cl-pulse {
  0%, 100% { opacity: 0.18; }
  50% { opacity: 0.06; }
}
.cl-pulse-node { animation: cl-pulse 3.5s ease-in-out infinite; }
</style>
```

- [ ] **Step 1.4: Add remaining ClosenessMap tests**

In `frontend/src/tests/map.test.js`, insert these `it(...)` blocks **before** the closing `})` of the `describe('ClosenessMap', ...)` block (i.e. before the last `})` in the file at this point):

```js
  it('renders YOU text at the center node', () => {
    const wrapper = mount(ClosenessMap, {
      props: { rawCoordinates: MOCK_COORDS, svgW: 800, svgH: 560 },
    })
    expect(wrapper.text()).toContain('YOU')
  })

  it('renders a line for each non-YOU node', () => {
    const wrapper = mount(ClosenessMap, {
      props: { rawCoordinates: MOCK_COORDS, svgW: 800, svgH: 560 },
    })
    expect(wrapper.findAll('line')).toHaveLength(3)
  })

  it('handles empty rawCoordinates gracefully', () => {
    const wrapper = mount(ClosenessMap, {
      props: { rawCoordinates: [], svgW: 800, svgH: 560 },
    })
    expect(wrapper.findAll('.cl-node-group')).toHaveLength(0)
    expect(wrapper.text()).toContain('YOU')
  })

  it('handles all-zero coordinates without crashing (maxMagnitude guard)', () => {
    const allZero = [
      { user_id: 'you', x: 0, y: 0, tier: 1, display_name: 'You' },
      { user_id: 'a',   x: 0, y: 0, tier: 1, display_name: 'A'   },
    ]
    expect(() => mount(ClosenessMap, {
      props: { rawCoordinates: allZero, svgW: 800, svgH: 560 },
    })).not.toThrow()
  })
```

- [ ] **Step 1.5: Run all ClosenessMap tests — expect PASS**

```bash
cd frontend && npm test -- map.test.js
```
Expected: all 5 tests in `describe('ClosenessMap')` pass

- [ ] **Step 1.6: Commit**

```bash
git add frontend/src/components/ClosenessMap.vue frontend/src/tests/map.test.js
git commit -m "feat: add ClosenessMap component with scaled x,y positioning"
```

---

## Task 2: Add toggle to PeopleMap.vue

**Files:**
- Modify: `frontend/src/views/PeopleMap.vue`
- Modify: `frontend/src/tests/map.test.js`

### Background
The toggle is a reactive `activeView` ref (`'connections'` | `'closeness'`). The existing template has a `v-if/v-else-if/v-else` chain for loading/error/empty/canvas states. The correct way to split the final `v-else` (canvas) into two views is to wrap it in a `<template v-else>` containing `v-if`/`v-else` on `activeView` — this keeps all four top-level branches valid Vue 3.

The existing `nodes` computed property (ring layout) is untouched. The Connections view renders when `activeView === 'connections'`; the Closeness view renders when `activeView === 'closeness'`.

`PeopleMap.vue` passes `:rawCoordinates="rawCoordinates"`, `:svgW="svgW"`, `:svgH="svgH"` as props. In Vue 3 templates, refs are auto-unwrapped, so passing `svgW` (a `ref`) as `:svgW="svgW"` works correctly without `.value`.

- [ ] **Step 2.1: Add failing toggle tests**

Append this new `describe` block at the **end** of `frontend/src/tests/map.test.js` (after the closing `})` of `describe('ClosenessMap', ...)`):

```js
import PeopleMap from '../views/PeopleMap.vue'

describe('PeopleMap toggle', () => {
  afterEach(() => vi.unstubAllGlobals())

  function mountWithFetch(responseOverride = {}) {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: vi.fn().mockResolvedValue({
        coordinates: [],
        computed_at: new Date().toISOString(),
        ...responseOverride,
      }),
    }))
    return mount(PeopleMap)
  }

  async function flush() {
    await new Promise(r => setTimeout(r, 50))
  }

  it('shows Connections view by default (ClosenessMap not rendered)', async () => {
    const wrapper = mountWithFetch()
    await flush()
    expect(wrapper.findComponent(ClosenessMap).exists()).toBe(false)
  })

  it('shows ClosenessMap after clicking Closeness button', async () => {
    const wrapper = mountWithFetch()
    await flush()
    await wrapper.find('[data-view="closeness"]').trigger('click')
    expect(wrapper.findComponent(ClosenessMap).exists()).toBe(true)
  })

  it('hides ClosenessMap after switching back to Connections', async () => {
    const wrapper = mountWithFetch()
    await flush()
    await wrapper.find('[data-view="closeness"]').trigger('click')
    await wrapper.find('[data-view="connections"]').trigger('click')
    expect(wrapper.findComponent(ClosenessMap).exists()).toBe(false)
  })
})
```

**Note:** `ClosenessMap` is already imported at the top of the file. `findComponent(ClosenessMap)` uses the imported reference directly — this is more reliable than `findComponent({ name: 'ClosenessMap' })` with `<script setup>` components.

- [ ] **Step 2.2: Run — expect FAIL**

```bash
cd frontend && npm test -- map.test.js
```
Expected: FAIL — `[data-view="closeness"]` not found

- [ ] **Step 2.3: Add import and toggle state to PeopleMap.vue**

At the top of `<script setup>` in `PeopleMap.vue`, add:
```js
import ClosenessMap from '../components/ClosenessMap.vue'
import { supabase } from '../lib/supabase.js'
```

After the line `const hoveredId = ref(null)`, add:
```js
const activeView = ref('connections')
```

- [ ] **Step 2.4: Replace the map header block in the template**

In `PeopleMap.vue`'s `<template>`, find the `<div class="map-header">` block and replace it entirely with:

```html
<div class="map-header">
  <h1 class="map-title">People Map</h1>
  <p class="map-subtitle">Your Social Map</p>
  <div class="view-controls">
    <div class="toggle-group">
      <button
        class="toggle-btn"
        :class="{ active: activeView === 'connections' }"
        data-view="connections"
        @click="activeView = 'connections'"
      >Connections</button>
      <button
        class="toggle-btn"
        :class="{ active: activeView === 'closeness' }"
        data-view="closeness"
        @click="activeView = 'closeness'"
      >Closeness</button>
    </div>
    <button class="refresh-btn" @click="triggerAndReload" :disabled="loading || triggering">
      <span v-if="triggering" class="spinner" />
      <span v-else>↻</span>
      {{ triggering ? 'Computing…' : 'Refresh Map' }}
    </button>
  </div>
</div>
```

- [ ] **Step 2.5: Add v-if to the tier legend**

Find `<div class="legend">` and change it to:
```html
<div class="legend" v-if="activeView === 'connections'">
```

- [ ] **Step 2.6: Restructure the canvas-wrap block**

The current template ends with this chain (simplified):
```html
<div v-if="loading" ...>
<div v-else-if="error" ...>
<div v-else-if="!nodes.length" ...>
<div v-else class="canvas-wrap" ref="canvasWrap">   ← THIS IS THE BLOCK TO CHANGE
  <svg ...>...</svg>
  <div class="map-footer">...</div>
</div>
```

Replace the entire final `<div v-else class="canvas-wrap" ...>...</div>` block with:

```html
<template v-else>
  <div v-if="activeView === 'connections'" class="canvas-wrap" ref="canvasWrap">
    <svg ref="svgEl" class="map-svg" :viewBox="`0 0 ${svgW} ${svgH}`" :width="svgW" :height="svgH">
      <!-- leave all existing SVG content exactly as-is -->
    </svg>
    <div class="map-footer">
      <span>{{ nodes.length }} connection{{ nodes.length !== 1 ? 's' : '' }}</span>
      <span v-if="computedAt"> · Updated {{ timeAgo(computedAt) }}</span>
      <span class="demo-badge">✦ Demo Mode</span>
    </div>
  </div>
  <div v-else class="canvas-wrap">
    <ClosenessMap
      :rawCoordinates="rawCoordinates"
      :svgW="svgW"
      :svgH="svgH"
    />
    <div class="map-footer">
      <span>{{ rawCoordinates.length > 0 ? rawCoordinates.length - 1 : 0 }} connection{{ rawCoordinates.length - 1 !== 1 ? 's' : '' }}</span>
      <span v-if="computedAt"> · Updated {{ timeAgo(computedAt) }}</span>
    </div>
  </div>
</template>
```

**Important:** The `<template v-else>` wrapper is a Vue 3 renderless wrapper — it produces no DOM element. Inside it, `v-if` / `v-else` on `activeView` works freely without conflicting with the outer chain.

- [ ] **Step 2.7: Add CSS for toggle controls**

Append to `<style scoped>` in `PeopleMap.vue`:

```css
.view-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.25rem;
  justify-content: center;
  flex-wrap: wrap;
}

.toggle-group {
  display: flex;
  border: 1px solid #252b50;
  border-radius: 999px;
  overflow: hidden;
}

.toggle-btn {
  padding: 0.5rem 1.25rem;
  background: transparent;
  color: #8090b4;
  border: none;
  font-family: 'DM Mono', monospace;
  font-size: 0.76rem;
  cursor: pointer;
  letter-spacing: 0.06em;
  transition: background 0.2s, color 0.2s;
}

.toggle-btn.active {
  background: #60d4f7;
  color: #0a0c18;
  font-weight: 600;
}

.toggle-btn:not(.active):hover {
  color: #60d4f7;
  background: rgba(96, 212, 247, 0.07);
}
```

- [ ] **Step 2.8: Run toggle tests — expect PASS**

```bash
cd frontend && npm test -- map.test.js
```
Expected: all tests pass

- [ ] **Step 2.9: Browser smoke test**

```bash
cd frontend && npm run dev
```
Open `http://localhost:5173/map`. Verify:
- Toggle buttons appear ("Connections" | "Closeness") alongside "Refresh Map"
- Clicking "Closeness" shows the ClosenessMap (YOU at center, mock nodes scattered by x,y)
- Clicking "Connections" returns to the original ring view
- Tier legend disappears on Closeness, reappears on Connections

- [ ] **Step 2.10: Commit**

```bash
git add frontend/src/views/PeopleMap.vue frontend/src/tests/map.test.js
git commit -m "feat: add Connections/Closeness toggle to PeopleMap"
```

---

## Task 3: Wire real API in PeopleMap.vue

**Files:**
- Modify: `frontend/src/views/PeopleMap.vue`
- Modify: `frontend/src/tests/map.test.js`

### Background
The real API call is already written but commented out in `PeopleMap.vue`. The `triggerAndReload` function uses mock data and needs to be replaced. Key behavior:
- `POST /map/trigger/{user_id}` returns the full map payload directly — **consume the response, do not fire a second GET**
- The `silent` parameter on the old `triggerAndReload` is dropped (it was only used to suppress the fake delay in mock mode)

### Auth pattern used in this codebase:
```js
const { data: { user } } = await supabase.auth.getUser()
const { data: { session } } = await supabase.auth.getSession()
```
`API_BASE` is already defined at the top of `PeopleMap.vue` as `import.meta.env.VITE_API_URL || 'http://localhost:8000'`.

- [ ] **Step 3.1: Add API wiring test**

Append this new `describe` block at the end of `frontend/src/tests/map.test.js`:

```js
describe('PeopleMap API wiring', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('calls trigger endpoint when GET /map returns 404, and uses trigger response directly', async () => {
    const triggerPayload = {
      coordinates: [{ user_id: 'user-1', x: 0, y: 0, tier: 1, display_name: 'Me' }],
      computed_at: new Date().toISOString(),
    }
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ ok: false, status: 404, json: vi.fn() })
      .mockResolvedValueOnce({ ok: true, status: 200, json: vi.fn().mockResolvedValue(triggerPayload) })
    vi.stubGlobal('fetch', fetchMock)

    mount(PeopleMap)
    await new Promise(r => setTimeout(r, 100))

    // First call: GET /map/user-1
    expect(fetchMock.mock.calls[0][0]).toContain('/map/user-1')
    expect(fetchMock.mock.calls[0][1]?.method).toBeUndefined() // GET has no explicit method

    // Second call: POST /map/trigger/user-1
    expect(fetchMock.mock.calls[1][0]).toContain('/map/trigger/user-1')
    expect(fetchMock.mock.calls[1][1]?.method).toBe('POST')

    // Only 2 calls total — no redundant second GET
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })
})
```

- [ ] **Step 3.2: Run — expect FAIL (still using mock fetchMap)**

```bash
cd frontend && npm test -- map.test.js
```
Expected: FAIL — fetch never called (mock data path used instead)

- [ ] **Step 3.3: Delete MOCK_CONNECTIONS**

In `PeopleMap.vue`, delete the entire `const MOCK_CONNECTIONS = [...]` block (lines ~255–279 — it starts with `// ─── MOCK DATA` and ends after the last `]`).

- [ ] **Step 3.4: Replace mock fetchMap with real API call**

Replace the entire `fetchMap` function (the one that calls `await new Promise(r => setTimeout(r, 1000))` and assigns `MOCK_CONNECTIONS`) with:

```js
async function fetchMap() {
  loading.value = true
  error.value = null
  try {
    const { data: { user } } = await supabase.auth.getUser()
    const { data: { session } } = await supabase.auth.getSession()
    if (!user || !session) { error.value = 'Not logged in.'; return }
    const res = await fetch(`${API_BASE}/map/${user.id}`, {
      headers: { Authorization: `Bearer ${session.access_token}` },
    })
    if (res.status === 404) { await triggerAndReload(); return }
    if (!res.ok) throw new Error(`Server error: ${res.status}`)
    const data = await res.json()
    rawCoordinates.value = data.coordinates || []
    computedAt.value = data.computed_at || null
  } catch (e) {
    error.value = e.message || 'Failed to load map.'
  } finally {
    loading.value = false
  }
}
```

- [ ] **Step 3.5: Replace mock triggerAndReload with real trigger call**

Replace the entire `triggerAndReload` function (the one that assigns `MOCK_CONNECTIONS` and uses `await new Promise(r => setTimeout(r, 800))`) with:

```js
async function triggerAndReload() {
  triggering.value = true
  error.value = null
  try {
    const { data: { user } } = await supabase.auth.getUser()
    const { data: { session } } = await supabase.auth.getSession()
    if (!user || !session) { error.value = 'Not logged in.'; return }
    const res = await fetch(`${API_BASE}/map/trigger/${user.id}`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${session.access_token}` },
    })
    if (!res.ok) throw new Error(`Trigger failed: ${res.status}`)
    const data = await res.json()
    rawCoordinates.value = data.coordinates || []
    computedAt.value = data.computed_at || null
  } catch (e) {
    error.value = e.message || 'Failed to compute map.'
  } finally {
    triggering.value = false
    loading.value = false
  }
}
```

Also delete the commented-out old `fetchMap` block (the `/* ... */` comment block below the mock `fetchMap`, lines ~293–316).

- [ ] **Step 3.6: Run all tests — expect PASS**

```bash
cd frontend && npm test -- map.test.js
```
Expected: all tests pass

- [ ] **Step 3.7: Run the full test suite to confirm no regressions**

```bash
cd frontend && npm test
```
Expected: all tests pass

- [ ] **Step 3.8: Commit**

```bash
git add frontend/src/views/PeopleMap.vue frontend/src/tests/map.test.js
git commit -m "feat: wire real API in PeopleMap, replace mock fetchMap and triggerAndReload"
```

---

## Task 4: Manual Visual Verification

**Files:** none (manual steps only)

### Background
Confirm the Closeness map visually reflects the algorithm output, and establish a baseline for the interaction-distance test.

- [ ] **Step 4.1: Start backend and frontend**

```bash
# Terminal 1 — backend (single worker only)
cd backend && source venv/bin/activate && uvicorn app:app --reload

# Terminal 2 — frontend
cd frontend && npm run dev
```

- [ ] **Step 4.2: Log in and open the People Map**

Navigate to `http://localhost:5173/map`. Log in if prompted. If the map shows "No connections yet", click "Refresh Map".

- [ ] **Step 4.3: Verify Connections view is unchanged**

The ring-based layout should look identical to before this feature was built. Tier legend visible. All existing behavior intact.

- [ ] **Step 4.4: Switch to Closeness view and verify layout**

Click "Closeness". Verify:
- YOU is at the center
- Nodes are **not** arranged in perfect rings — positions vary organically by t-SNE distance
- Nodes closest to center are bright cyan; outer nodes are dim blue
- Hovering a node shows their `display_name`
- Clicking a node navigates to `/profile/:userId`

- [ ] **Step 4.5: Interaction distance test**

1. Note the current position of two users on the Closeness map — take a screenshot
2. Create several likes, comments, or DMs between your account and one of those users
3. Click "Refresh Map" — wait for recompute
4. Switch to Closeness view — confirm the heavily-interacted user moved visibly closer to center
5. Save before/after screenshots

- [ ] **Step 4.6: Commit any fixes found during verification**

```bash
git add -p
git commit -m "fix: address issues found during visual verification"
```
