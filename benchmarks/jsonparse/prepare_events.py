"""Generates a synthetic nested JSON array for the JSON-parsing benchmark
(category E). Deterministic (seed=42) -- rerunning produces byte-identical
output. Not part of the timed benchmark.

Deliberately nested (object-in-object, arrays of strings), unlike the flat
CSV in category D, so this actually exercises JSON-specific parsing --
object/array traversal and string escaping -- rather than duplicating the
comma-split story. All numeric fields are integers (amount_cents), never
floats, so every language's checksum is byte-identical by construction --
same reasoning category D used to sidestep a repeat of category A's
floating-point evaluation-order bug.

Usage:
    pixi run prepare-events
"""

import json
import random

random.seed(42)

N_EVENTS = 3_000_000

EVENT_TYPES = [
    "purchase", "refund", "signup", "login", "logout", "upgrade", "downgrade",
    "cancel", "renew", "trial_start", "trial_end", "invite_sent",
    "invite_accepted", "support_ticket", "review_posted", "share",
    "comment", "like", "follow", "unfollow", "export", "import",
    "password_reset", "email_verified", "two_factor_enabled", "payment_failed",
    "payment_retry", "chargeback", "referral", "milestone_reached",
    "purchase_premium", "purchase_addon", "team_created", "team_joined",
    "team_left", "webhook_fired", "api_key_created", "api_key_revoked",
]

TIERS = ["bronze", "silver", "gold", "platinum"]

TAGS = [
    "sale", "mobile", "web", "desktop", "promo", "beta", "affiliate",
    "organic", "paid", "trial", "enterprise", "self_serve", "annual",
    "monthly", "gift",
]


def zipf_weights(n):
    return [1.0 / (rank + 1) for rank in range(n)]


TYPE_WEIGHTS = zipf_weights(len(EVENT_TYPES))
TIER_WEIGHTS = [40, 35, 20, 5]  # bronze common, platinum rare


def make_tag(rng):
    tag = rng.choice(TAGS)
    # Rare, deterministic escape-sequence exercise: every ~500th tag gets an
    # embedded quote or backslash, properly JSON-escaped by json.dump below
    # (json.dump handles the escaping -- we just pick raw characters here).
    roll = rng.random()
    if roll < 0.001:
        tag = tag + '"quoted"'
    elif roll < 0.002:
        tag = tag + "\\backslash"
    return tag


def main():
    events = []
    for i in range(1, N_EVENTS + 1):
        etype = random.choices(EVENT_TYPES, weights=TYPE_WEIGHTS, k=1)[0]
        tier = random.choices(TIERS, weights=TIER_WEIGHTS, k=1)[0]
        amount_cents = random.randint(50, 999_999)
        n_tags = random.choices([0, 1, 2, 3], weights=[10, 40, 35, 15], k=1)[0]
        tags = [make_tag(random) for _ in range(n_tags)]
        events.append({
            "id": i,
            "type": etype,
            "user": {"id": random.randint(1, 500_000), "tier": tier},
            "amount_cents": amount_cents,
            "tags": tags,
        })

    out_path = "benchmarks/jsonparse/data/events.json"
    with open(out_path, "w") as f:
        json.dump(events, f, separators=(",", ":"))

    import os
    size_mb = os.path.getsize(out_path) / 1024 / 1024
    print(f"Wrote {len(events)} events, {size_mb:.1f} MiB -> {out_path}")


if __name__ == "__main__":
    main()
