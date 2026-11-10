"""Benchmark harness: runs each language variant of each benchmark N times,
verifies correctness via checksum agreement, and reports timing statistics.

Cross-variant checksum failure aborts the run before results.json is written.
Timing summaries are published only after all selected categories validate.

Usage:
    pixi run bench
    pixi run bench --trials 7 --only mandelbrot,sieve
"""

import argparse
import json
import math
import statistics
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable

BENCHMARKS = [
    {
        "name": "mandelbrot",
        "category": "A — SIMD-friendly, compute-dense",
        "params": {"width": 800, "height": 600, "max_iter": 500},
        "variants": [
            {
                "label": "mojo",
                "cmd": [
                    str(ROOT / "dist" / "mandelbrot-mojo"),
                    "--width", "800", "--height", "600", "--max-iter", "500",
                ],
            },
            {
                "label": "rust",
                "cmd": [
                    str(ROOT / "dist" / "mandelbrot-rust"),
                    "--width", "800", "--height", "600", "--max-iter", "500",
                ],
            },
            {
                "label": "c",
                "cmd": [
                    str(ROOT / "dist" / "mandelbrot-c"),
                    "--width", "800", "--height", "600", "--max-iter", "500",
                ],
            },
            {
                "label": "numpy",
                "cmd": [
                    PY, str(ROOT / "benchmarks/mandelbrot/mandelbrot_numpy.py"),
                    "--width", "800", "--height", "600", "--max-iter", "500",
                ],
            },
            {
                "label": "python",
                "cmd": [
                    PY, str(ROOT / "benchmarks/mandelbrot/mandelbrot_python.py"),
                    "--width", "800", "--height", "600", "--max-iter", "500",
                ],
            },
        ],
    },
    {
        "name": "sieve",
        "category": "B — memory/branch-intensive, not SIMD-friendly",
        "params": {"limit": 50_000_000},
        "variants": [
            {
                "label": "mojo",
                "cmd": [str(ROOT / "dist" / "sieve-mojo"), "--limit", "50000000"],
            },
            {
                "label": "rust",
                "cmd": [str(ROOT / "dist" / "sieve-rust"), "--limit", "50000000"],
            },
            {
                "label": "c",
                "cmd": [str(ROOT / "dist" / "sieve-c"), "--limit", "50000000"],
            },
            {
                "label": "numpy",
                "cmd": [
                    PY, str(ROOT / "benchmarks/sieve/sieve_numpy.py"),
                    "--limit", "50000000",
                ],
            },
            {
                "label": "python",
                "cmd": [
                    PY, str(ROOT / "benchmarks/sieve/sieve_python.py"),
                    "--limit", "50000000",
                ],
            },
        ],
    },
    {
        "name": "wordfreq",
        "category": "C — real-world string/hash-table processing",
        "params": {"corpus": "benchmarks/wordfreq/data/corpus.txt"},
        "variants": [
            {
                "label": "mojo",
                "cmd": [
                    str(ROOT / "dist" / "wordfreq-mojo"),
                    "--corpus", str(ROOT / "benchmarks/wordfreq/data/corpus.txt"),
                ],
            },
            {
                "label": "rust",
                "cmd": [
                    str(ROOT / "dist" / "wordfreq-rust"),
                    "--corpus", str(ROOT / "benchmarks/wordfreq/data/corpus.txt"),
                ],
            },
            {
                "label": "c",
                "cmd": [
                    str(ROOT / "dist" / "wordfreq-c"),
                    "--corpus", str(ROOT / "benchmarks/wordfreq/data/corpus.txt"),
                ],
            },
            {
                "label": "python (Counter)",
                "cmd": [
                    PY, str(ROOT / "benchmarks/wordfreq/wordfreq_counter.py"),
                    "--corpus", str(ROOT / "benchmarks/wordfreq/data/corpus.txt"),
                ],
            },
            {
                "label": "python (dict)",
                "cmd": [
                    PY, str(ROOT / "benchmarks/wordfreq/wordfreq_python.py"),
                    "--corpus", str(ROOT / "benchmarks/wordfreq/data/corpus.txt"),
                ],
            },
        ],
    },
    {
        "name": "csvagg",
        "category": "D — real-world tabular CSV aggregation",
        "params": {"csv": "benchmarks/csvagg/data/orders.csv"},
        "variants": [
            {
                "label": "mojo",
                "cmd": [
                    str(ROOT / "dist" / "csvagg-mojo"),
                    "--csv", str(ROOT / "benchmarks/csvagg/data/orders.csv"),
                ],
            },
            {
                "label": "rust",
                "cmd": [
                    str(ROOT / "dist" / "csvagg-rust"),
                    "--csv", str(ROOT / "benchmarks/csvagg/data/orders.csv"),
                ],
            },
            {
                "label": "c",
                "cmd": [
                    str(ROOT / "dist" / "csvagg-c"),
                    "--csv", str(ROOT / "benchmarks/csvagg/data/orders.csv"),
                ],
            },
            {
                "label": "python (pandas)",
                "cmd": [
                    PY, str(ROOT / "benchmarks/csvagg/csvagg_pandas.py"),
                    "--csv", str(ROOT / "benchmarks/csvagg/data/orders.csv"),
                ],
            },
            {
                "label": "python (manual)",
                "cmd": [
                    PY, str(ROOT / "benchmarks/csvagg/csvagg_python.py"),
                    "--csv", str(ROOT / "benchmarks/csvagg/data/orders.csv"),
                ],
            },
        ],
    },
    {
        "name": "jsonparse",
        "category": "E — real-world nested JSON parsing",
        "params": {"json": "benchmarks/jsonparse/data/events.json"},
        "variants": [
            {
                "label": "mojo",
                "cmd": [
                    str(ROOT / "dist" / "jsonparse-mojo"),
                    "--json", str(ROOT / "benchmarks/jsonparse/data/events.json"),
                ],
            },
            {
                "label": "rust",
                "cmd": [
                    str(ROOT / "dist" / "jsonparse-rust"),
                    "--json", str(ROOT / "benchmarks/jsonparse/data/events.json"),
                ],
            },
            {
                "label": "c",
                "cmd": [
                    str(ROOT / "dist" / "jsonparse-c"),
                    "--json", str(ROOT / "benchmarks/jsonparse/data/events.json"),
                ],
            },
            {
                "label": "python (json)",
                "cmd": [
                    PY, str(ROOT / "benchmarks/jsonparse/jsonparse_stdlib.py"),
                    "--json", str(ROOT / "benchmarks/jsonparse/data/events.json"),
                ],
            },
            {
                "label": "python (manual)",
                "cmd": [
                    PY, str(ROOT / "benchmarks/jsonparse/jsonparse_python.py"),
                    "--json", str(ROOT / "benchmarks/jsonparse/data/events.json"),
                ],
            },
        ],
    },
]


def parse_output(stdout):
    time_seconds = None
    checksum = None
    for line in stdout.splitlines():
        line = line.strip()
        if line.startswith("TIME_SECONDS:"):
            if time_seconds is not None:
                raise RuntimeError("duplicate TIME_SECONDS in benchmark stdout")
            time_seconds = float(line.split(":", 1)[1].strip())
        elif line.startswith("CHECKSUM:"):
            if checksum is not None:
                raise RuntimeError("duplicate CHECKSUM in benchmark stdout")
            checksum = line.split(":", 1)[1].strip()
            if not checksum:
                raise RuntimeError("empty CHECKSUM in benchmark stdout")
    return time_seconds, checksum


def run_variant(cmd, trials, warmup):
    times = []
    checksums = set()
    for i in range(warmup + trials):
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
        if result.returncode != 0:
            raise RuntimeError(
                f"command failed ({result.returncode}): {' '.join(cmd)}\n"
                f"stderr:\n{result.stderr}"
            )
        t, c = parse_output(result.stdout)
        if t is None or c is None:
            raise RuntimeError(
                f"missing TIME_SECONDS/CHECKSUM in output of: {' '.join(cmd)}\n"
                f"stdout:\n{result.stdout}"
            )
        # The stdout protocol is untrusted input. Python accepts nan/inf,
        # and json.dumps permits NaN/Infinity by default; a nonpositive or
        # nonfinite duration cannot support a valid benchmark comparison.
        if not math.isfinite(t) or t <= 0:
            raise RuntimeError(
                f"invalid TIME_SECONDS {t!r} from: {' '.join(cmd)}\\n"
                "Expected a finite, strictly positive elapsed time; "
                "refusing to publish benchmark results."
            )
        checksums.add(c)
        if i >= warmup:
            times.append(t)
    if len(checksums) != 1:
        raise RuntimeError(
            f"non-deterministic checksum across runs of: {' '.join(cmd)}\n"
            f"checksums seen: {checksums}"
        )
    return times, checksums.pop()


def stats(times):
    return {
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "stdev": statistics.stdev(times) if len(times) > 1 else 0.0,
        "min": min(times),
        "max": max(times),
        "n": len(times),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=5)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--only", type=str, default=None,
                         help="comma-separated benchmark names to run")
    args = parser.parse_args()
    # Reject invalid trial protocols before launching children or touching results.
    # Zero trials has no sample statistics; negative warmups silently change
    # which iterations count as measurements.
    if args.trials < 1:
        parser.error("--trials must be at least 1")
    if args.warmup < 0:
        parser.error("--warmup must be nonnegative")

    # An explicit selection must resolve to real benchmark categories.  A
    # typo or an empty token must not turn a requested run into a successful
    # no-op that republishes the previous results as though tested.
    only = None
    if args.only is not None:
        names = [name.strip() for name in args.only.split(",")]
        available = {bench["name"] for bench in BENCHMARKS}
        if not all(names):
            parser.error("--only requires nonempty comma-separated benchmark names")
        unknown = sorted(set(names) - available)
        if unknown:
            parser.error(
                "unknown benchmark(s) in --only: " + ", ".join(unknown)
                + "; available: " + ", ".join(sorted(available))
            )
        only = set(names)
    benchmarks = [b for b in BENCHMARKS if only is None or b["name"] in only]

    # A partial (--only) run must not wipe out other categories already in
    # results.json -- merge into whatever's there instead of starting fresh.
    # A full run (no --only) starts clean, since it's meant to be the
    # canonical, complete snapshot.
    out_path = ROOT / "results" / "results.json"
    if only is not None and out_path.exists():
        results = json.loads(out_path.read_text())
    else:
        results = {}
    for bench in benchmarks:
        print(f"\n=== {bench['name']} ({bench['category']}) ===")
        bench_checksums = {}
        bench_results = {}
        for variant in bench["variants"]:
            label = variant["label"]
            print(f"  running {label}...", end=" ", flush=True)
            times, checksum = run_variant(variant["cmd"], args.trials, args.warmup)
            bench_checksums[label] = checksum
            bench_results[label] = {"times": times, "checksum": checksum, **stats(times)}
            print(f"collected {len(times)} trials; checksum validation pending")

        distinct = set(bench_checksums.values())
        if len(distinct) != 1:
            # Fail closed: a warning/JSON flag is not a failing CI exit status.
            # Results are staged in memory until every selected category passes,
            # so a failed full or partial run leaves the previous file untouched.
            raise RuntimeError(
                f"CHECKSUM MISMATCH for {bench['name']} across variants: "
                f"{bench_checksums}\n"
                "Refusing to publish timings or overwrite results/results.json."
            )
        print(f"  checksum agreement: {distinct.pop()}")
        bench_results["_checksum_ok"] = True

        results[bench["name"]] = {
            "category": bench["category"],
            "params": bench["params"],
            "variants": bench_results,
        }

    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2))
    print(f"\nWrote {out_path}")

    print("\n=== Summary (mean seconds, lower is better) ===")
    for name, data in results.items():
        print(f"\n{name}:")
        base = None
        for label, v in data["variants"].items():
            if label.startswith("_"):
                continue
            if base is None:
                base = v["mean"]
            speedup = base / v["mean"] if v["mean"] else float("inf")
            print(f"  {label:20s} {v['mean']:10.4f}s  (median {v['median']:.4f}s, "
                  f"stdev {v['stdev']:.4f}s, n={v['n']})")


if __name__ == "__main__":
    main()
