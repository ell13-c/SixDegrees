---
phase: 02-core-algorithm
verified: 2026-02-22T00:00:00Z
status: passed
score: 15/15 must-haves verified
re_verification: false
---

# Phase 2: Core Algorithm Verification Report

**Phase Goal:** The full computation pipeline — interaction scoring, combined distance matrix, t-SNE projection, and origin translation — runs correctly on in-memory test data and produces a verifiable 2D coordinate output
**Verified:** 2026-02-22
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | `config.algorithm` exposes ALPHA=0.6, BETA=0.4, INTERACTION_WEIGHTS summing to 1.0, PROFILE_WEIGHTS summing to 1.0 | VERIFIED | File exists; runtime check confirmed ALPHA=0.6, BETA=0.4, IW sum=1.0, PW sum=1.0 |
| 2 | `project_tsne()` raises ValueError with message containing "10" when N < 10 | VERIFIED | `test_raises_on_fewer_than_10_users` and `test_raises_on_exact_9_users` both PASSED |
| 3 | `project_tsne()` returns (N, 2) ndarray for N >= 10 with metric='precomputed', init='random', random_state=42 | VERIFIED | Source confirmed all four params; `test_output_shape_10_users`, `test_output_shape_20_users`, `test_output_is_ndarray` PASSED |
| 4 | Perplexity computed as min(30, max(5, int(sqrt(N)))) — never exceeding N | VERIFIED | Runtime formula check across N=10,15,20,30 all pass; perplexity always < N |
| 5 | Raw t-SNE coordinates returned before any translation (TSNE-04) | VERIFIED | `test_returns_raw_coordinates` PASSED; pipeline.py preserves `raw_coords` in output dict |
| 6 | `compute_interaction_scores()` reads weights exclusively from INTERACTION_WEIGHTS — adding new key flows through automatically | VERIFIED | Source uses dict-only dispatch; `test_new_interaction_type_requires_only_config_change` PASSED |
| 7 | Each interaction type normalized independently using 95th-pct clip then divide by clip_val | VERIFIED | Source uses `np.percentile(..., 95, method="lower")` then `norm_vals = clipped / clip_val` |
| 8 | Missing pairs produce interaction_score = 0.0 with no special-case code | VERIFIED | Absent pairs simply never set matrix[i][j]; `test_no_interactions_produces_zero_matrix` and `test_missing_pair_produces_zero` PASSED |
| 9 | Final per-pair interaction score is weighted sum in [0, 1]; output matrix symmetric, zeros on diagonal | VERIFIED | `test_all_scores_in_range`, `test_matrix_is_symmetric`, `test_diagonal_is_zero` PASSED |
| 10 | `build_combined_distance_matrix()` applies formula: α × profile_dist + β × (1 - interaction_score) | VERIFIED | Source: `ALPHA * profile_dist + BETA * (1.0 - interaction_matrix)`; `test_zero_interactions_equals_profile_distance` PASSED |
| 11 | Profile distance computation delegates to `services/matching/scoring.py` — no reimplementation | VERIFIED | Source imports `build_similarity_matrix`, `apply_weights`, `similarity_to_distance` from `services.matching.scoring`; `test_reuses_existing_matching_scoring` PASSED |
| 12 | `translate_and_assign_tiers()` shifts all coordinates so requesting user is at exactly (0.0, 0.0) | VERIFIED | Source: `translated = raw_coords - raw_coords[req_idx]`; `test_requesting_user_at_origin` PASSED (end-to-end) |
| 13 | Tier assignment: Tier 1 = 5 nearest, Tier 2 = ranks 6-15, Tier 3 = all remaining; requesting user at (0,0) is Tier 1 | VERIFIED | `_K1=5`, `_K2=15` in source; `test_tier_1_count`, `test_requesting_user_is_tier_1` PASSED |
| 14 | Origin translation is stateless — different requesting_user_id produces independent coordinate sets | VERIFIED | `test_different_requesting_users_produce_different_origins` PASSED |
| 15 | `run_pipeline()` accepts in-memory data, returns dict with raw_coords + translated_results; high-interaction users appear measurably closer | VERIFIED | `test_high_interaction_users_appear_closer` PASSED (SC-2 — hardest test) |

**Score:** 15/15 truths verified

---

### Required Artifacts

| Artifact | Expected | Lines | Status | Details |
|---------|---------|-------|--------|---------|
| `backend/config/algorithm.py` | All algorithm constants | 29 | VERIFIED | ALPHA=0.6, BETA=0.4, INTERACTION_WEIGHTS (3 keys, sum=1.0), PROFILE_WEIGHTS (7 keys, sum=1.0) |
| `backend/services/map_pipeline/__init__.py` | Package marker | — | VERIFIED | Exists |
| `backend/services/map_pipeline/tsne_projector.py` | `project_tsne()` | 47 | VERIFIED | Substantive: N<10 guard, perplexity formula, TSNE with 4 required params, returns fit_transform |
| `backend/services/map_pipeline/interaction.py` | `compute_interaction_scores()` | 96 (min: 50) | VERIFIED | Substantive: 95th-pct clip, dict dispatch, symmetric NxN output |
| `backend/services/map_pipeline/scoring.py` | `build_combined_distance_matrix()` | 52 (min: 40) | VERIFIED | Substantive: delegates to matching/scoring, DIST-01 formula, symmetry enforcement |
| `backend/services/map_pipeline/origin_translator.py` | `translate_and_assign_tiers()` | 91 (min: 50) | VERIFIED | Substantive: broadcast subtraction, Euclidean distances, tier assignment, all users in output |
| `backend/services/map_pipeline/pipeline.py` | `run_pipeline()` | 81 (min: 50) | VERIFIED | Substantive: wires all 4 stages, returns raw_coords + translated_results + user_ids |
| `backend/tests/map_pipeline/test_tsne_projector.py` | TDD tests | 80 (min: 40) | VERIFIED | 8 tests, all green |
| `backend/tests/map_pipeline/test_interaction.py` | TDD tests | 131 (min: 50) | VERIFIED | 8 tests, all green |
| `backend/tests/map_pipeline/test_scoring.py` | TDD tests | 126 (min: 40) | VERIFIED | 7 tests, all green |
| `backend/tests/map_pipeline/test_origin_translator.py` | TDD tests | 130 (min: 40) | VERIFIED | 10 tests, all green |
| `backend/tests/map_pipeline/test_pipeline.py` | Integration tests | 203 (min: 60) | VERIFIED | 11 tests, all green |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `interaction.py` | `config/algorithm.py` | `from config.algorithm import INTERACTION_WEIGHTS` | WIRED | Line 18; import confirmed, dict keys iterated at runtime |
| `interaction.py` | `numpy` | `np.percentile(..., 95, method="lower")` | WIRED | Line 64; method='lower' confirmed |
| `scoring.py` | `services/matching/scoring.py` | `from services.matching.scoring import build_similarity_matrix, apply_weights, similarity_to_distance` | WIRED | Lines 16-20; all three functions called in body |
| `scoring.py` | `config/algorithm.py` | `from config.algorithm import ALPHA, BETA, PROFILE_WEIGHTS` | WIRED | Line 15; all three constants used in formula |
| `tsne_projector.py` | `sklearn.manifold.TSNE` | `metric='precomputed', init='random', random_state=42, max_iter=1000` | WIRED | All four required params confirmed in source |
| `pipeline.py` | `interaction.py` | `from services.map_pipeline.interaction import compute_interaction_scores` | WIRED | Line 19; called at Stage 1 |
| `pipeline.py` | `scoring.py` | `from services.map_pipeline.scoring import build_combined_distance_matrix` | WIRED | Line 20; called at Stage 2 |
| `pipeline.py` | `tsne_projector.py` | `from services.map_pipeline.tsne_projector import project_tsne` | WIRED | Line 21; called at Stage 3 |
| `pipeline.py` | `origin_translator.py` | `from services.map_pipeline.origin_translator import translate_and_assign_tiers` | WIRED | Line 22; called at Stage 4 |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|---------|
| INT-01 | 02-02, 02-04 | Interaction score reads from INTERACTION_WEIGHTS dict — adding type requires only dict entry | SATISFIED | Dict-dispatch confirmed in source; `test_new_interaction_type_requires_only_config_change` PASSED |
| INT-02 | 02-02, 02-04 | Each interaction type normalized independently with 95th-pct clip | SATISFIED | `np.percentile(..., 95, method="lower")` + `/clip_val`; `test_superuser_clipping` PASSED |
| INT-03 | 02-02, 02-04 | Final interaction score is weighted sum in [0, 1] | SATISFIED | `test_all_scores_in_range` PASSED; matrix.min()>=0 and matrix.max()<=1.0 verified |
| INT-04 | 02-02, 02-04 | Missing pairs produce 0.0 — no special case code | SATISFIED | Absent pairs leave matrix zeros; `test_no_interactions_produces_zero_matrix` PASSED |
| DIST-01 | 02-03, 02-04 | Combined distance = α × profile_dist + β × (1 - interaction_score) | SATISFIED | `ALPHA * profile_dist + BETA * (1.0 - interaction_matrix)` in source; `test_zero_interactions_equals_profile_distance` PASSED |
| DIST-02 | 02-01, 02-04 | α=0.6, β=0.4 stored in config/algorithm.py; no magic numbers | SATISFIED | `ALPHA: float = 0.6`, `BETA: float = 0.4` in algorithm.py; imported by scoring.py |
| DIST-03 | 02-03, 02-04 | Profile distance preserves existing field weights from matching module | SATISFIED | scoring.py delegates to `services.matching.scoring`; PROFILE_WEIGHTS from config; `test_reuses_existing_matching_scoring` PASSED |
| DIST-04 | 02-03, 02-04 | NxN distance matrix: values in [0,1], symmetric, zeros on diagonal | SATISFIED | `(combined + combined.T)/2.0` + `np.fill_diagonal(combined, 0.0)`; `test_is_symmetric`, `test_diagonal_is_zero`, `test_values_in_range` PASSED |
| TSNE-01 | 02-01, 02-04 | t-SNE with metric='precomputed', init='random', random_state=42 | SATISFIED | All 4 params confirmed in tsne_projector.py source; `test_deterministic_with_random_state` PASSED |
| TSNE-02 | 02-01, 02-04 | Dynamic perplexity = min(30, max(5, int(sqrt(N)))) | SATISFIED | Formula confirmed in source; perplexity always < N verified at boundary |
| TSNE-03 | 02-01, 02-04 | Pipeline raises clear error if N < 10 | SATISFIED | ValueError with message containing "10"; 2 tests PASSED at boundary |
| TSNE-04 | 02-01, 02-04 | Raw t-SNE coordinates preserved before origin translation | SATISFIED | `raw_coords` key in pipeline output; `test_raw_coords_preserved_distinct_from_translated` PASSED |
| ORIG-01 | 02-03, 02-04 | Coordinates translated so requesting user is at (0.0, 0.0) | SATISFIED | `translated = raw_coords - raw_coords[req_idx]`; `test_requesting_user_at_origin` PASSED |
| ORIG-02 | 02-03, 02-04 | Tier 1=5 nearest, Tier 2=next 10, Tier 3=all remaining; requesting user at (0,0) as Tier 1 | SATISFIED | _K1=5, _K2=15 in source; all tier tests PASSED; requesting user always tier=1 |
| ORIG-03 | 02-03, 02-04 | Translation applied independently per requesting user; stateless | SATISFIED | Pure function; `test_different_requesting_users_produce_different_origins` PASSED |

**All 15 Phase 2 requirements satisfied.**

No orphaned requirements found — all INT-*, DIST-*, TSNE-*, ORIG-* IDs are mapped to Phase 2 in REQUIREMENTS.md and claimed by plans 02-01 through 02-04.

---

### Anti-Patterns Found

None. Grep across all Phase 2 source files (`services/map_pipeline/*.py`, `config/algorithm.py`) found zero instances of: TODO, FIXME, XXX, HACK, PLACEHOLDER, `return null`, `return {}`, `return []`, `=> {}`, console.log, or other stub indicators.

---

### Human Verification Required

None. All phase goals are verified programmatically:
- Algorithm correctness (43 passing tests including SC-2 interaction sensitivity)
- Formula implementation (inspected via source)
- Parameter values (TSNE, perplexity, weights all confirmed)
- Pipeline wiring (all 4 stage imports confirmed)

This phase is pure-computation backend code with no UI, no external services in the computation path, and no real-time behavior — fully automatable verification.

---

## Test Suite Summary

| Test File | Tests | Result |
|-----------|-------|--------|
| `test_tsne_projector.py` | 8 | 8 passed |
| `test_interaction.py` | 8 | 8 passed |
| `test_scoring.py` | 7 | 7 passed |
| `test_origin_translator.py` | 10 | 10 passed |
| `test_pipeline.py` | 11 | 11 passed |
| **Total** | **43** | **43 passed in 5.12s** |

**Phase 2 ROADMAP Success Criteria:**

| Criterion | Test | Status |
|-----------|------|--------|
| SC-1: New interaction type = 1 dict entry, zero logic changes | `test_new_interaction_type_requires_only_config_change` | PASSED |
| SC-2: High-interaction users measurably closer in 2D output | `test_high_interaction_users_appear_closer` | PASSED |
| SC-3: Requesting user at exactly (0.0, 0.0) | `test_requesting_user_at_origin` | PASSED |
| SC-4: N < 10 raises clear descriptive ValueError | `test_raises_on_fewer_than_10_users` | PASSED |
| SC-5: NxN matrix symmetric, zeros diagonal, values in [0,1] | Unit tests in 02-01 through 02-03 | PASSED |

---

_Verified: 2026-02-22_
_Verifier: Claude (gsd-verifier)_
