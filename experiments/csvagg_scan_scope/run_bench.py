"""Category-D file-ingestion versus in-memory scanner timing boundary.

Run one Mojo binary and one C binary under two timing scopes:
- full: timer starts before reading the CSV from disk
- scan: exact same CSV bytes are loaded before the timer

Both scopes then execute the same scanner implementation and emit the same
checksum. This localizes whether the cross-language ratio is dominated by file
materialization or remains in byte scanning / loop control.
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
    scope = None
    for line in stdout.splitlines():
        if line.startswith("SCOPE:"):
            scope = line.split(":", 1)[1].strip()
        elif line.startswith("TIME_SECONDS:"):
            elapsed = float(line.split(":", 1)[1].strip())
        elif line.startswith("CHECKSUM:"):
            checksum = line.split(":", 1)[1].strip()
    if elapsed is None or checksum is None or scope is None:
        raise RuntimeError(f"missing scope/timing/checksum in output:\n{stdout}")
    return scope, elapsed, checksum


def one_run(binary: Path, csv: Path, scope: str):
    proc = subprocess.run(
        [str(binary), "--csv", str(csv), "--scope", scope],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    got_scope, elapsed, checksum = parse_output(proc.stdout)
    if got_scope != scope:
        raise RuntimeError(f"scope mismatch: asked {scope}, got {got_scope}")
    return elapsed, checksum


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
    p.add_argument("--bin-dir", type=Path, default=Path("/tmp/csvagg-scan-scope"))
    p.add_argument("--out-dir", type=Path, default=Path("/tmp/csvagg-scan-scope"))
    args = p.parse_args()

    csv = ROOT / "benchmarks" / "csvagg" / "data" / "orders.csv"
    variants = [
        ("mojo-full", "mojo", "full"),
        ("c-full", "c", "full"),
        ("mojo-scan", "mojo", "scan"),
        ("c-scan", "c", "scan"),
    ]
    bins = {"mojo": args.bin_dir / "scan-scope-mojo", "c": args.bin_dir / "scan-scope-c"}
    times = {name: [] for name, _, _ in variants}
    checksums = {name: set() for name, _, _ in variants}

    for round_idx in range(args.warmup + args.trials):
        offset = round_idx % len(variants)
        order = variants[offset:] + variants[:offset]
        for name, lang, scope in order:
            elapsed, checksum = one_run(bins[lang], csv, scope)
            checksums[name].add(checksum)
            if round_idx >= args.warmup:
                times[name].append(elapsed)

    results = {name: summarize(times[name], checksums[name]) for name, _, _ in variants}
    checksum_set = {r["checksum"] for r in results.values()}
    if len(checksum_set) != 1:
        raise RuntimeError(f"cross-language/scope checksum mismatch: {checksum_set}")

    mf = results["mojo-full"]["mean"]
    cf = results["c-full"]["mean"]
    ms = results["mojo-scan"]["mean"]
    cs = results["c-scan"]["mean"]
    payload = {
        "question": "Does excluding bulk file ingestion materially collapse Category-D's scanner-only Mojo-vs-C gap?",
        "arch": args.arch,
        "trials": args.trials,
        "warmup": args.warmup,
        "interleaved_rounds": True,
        "same_binary_per_language": True,
        "cross_scope_checksum_ok": True,
        "results": results,
        "ratios": {
            "full_mojo_over_c": mf / cf,
            "scan_mojo_over_c": ms / cs,
            "ratio_change_after_excluding_file_ingestion": (ms / cs) - (mf / cf),
            "mojo_scan_fraction_of_full": ms / mf,
            "c_scan_fraction_of_full": cs / cf,
        },
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out = args.out_dir / f"csvagg-scan-scope-{args.arch}.json"
    out.write_text(json.dumps(payload, indent=2) + "\n")

    print(f"checksum: {next(iter(checksum_set))}")
    for name, _, _ in variants:
        r = results[name]
        print(
            f"{name:10s} mean/median/stdev: "
            f"{r['mean']:.6f}s / {r['median']:.6f}s / {r['stdev']:.6f}s"
        )
    print(f"full Mojo/C: {payload['ratios']['full_mojo_over_c']:.4f}x")
    print(f"scan Mojo/C: {payload['ratios']['scan_mojo_over_c']:.4f}x")
    print(f"Mojo scan/full: {payload['ratios']['mojo_scan_fraction_of_full']:.4f}")
    print(f"C scan/full: {payload['ratios']['c_scan_fraction_of_full']:.4f}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
