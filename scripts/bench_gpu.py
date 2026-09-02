"""Separate mini-harness for the Mandelbrot CPU-vs-GPU comparison.

This does NOT use the cross-language checksum-agreement gate scripts/bench.py
enforces elsewhere in this repo: the GPU kernel legitimately runs in Float32
(Apple Metal has no compute-kernel float64 support — see
benchmarks/mandelbrot/mandelbrot_gpu.mojo's header comment), so its checksum
differs from the Float64 CPU/SIMD reference by design, not by bug. Correctness
here instead means: both binaries ran, both printed a plausible non-zero
checksum, and neither crashed — checked below, just not required to *match*.

Usage:
    pixi run bench-gpu
"""

import json
import statistics
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SIZES = [
    {"label": "800×600\n(480K px, default)", "width": 800, "height": 600, "max_iter": 500},
    {"label": "4000×3000\n(12M px)", "width": 4000, "height": 3000, "max_iter": 500},
]

TRIALS = 7
WARMUP = 2


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


def run(binary, size):
    cmd = [
        str(ROOT / "dist" / binary),
        "--width", str(size["width"]), "--height", str(size["height"]),
        "--max-iter", str(size["max_iter"]),
    ]
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
    out = {"sizes": []}
    for size in SIZES:
        print(f"=== {size['width']}x{size['height']} ===")
        print("  cpu...", end=" ", flush=True)
        cpu = run("mandelbrot-mojo", size)
        print(f"mean={cpu['mean']:.4f}s checksum={cpu['checksum']}")
        print("  gpu...", end=" ", flush=True)
        gpu = run("mandelbrot-gpu", size)
        print(f"mean={gpu['mean']:.4f}s checksum={gpu['checksum']}")
        out["sizes"].append({
            "label": size["label"], "width": size["width"], "height": size["height"],
            "cpu": cpu, "gpu": gpu,
        })

    results_path = ROOT / "results" / "results.json"
    results = json.loads(results_path.read_text()) if results_path.exists() else {}
    results["mandelbrot_gpu"] = out
    results_path.write_text(json.dumps(results, indent=2))
    print(f"\nWrote mandelbrot_gpu section to {results_path}")


if __name__ == "__main__":
    main()
