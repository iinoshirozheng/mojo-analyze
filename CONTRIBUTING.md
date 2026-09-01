# Contributing to mojo-analyze

Thanks for taking a look. This is a benchmark repo — the bar for contributing
is low, but a few things matter more here than in typical projects because
the whole point is that the numbers have to be trustworthy.

## Setup

```bash
git clone https://github.com/iinoshirozheng/mojo-analyze.git
cd mojo-analyze
pixi install
pixi run build            # compiles all three Mojo binaries -> dist/
pixi run prepare-corpus   # regenerates the synthetic word-frequency corpus
pixi run bench             # runs the full suite, writes results/results.json
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

Every benchmark's Mojo/Python/NumPy variants must produce byte-identical
`CHECKSUM` output for the same input (see each benchmark's own comments for
what's hashed). `scripts/bench.py` enforces this automatically and refuses to
report timings if variants disagree. If you're tempted to skip this check to
"just see the numbers" — don't. A fast wrong answer isn't a result, it's a
bug wearing a result's clothes. This project's whole value is honest,
reproducible comparisons; a mismatched checksum means something is broken,
not that "Mojo does it differently."

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

## Ideas that would be welcome

- A Rust variant per benchmark, for a fourth reference point.
- Testing on Linux (`pixi.toml` pins `osx-arm64`, `linux-64`, and
  `linux-aarch64`) — everything so far has only been run on Apple Silicon.
- More tasks in category C (real-world data processing) — CSV/JSON
  aggregation is an obvious next candidate.
- A GPU variant of the Mandelbrot renderer via MAX, for comparison against
  the CPU/SIMD numbers already in here.

## Reporting issues

If a benchmark's numbers look implausible (a variant reporting near-zero
time, or losing to an interpreted language by an amount that doesn't make
sense), include your hardware, OS, and the full `pixi run bench` output —
timing bugs are usually visible in the raw per-trial numbers before they're
averaged away.
