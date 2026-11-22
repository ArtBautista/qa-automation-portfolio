# QA Automation Portfolio - Content Portal

[![QA Pipeline](https://github.com/ArtBautista/qa-automation-portfolio/actions/workflows/qa-pipeline.yml/badge.svg?branch=main)](https://github.com/ArtBautista/qa-automation-portfolio/actions/workflows/qa-pipeline.yml)

End-to-end quality engineering on a small CMS-style web app: functional, accessibility,
security and performance testing, all running in a CI/CD pipeline on every push.

| Area | Tools | Tests |
|---|---|---|
| API | pytest, requests | 28 |
| UI (Chrome + Firefox) | Selenium 4 (Python), Page Object Model, pytest-html | 14 |
| Accessibility | axe-core (WCAG) | 4 |
| Security | pytest checks, OWASP ZAP baseline | 27 |
| CMS | Selenium against a local Drupal 10 (Docker) | 2 |
| Performance | Locust (CI budget: p95 < 500 ms, < 1% errors), JMeter | 2 load models |
| CI/CD | GitHub Actions (primary), Jenkinsfile, GitLab CI | 5 jobs |

## Results

| Check | Result |
|---|---|
| Load test, 20 concurrent users (Locust) | 587 requests, 0 failures, 9.9 req/s, p95 53 ms |
| OWASP ZAP baseline | 0 FAIL, 63 PASS, 4 WARN triaged (1 fixed, 1 logged as a defect, 2 accepted) |
| Planted-defect exercise | 4 of 4 seeded defects caught (functional, security, performance) |
| Performance regression caught | `/api/reports/popular` p95 54 ms → 600 ms (11×), build failed on budget |

## Run locally (Windows PowerShell)

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app/portal.py                                        # terminal 1
python -m pytest tests/api tests/security                   # terminal 2
python -m pytest tests/ui -m "not drupal" --browser chrome
locust -f perf/locustfile.py --host http://127.0.0.1:5000
```

## Pipeline

```text
lint -> api-tests -> ui-tests (chrome, firefox)
                  -> security-tests + OWASP ZAP baseline
                  -> performance-smoke (Locust + budget check)
```

Every job publishes HTML and JUnit reports as artifacts; failed UI tests attach screenshots.
`main` is protected: a pull request cannot merge unless every check is green.

## Docs

[Test plan](docs/test-plan.md) · [Strategy](docs/test-strategy.md) · [Defect reports](docs/defects)