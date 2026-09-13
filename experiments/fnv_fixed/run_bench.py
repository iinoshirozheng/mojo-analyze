#!/usr/bin/env python3
import json
import statistics
import subprocess
import sys


def run_one(path: str):
    out = subprocess.check_output([path], text=True)
    elapsed = None
    checksum = None
    for line in out.splitlines():
        if line.startswith("TIME_SECONDS:"):
            elapsed = float(line.split(":", 1)[1].strip())
        elif line.startswith("CHECKSUM:"):
            checksum = line.split(":", 1)[1].strip()
    if elapsed is None or checksum is None:
        raise RuntimeError(f"missing timing/checksum from {path}: {out!r}")
    return elapsed, checksum


def measure(path: str):
    for _ in range(2):
        run_one(path)
    times = []
    checksum = None
    for _ in range(7):
        elapsed, got = run_one(path)
        if checksum is None:
            checksum = got
        elif got != checksum:
            raise RuntimeError(f"unstable checksum for {path}: {got} != {checksum}")
        times.append(elapsed)
    return {
        "checksum": checksum,
        "times": times,
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "min": min(times),
        "max": max(times),
    }


if len(sys.argv) != 5:
    raise SystemExit("usage: run_bench.py <mojo-loop-bin> <mojo-unrolled-bin> <c-bin> <out-json>")

mojo_loop = measure(sys.argv[1])
mojo_unrolled = measure(sys.argv[2])
c = measure(sys.argv[3])
checksums = {mojo_loop["checksum"], mojo_unrolled["checksum"], c["checksum"]}
if len(checksums) != 1:
    raise SystemExit(
        "checksum mismatch: "
        f"Mojo-loop={mojo_loop['checksum']} "
        f"Mojo-unrolled={mojo_unrolled['checksum']} C={c['checksum']}"
    )

result = {
    "contract": {
        "blocks": 4096,
        "bytes_per_block": 32,
        "iterations": 4_000_000,
        "warmups": 2,
        "measured_trials": 7,
        "hash": "FNV-1a 64-bit",
        "intervention": "replace only Mojo's 32-byte counted hash loop with 32 explicit steps",
    },
    "mojo_loop": mojo_loop,
    "mojo_unrolled": mojo_unrolled,
    "c": c,
    "unrolled_over_loop_mean_ratio": mojo_unrolled["mean"] / mojo_loop["mean"],
    "unrolled_over_loop_median_ratio": mojo_unrolled["median"] / mojo_loop["median"],
    "loop_over_c_mean_ratio": mojo_loop["mean"] / c["mean"],
    "unrolled_over_c_mean_ratio": mojo_unrolled["mean"] / c["mean"],
    "loop_over_c_median_ratio": mojo_loop["median"] / c["median"],
    "unrolled_over_c_median_ratio": mojo_unrolled["median"] / c["median"],
}
print(json.dumps(result, indent=2, sort_keys=True))
with open(sys.argv[4], "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, sort_keys=True)
    f.write("\n")
