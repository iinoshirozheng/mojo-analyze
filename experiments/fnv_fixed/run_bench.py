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


if len(sys.argv) != 4:
    raise SystemExit("usage: run_bench.py <mojo-bin> <c-bin> <out-json>")

mojo = measure(sys.argv[1])
c = measure(sys.argv[2])
if mojo["checksum"] != c["checksum"]:
    raise SystemExit(f"checksum mismatch: Mojo={mojo['checksum']} C={c['checksum']}")

result = {
    "contract": {
        "blocks": 4096,
        "bytes_per_block": 32,
        "iterations": 4_000_000,
        "warmups": 2,
        "measured_trials": 7,
        "hash": "FNV-1a 64-bit",
    },
    "mojo": mojo,
    "c": c,
    "mojo_over_c_mean_ratio": mojo["mean"] / c["mean"],
    "mojo_over_c_median_ratio": mojo["median"] / c["median"],
}
print(json.dumps(result, indent=2, sort_keys=True))
with open(sys.argv[3], "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, sort_keys=True)
    f.write("\n")
