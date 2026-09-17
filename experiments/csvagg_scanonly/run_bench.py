"""Category-D scanner-only versus parser-only semantic-boundary decomposition.

Preserve file read and all four delimiter scans in a scanner-only Mojo/C pair,
remove quantity/price digit accumulation, and run those binaries in the same
interleaved rounds as the existing parser-only pair. The ratio movement tells us
whether the severe parser-prefix gap already exists before numeric parsing.
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
        [str(binary), "--csv", str(csv)], cwd=ROOT, capture_output=True, text=True, check=True
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
    p.add_argument("--bin-dir", type=Path, default=Path("/tmp/csvagg-scanonly"))
    p.add_argument("--out-dir", type=Path, default=Path("/tmp/csvagg-scanonly"))
    args = p.parse_args()

    csv = ROOT / "benchmarks" / "csvagg" / "data" / "orders.csv"
    names = ["scan-mojo", "scan-c", "parser-mojo", "parser-c"]
    bins = {name: args.bin_dir / name for name in names}
    times = {name: [] for name in names}
    checksums = {name: set() for name in names}

    for round_idx in range(args.warmup + args.trials):
        offset = round_idx % len(names)
        order = names[offset:] + names[:offset]
        for name in order:
            elapsed, checksum = one_run(bins[name], csv)
            checksums[name].add(checksum)
            if round_idx >= args.warmup:
                times[name].append(elapsed)

    results = {name: summarize(times[name], checksums[name]) for name in names}
    if results["scan-mojo"]["checksum"] != results["scan-c"]["checksum"]:
        raise RuntimeError("scanner-only Mojo/C checksum mismatch")
    if results["parser-mojo"]["checksum"] != results["parser-c"]["checksum"]:
        raise RuntimeError("parser-only Mojo/C checksum mismatch")

    sm = results["scan-mojo"]["mean"]
    sc = results["scan-c"]["mean"]
    pm = results["parser-mojo"]["mean"]
    pc = results["parser-c"]["mean"]
    payload = {
        "question": "How much of Category-D's parser-prefix Mojo-vs-C gap exists before quantity/price numeric parsing?",
        "arch": args.arch,
        "trials": args.trials,
        "warmup": args.warmup,
        "interleaved_rounds": True,
        "scanner_checksum_ok": True,
        "parser_checksum_ok": True,
        "results": results,
        "ratios": {
            "scanner_mojo_over_c": sm / sc,
            "parser_mojo_over_c": pm / pc,
            "ratio_change_with_numeric_parse": (pm / pc) - (sm / sc),
            "mojo_scanner_fraction_of_parser": sm / pm,
            "c_scanner_fraction_of_parser": sc / pc,
        },
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out = args.out_dir / f"csvagg-scanonly-{args.arch}.json"
    out.write_text(json.dumps(payload, indent=2) + "\n")

    print(f"scanner checksum: {results['scan-mojo']['checksum']}")
    print(f"parser checksum:  {results['parser-mojo']['checksum']}")
    for name in names:
        r = results[name]
        print(f"{name:12s} mean/median: {r['mean']:.6f}s / {r['median']:.6f}s")
    print(f"scanner Mojo/C: {payload['ratios']['scanner_mojo_over_c']:.4f}x")
    print(f"parser Mojo/C:  {payload['ratios']['parser_mojo_over_c']:.4f}x")
    print(f"Mojo scan/parser: {payload['ratios']['mojo_scanner_fraction_of_parser']:.3f}")
    print(f"C scan/parser:    {payload['ratios']['c_scanner_fraction_of_parser']:.3f}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
