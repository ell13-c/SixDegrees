# Requirements: SixDegrees

**Defined:** 2026-02-26
**Core Value:** A user opens the People Map and sees meaningful nearby people around themselves at (0,0), with stable daily-updated positions.

## v2.0 Requirements

Requirements for milestone v2.0 Global Coordinate Map Engine.

### Data Contract + Migration

- [ ] **DATA-01**: User map positions are stored as one global current row per user in `map_coordinates`.
- [ ] **DATA-02**: User map write path preserves exactly one previous coordinate snapshot (`prev_x`, `prev_y`) per user for motion continuity.
- [ ] **DATA-03**: User map reads/writes do not depend on legacy per-viewer map semantics.
- [ ] **DATA-04**: User map data version is explicit (`version_date`, `computed_at`) and returned in API metadata.
- [ ] **DATA-05**: User map persistence/update operations are executed through secured backend data-access interfaces consistent with existing runtime patterns.

### Algorithm Engine + Validation

- [ ] **ALGO-01**: User global position is computed from profile-vector manifold embedding that avoids full dense NxN distance materialization.
- [ ] **ALGO-02**: User global position is refined by sparse interaction graph forces using `interactions` counts and recency weighting.
- [ ] **ALGO-03**: User coordinate updates are bounded by movement-stability controls to prevent visual jitter.
- [ ] **ALGO-04**: User coordinate publish is blocked when validation gates detect invalid input, unstable embedding, or persistence mismatch.
- [ ] **ALGO-05**: User map compute run emits measurable quality/performance metrics and stores run-level diagnostics.

### Ego API + Suggestions

- [ ] **EGO-01**: User map response always places the requesting user exactly at `(0,0)`.
- [ ] **EGO-02**: User map includes only mutual friends (`profiles.friends` reciprocity) as primary visible nodes.
- [ ] **EGO-03**: User map node coordinates are translated at request time from global coordinates to requester-centered coordinates.
- [ ] **EGO-04**: User with empty/sparse mutual graph receives bounded fallback suggestions marked with `is_suggestion=true`.
- [ ] **EGO-05**: User map response remains backward-compatible for existing frontend usage while adding non-breaking metadata fields.

### Scheduler + Operations

- [ ] **OPS-01**: User global coordinates are recomputed by one daily batch schedule at fixed UTC time.
- [ ] **OPS-02**: User 7pm local-time jobs perform delivery/cache warm only and never trigger global recompute.
- [ ] **OPS-03**: User scheduler runtime prevents duplicate compute execution from multi-worker or restart conditions.
- [ ] **OPS-04**: User cache warm path (if enabled) is version-aware and invalidates stale payloads safely.

### Compatibility + Security

- [ ] **COMP-01**: User map endpoints enforce authenticated access and prevent unauthorized cross-user map reads.
- [ ] **COMP-02**: User suggestion payload excludes sensitive profile fields beyond allowed API contract.
- [ ] **COMP-03**: User milestone rollout preserves existing frontend behavior without frontend code changes.
- [ ] **COMP-04**: User migration and rollout path includes safe fallback/rollback behavior if v2 validation fails.

## Future Requirements

Deferred to future milestones.

### Discovery and Product Expansion

- **DISC-01**: User map suggestions include explainable "why shown" factors.
- **DISC-02**: User map updates support near-real-time incremental recompute.
- **DISC-03**: User receives push/in-app map update notifications.

### Platform Scale Evolution

- **SCALE-01**: User global compute runs in dedicated worker/service topology when scale thresholds are exceeded.
- **SCALE-02**: User map serving path supports advanced cache distribution and hot-shard mitigation.

## Out of Scope

Explicitly excluded for v2.0.

| Feature | Reason |
|---------|--------|
| Frontend code changes | Locked scope from milestone context |
| `profiles` schema changes | Locked constraint to preserve frontend compatibility |
| `pending_requests` table changes | Explicitly excluded by milestone constraints |
| New follow-system product rollout | Not required for v2.0 map backend milestone |
| Push notification delivery infrastructure | Deferred until backend map engine is stable |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-01 | TBD | Pending |
| DATA-02 | TBD | Pending |
| DATA-03 | TBD | Pending |
| DATA-04 | TBD | Pending |
| DATA-05 | TBD | Pending |
| ALGO-01 | TBD | Pending |
| ALGO-02 | TBD | Pending |
| ALGO-03 | TBD | Pending |
| ALGO-04 | TBD | Pending |
| ALGO-05 | TBD | Pending |
| EGO-01 | TBD | Pending |
| EGO-02 | TBD | Pending |
| EGO-03 | TBD | Pending |
| EGO-04 | TBD | Pending |
| EGO-05 | TBD | Pending |
| OPS-01 | TBD | Pending |
| OPS-02 | TBD | Pending |
| OPS-03 | TBD | Pending |
| OPS-04 | TBD | Pending |
| COMP-01 | TBD | Pending |
| COMP-02 | TBD | Pending |
| COMP-03 | TBD | Pending |
| COMP-04 | TBD | Pending |

**Coverage:**
- v2.0 requirements: 23 total
- Mapped to phases: 0
- Unmapped: 23 ⚠️

---
*Requirements defined: 2026-02-26*
*Last updated: 2026-02-26 after initial milestone v2.0 definition*
