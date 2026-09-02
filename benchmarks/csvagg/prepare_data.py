"""Generates a synthetic orders CSV for the category-D (tabular aggregation)
benchmark. No internet access in this environment (verified: requests to
gutenberg.org time out), so this is synthetic data, not scraped — seeded for
full reproducibility. All fields are integers (order_id, quantity,
price_cents) specifically so every language's aggregation is exact-integer
arithmetic with zero floating-point summation-order risk — see ANALYSIS.md
for why that matters (the Mandelbrot benchmark already hit a real FMA
rounding bug once).

Usage:
    pixi run prepare-data
"""

import csv
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
OUT_PATH = ROOT / "benchmarks/csvagg/data/orders.csv"
NUM_ROWS = 10_000_000

CATEGORIES = [
    "electronics", "home-goods", "sporting-equipment", "office-supplies",
    "kitchenware", "outdoor-gear", "toys", "books", "apparel", "footwear",
    "beauty", "automotive-parts", "garden-tools", "pet-supplies", "furniture",
    "lighting", "hardware", "stationery", "luggage", "musical-instruments",
    "board-games", "video-games", "computer-accessories", "phone-cases",
    "audio-equipment", "cameras", "watches", "jewelry", "bags", "wallets",
    "sunglasses", "hats", "gloves", "socks", "underwear", "swimwear",
    "outerwear", "activewear", "bedding", "bath-towels", "rugs", "curtains",
    "wall-art", "candles", "cookware", "bakeware", "cutlery", "dinnerware",
    "glassware", "storage-bins", "cleaning-supplies", "laundry-supplies",
    "pest-control", "plumbing-parts", "electrical-parts", "paint",
    "power-tools", "hand-tools", "fasteners", "safety-equipment",
    "camping-gear", "fishing-gear", "cycling-gear", "fitness-equipment",
    "yoga-gear", "team-sports", "water-sports", "winter-sports",
    "party-supplies", "gift-wrap", "greeting-cards", "office-furniture",
    "printer-supplies", "filing-supplies", "art-supplies", "craft-supplies",
    "sewing-supplies", "baby-gear", "baby-clothing", "baby-feeding",
    "baby-safety", "educational-toys", "puzzles", "action-figures",
    "dolls", "outdoor-toys", "ride-on-toys", "building-blocks",
    "diecast-vehicles", "remote-control-toys", "seasonal-decor",
    "holiday-lighting", "pet-food", "pet-toys", "pet-grooming", "pet-beds",
    "aquarium-supplies", "bird-supplies", "reptile-supplies",
]


def main():
    random.seed(42)
    OUT_PATH.parent.mkdir(exist_ok=True)

    ranks = list(range(1, len(CATEGORIES) + 1))
    weights = [1.0 / r for r in ranks]
    cum_weights = []
    running = 0.0
    for w in weights:
        running += w
        cum_weights.append(running)

    # Batch-generate all categories in one call (random.choices recomputes
    # cumulative weights per call if given raw `weights` repeatedly — doing
    # that 10M times is the actual bottleneck, not the CSV writing itself).
    categories = random.choices(CATEGORIES, cum_weights=cum_weights, k=NUM_ROWS)

    with OUT_PATH.open("w", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["order_id", "category", "quantity", "price_cents"])
        for order_id in range(1, NUM_ROWS + 1):
            quantity = random.randint(1, 20)
            price_cents = random.randint(100, 500_000)
            writer.writerow([order_id, categories[order_id - 1], quantity, price_cents])

    size_mb = OUT_PATH.stat().st_size / (1024 * 1024)
    print(f"Wrote {OUT_PATH}: {NUM_ROWS:,} rows, {size_mb:.1f} MiB, "
          f"{len(CATEGORIES)} categories")


if __name__ == "__main__":
    main()
