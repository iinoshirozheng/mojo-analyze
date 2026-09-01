#!/usr/bin/env python3
import argparse
import time

RE_MIN, RE_MAX = -2.0, 1.0
IM_MIN, IM_MAX = -1.5, 1.5


def compute(width, height, max_iter):
    w_div = max(width - 1, 1)
    h_div = max(height - 1, 1)
    dre = (RE_MAX - RE_MIN) / w_div
    dim = (IM_MAX - IM_MIN) / h_div

    total = 0
    for y in range(height):
        im = IM_MAX - dim * y
        for x in range(width):
            re = RE_MIN + dre * x
            zr = 0.0
            zi = 0.0
            count = 0
            while count < max_iter and zr * zr + zi * zi <= 4.0:
                new_zr = zr * zr - zi * zi + re
                zi = 2.0 * zr * zi + im
                zr = new_zr
                count += 1
            total += count
    return total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--width", type=int, default=800)
    parser.add_argument("--height", type=int, default=600)
    parser.add_argument("--max-iter", type=int, default=500)
    args = parser.parse_args()

    start = time.perf_counter()
    total = compute(args.width, args.height, args.max_iter)
    elapsed = time.perf_counter() - start

    print(f"TIME_SECONDS: {elapsed:.6f}")
    print(f"CHECKSUM: {total}")


if __name__ == "__main__":
    main()
