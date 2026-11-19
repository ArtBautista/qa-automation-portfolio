import pytest
from axe_selenium_python import Axe
pytestmark = [pytest.mark.ui, pytest.mark.a11y]
PAGES = ["/", "/login", "/search?q=exam", "/articles/1"]

@pytest.mark.parametrize("path", PAGES)
def test_no_serious_accessibility_violations(driver, base_url, path):
    """UI-TC-020: axe-core finds no serious or critical WCAG violations."""
    driver.get(base_url + path)
    axe = Axe(driver)
    axe.inject()
    results = axe.run()
    serious = [v for v in results["violations"] if v["impact"] in ("serious", "critical")]
    assert not serious, axe.report(serious)
