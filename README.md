# 🔬 mojo-analyze

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Mojo](https://img.shields.io/badge/mojo-%3E%3D1.0.0-fa4d24.svg)](https://mojolang.org)
[![Managed by pixi](https://img.shields.io/badge/managed%20by-pixi-ffd24d.svg)](https://pixi.prefix.dev)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey.svg)](#requirements)

A rigorous, reproducible Mojo-vs-Rust-vs-Python-vs-NumPy/pandas benchmark
suite — four tasks chosen to span four different compute profiles
(SIMD-friendly, memory/branch-bound, real-world string/hash, real-world
tabular aggregation), every result gated on cross-language checksum
agreement, every number honestly reported — including two categories
where the first Mojo attempt lost, and the specific rewrite that turned
each into the fastest implementation in the suite.

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

![Same four categories, indexed to a common base — who wins each one](results/chart_speedup.png)

| Category | Task | Winner | Mojo vs. fastest other |
|---|---|---|---|
| A — SIMD-friendly | Mandelbrot render | **Mojo** | fastest — 2.0x faster than Rust |
| B — memory/branch-bound | Sieve of Eratosthenes | **Mojo** | fastest — 1.15x faster than Rust *(previously lost to NumPy — see analysis)* |
| C — real-world string/hash | Word-frequency count | **Mojo** | fastest — 1.5x faster than Rust *(previously lost to `Counter` — see analysis)* |
| D — real-world tabular agg. | CSV group-by + sum | **Rust** | Mojo is 1.2x slower, but beats pandas by 2.3x |

Mojo wins three of four categories, including two it initially *lost* — the
full write-up covers both the losing first attempt and the specific,
disclosed rewrite (raw-pointer allocation for B, a byte-span hash table for
C) that turned each into the fastest implementation measured. Full
methodology, per-category charts, root-cause analysis for every result
(including a real FMA-rounding bug the checksum gate caught, and a
CPU-vs-GPU comparison for Mandelbrot), and threats to validity are in
[`ANALYSIS.md`](ANALYSIS.md).

## What it does

- **A — Mandelbrot set rendering**: SIMD-vectorized escape-time computation
  over an 800×600 grid — the case Mojo's SIMD API is built for. Also has a
  standalone GPU (MAX/Metal) implementation, compared separately.
- **B — Sieve of Eratosthenes**: primes up to 50,000,000 — deliberately
  *not* SIMD-friendly, to test raw compiled-loop speed against Python and
  against NumPy's vectorized bulk-memory-write trick.
- **C — Word-frequency counting**: tokenize and count 15,000,000 words
  from a 62.4 MiB corpus — tests Mojo's current `Dict[String, Int]` and
  string-allocation maturity against CPython's `dict` and
  `collections.Counter`.
- **D — CSV group-by aggregation**: 10,000,000 order rows, group by
  category and sum revenue — tests real-world tabular parsing against
  pandas.

Every task ships a Mojo, a Rust (`std`-only, `--release`), a naive-Python,
and an "optimized library" (NumPy / `Counter` / pandas) implementation, all
built to a shared contract (`scripts/bench.py`'s docstring): each program
times only its own core computation and prints a `CHECKSUM:` line, so the
harness can refuse to report timings unless every variant of a benchmark
agrees on the answer.

## Requirements

- [pixi](https://pixi.prefix.dev) — manages the Mojo + Python + NumPy +
  pandas toolchain.
- [Rust](https://rustup.rs) (`rustc`/`cargo`) — for the Rust reference
  implementations.
- macOS (Apple Silicon) or Linux (x86_64 / aarch64) — `pixi.toml` pins
  `osx-arm64`, `linux-64`, and `linux-aarch64`. Windows isn't supported by
  Mojo directly; use WSL2, which resolves as one of the Linux platforms.
- A GPU is only needed for the optional `pixi run build-gpu` /
  `pixi run bench-gpu` CPU-vs-GPU Mandelbrot comparison — everything else
  runs CPU-only.
- All published numbers in `ANALYSIS.md` were measured on an Apple M4 Pro
  (macOS, arm64), with a Linux CI job providing a second reference point —
  see its [Methodology](ANALYSIS.md#methodology) section before citing a
  number as portable to other hardware.

## Quick start

```bash
git clone https://github.com/iinoshirozheng/mojo-analyze.git
cd mojo-analyze
pixi install
pixi run build              # compiles the four CPU Mojo binaries -> dist/
pixi run build-rust         # cargo build --release, copies binaries -> dist/
pixi run prepare-corpus     # regenerates the synthetic word-frequency corpus (seeded, deterministic)
pixi run prepare-data       # regenerates the synthetic CSV aggregation data (seeded, deterministic)
pixi run bench               # runs the full suite, writes results/results.json
pixi run charts              # renders the charts in ANALYSIS.md from results.json
```

`pixi run bench` accepts `--trials N` (default 5), `--warmup N` (default 1),
and `--only mandelbrot,sieve` to run a subset. The numbers and charts in
[`ANALYSIS.md`](ANALYSIS.md) were produced with `--trials 7 --warmup 2`.
Optional GPU comparison: `pixi run build-gpu && pixi run bench-gpu`.

## How it works

```
benchmarks/
  mandelbrot/   mandelbrot.mojo, mandelbrot_gpu.mojo, mandelbrot_python.py,
                mandelbrot_numpy.py
  sieve/        sieve.mojo, sieve_python.py, sieve_numpy.py
  wordfreq/     wordfreq.mojo, wordfreq_python.py, wordfreq_counter.py,
                prepare_corpus.py (generates data/corpus.txt, gitignored)
  csvagg/       csvagg.mojo, csvagg_python.py, csvagg_pandas.py,
                prepare_data.py (generates data/orders.csv, gitignored)
rust/
  src/bin/      mandelbrot.rs, sieve.rs, wordfreq.rs, csvagg.rs
scripts/
  bench.py      the harness: N warmup + N measured trials per variant,
                parses each program's TIME_SECONDS/CHECKSUM stdout,
                refuses to report timings on checksum disagreement,
                writes results/results.json
  bench_gpu.py  separate CPU-vs-GPU Mandelbrot mini-harness (not checksum-
                gated — see ANALYSIS.md for why)
```

Each benchmark binary/script is a standalone process taking CLI flags
(`--width`/`--height`/`--max-iter` for Mandelbrot, `--limit` for the sieve,
`--corpus` for word-frequency, `--csv` for CSV aggregation) and prints
exactly two lines at the end of its output:

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
