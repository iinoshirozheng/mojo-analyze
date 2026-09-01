import argparse
import time
from math import isqrt


def sieve(limit: int) -> tuple[int, int]:
    is_prime = bytearray([1]) * (limit + 1)
    is_prime[0] = 0
    if limit >= 1:
        is_prime[1] = 0

    for i in range(2, isqrt(limit) + 1):
        if is_prime[i]:
            for j in range(i * i, limit + 1, i):
                is_prime[j] = 0

    count = 0
    total = 0
    for i in range(2, limit + 1):
        if is_prime[i]:
            count += 1
            total += i

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
