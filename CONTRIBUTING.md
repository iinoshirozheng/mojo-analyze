# Contributing to mojo-analyze

Thanks for taking a look. This is a benchmark repo — the bar for contributing
is low, but a few things matter more here than in typical projects because
the whole point is that the numbers have to be trustworthy.

## Setup

```bash
git clone https://github.com/iinoshirozheng/mojo-analyze.git
cd mojo-analyze
pixi install
pixi run build            # compiles the four CPU Mojo binaries -> dist/
pixi run build-rust       # cargo build --release, copies binaries -> dist/
pixi run build-gpu        # compiles the GPU Mandelbrot kernel (needs a GPU)
pixi run prepare-corpus   # regenerates the synthetic word-frequency corpus
pixi run prepare-data     # regenerates the synthetic CSV aggregation data
pixi run bench             # runs the four core categories, writes results/results.json
pixi run bench-gpu         # separate CPU-vs-GPU Mandelbrot mini-benchmark
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

Every benchmark's Mojo/Rust/Python/NumPy(-or-pandas) variants must produce
byte-identical `CHECKSUM` output for the same input (see each benchmark's
own comments for what's hashed). `scripts/bench.py` enforces this
automatically and refuses to report timings if variants disagree. If you're
tempted to skip this check to "just see the numbers" — don't. A fast wrong
answer isn't a result, it's a bug wearing a result's clothes. This
project's whole value is honest, reproducible comparisons; a mismatched
checksum means something is broken, not that "Mojo does it differently."

The one deliberate, disclosed exception is `scripts/bench_gpu.py` — Apple
Metal has no compute-kernel float64 support, so the GPU Mandelbrot kernel
runs in Float32 against a Float64 CPU reference by hardware necessity, and
that comparison is explicitly *not* checksum-gated (see `ANALYSIS.md`'s GPU
section). Don't extend that exception to anything else without an equally
concrete hardware reason.

## Before opening a PR

- `pixi run build` succeeds with no warnings you introduced.
- `pixi run bench` reports checksum agreement for every benchmark you
  touched — paste the summary table into the PR description.
- If you're adding a new benchmark task or a new language variant, keep the
  timing contract in `scripts/bench.py`'s docstring (`TIME_SECONDS:` /
  `CHECKSUM:` as the last two stdout lines) — the harness parses on that.
- If a change moves the numbers meaningfully, update `ANALYSIS.md` with a
  fresh run rather than leaving stale numbers next to new code — include
  your hardware (`ANALYSIS.md`'s methodology section shows the format) since
  these are wall-clock comparisons, not portable benchmarks.
- Re-run `pixi run charts` after any `pixi run bench` that changes
  `results/results.json`, and commit the regenerated PNGs alongside it — a
  chart that doesn't match the numbers next to it is worse than no chart.

## Ideas that would be welcome

- A hand-written C (`-O3`) reference point alongside Rust, especially for
  category D (CSV aggregation) — the one category where Mojo currently
  trails Rust; a C baseline would help tell "genuine current Mojo gap" apart
  from "Rust's allocator/HashMap happens to be very good here."
- A byte-span/borrowed-slice rewrite of category D's Mojo `Dict` key (it
  currently allocates a `String` per row for the category field, the last
  remaining per-row allocation in that benchmark) to see if it can close
  the ~20% gap with Rust the way categories B and C's rewrites did.
- More tasks in category-C/D's spirit (real-world data processing) — JSON
  parsing, a hash-table-heavy workload independent of string parsing, or a
  sort/dedup benchmark are open candidates.
- GPU implementations of the other three CPU benchmarks (sieve, word-freq,
  CSV agg), for comparison against `mandelbrot_gpu.mojo`'s pattern.
- Now that Linux CI (`.github/workflows/benchmark.yml`) is live, watch its
  results for a few runs and fold a real cross-architecture comparison
  into `ANALYSIS.md` once there's enough Linux data to trust — right now
  it runs but isn't yet summarized in the doc.

## Reporting issues

If a benchmark's numbers look implausible (a variant reporting near-zero
time, or losing to an interpreted language by an amount that doesn't make
sense), include your hardware, OS, and the full `pixi run bench` output —
timing bugs are usually visible in the raw per-trial numbers before they're
averaged away.
