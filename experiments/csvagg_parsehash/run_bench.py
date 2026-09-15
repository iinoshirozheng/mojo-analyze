"""Category-D parse+hash decomposition.

Measure the canonical CSV aggregation implementations alongside variants that
preserve file read, delimiter scans, numeric parsing, and variable-length
FNV-1a hashing but remove table probing/equality/aggregation. The parse+hash
variants have their own shared checksum contract; canonical implementations
retain the existing Category-D checksum. Runs are interleaved by round to
reduce shared-runner drift bias.
"""

import argparse
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


def one_run(binary: Path, csv: Path):
    proc = subprocess.run(
        [str(binary), "--csv", str(csv)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return parse_output(proc.stdout)


def summarize(times, checksums):
    if len(checksums) != 1:
        raise RuntimeError(f"nondeterministic checksums: {checksums}")
    return {
        "times": times,
        "checksum": next(iter(checksums)),
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "stdev": statistics.stdev(times) if len(times) > 1 else 0.0,
        "min": min(times),
        "max": max(times),
        "n": len(times),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--arch", required=True)
    p.add_argument("--trials", type=int, default=7)
    p.add_argument("--warmup", type=int, default=2)
    p.add_argument("--bin-dir", type=Path, default=Path("/tmp/csvagg-parsehash"))
    p.add_argument("--out-dir", type=Path, default=Path("/tmp/csvagg-parsehash"))
    args = p.parse_args()

    csv = ROOT / "benchmarks" / "csvagg" / "data" / "orders.csv"
    names = ["parsehash-mojo", "parsehash-c", "full-mojo", "full-c"]
    bins = {name: args.bin_dir / name for name in names}
    times = {name: [] for name in names}
    checksums = {name: set() for name in names}

    # Two warmup rounds plus seven measured rounds. Rotate the first binary
    # each round so one implementation does not systematically run first/last.
    for round_idx in range(args.warmup + args.trials):
        offset = round_idx % len(names)
        order = names[offset:] + names[:offset]
        for name in order:
            elapsed, checksum = one_run(bins[name], csv)
            checksums[name].add(checksum)
            if round_idx >= args.warmup:
                times[name].append(elapsed)

    results = {name: summarize(times[name], checksums[name]) for name in names}

    if results["parsehash-mojo"]["checksum"] != results["parsehash-c"]["checksum"]:
        raise RuntimeError(
            "parse+hash checksum mismatch: "
            f"Mojo={results['parsehash-mojo']['checksum']} C={results['parsehash-c']['checksum']}"
        )
    if results["full-mojo"]["checksum"] != results["full-c"]["checksum"]:
        raise RuntimeError(
            "canonical checksum mismatch: "
            f"Mojo={results['full-mojo']['checksum']} C={results['full-c']['checksum']}"
        )

    ph_m = results["parsehash-mojo"]["mean"]
    ph_c = results["parsehash-c"]["mean"]
    full_m = results["full-mojo"]["mean"]
    full_c = results["full-c"]["mean"]

    payload = {
        "question": "How much of the Category-D Mojo-vs-C gap is already present after file read, delimiter scanning, numeric parsing, and FNV hashing, before table probing/equality/aggregation?",
        "arch": args.arch,
        "trials": args.trials,
        "warmup": args.warmup,
        "interleaved_rounds": True,
        "parsehash_checksum_ok": True,
        "canonical_checksum_ok": True,
        "results": results,
        "ratios": {
            "parsehash_mojo_over_c": ph_m / ph_c,
            "full_mojo_over_c": full_m / full_c,
            "mojo_parsehash_fraction_of_full": ph_m / full_m,
            "c_parsehash_fraction_of_full": ph_c / full_c,
            "ratio_reduction_after_removing_table": (full_m / full_c) - (ph_m / ph_c),
        },
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out = args.out_dir / f"csvagg-parsehash-{args.arch}.json"
    out.write_text(json.dumps(payload, indent=2) + "\n")

    print(f"parse+hash checksum: {results['parsehash-mojo']['checksum']}")
    print(f"canonical checksum: {results['full-mojo']['checksum']}")
    for name in names:
        r = results[name]
        print(f"{name:14s} mean/median: {r['mean']:.6f}s / {r['median']:.6f}s")
    print(f"parse+hash Mojo/C: {payload['ratios']['parsehash_mojo_over_c']:.4f}x")
    print(f"full Mojo/C:       {payload['ratios']['full_mojo_over_c']:.4f}x")
    print(f"Mojo parse+hash/full: {payload['ratios']['mojo_parsehash_fraction_of_full']:.3f}")
    print(f"C parse+hash/full:    {payload['ratios']['c_parsehash_fraction_of_full']:.3f}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
