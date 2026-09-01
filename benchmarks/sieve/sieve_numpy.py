import argparse
import time
from math import isqrt

import numpy as np


def sieve(limit: int) -> tuple[int, int]:
    is_prime = np.ones(limit + 1, dtype=bool)
    is_prime[0] = False
    if limit >= 1:
        is_prime[1] = False

    for i in range(2, isqrt(limit) + 1):
        if is_prime[i]:
            is_prime[i * i :: i] = False

    primes = np.nonzero(is_prime)[0]
    count = int(primes.size)
    total = int(primes.sum())

    return count, total


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=50_000_000)
    args = parser.parse_args()

    start = time.perf_counter()
    count, total = sieve(args.limit)
    elapsed = time.perf_counter() - start

    sum_mod = total % 1_000_000_007
    print(f"TIME_SECONDS: {elapsed:.6f}")
    print(f"CHECKSUM: {count}:{sum_mod}")


if __name__ == "__main__":
    main()
