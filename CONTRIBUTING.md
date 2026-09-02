# Contributing to mojo-analyze

Thanks for taking a look. This is a benchmark repo — the bar for contributing
is low, but a few things matter more here than in typical projects because
the whole point is that the numbers have to be trustworthy.

## Setup

```bash
git clone https://github.com/iinoshirozheng/mojo-analyze.git
cd mojo-analyze
pixi install
pixi run build            # compiles the five CPU Mojo binaries -> dist/
pixi run build-rust       # cargo build --release, copies binaries -> dist/
pixi run build-c          # clang -O3, five binaries -> dist/
pixi run build-gpu        # compiles four GPU kernels (needs a GPU)
pixi run prepare-corpus   # regenerates the synthetic word-frequency corpus
pixi run prepare-data     # regenerates the synthetic CSV aggregation data
pixi run prepare-events   # regenerates the synthetic JSON event data
pixi run bench             # runs the five core categories, writes results/results.json
pixi run bench-gpu         # four CPU-vs-GPU mini-benchmarks
pixi run charts            # renders results/chart_*.png from results.json
```

If `pixi run` fails with `unable to locate module 'std'` right after cloning
or moving the folder, delete `.pixi/` and run `pixi install` again — the
environment bakes in absolute paths and doesn't survive being relocated.

## Mojo is a moving target

Mojo's syntax has changed significantly across versions (`fn` → `def`,
`alias` → `comptime`, `inout` → `mut`, etc.). Pretrained-model knowledge and
older blog posts/tutorials are frequently wrong for the current stable
release this project targets (`pixi.toml` pins `mojo >=1.0.0,<2`). Before
relying on remembered syntax, check the actual behavior against the
installed toolchain — `pixi run mojo run <scratch-file>` is the fastest way
to confirm a pattern compiles the way you expect.

## The rule that matters most: checksums must agree

Every benchmark's Mojo/Rust/C/Python/NumPy(-or-pandas-or-json) variants
must produce byte-identical `CHECKSUM` output for the same input (see each
benchmark's own comments for what's hashed). `scripts/bench.py` enforces
this automatically and refuses to report timings if variants disagree. If
you're tempted to skip this check to "just see the numbers" — don't. A fast
wrong answer isn't a result, it's a bug wearing a result's clothes. This
project's whole value is honest, reproducible comparisons; a mismatched
checksum means something is broken, not that "Mojo does it differently" —
and it's the same standard when the fast-but-wrong variant is Rust or C,
not just Mojo.

The one deliberate, disclosed exception is Mandelbrot's GPU kernel in
`scripts/bench_gpu.py` — Apple Metal has no compute-kernel float64 support,
so it runs in Float32 against a Float64 CPU reference by hardware
necessity, and that one comparison is explicitly *not* checksum-gated (see
`ANALYSIS.md`'s GPU section). The other three GPU kernels (sieve,
word-frequency, CSV agg) use integer-only arithmetic and *are* held to the
normal exact-match standard — don't extend the Mandelbrot exception to
anything else without an equally concrete hardware reason (a real one
turned up mid-project: Apple GPU also has no 64-bit atomic add, which the
CSV-agg GPU kernel works around with a disclosed 32-bit carry-propagation
trick rather than an exemption — see its header comment).

## Before opening a PR

- `pixi run build` (and `build-rust`/`build-c`/`build-gpu` if you touched
  those) succeeds with no warnings you introduced.
- `pixi run bench` reports checksum agreement for every benchmark you
  touched — paste the summary table into the PR description.
- If you're adding a new benchmark task or a new language variant, keep the
  timing contract in `scripts/bench.py`'s docstring (`TIME_SECONDS:` /
  `CHECKSUM:` as the last two stdout lines) — the harness parses on that.
  If you add a systems-language variant (Mojo/Rust/C), match the existing
  role-color convention in `scripts/make_charts.py` (orange/violet/magenta
  respectively) rather than inventing a new one — see that file's palette
  comment for the validated adjacent-pairs color order.
- If a change moves the numbers meaningfully, update `ANALYSIS.md` with a
  fresh run rather than leaving stale numbers next to new code — include
  your hardware (`ANALYSIS.md`'s methodology section shows the format) since
  these are wall-clock comparisons, not portable benchmarks.
- Re-run `pixi run charts` after any `pixi run bench` that changes
  `results/results.json`, and commit the regenerated PNGs alongside it — a
  chart that doesn't match the numbers next to it is worse than no chart.

## Ideas that would be welcome

- **A raw-pointer rewrite of the word-freq/csvagg hash tables' slot
  arrays.** `ANALYSIS.md`'s category-C section found that C beats Mojo by
  ~1.6x on the *identical* byte-span hash-table algorithm, and attributes
  the gap to Mojo's `List[Bool]`/`List[UInt64]`/`List[Int]` slot arrays
  still paying `List`'s bounds-check overhead per hash-table probe — the
  same mechanism category B's raw-pointer sieve rewrite eliminated.
  Applying that fix to categories C and D (both share the identical
  hash-table pattern) would directly test that hypothesis. **Category E
  was a different story, and it's now been profiled, not just guessed
  at** (see `ANALYSIS.md`'s category-E section): `@always_inline` on the
  scanning helpers was a real, confirmed ~24% win (verified via
  `mojo build --emit asm` — zero calls to those functions remain), but
  removing the hash table entirely only saved ~5-8% of total time, so the
  scanning loop itself — not the hash table, and not un-inlined function
  calls — is genuinely where the remaining 2.2x-behind-C gap lives. A
  further win here isn't a small tuning fix; it needs a different
  *algorithm* (structural pre-indexing / fewer branches per byte,
  ultimately SIMD, the way simdjson does it) — open, not attempted in this
  round.
- **Give Rust's hash-table variants a fair non-cryptographic-hasher
  comparison.** Every Rust variant in this repo uses
  `std::collections::HashMap`'s default hasher, SipHash — deliberately
  DoS-resistant, and well-documented as slower than a plain hash like
  FNV-1a for short keys. Category C's Rust also allocates an owned
  `Vec<u8>` key per token (unlike its own category D variant, which borrows
  a `&str`) — that inconsistency between Rust's *own* two implementations
  is disclosed in `ANALYSIS.md` but not fixed. A `FxHashMap`/`ahash`-style
  swap (or a hand-rolled byte-span table matching Mojo/C's) would separate
  "Rust's default HashMap is a poor fit for this workload" from "Rust the
  compiler is slower" — right now this repo can't tell those apart, by
  design (every variant is "standard library only," which is honest but
  means the *default* std HashMap's known-slow-for-this-case hasher never
  gets a fair alternative measured).
- **A fair `unsafe` Rust variant for category B (Sieve).** Rust's `Vec<bool>`
  pays a bounds check on every marking write; Mojo and C both mark through
  unchecked raw memory. An `unsafe`/`get_unchecked` Rust rewrite, cheap to
  write, would tell you whether Rust landing behind C/Mojo here is really
  "safe-Rust's bounds-checking tax" (the current best guess) or something
  else.
- **Investigate the Linux arm64 Sieve reversal at the codegen level.**
  `ANALYSIS.md`'s cross-platform section confirms — across 7 independent CI
  runs — that NumPy beats Mojo's raw-pointer sieve specifically on Linux
  arm64 (GitHub-hosted runners), while Mojo wins on both macOS arm64 and
  Linux x86_64. The current write-up flags a codegen-difference hypothesis
  (NEON/SVE autovectorization differences between Apple's and this Linux
  runner's LLVM backend) but doesn't confirm it. Real (non-shared) arm64
  Linux hardware and a look at the actual generated assembly would turn
  this from a hypothesis into an answer.
- **A GPU port for category E (JSON parsing).** The other four categories
  all have a GPU kernel (`benchmarks/*/[name]_gpu.mojo`); JSON parsing does
  not, since its work is dominated by inherently sequential byte-scanning.
  A CPU-scan/GPU-parallel-something split, following the disclosed-split
  pattern the word-freq and CSV-agg GPU kernels already use, is an open
  design problem, not a mechanical port.
- **A cleaner Linux CI comparison across all five categories with C
  included.** The workflow was just updated to build C and add category E;
  the cross-platform table in `ANALYSIS.md` will need a fresh set of runs
  to include both once they've accumulated a few pushes' worth of data.
- More tasks in category C/D/E's spirit (real-world data processing) — a
  hash-table-heavy workload independent of string parsing, or a sort/dedup
  benchmark, are open candidates.

## Reporting issues

If a benchmark's numbers look implausible (a variant reporting near-zero
time, or losing to an interpreted language by an amount that doesn't make
sense), include your hardware, OS, and the full `pixi run bench` output —
timing bugs are usually visible in the raw per-trial numbers before they're
averaged away.
