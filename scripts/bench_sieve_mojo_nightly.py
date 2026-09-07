"""Compare category-B Sieve under stable Mojo and one exact nightly compiler.

Both binaries are built from the same source and keep the benchmark's existing
TIME_SECONDS/CHECKSUM contract. This is an advisory compiler-differential
experiment: it does not replace the canonical stable result.
"""

import argparse
import hashlib
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


def asm_info(path: Path):
    data = path.read_bytes()
    text = data.decode("utf-8", errors="replace")
    return {
        "bytes": len(data),
        "lines": text.count("\n"),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=50_000_000)
    parser.add_argument("--trials", type=int, default=7)
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--arch", default="unknown")
    parser.add_argument("--stable-version", required=True)
    parser.add_argument("--nightly-version", required=True)
    args = parser.parse_args()

    exp = ROOT / "dist" / "experiments"
    stable = run(exp / "sieve-mojo-stable", args.limit, args.trials, args.warmup)
    nightly = run(exp / "sieve-mojo-nightly", args.limit, args.trials, args.warmup)

    if stable["checksum"] != nightly["checksum"]:
        raise RuntimeError(
            f"checksum mismatch: stable={stable['checksum']} nightly={nightly['checksum']}"
        )

    ratio = stable["mean"] / nightly["mean"]
    payload = {
        "question": "Does the Sep-7 Mojo 1.1 nightly materially change category-B Sieve versus stable Mojo 1.0?",
        "arch": args.arch,
        "limit": args.limit,
        "trials": args.trials,
        "warmup": args.warmup,
        "stable_version": args.stable_version,
        "nightly_version": args.nightly_version,
        "stable": stable,
        "nightly": nightly,
        "stable_over_nightly_ratio": ratio,
        "checksum_ok": True,
        "assembly": {
            "stable": asm_info(exp / "sieve-mojo-stable.s"),
            "nightly": asm_info(exp / "sieve-mojo-nightly.s"),
        },
    }

    out = ROOT / "results" / "experiments" / f"sieve-mojo-nightly-20260907-{args.arch}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")

    print(f"checksum agreement: {stable['checksum']}")
    print(f"stable mean:  {stable['mean']:.6f}s")
    print(f"nightly mean: {nightly['mean']:.6f}s")
    print(f"stable/nightly: {ratio:.4f}x")
    print(f"stable asm:  {payload['assembly']['stable']}")
    print(f"nightly asm: {payload['assembly']['nightly']}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
