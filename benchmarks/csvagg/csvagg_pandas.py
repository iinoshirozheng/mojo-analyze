"""Category D (real-world tabular aggregation), pandas variant — the
"optimized library" role, matching NumPy/Counter's role in categories A/B/C.
"""

import argparse
import time

import pandas as pd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="benchmarks/csvagg/data/orders.csv")
    args = parser.parse_args()

    start = time.perf_counter()

    df = pd.read_csv(args.csv)
    df["revenue"] = df["quantity"].astype("int64") * df["price_cents"].astype("int64")
    grp = df.groupby("category")["revenue"].sum()

    total_rows = len(df)
    unique_categories = grp.shape[0]
    top_category, top_revenue = sorted(grp.items(), key=lambda kv: (-kv[1], kv[0]))[0]

    elapsed = time.perf_counter() - start

    print(f"TIME_SECONDS: {elapsed}")
    print(f"CHECKSUM: {total_rows}:{unique_categories}:{top_category}:{top_revenue}")


if __name__ == "__main__":
    main()
