"""Focused Category-D variable-length FNV unrolling experiment.

Compare the canonical Mojo CSV aggregation implementation against a variant
that changes only the variable-length FNV-1a byte loop to four explicitly
unrolled dependent steps plus a scalar tail. C is reported only as context.
All implementations must agree on CHECKSUM before timings are accepted.
"""

import argparse
import hashlib
import json
import statistics
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


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


def run(binary: Path, csv: Path, trials: int, warmup: int):
    times = []
    checksums = set()
    for n in range(warmup + trials):
        proc = subprocess.run(
            [str(binary), "--csv", str(csv)],
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


def file_info(path: Path):
    data = path.read_bytes()
    return {
        "bytes": len(data),
        "lines": data.count(b"\n"),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--arch", required=True)
    p.add_argument("--trials", type=int, default=7)
    p.add_argument("--warmup", type=int, default=2)
    p.add_argument("--bin-dir", type=Path, default=Path("/tmp/csvagg-unroll"))
    p.add_argument("--out-dir", type=Path, default=Path("/tmp/csvagg-unroll"))
    args = p.parse_args()

    csv = ROOT / "benchmarks" / "csvagg" / "data" / "orders.csv"
    baseline = run(args.bin_dir / "csvagg-mojo-baseline", csv, args.trials, args.warmup)
    unroll4 = run(args.bin_dir / "csvagg-mojo-unroll4", csv, args.trials, args.warmup)
    c_impl = run(args.bin_dir / "csvagg-c", csv, args.trials, args.warmup)

    checksums = {baseline["checksum"], unroll4["checksum"], c_impl["checksum"]}
    if len(checksums) != 1:
        raise RuntimeError(
            "checksum mismatch: "
            f"baseline={baseline['checksum']} unroll4={unroll4['checksum']} c={c_impl['checksum']}"
        )

    payload = {
        "question": "Does 4x manual unrolling of the real variable-length Category-D FNV loop materially improve end-to-end Mojo CSV aggregation?",
        "arch": args.arch,
        "trials": args.trials,
        "warmup": args.warmup,
        "checksum_ok": True,
        "checksum": baseline["checksum"],
        "mojo_baseline": baseline,
        "mojo_unroll4": unroll4,
        "c_context": c_impl,
        "baseline_over_unroll4": baseline["mean"] / unroll4["mean"],
        "unroll4_speedup_pct": (baseline["mean"] / unroll4["mean"] - 1.0) * 100.0,
        "unroll4_over_c": unroll4["mean"] / c_impl["mean"],
        "assembly": {
            "baseline": file_info(args.bin_dir / f"csvagg-mojo-baseline-{args.arch}.s"),
            "unroll4": file_info(args.bin_dir / f"csvagg-mojo-unroll4-{args.arch}.s"),
            "c": file_info(args.bin_dir / f"csvagg-c-{args.arch}.s"),
        },
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out = args.out_dir / f"csvagg-hash-unroll-{args.arch}.json"
    out.write_text(json.dumps(payload, indent=2) + "\n")

    print(f"checksum agreement: {baseline['checksum']}")
    print(f"baseline mean/median: {baseline['mean']:.6f}s / {baseline['median']:.6f}s")
    print(f"unroll4  mean/median: {unroll4['mean']:.6f}s / {unroll4['median']:.6f}s")
    print(f"C        mean/median: {c_impl['mean']:.6f}s / {c_impl['median']:.6f}s")
    print(f"baseline/unroll4: {payload['baseline_over_unroll4']:.4f}x")
    print(f"unroll4 speedup: {payload['unroll4_speedup_pct']:.2f}%")
    print(f"unroll4/C: {payload['unroll4_over_c']:.4f}x")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
