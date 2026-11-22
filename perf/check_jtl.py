"""Summarise a JMeter .jtl (CSV) result file and fail on error rate or p95.
Usage: python perf/check_jtl.py reports/jmeter.jtl --p95-ms 500 --max-error-pct 1
"""
import argparse
import csv
import math
import sys
from collections import defaultdict
def percentile(values, pct):
    ordered = sorted(values)
    index = max(0, math.ceil(pct / 100 * len(ordered)) - 1)
    return ordered[index]

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jtl")
    parser.add_argument("--p95-ms", type=float, default=500.0)
    parser.add_argument("--max-error-pct", type=float, default=1.0)
    args = parser.parse_args(argv)
    by_label = defaultdict(list)
    errors = defaultdict(int)
    with open(args.jtl, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            by_label[row["label"]].append(int(row["elapsed"]))
            if row["success"].lower() != "true":
                errors[row["label"]] += 1

    if not by_label:
        print("ERROR: the .jtl file has no samples")
        return 2

    all_elapsed = [value for values in by_label.values() for value in values]
    print(f"{'Label':<36}{'Samples':>9}{'Errors':>8}{'p95 ms':>9}")
    for label, values in sorted(by_label.items()):
        print(f"{label[:35]:<36}{len(values):>9}{errors[label]:>8}{percentile(values, 95):>9}")

    error_pct = 100 * sum(errors.values()) / len(all_elapsed)
    p95 = percentile(all_elapsed, 95)
    print(f"\nTotal: samples={len(all_elapsed)}, errors={error_pct:.2f}%, p95={p95} ms")
    if p95 > args.p95_ms or error_pct > args.max_error_pct:
        print("PERFORMANCE BUDGET FAILED")
        return 1
    print("PERFORMANCE BUDGET PASSED")
    return 0
if __name__ == "__main__":
    sys.exit(main())
