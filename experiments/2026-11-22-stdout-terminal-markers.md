# 2026-11-22 — Terminal timing/checksum stdout protocol gate

## One focused research question

Can the current benchmark harness publish measurements from a child process that prints a syntactically valid `TIME_SECONDS:` / `CHECKSUM:` pair **and then prints additional output**, even though the project contract requires those records to be the final two stdout lines?

This is a benchmark *methodology/correctness* experiment, **not** new Mojo speed data. The higher-priority native-arm64 checked-Span CPU-clock experiment still cannot be reproduced without a Mojo-equipped arm64 runner.

## Baseline and falsifying fixture

On `main` (before intervention), `scripts/bench.py::parse_output` searched all stdout lines and returned the first valid values regardless of their final position. For example:

```text
TIME_SECONDS: 0.25
CHECKSUM: abc123
ERROR: post-run verification failed
```

The original parser returned `(0.25, "abc123")` instead of raising. The returned data would be eligible for the checksum comparison and results publication as long as the child exited successfully. A status/error trailer can thus invalidate the temporal meaning of the measured interval without failing the parser.

## Single intervention and regression suite

`scripts/bench.py` now requires valid timing and checksum markers to occupy the **final two nonempty stdout lines**, in that order. Earlier benign diagnostics remain allowed; blank trailing lines remain allowed. Existing numeric grammar, finite-positive timing checks, duplicate-marker rejection, empty-checksum rejection and missing-marker error handling are preserved.

The targeted suite `tests/test_bench_time_protocol.py` now covers leading diagnostics accepted, trailing failure rejected, inverted order rejected, an interleaved diagnostic rejected, duplicate marker rejected and missing markers unmodified. The old decimal-token regression cases remain.

## Verification — discovery of a regression and repair

1. The original source and counterexample were inspected; a Python-isolated execution confirmed the original accepted the trailing-ERROR fixture and the candidate rejected it. The local isolated fixture set covered 7 cases.
2. Initial code and new regression tests were committed as [`913e87d`](https://github.com/iinoshirozheng/mojo-analyze/commit/913e87df6c28977550d4ffd3343d9ed0823bf13d) and [`ac4abc9`](https://github.com/iinoshirozheng/mojo-analyze/commit/ac4abc932d5acac4d37afa8dcfb6873dbf78da1c). The GitHub Actions [benchmark run 197](https://github.com/iinoshirozheng/mojo-analyze/actions/runs/45010790319) **failed on both x86_64 and arm64**: the early positional check masked three pre-existing expected error messages (two duplicate-CHECKSUM subtests and one missing-CHECKSUM test). The six new terminal-marker tests passed on both runners. This demonstrates why testing a parser repair against the **full existing suite** matters; it is not just an isolated grammar proof.
3. Follow-up [`ebd2b40`](https://github.com/iinoshirozheng/mojo-analyze/commit/ebd2b405287410d78ab6f59b754ee9a67d228f7f) moves the positional check **after parsing only if both records are present**, so duplicate errors are raised first and missing records continue to be diagnosed by `run_variant`. Static inspection verifies that order; the corrected commit's [workflow 45010894029](https://github.com/iinoshirozheng/mojo-analyze/actions/runs/45010894029) passed the **Test checksum publication gate** step on both x86_64 and arm64, and completed all three language-build steps on both architectures. At observation, the full benchmark jobs were still running; do not equate step success with completed workflow success. This note does not conceal the initial failure.
4. No live Mojo compiler, native arm64 timing run, assembly output, or new hardware measurement was available in this environment. The correction is evidence for a stdout contract bug, *not* a change to benchmark performance ranking.

## Conclusion and required follow-up

**Confirmed method flaw:** valid field syntax and checksum equality are insufficient if the protocol tail is not checked. **Corrected and cross-architecture protocol-step-verified repair**, with regression tests and a CI-discovered diagnostic compatibility bug fixed in a follow-up commit. The corrected workflow's full benchmark and artifact steps were still in progress; a protocol test pass is not a new Mojo performance finding. Do not update `ANALYSIS.md`, results or charts solely from this finding. Reproduce in a checkout via:

```bash
python3 -m unittest discover -s tests -p 'test_bench*.py' -v
```

Repo: `iinoshirozheng/mojo-analyze`, main, observed 2026-11-22 Asia/Taipei. Key files: `scripts/bench.py`, `tests/test_bench_time_protocol.py`, `tests/test_bench_checksum_gate.py`.
