# DEF-001: Reflected XSS in /search - query string rendered as raw HTML
| Field | Value |
|---|---|
| Severity | Critical |
| Priority | P1 |
| Environment | Content Portal v1.0, Windows 11, Chrome, PORTAL_BUGS=1 |
| Component | Security / Search page |
| Found by | Automated test SEC-TC-010 (`test_reflected_xss_is_escaped`) |
| Status | New |
## Steps to reproduce
1. Start the app with `PORTAL_BUGS=1`.
2. Open `http://127.0.0.1:5000/search?q=<script>alert('xss')</script>`.
3. View the page source of the results summary.
## Expected result
The summary shows the text `<script>alert('xss')</script>` HTML-escaped
(`&lt;script&gt;...`). No script runs.
## Actual result
The raw `<script>` tag is written into the page. The browser's CSP blocks the
inline script today, but any CSP relaxation would make it executable.
## Evidence
`AssertionError: assert "<script>alert('xss')</script>" not in response.text`
## Root-cause hint
`app/portal.py` `search()` wraps the query in `Markup(q)`, which marks untrusted
input as safe and bypasses Jinja autoescaping.
## Impact
An attacker can send a crafted link that runs JavaScript in a victim's session
(cookie theft is limited by HttpOnly, but actions and phishing overlays are possible).
OWASP A03:2021 Injection.
