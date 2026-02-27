# Phase 26 UAT Checklist

## Objective

Confirm staging behavior is acceptable for profiles-only map serving and sensitivity demo modes before production promotion.

## Staging Checklist

| Check | Expected Outcome | Status |
| --- | --- | --- |
| Authenticated `GET /map/{user_id}` self-only access | 200 for self, 403 for non-self | Pending |
| Authenticated `POST /map/trigger/{user_id}` self-only access | 200/422 for self, 403 for non-self, no 500s | Pending |
| Missing profile projection handling | 503 with explicit incomplete projection detail | Pending |
| Strong-bounded demo sweep | Eleanor/Winston distance and rank do not regress as amplification grows | Verified by automated test |
| Uncapped demo sweep | Eleanor/Winston distance and rank do not regress as amplification grows | Verified by automated test |
| Natural-mode baseline | Baseline distance/rank/weight remains unchanged from regression guard values | Verified by automated test |

## Evidence Links

- Automated verification log: `26-VERIFICATION.md`
- Runtime/API contracts: `backend/tests/test_contracts.py`
- Dynamic sensitivity checks: `backend/tests/map_pipeline/test_dynamic_tuning.py`

## Sign-off

- Staging QA owner: _TBD_
- Sign-off timestamp: _TBD_
- Decision: _Pending_
