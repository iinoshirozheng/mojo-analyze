# 🔬 mojo-analyze

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Mojo](https://img.shields.io/badge/mojo-%3E%3D1.0.0-fa4d24.svg)](https://mojolang.org)
[![Managed by pixi](https://img.shields.io/badge/managed%20by-pixi-ffd24d.svg)](https://pixi.prefix.dev)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey.svg)](#requirements)

A rigorous, reproducible Mojo-vs-Rust-vs-C-vs-Python benchmark suite — five
tasks chosen to span five different compute profiles (SIMD-friendly,
memory/branch-bound, real-world string/hash, real-world tabular
aggregation, nested JSON parsing), every result gated on cross-language
checksum agreement, every number honestly reported — including a headline
that isn't flattering to the language this repo is actually about: **C
wins four of the five categories**. Mojo wins the one built for it, and
two categories tell a before/after story where the first honest Mojo
attempt lost, the cause was found, and a disclosed rewrite closed the gap
to a near-tie with C.

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

![Who leads each category, and by how much](results/lieflat/chart_margin_overview.png)

| Category | Task | Winner | Mojo's place |
|---|---|---|---|
| A — SIMD-friendly | Mandelbrot render | **Mojo** | 1st — 1.6x faster than C |
| B — memory/branch-bound | Sieve of Eratosthenes | **C** | 2nd, 1.02x behind — *previously lost to NumPy, see analysis* |
| C — real-world string/hash | Word-frequency count | **C** | 2nd, 1.6x behind — *previously lost to `Counter`, see analysis* |
| D — real-world tabular agg. | CSV group-by + sum | **C** | 2nd, 2.2x behind |
| E — nested JSON parsing | Group-by + sum over JSON | **C** | 3rd, 2.9x behind |

Mojo wins outright only where its SIMD API gets real work to do
(Mandelbrot). Everywhere else, C's decades-mature compiler and total
absence of runtime safety bookkeeping wins — usually by a modest margin,
with Mojo typically the closer 2nd-place finisher, ahead of Rust in every
category but one. Two categories (B, C) shipped a losing first Mojo
attempt, a found root cause, and a disclosed rewrite that closed the gap
to within 2% of C — full story, including *why*, in
[`ANALYSIS.md`](ANALYSIS.md).

![Three losing Mojo attempts, and the rewrite that fixed each one](results/lieflat/chart_rewrite_story.png)

![Same five categories, indexed to a common base — who wins each one](results/chart_speedup.png)

Full methodology, per-category charts, root-cause analysis for every
result (including a real FMA-rounding bug that hit *two independent
compilers* the same way, a 4-way CPU-vs-GPU comparison, and a
cross-platform finding — confirmed across 7 independent CI runs, not a
one-off — that Mojo's Sieve ranking flips on Linux arm64 specifically) and
threats to validity are all in [`ANALYSIS.md`](ANALYSIS.md).

![Does Mojo's Sieve win hold across hardware?](results/lieflat/chart_crossplatform_flip.png)

## What it does

- **A — Mandelbrot set rendering**: SIMD-vectorized escape-time computation
  over an 800×600 grid — the case Mojo's SIMD API is built for. Also has a
  standalone GPU (MAX/Metal) implementation, compared separately.
- **B — Sieve of Eratosthenes**: primes up to 50,000,000 — deliberately
  *not* SIMD-friendly, to test raw compiled-loop speed.
- **C — Word-frequency counting**: tokenize and count 15,000,000 words
  from a 62.4 MiB corpus — tests hash-table and string-allocation
  maturity across languages.
- **D — CSV group-by aggregation**: 10,000,000 order rows, group by
  category and sum revenue — real-world tabular parsing.
- **E — JSON parsing**: 3,000,000 nested event objects, 327 MiB — tests
  real JSON structure traversal (objects, arrays, string escaping),
  deliberately distinct from D's flat CSV.

Every task ships a Mojo, a Rust (`std`-only, `--release`), a C (`-O3`,
std-only), a naive-Python, and an "optimized library" (NumPy / `Counter` /
pandas / `json`) implementation, all built to a shared contract
(`scripts/bench.py`'s docstring): each program times only its own core
computation and prints a `CHECKSUM:` line, so the harness can refuse to
report timings unless every variant of a benchmark agrees on the answer.

## Requirements

- [pixi](https://pixi.prefix.dev) — manages the Mojo + Python + NumPy +
  pandas toolchain.
- [Rust](https://rustup.rs) (`rustc`/`cargo`) — for the Rust reference
  implementations.
- A C compiler (`clang` or `gcc`) — for the C reference implementations.
- macOS (Apple Silicon) or Linux (x86_64 / aarch64) — `pixi.toml` pins
  `osx-arm64`, `linux-64`, and `linux-aarch64`. Windows isn't supported by
  Mojo directly; use WSL2, which resolves as one of the Linux platforms.
- A GPU is only needed for the optional `pixi run build-gpu` /
  `pixi run bench-gpu` CPU-vs-GPU comparisons (Mandelbrot, Sieve,
  word-frequency, CSV agg) — everything else runs CPU-only.
- All published numbers in `ANALYSIS.md` were measured on an Apple M4 Pro
  (macOS, arm64), with a Linux CI job providing a second reference point —
  see its [Methodology](ANALYSIS.md#methodology) section before citing a
  number as portable to other hardware.

## Quick start

```bash
git clone https://github.com/iinoshirozheng/mojo-analyze.git
cd mojo-analyze
pixi install
pixi run build              # compiles the five CPU Mojo binaries -> dist/
pixi run build-rust         # cargo build --release, copies binaries -> dist/
pixi run build-c            # clang -O3, five binaries -> dist/
pixi run prepare-corpus     # regenerates the synthetic word-frequency corpus (seeded, deterministic)
pixi run prepare-data       # regenerates the synthetic CSV aggregation data (seeded, deterministic)
pixi run prepare-events     # regenerates the synthetic JSON event data (seeded, deterministic)
pixi run bench               # runs the full suite, writes results/results.json
pixi run charts              # renders the charts in ANALYSIS.md from results.json
```

`pixi run bench` accepts `--trials N` (default 5), `--warmup N` (default 1),
and `--only mandelbrot,sieve` to run a subset. The numbers and charts in
[`ANALYSIS.md`](ANALYSIS.md) were produced with `--trials 7 --warmup 2`.
Optional GPU comparisons: `pixi run build-gpu && pixi run bench-gpu`.

## How it works

```
benchmarks/
  mandelbrot/   mandelbrot.mojo, mandelbrot_gpu.mojo, mandelbrot_python.py,
                mandelbrot_numpy.py
  sieve/        sieve.mojo, sieve_gpu.mojo, sieve_python.py, sieve_numpy.py
  wordfreq/     wordfreq.mojo, wordfreq_gpu.mojo, wordfreq_python.py,
                wordfreq_counter.py, prepare_corpus.py (gitignored data/)
  csvagg/       csvagg.mojo, csvagg_gpu.mojo, csvagg_python.py,
                csvagg_pandas.py, prepare_data.py (gitignored data/)
  jsonparse/    jsonparse.mojo, jsonparse_python.py, jsonparse_stdlib.py,
                prepare_events.py (gitignored data/)
rust/
  src/bin/      mandelbrot.rs, sieve.rs, wordfreq.rs, csvagg.rs, jsonparse.rs
c/
  mandelbrot.c, sieve.c, wordfreq.c, csvagg.c, jsonparse.c
scripts/
  bench.py      the harness: N warmup + N measured trials per variant,
                parses each program's TIME_SECONDS/CHECKSUM stdout,
                refuses to report timings on checksum disagreement,
                writes results/results.json
  bench_gpu.py  four CPU-vs-GPU mini-harnesses (checksum-gated for three
                of four — see ANALYSIS.md for the one disclosed exception)
```

Each benchmark binary/script is a standalone process taking CLI flags
(`--width`/`--height`/`--max-iter` for Mandelbrot, `--limit` for the sieve,
`--corpus` for word-frequency, `--csv` for CSV aggregation, `--json` for
JSON parsing) and prints exactly two lines at the end of its output:

```
TIME_SECONDS: 0.056339
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
[mojo-syntax](https://mojolang.org) conventions of current Mojo 1.0. The
narrative charts (rewrite story, cross-platform, margin overview) are built
with [Lieflat Charts](https://github.com/larashero3-dotcom/lieflat-charts)
— source in [`results/lieflat/charts.html`](results/lieflat/charts.html);
the per-category, speedup, and GPU charts are plain matplotlib
(`scripts/make_charts.py`).

## License

[MIT](LICENSE)
