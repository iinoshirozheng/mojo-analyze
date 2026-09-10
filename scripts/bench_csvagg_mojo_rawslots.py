"""Measure Category D Mojo List-slot vs raw-pointer-slot hash-table storage.

The two binaries use the same CSV input, parser, byte-span keys, FNV-1a hash,
open-addressing probe sequence, aggregation, and checksum. The experimental
variant changes only the five fixed-capacity slot arrays from List[...] to raw
pointers with unsafe_offset indexing.
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
    parser.add_argument("--trials", type=int, default=7)
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--arch", default="unknown")
    args = parser.parse_args()

    csv = ROOT / "benchmarks" / "csvagg" / "data" / "orders.csv"
    exp = ROOT / "dist" / "experiments"
    canonical = run(exp / "csvagg-mojo-list", csv, args.trials, args.warmup)
    raw = run(exp / "csvagg-mojo-rawslots", csv, args.trials, args.warmup)

    if canonical["checksum"] != raw["checksum"]:
        raise RuntimeError(
            "checksum mismatch: "
            f"list={canonical['checksum']} raw={raw['checksum']}"
        )

    ratio = canonical["mean"] / raw["mean"]
    payload = {
        "question": "Do raw-pointer slot arrays materially reduce Category D Mojo hash-table storage overhead?",
        "arch": args.arch,
        "trials": args.trials,
        "warmup": args.warmup,
        "list_slots": canonical,
        "raw_pointer_slots": raw,
        "list_over_raw_ratio": ratio,
        "checksum_ok": True,
        "assembly": {
            "list_slots": asm_info(exp / f"csvagg-mojo-list-{args.arch}.s"),
            "raw_pointer_slots": asm_info(exp / f"csvagg-mojo-rawslots-{args.arch}.s"),
        },
    }

    out = ROOT / "results" / "experiments" / f"csvagg-mojo-rawslots-{args.arch}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")

    print(f"checksum agreement: {canonical['checksum']}")
    print(f"List-slot mean: {canonical['mean']:.6f}s")
    print(f"raw-slot mean:  {raw['mean']:.6f}s")
    print(f"List/raw:       {ratio:.4f}x")
    print(f"List asm:       {payload['assembly']['list_slots']}")
    print(f"raw asm:        {payload['assembly']['raw_pointer_slots']}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
