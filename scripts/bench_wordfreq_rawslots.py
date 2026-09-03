"""Measure category C's Mojo List-slot vs raw-pointer-slot hash table.

The two Mojo binaries use the same corpus parser, FNV-1a hash, open-addressing
probe sequence, byte-span keys, sorting, and checksum. The experimental variant
changes only the five fixed-capacity slot arrays from List[...] to raw pointers.
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


def run(binary: Path, corpus: Path, trials: int, warmup: int):
    times = []
    checksums = set()
    for n in range(warmup + trials):
        proc = subprocess.run(
            [str(binary), "--corpus", str(corpus)],
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
    parser.add_argument("--trials", type=int, default=7)
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--arch", default="unknown")
    args = parser.parse_args()

    corpus = ROOT / "benchmarks" / "wordfreq" / "data" / "corpus.txt"
    canonical = run(ROOT / "dist" / "wordfreq-mojo-list", corpus, args.trials, args.warmup)
    raw = run(ROOT / "dist" / "wordfreq-mojo-rawslots", corpus, args.trials, args.warmup)

    if canonical["checksum"] != raw["checksum"]:
        raise RuntimeError(
            "checksum mismatch: "
            f"list={canonical['checksum']} raw={raw['checksum']}"
        )

    ratio = canonical["mean"] / raw["mean"]
    payload = {
        "question": "Do raw-pointer hash-table slot arrays remove category C's Mojo List overhead?",
        "arch": args.arch,
        "trials": args.trials,
        "warmup": args.warmup,
        "list_slots": canonical,
        "raw_pointer_slots": raw,
        "list_over_raw_ratio": ratio,
        "checksum_ok": True,
    }

    out = ROOT / "results" / "experiments" / f"wordfreq-mojo-rawslots-{args.arch}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")

    print(f"checksum agreement: {canonical['checksum']}")
    print(f"List-slot mean: {canonical['mean']:.6f}s")
    print(f"raw-slot mean:  {raw['mean']:.6f}s")
    print(f"List/raw:       {ratio:.4f}x")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
