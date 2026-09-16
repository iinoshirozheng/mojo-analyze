"""Category-D parser-only versus parse+hash decomposition.

Preserve file read, delimiter scans, category-span discovery, and quantity/price
parsing in a parser-only Mojo/C pair. Run those binaries in the same
interleaved rounds as the existing parse+hash pair, so the change in the
Mojo/C ratio at the semantic boundary can show whether variable-length FNV
materially widens the cross-language gap.
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
    p.add_argument("--bin-dir", type=Path, default=Path("/tmp/csvagg-parseronly"))
    p.add_argument("--out-dir", type=Path, default=Path("/tmp/csvagg-parseronly"))
    args = p.parse_args()

    csv = ROOT / "benchmarks" / "csvagg" / "data" / "orders.csv"
    names = ["parser-mojo", "parser-c", "parsehash-mojo", "parsehash-c"]
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
    if results["parser-mojo"]["checksum"] != results["parser-c"]["checksum"]:
        raise RuntimeError("parser-only Mojo/C checksum mismatch")
    if results["parsehash-mojo"]["checksum"] != results["parsehash-c"]["checksum"]:
        raise RuntimeError("parse+hash Mojo/C checksum mismatch")

    pm = results["parser-mojo"]["mean"]
    pc = results["parser-c"]["mean"]
    hm = results["parsehash-mojo"]["mean"]
    hc = results["parsehash-c"]["mean"]
    payload = {
        "question": "How much of Category-D's pre-table Mojo-vs-C gap exists before variable-length FNV hashing?",
        "arch": args.arch,
        "trials": args.trials,
        "warmup": args.warmup,
        "interleaved_rounds": True,
        "parser_checksum_ok": True,
        "parsehash_checksum_ok": True,
        "results": results,
        "ratios": {
            "parser_mojo_over_c": pm / pc,
            "parsehash_mojo_over_c": hm / hc,
            "ratio_increase_with_hash": (hm / hc) - (pm / pc),
            "mojo_parser_fraction_of_parsehash": pm / hm,
            "c_parser_fraction_of_parsehash": pc / hc,
        },
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out = args.out_dir / f"csvagg-parseronly-{args.arch}.json"
    out.write_text(json.dumps(payload, indent=2) + "\n")

    print(f"parser checksum: {results['parser-mojo']['checksum']}")
    print(f"parse+hash checksum: {results['parsehash-mojo']['checksum']}")
    for name in names:
        r = results[name]
        print(f"{name:14s} mean/median: {r['mean']:.6f}s / {r['median']:.6f}s")
    print(f"parser Mojo/C:     {payload['ratios']['parser_mojo_over_c']:.4f}x")
    print(f"parse+hash Mojo/C: {payload['ratios']['parsehash_mojo_over_c']:.4f}x")
    print(f"Mojo parser/parse+hash: {payload['ratios']['mojo_parser_fraction_of_parsehash']:.3f}")
    print(f"C parser/parse+hash:    {payload['ratios']['c_parser_fraction_of_parsehash']:.3f}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
