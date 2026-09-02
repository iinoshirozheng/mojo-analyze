"""Category D (real-world tabular aggregation), pure Python variant — the
"naive/pure" role: stdlib csv module + manual dict aggregation, no pandas.
"""

import argparse
import csv
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="benchmarks/csvagg/data/orders.csv")
    args = parser.parse_args()

    start = time.perf_counter()

    revenue_by_category = {}
    total_rows = 0
    with open(args.csv, newline="") as f:
        reader = csv.reader(f)
        next(reader)  # header
        for row in reader:
            category = row[1]
            quantity = int(row[2])
            price_cents = int(row[3])
            revenue_by_category[category] = (
                revenue_by_category.get(category, 0) + quantity * price_cents
            )
            total_rows += 1

    unique_categories = len(revenue_by_category)
    top_category, top_revenue = sorted(
        revenue_by_category.items(), key=lambda kv: (-kv[1], kv[0])
    )[0]

    elapsed = time.perf_counter() - start

    print(f"TIME_SECONDS: {elapsed}")
    print(f"CHECKSUM: {total_rows}:{unique_categories}:{top_category}:{top_revenue}")


if __name__ == "__main__":
    main()
