# 2026-11-16 — Portable TIME_SECONDS token grammar

## One research question

Can a benchmark subprocess emit a Python-specific numeric token that the harness silently interprets as a valid portable timing value?

## Reproduction and finding

The prior `scripts/bench.py` passed the trimmed `TIME_SECONDS` token directly to Python's `float()`. Python accepts underscores between digits: `float("1_0") == 10.0` and `float("1e1_0") == 10000000000.0`. These tokens are not ordinary decimal wire representations and can conceal producer-formatting mistakes. This is a **protocol correctness** finding, not a Mojo performance finding.

## Single intervention

Constrain the token to signed ASCII decimal / exponent notation via a full-match regular expression before conversion; leave the existing finite/positive check in `run_variant` unchanged. Standard forms such as `0.25`, `.5`, `+2.5E+1`, and `1e-3` remain accepted; underscores, `nan`, `inf`, hex floats and trailing words are rejected by the parser. Added `tests/test_bench_time_protocol.py` with positive and negative fixtures.

## Verification and limits

An isolated Python 3 reproduction confirmed `float("1_0")` and `float("1e1_0")` accept underscores. The proposed regular expression was independently exercised against accepted/rejected fixtures in a local Python shell. The full repository unit-test suite, CI and native Mojo benchmark were **not** run or verified in this session. The new test file and source change are committed but their CI outcome remains unconfirmed. No timing claim or benchmark result is published. This intervention deliberately does not change checksum semantics, benchmark code, `ANALYSIS.md`, or canonical results.

## Reproduce

```bash
python -m unittest discover -s tests -p 'test_bench_time_protocol.py'
python -m unittest discover -s tests
```

Source: `scripts/bench.py` and `tests/test_bench_time_protocol.py` on `main`; observed 2026-11-16. Code commit `ecdc44a46adb8be8b8b0067fe854b06a62d82a9d`; test commit `f28a3cc123f4f20f141e0aeefe8e8aa9bcdce624`.

## Conclusion

**Confirmed parser permissiveness; remediation committed; end-to-end verification pending.** This is an independently reproducible protocol-boundary issue, not evidence of a current faulty Mojo executable. No canonical performance conclusion changes.
