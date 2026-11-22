"""Fail the build when a Locust run breaks its performance budget.

Usage: python perf/check_thresholds.py reports/perf_stats.csv --p95-ms 500 \
           --endpoint-p95-ms 500 --max-failure-ratio 0.01
"""
import argparse
import csv
import sys


def load_rows(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stats_csv", help="Locust *_stats.csv file")
    parser.add_argument("--p95-ms", type=float, default=500.0)
    parser.add_argument("--max-failure-ratio", type=float, default=0.01)
    parser.add_argument("--min-rps", type=float, default=0.0)
    parser.add_argument(
        "--endpoint-p95-ms", type=float, default=None, help="Optional p95 budget per endpoint"
    )
    args = parser.parse_args(argv)

    rows = load_rows(args.stats_csv)
    print(f"{'Endpoint':<36}{'Requests':>10}{'Failures':>10}{'p95 ms':>10}{'RPS':>8}")
    for row in rows:
        print(
            f"{row['Name'][:35]:<36}{row['Request Count']:>10}{row['Failure Count']:>10}"
            f"{row['95%']:>10}{float(row['Requests/s']):>8.1f}"
        )

    total = next((row for row in rows if row["Name"] == "Aggregated"), None)
    if total is None:
        print("ERROR: no 'Aggregated' row found")
        return 2

    requests_made = int(total["Request Count"])
    failure_ratio = int(total["Failure Count"]) / requests_made if requests_made else 1.0
    p95 = float(total["95%"])
    rps = float(total["Requests/s"])

    violations = []
    if requests_made == 0:
        violations.append("no requests were made")
    if p95 > args.p95_ms:
        violations.append(f"p95 {p95:.0f} ms > budget {args.p95_ms:.0f} ms")
    if failure_ratio > args.max_failure_ratio:
        violations.append(f"failure ratio {failure_ratio:.2%} > {args.max_failure_ratio:.2%}")
    if rps < args.min_rps:
        violations.append(f"throughput {rps:.1f} rps < {args.min_rps:.1f} rps")
    if args.endpoint_p95_ms is not None:
        for row in rows:
            if row["Name"] != "Aggregated" and float(row["95%"]) > args.endpoint_p95_ms:
                violations.append(
                    f"{row['Name']} p95 {float(row['95%']):.0f} ms > {args.endpoint_p95_ms:.0f} ms"
                )

    print(f"\nAggregated: p95={p95:.0f} ms, failures={failure_ratio:.2%}, rps={rps:.1f}")
    if violations:
        print("PERFORMANCE BUDGET FAILED: " + "; ".join(violations))
        return 1
    print("PERFORMANCE BUDGET PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
