"""Turn JUnit XML files into a Markdown table for the GitHub Actions job summary.
Usage: python scripts/junit_summary.py reports/*-junit.xml >> "$GITHUB_STEP_SUMMARY"
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
def summarise(path):
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else root.findall("testsuite")
    totals = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0, "time": 0.0}
    for suite in suites:
        for key in ("tests", "failures", "errors", "skipped"):
                totals[key] += int(suite.get(key, 0))
        totals["time"] += float(suite.get("time", 0))
    return totals
def main(paths):
    lines = [
        "| Report | Tests | Passed | Failed | Skipped | Time (s) |",
        "|---|---|---|---|---|---|",
    ]
    found = False
    for raw in paths:
        path = Path(raw)
        if not path.is_file():
            continue
        found = True
        t = summarise(path)
        failed = t["failures"] + t["errors"]
        passed = t["tests"] - failed - t["skipped"]
        icon = "PASS" if failed == 0 else "FAIL"
        lines.append(
            f"| {icon} {path.stem} | {t['tests']} | {passed} | {failed} | {t['skipped']} "
            f"| {t['time']:.1f} |"
        )
    if not found:
        lines.append("| No JUnit reports found | - | - | - | - | - |")
    print("\n".join(lines))
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
