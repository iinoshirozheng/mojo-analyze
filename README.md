# 🔬 mojo-analyze

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Mojo](https://img.shields.io/badge/mojo-%3E%3D1.0.0-fa4d24.svg)](https://mojolang.org)
[![Managed by pixi](https://img.shields.io/badge/managed%20by-pixi-ffd24d.svg)](https://pixi.prefix.dev)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey.svg)](#requirements)

A rigorous, reproducible Mojo-vs-Python-vs-NumPy benchmark suite — three
tasks chosen to span three different compute profiles (SIMD-friendly,
memory/branch-bound, real-world string/hash processing), every result
gated on cross-language checksum agreement, every number honestly
reported including the two where Mojo doesn't win.

**[Read the full analysis →](ANALYSIS.md)**

## Table of Contents

- [Results at a glance](#results-at-a-glance)
- [What it does](#what-it-does)
- [Requirements](#requirements)
- [Quick start](#quick-start)
- [How it works](#how-it-works)
- [Contributing](#contributing)
- [Credits](#credits)
- [License](#license)

## Results at a glance

![Same three categories, indexed to a common base — who wins each one](results/chart_speedup.png)

| Category | Task | Winner | Mojo vs. fastest non-Mojo |
|---|---|---|---|
| A — SIMD-friendly | Mandelbrot render | **Mojo** | 12.1x faster than NumPy |
| B — memory/branch-bound | Sieve of Eratosthenes | **NumPy** | Mojo is 1.5x *slower* |
| C — real-world string/hash | Word-frequency count | **Python `Counter`** | Mojo is 1.2x *slower* |

Mojo wins decisively on embarrassingly-parallel numeric SIMD work and loses
or ties where memory allocation and hash-table/string maturity dominate
instead of raw arithmetic. Full methodology, per-category charts, root-cause
analysis for each result (including a real FMA-rounding bug the checksum
gate caught), and threats to validity are in [`ANALYSIS.md`](ANALYSIS.md).

## What it does

- **A — Mandelbrot set rendering**: SIMD-vectorized escape-time computation
  over an 800×600 grid — the case Mojo's SIMD API is built for.
- **B — Sieve of Eratosthenes**: primes up to 50,000,000 — deliberately
  *not* SIMD-friendly, to test raw compiled-loop speed against Python and
  against NumPy's vectorized bulk-memory-write trick.
- **C — Word-frequency counting**: tokenize and count 15,000,000 words
  from a 62.4 MiB corpus — tests Mojo's current `Dict[String, Int]` and
  string-allocation maturity against CPython's `dict` and
  `collections.Counter`.

Every task ships three (or, for C, three) independent implementations, all
built to a shared contract (`scripts/bench.py`'s docstring): each program
times only its own core computation and prints a `CHECKSUM:` line, so the
harness can refuse to report timings unless every variant of a benchmark
agrees on the answer.

## Requirements

- [pixi](https://pixi.prefix.dev) — manages the Mojo + Python + NumPy
  toolchain.
- macOS (Apple Silicon) or Linux (x86_64 / aarch64) — `pixi.toml` pins
  `osx-arm64`, `linux-64`, and `linux-aarch64`. Windows isn't supported by
  Mojo directly; use WSL2, which resolves as one of the Linux platforms.
- All published numbers in `ANALYSIS.md` were measured on an Apple M4 Pro
  (macOS, arm64) — see its [Methodology](ANALYSIS.md#methodology) section
  before citing a number as portable to other hardware.

## Quick start

```bash
git clone https://github.com/iinoshirozheng/mojo-analyze.git
cd mojo-analyze
pixi install
pixi run build             # compiles the three Mojo binaries -> dist/
pixi run prepare-corpus    # regenerates the synthetic word-frequency corpus (seeded, deterministic)
pixi run bench              # runs the full suite, writes results/results.json
pixi run charts             # renders the charts in ANALYSIS.md from results.json
```

`pixi run bench` accepts `--trials N` (default 5), `--warmup N` (default 1),
and `--only mandelbrot,sieve` to run a subset. The numbers and charts in
[`ANALYSIS.md`](ANALYSIS.md) were produced with `--trials 7 --warmup 2`.

## How it works

```
benchmarks/
  mandelbrot/   mandelbrot.mojo, mandelbrot_python.py, mandelbrot_numpy.py
  sieve/        sieve.mojo, sieve_python.py, sieve_numpy.py
  wordfreq/     wordfreq.mojo, wordfreq_python.py, wordfreq_counter.py,
                prepare_corpus.py (generates data/corpus.txt, gitignored)
scripts/
  bench.py      the harness: N warmup + N measured trials per variant,
                parses each program's TIME_SECONDS/CHECKSUM stdout,
                refuses to report timings on checksum disagreement,
                writes results/results.json
```

Each benchmark binary/script is a standalone process taking CLI flags
(`--width`/`--height`/`--max-iter` for Mandelbrot, `--limit` for the sieve,
`--corpus` for word-frequency) and prints exactly two lines at the end of
its output:

```
TIME_SECONDS: 0.054766
CHECKSUM: 42411634
```

`scripts/bench.py` runs each variant several times, verifies every trial's
checksum matches, verifies every variant's checksum for the same benchmark
matches every other variant's, and only then computes mean/median/stdev.
This is the whole methodology in one paragraph: **no fast answer is
reported without first being proven to be the same answer**.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) — the short version is: the
checksum-agreement rule is non-negotiable, and if you change a number,
update `ANALYSIS.md` in the same PR rather than leaving it stale next to
new code.

## Credits

Built with the same benchmark-honesty methodology established while
building [`fire-cube`](https://github.com/iinoshirozheng/fire-cube), a
SIMD-accelerated Mojo terminal demo, and following the
[mojo-syntax](https://mojolang.org) conventions of current Mojo 1.0.

## License

[MIT](LICENSE)
