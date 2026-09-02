"""Separate mini-harness for CPU-vs-GPU comparisons, one per category that
has a GPU port (Mandelbrot, Sieve, word-frequency, CSV aggregation).

Unlike scripts/bench.py, this is NOT uniformly checksum-gated: Mandelbrot's
GPU kernel legitimately runs in Float32 (Apple Metal has no compute-kernel
float64 support -- see benchmarks/mandelbrot/mandelbrot_gpu.mojo's header),
so its checksum differs from the Float64 CPU reference by design, not by
bug, and that one comparison is exempted from the equality check (both
checksums are still printed for inspection). The other three GPU ports
(sieve, word-freq, csvagg) use integer-only arithmetic with no such
hardware constraint, so THEIR checksums are held to the same exact-match
standard as every other benchmark in this repo -- see each *_gpu.mojo
file's header for its own disclosed CPU/GPU work split.

Usage:
    pixi run bench-gpu
"""

import json
import statistics
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TRIALS = 7
WARMUP = 2

COMPARISONS = [
    {
        "key": "mandelbrot_gpu",
        "cpu_bin": "mandelbrot-mojo",
        "gpu_bin": "mandelbrot-gpu",
        "checksum_gated": False,
        "sizes": [
            {"label": "800×600\n(480K px, default)",
             "args": ["--width", "800", "--height", "600", "--max-iter", "500"]},
            {"label": "4000×3000\n(12M px)",
             "args": ["--width", "4000", "--height", "3000", "--max-iter", "500"]},
        ],
    },
    {
        "key": "sieve_gpu",
        "cpu_bin": "sieve-mojo",
        "gpu_bin": "sieve-gpu",
        "checksum_gated": True,
        "sizes": [
            {"label": "limit=50,000,000\n(default)", "args": ["--limit", "50000000"]},
        ],
    },
    {
        "key": "wordfreq_gpu",
        "cpu_bin": "wordfreq-mojo",
        "gpu_bin": "wordfreq-gpu",
        "checksum_gated": True,
        "sizes": [
            {"label": "62.4 MiB corpus\n(default)",
             "args": ["--corpus", str(ROOT / "benchmarks/wordfreq/data/corpus.txt")]},
        ],
    },
    {
        "key": "csvagg_gpu",
        "cpu_bin": "csvagg-mojo",
        "gpu_bin": "csvagg-gpu",
        "checksum_gated": True,
        "sizes": [
            {"label": "277.9 MiB CSV\n(default)",
             "args": ["--csv", str(ROOT / "benchmarks/csvagg/data/orders.csv")]},
        ],
    },
]


def parse_output(stdout):
    time_seconds = None
    checksum = None
    for line in stdout.splitlines():
        line = line.strip()
        if line.startswith("TIME_SECONDS:"):
            time_seconds = float(line.split(":", 1)[1].strip())
        elif line.startswith("CHECKSUM:"):
            checksum = line.split(":", 1)[1].strip()
    return time_seconds, checksum


def run(binary, args):
    cmd = [str(ROOT / "dist" / binary)] + args
    times = []
    checksum = None
    for i in range(WARMUP + TRIALS):
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
        if result.returncode != 0:
            raise RuntimeError(f"{' '.join(cmd)} failed:\n{result.stderr}")
        t, c = parse_output(result.stdout)
        if t is None or c is None:
            raise RuntimeError(f"missing TIME_SECONDS/CHECKSUM: {result.stdout}")
        checksum = c
        if i >= WARMUP:
            times.append(t)
    return {
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "stdev": statistics.stdev(times),
        "checksum": checksum,
        "n": len(times),
    }


def main():
    out = {}
    for comp in COMPARISONS:
        print(f"=== {comp['key']} ===")
        sizes_out = []
        for size in comp["sizes"]:
            print(f"  {size['label'].splitlines()[0]}:")
            print("    cpu...", end=" ", flush=True)
            cpu = run(comp["cpu_bin"], size["args"])
            print(f"mean={cpu['mean']:.4f}s checksum={cpu['checksum']}")
            print("    gpu...", end=" ", flush=True)
            gpu = run(comp["gpu_bin"], size["args"])
            print(f"mean={gpu['mean']:.4f}s checksum={gpu['checksum']}")

            if comp["checksum_gated"] and cpu["checksum"] != gpu["checksum"]:
                raise RuntimeError(
                    f"{comp['key']} @ {size['label']}: CPU/GPU checksum mismatch "
                    f"({cpu['checksum']} vs {gpu['checksum']}) -- this comparison "
                    f"is checksum-gated (integer-only, no hardware precision "
                    f"exemption), so this is a real bug, not expected drift."
                )
            sizes_out.append({"label": size["label"], "cpu": cpu, "gpu": gpu})
        out[comp["key"]] = {"sizes": sizes_out, "checksum_gated": comp["checksum_gated"]}

    results_path = ROOT / "results" / "results.json"
    results = json.loads(results_path.read_text()) if results_path.exists() else {}
    results.update(out)
    results_path.write_text(json.dumps(results, indent=2))
    print(f"\nWrote GPU comparisons to {results_path}")


if __name__ == "__main__":
    main()
