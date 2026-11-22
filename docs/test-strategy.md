# Test Automation Strategy - Content Portal
## Goals
Catch regressions before merge, keep the main branch releasable, and make quality
visible to developers and Product Owners in every pull request.
## Test pyramid
| Layer | Share | Why |
|---|---|---|
| API tests | ~40% | Fast, stable, cover business rules and contracts |
| Security checks | ~35% | Cheap to automate, high impact if missed |
| UI + accessibility | ~25% | Only critical user journeys, run on two browsers |
| Performance | smoke on every push, full runs before release | Protect the p95 budget |
## What we automate (decision rule)
Automate when a test is repeated each release, is high-risk, is data-driven, or is
tedious by hand. Keep manual: exploratory testing, one-off visual checks, usability.
## Framework design
- Page Object Model in `framework/pages`, one class per page, locators by `data-testid`.
- Explicit waits only (no `time.sleep`, no implicit waits).
- Configuration through environment variables (`framework/config.py`).
- Each test creates and deletes its own data, so tests run in any order and in parallel.
- Failure evidence: screenshots and HTML reports attached to every CI run.
## CI/CD quality gates
lint -> API -> (UI x2 browsers | security + ZAP | performance smoke).
A pull request cannot merge unless every job is green.
## Flaky test policy
A flaky test is fixed or quarantined within one working day. Root causes are usually
missing waits, shared test data or environment timing. Never add blind retries.
## Metrics we report
Pass rate per run, duration per job, defects found by automation vs production,
p95 latency trend, number of ZAP warnings.
