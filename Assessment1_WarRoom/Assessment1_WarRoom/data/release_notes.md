# Release Notes — Smart Recommendations Engine v2.0

## Feature Description
Complete overhaul of the product recommendation engine. Replaces rule-based filtering with a
real-time ML model that personalises suggestions based on user behaviour, purchase history,
and collaborative filtering from similar users.

## What Changed
- New ML inference service (Python FastAPI) replacing legacy Node.js recommender
- Recommendations now computed in real-time instead of batch (every 6 hours)
- New personalisation signals: scroll depth, dwell time, click-through history
- Revamped recommendation UI with horizontal scroll carousel
- Payment flow updated to include "Add recommended items before checkout" modal

## Known Risks at Launch
1. **ML inference service under load**: Not load-tested beyond 5,000 concurrent users.
   Production peak is ~14,000 DAU. Risk: HIGH.
2. **New payment modal**: Added a new step in checkout flow. Not A/B tested.
   Risk: MEDIUM — could cause drop-offs.
3. **Cold start problem**: New users have no history — fallback is top-sellers list.
   Risk: LOW.
4. **Memory leak in recommendation cache**: Known issue in v2.0.1, patch in v2.0.2 (not yet deployed).
   Risk: HIGH — could cause gradual performance degradation.
5. **Database connection pool**: Pool size not increased to account for real-time queries.
   Risk: HIGH — could cause timeouts under load.

## Rollback Plan
- Feature flag `ENABLE_V2_RECOMMENDATIONS` — set to `false` to revert to v1
- Estimated rollback time: 5 minutes
- Data impact: None (v1 model still warm)

## Version
- v2.0.1 (deployed 2026-04-01 00:00 UTC)
- v2.0.2 (memory leak patch) — PENDING DEPLOYMENT
