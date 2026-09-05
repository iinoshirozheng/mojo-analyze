<div align="center">

# 🔬 mojo-analyze

**Rigorous, checksum-gated performance research on Mojo — with reproducible cross-language benchmarks and a daily ecosystem research log.**

[Full Analysis](ANALYSIS.md) · [Experiments](experiments/) · [Mojo Ecosystem Radar](ecosystem/README.md) · [Contributing](CONTRIBUTING.md)

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Mojo](https://img.shields.io/badge/mojo-%3E%3D1.0.0-fa4d24.svg)](https://mojolang.org)
[![Managed by pixi](https://img.shields.io/badge/managed%20by-pixi-ffd24d.svg)](https://pixi.prefix.dev)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey.svg)](#requirements)

</div>

---

## Overview

`mojo-analyze` started as a fair Mojo-vs-Rust-vs-C-vs-Python benchmark suite and now also serves as an ongoing performance-research notebook for the Mojo ecosystem.

The rule is simple: **no fast answer is reported until it has first been shown to be the same answer**. Benchmark variants are checksum-gated, performance claims use repeated trials, and codegen or assembly is inspected when it is material to the explanation.

The core suite spans five different compute profiles: SIMD-friendly rendering, memory/branch-bound integer work, string/hash processing, tabular aggregation, and nested JSON parsing. The headline is intentionally not flattering to the language this repo studies: **C wins four of the five canonical categories; Mojo wins the SIMD-heavy Mandelbrot case.** The detailed methodology, root-cause analysis, caveats, and cross-platform findings live in [`ANALYSIS.md`](ANALYSIS.md).

## Results at a Glance

| Category | Task | Winner | Mojo's place |
|---|---|---|---|
| A — SIMD-friendly | Mandelbrot render | **Mojo** | 1st — 1.6x faster than C |
| B — memory/branch-bound | Sieve of Eratosthenes | **C** | 2nd, 1.05x behind |
| C — real-world string/hash | Word-frequency count | **C** | 2nd, 1.6x behind |
| D — real-world tabular agg. | CSV group-by + sum | **C** | 2nd, 2.3x behind |
| E — nested JSON parsing | Group-by + sum over JSON | **C** | 3rd, 2.3x behind; `@always_inline` recovered ~24% |

![Same five categories, indexed to a common base](results/chart_speedup.png)

See [`ANALYSIS.md`](ANALYSIS.md) before citing these numbers as portable: the canonical published measurements were taken on Apple M4 Pro, with Linux CI used as a second reference point.

## Ongoing Research

The repository is no longer limited to the five canonical benchmark categories. Small, independently verifiable investigations are recorded separately so experimental work does not silently rewrite the baseline suite.

### Experiment log

[`experiments/`](experiments/) contains focused research notes, one question per investigation. Recent work includes:

- Rust unsafe/indexing variants for the sieve workload;
- a Mojo raw-slot word-frequency implementation that isolates hash-table/data-layout costs;
- Linux cross-checks of the five-category benchmark suite;
- a Rust FNV CSV-aggregation variant to separate hasher choice from language effects.

Experimental variants remain clearly separated from canonical benchmark implementations unless the evidence justifies changing the shipped baseline.

### Mojo Ecosystem Radar

[`ecosystem/README.md`](ecosystem/README.md) indexes daily ecosystem briefs under `ecosystem/YYYY-MM-DD.md`. These track relevant Mojo/Modular releases, active repositories, compiler/codegen work, GPU/system experiments, performance findings, and concrete candidates worth reproducing in this repository.

The radar is an input to research, not a feed of popularity metrics: candidates are useful only when they can be reduced to a fair, reproducible experiment.

## Benchmark Workloads

- **A — Mandelbrot:** SIMD-vectorized escape-time computation over an 800×600 grid, plus a separate MAX/Metal GPU implementation.
- **B — Sieve:** primes up to 50,000,000, deliberately not SIMD-friendly.
- **C — Word frequency:** tokenize and count 15,000,000 words from a deterministic corpus.
- **D — CSV aggregation:** 10,000,000 order rows grouped by category and summed.
- **E — JSON parsing:** 3,000,000 nested event objects, testing real structure traversal rather than flat CSV parsing.

Each canonical workload ships Mojo, Rust (`std`-only, release), C (`-O3`, std-only), naive Python, and an optimized Python-library comparison where appropriate. Technique differences are disclosed rather than hidden behind language labels.

## Requirements

- [pixi](https://pixi.prefix.dev) for Mojo and the Python data/plotting toolchain.
- Rust (`rustc` / `cargo`) for Rust references and research variants.
- `clang` or `gcc` for C references.
- macOS Apple Silicon or Linux x86-64/aarch64. Windows users should use WSL2 because Mojo itself does not provide a native Windows toolchain here.
- A supported GPU only for optional `build-gpu` / `bench-gpu` comparisons.

## Quick Start

```bash
git clone https://github.com/iinoshirozheng/mojo-analyze.git
cd mojo-analyze
pixi install

pixi run build
pixi run build-rust
pixi run build-c
pixi run prepare-corpus
pixi run prepare-data
pixi run prepare-events
pixi run bench
pixi run charts
```

`pixi run bench` supports `--trials N`, `--warmup N`, and `--only category,...`. Published analysis uses repeated trials; partial `--only` runs merge into the existing results set rather than deleting unrelated categories.

Optional GPU comparisons:

```bash
pixi run build-gpu
pixi run bench-gpu
```

## Methodology

Every benchmark program reports its computation time and a deterministic checksum. The harness:

1. performs warm-up runs;
2. runs multiple measured trials;
3. verifies checksum stability inside each implementation;
4. verifies checksum agreement across implementations of the same workload;
5. only then reports mean/median/stdev and regenerates result artifacts.

When a surprising gap appears, the repository treats it as a research question rather than a conclusion. Examples in the analysis include bounds-checking effects, allocating hash-map keys, default hasher costs, an FMA-rounding correctness bug, platform-specific ranking changes, and JSON parser instruction density.

## Repository Map

```text
benchmarks/      canonical Mojo/Python workloads and selected research variants
rust/            Rust reference binaries and isolated comparison variants
c/               C reference implementations
scripts/         benchmark harnesses, data preparation, and chart generation
results/         canonical result data and generated charts
experiments/     dated, focused research notes
ecosystem/       daily Mojo Ecosystem Radar briefs
ANALYSIS.md      canonical performance analysis and methodology
CONTRIBUTING.md  benchmark contracts, research rules, and open questions
```

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). The checksum-agreement rule is non-negotiable. Performance changes should be backed by enough trials to support the claim, and changes to canonical results must keep [`ANALYSIS.md`](ANALYSIS.md) synchronized.

A useful contribution answers one focused question. Do not add artificial variants or commits solely to create activity.

## Credits

The benchmark-honesty methodology grew out of work on [`fire-cube`](https://github.com/iinoshirozheng/fire-cube). Narrative charts use [Lieflat Charts](https://github.com/larashero3-dotcom/lieflat-charts); the remaining result charts are generated with matplotlib from repository data.

## License

[MIT](LICENSE)
