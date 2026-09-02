"""Isolate the cost of Rust bounds checks in category B's hot marking write.

Runs the existing safe Rust sieve against an otherwise-identical variant whose
inner `is_prime[j] = false` uses `get_unchecked_mut`. Both binaries keep the
same timing/checksum output contract as the main harness.

This deliberately does *not* replace the canonical Rust result. It is a
one-variable experiment answering a causal question from CONTRIBUTING.md.
"""

import argparse
import json
import statistics
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def parse_output(stdout: str):
    elapsed = None
    checksum = None
    for line in stdout.splitlines():
        if line.startswith("TIME_SECONDS:"):
            elapsed = float(line.split(":", 1)[1].strip())
        elif line.startswith("CHECKSUM:"):
            checksum = line.split(":", 1)[1].strip()
    if elapsed is None or checksum is None:
        raise RuntimeError(f"missing timing/checksum in output:\n{stdout}")
    return elapsed, checksum


def run(binary: Path, limit: int, trials: int, warmup: int):
    times = []
    checksums = set()
    for n in range(warmup + trials):
        proc = subprocess.run(
            [str(binary), "--limit", str(limit)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        elapsed, checksum = parse_output(proc.stdout)
        checksums.add(checksum)
        if n >= warmup:
            times.append(elapsed)
    if len(checksums) != 1:
        raise RuntimeError(f"{binary.name}: nondeterministic checksums {checksums}")
    return {
        "times": times,
        "checksum": checksums.pop(),
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "stdev": statistics.stdev(times) if len(times) > 1 else 0.0,
        "min": min(times),
        "max": max(times),
        "n": len(times),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=50_000_000)
    parser.add_argument("--trials", type=int, default=7)
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--arch", default="unknown")
    args = parser.parse_args()

    release = ROOT / "rust" / "target" / "release"
    safe = run(release / "sieve", args.limit, args.trials, args.warmup)
    unsafe = run(release / "sieve_unsafe", args.limit, args.trials, args.warmup)

    if safe["checksum"] != unsafe["checksum"]:
        raise RuntimeError(
            f"checksum mismatch: safe={safe['checksum']} unsafe={unsafe['checksum']}"
        )

    ratio = safe["mean"] / unsafe["mean"]
    payload = {
        "question": "Does removing only the Rust sieve hot-write bounds check explain its gap?",
        "arch": args.arch,
        "limit": args.limit,
        "trials": args.trials,
        "warmup": args.warmup,
        "safe": safe,
        "unsafe_marking_write": unsafe,
        "safe_over_unsafe_ratio": ratio,
        "checksum_ok": True,
    }

    out = ROOT / "results" / "experiments" / f"sieve-rust-unsafe-{args.arch}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")

    print(f"checksum agreement: {safe['checksum']}")
    print(f"safe mean:   {safe['mean']:.6f}s")
    print(f"unsafe mean: {unsafe['mean']:.6f}s")
    print(f"safe/unsafe: {ratio:.4f}x")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
