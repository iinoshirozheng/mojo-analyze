"""Focused Category-D experiment: Rust default HashMap hasher vs FNV-1a.

Runs the two otherwise-identical Rust CSV aggregation binaries, enforces exact
checksum agreement, and writes raw samples plus summary statistics to a JSON
artifact. This does not touch canonical results/results.json.
"""

import argparse
import json
import statistics
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "benchmarks/csvagg/data/orders.csv"
OUT_DIR = ROOT / "results/experiments"


def parse_output(stdout: str):
    elapsed = None
    checksum = None
    for raw in stdout.splitlines():
        line = raw.strip()
        if line.startswith("TIME_SECONDS:"):
            elapsed = float(line.split(":", 1)[1].strip())
        elif line.startswith("CHECKSUM:"):
            checksum = line.split(":", 1)[1].strip()
    if elapsed is None or checksum is None:
        raise RuntimeError(f"missing timing/checksum in output:\n{stdout}")
    return elapsed, checksum


def run(binary: Path, warmup: int, trials: int):
    times = []
    checksums = set()
    cmd = [str(binary), "--csv", str(CSV)]
    for idx in range(warmup + trials):
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=True)
        elapsed, checksum = parse_output(proc.stdout)
        checksums.add(checksum)
        if idx >= warmup:
            times.append(elapsed)
    if len(checksums) != 1:
        raise RuntimeError(f"non-deterministic checksum for {binary}: {checksums}")
    return times, checksums.pop()


def summarize(times):
    return {
        "times": times,
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "stdev": statistics.stdev(times) if len(times) > 1 else 0.0,
        "min": min(times),
        "max": max(times),
        "n": len(times),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=7)
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--arch", required=True)
    args = parser.parse_args()

    safe_times, safe_checksum = run(ROOT / "rust/target/release/csvagg", args.warmup, args.trials)
    fnv_times, fnv_checksum = run(ROOT / "rust/target/release/csvagg_fnv", args.warmup, args.trials)
    if safe_checksum != fnv_checksum:
        raise RuntimeError(f"checksum mismatch: default={safe_checksum} fnv={fnv_checksum}")

    default = summarize(safe_times)
    fnv = summarize(fnv_times)
    ratio = default["mean"] / fnv["mean"]

    payload = {
        "experiment": "csvagg-rust-default-vs-fnv1a",
        "arch": args.arch,
        "warmup": args.warmup,
        "checksum": safe_checksum,
        "default_hashmap": default,
        "fnv1a_hashmap": fnv,
        "default_over_fnv_mean_ratio": ratio,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"csvagg-rust-fnv-{args.arch}.json"
    out.write_text(json.dumps(payload, indent=2) + "\n")

    print(f"checksum: {safe_checksum}")
    print(f"default mean: {default['mean']:.6f}s")
    print(f"fnv1a mean:   {fnv['mean']:.6f}s")
    print(f"default/fnv:  {ratio:.4f}x")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
