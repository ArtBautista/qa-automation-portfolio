# QA Automation Portfolio - Content Portal

![QA Pipeline](https://github.com/ArtBautista/qa-automation-portfolio/actions/workflows/qapipeline.yml/badge.svg)
End-to-end quality engineering on a small CMS-style web app: functional, accessibility,
security and performance testing, all running in a CI/CD pipeline.

| Area | Tools | Tests |
|---|---|---|
| API | pytest, requests | 28 |
| UI (Chrome + Firefox) | Selenium 4 (Python), Page Object Model, pytest-html | 14 |
| Accessibility | axe-core | 4 |
| Security | pytest checks, OWASP ZAP baseline | 27 |
| Performance | Locust (CI budget: p95 < 500 ms, < 1% errors), JMeter | 2 load models |
| CI/CD | GitHub Actions (primary), Jenkinsfile, GitLab CI | 5 jobs |

## Run locally (Windows PowerShell)
```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app/portal.py # terminal 1
pytest tests/api tests/security # terminal 2
pytest tests/ui -m "not drupal" --browser chrome
locust -f perf/locustfile.py --host http://127.0.0.1:5000
```

## Pipeline
`lint -> api-tests -> ui-tests (chrome, firefox) | security-tests + ZAP | performance-smoke`

## Docs
[Test plan](docs/test-plan.md) - [Strategy](docs/test-strategy.md) - [Defect reports](docs/defects)