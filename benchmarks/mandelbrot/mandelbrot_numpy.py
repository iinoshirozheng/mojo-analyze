#!/usr/bin/env python3
import argparse
import time

import numpy as np

RE_MIN, RE_MAX = -2.0, 1.0
IM_MIN, IM_MAX = -1.5, 1.5


def compute(width, height, max_iter):
    w_div = max(width - 1, 1)
    h_div = max(height - 1, 1)
    dre = (RE_MAX - RE_MIN) / w_div
    dim = (IM_MAX - IM_MIN) / h_div

    x = np.arange(width, dtype=np.float64)
    y = np.arange(height, dtype=np.float64)
    re_row = RE_MIN + dre * x
    im_col = IM_MAX - dim * y
    RE, IM = np.meshgrid(re_row, im_col)  # both shape (height, width)

    zr = np.zeros((height, width), dtype=np.float64)
    zi = np.zeros((height, width), dtype=np.float64)
    count = np.zeros((height, width), dtype=np.int64)
    active = np.ones((height, width), dtype=bool)

    for _ in range(max_iter):
        if not np.any(active):
            break

        zr_a = zr[active]
        zi_a = zi[active]
        re_a = RE[active]
        im_a = IM[active]

        new_zr = zr_a * zr_a - zi_a * zi_a + re_a
        new_zi = 2.0 * zr_a * zi_a + im_a
        mag2 = new_zr * new_zr + new_zi * new_zi

        zr[active] = new_zr
        zi[active] = new_zi
        count[active] += 1

        active[active] = mag2 <= 4.0

    total = int(count.sum())
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
