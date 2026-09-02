"""JSON parsing benchmark -- Python stdlib `json` module (C-accelerated via
the `_json` extension), the "optimized library" role in this repo's
established pattern (parallel to NumPy/Counter/pandas in categories A-D).
"""

import argparse
import json
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", default="benchmarks/jsonparse/data/events.json")
    args = parser.parse_args()

    start = time.perf_counter()

    with open(args.json, "r") as f:
        events = json.load(f)

    totals = {}
    for ev in events:
        t = ev["type"]
        totals[t] = totals.get(t, 0) + ev["amount_cents"]

    total_events = len(events)
    unique_types = len(totals)
    top_type, top_revenue = None, -1
    for t, revenue in totals.items():
        if revenue > top_revenue or (revenue == top_revenue and t < top_type):
            top_type, top_revenue = t, revenue

    elapsed = time.perf_counter() - start

    print(f"TIME_SECONDS: {elapsed}")
    print(f"CHECKSUM: {total_events}:{unique_types}:{top_type}:{top_revenue}")


if __name__ == "__main__":
    main()
