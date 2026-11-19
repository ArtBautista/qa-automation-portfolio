# Test Plan - Content Portal v1.0
## 1. Scope
In scope: sign-in/sign-out, article listing, article page, article editor, search,
REST API (`/api/auth/token`, `/api/articles`, `/api/reports/popular`, `/api/health`),
security headers, access control, performance of read endpoints.
Out of scope: email, file uploads, multi-language content.
## 2. User stories and acceptance criteria
| Story | Acceptance criteria |
|---|---|
| US-01 As a visitor I can read published articles | Home lists published only; drafts return 404 |
| US-02 As an editor I can sign in | Valid login shows "Signed in successfully."; 5 failures lock the
account for 5 min |
| US-03 As an editor I can create an article | Title 3-120 chars, body required, status draft/published;
success shows "Article created." |
| US-04 As a visitor I can search | Case-insensitive title match; zero results shows "0 results" |
| US-05 As an integrator I can use the API | Token auth; 401 without token, 403 for viewers; JSON errors |
## 3. Risk-based prioritisation
| Risk | Likelihood | Impact | Priority | Mitigation |
|---|---|---|---|---|
| Drafts leak to the public | Medium | High | P1 | API-TC-013, SEC-TC-024 |
| Login bypass / brute force | Low | High | P1 | SEC-TC-012, SEC-TC-021 |
| Invalid content saved | Medium | Medium | P2 | API-TC-021/022, UI-TC-013 |
| XSS through search or titles | Medium | High | P1 | SEC-TC-010, SEC-TC-013 |
| Slow pages under exam-season traffic | Medium | High | P1 | Locust budget p95 < 500 ms |
| Visual/cross-browser defects | Medium | Low | P3 | UI suite on Chrome + Firefox |
## 4. Test types and tools
| Level | Tool | Runs |
|---|---|---|
| API functional | pytest + requests | every push |
| UI end-to-end | Selenium (Python), POM, pytest-html | every push, Chrome + Firefox |
| Accessibility | axe-core via axe-selenium-python | every push |
| Security | pytest checks + OWASP ZAP baseline | every push |
| Performance | Locust (CI smoke), JMeter (deep runs) | every push (smoke), on demand |
## 5. Test design techniques used
Equivalence partitioning (valid/invalid status), boundary value analysis (title 2/3/120/121),
decision tables (role x action), error guessing (SQL/XSS payloads), state transition (login lockout).
## 6. Entry / exit criteria
Entry: build deploys, `/api/health` returns 200. Exit: 100% P1 tests pass, no open
Critical/High defects, performance budget met, ZAP baseline has no FAIL rules.
## 7. Estimation
| Activity | Estimate |
|---|---|
| Test design | 4 h |
| API automation | 4 h |
| UI automation | 6 h |
| Non-functional (perf + security) | 6 h |
| CI/CD integration | 3 h |
