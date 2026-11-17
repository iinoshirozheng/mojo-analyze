# 2026-11-17 — Decimal-point grammar regression in benchmark timing protocol

## One research question

Does the decimal grammar added on 2026-11-16 actually accept ordinary fractional `TIME_SECONDS` tokens and reject escaped lookalikes?

## Evidence and finding

Inspected `scripts/bench.py` on `main` after the radar commit and the existing `tests/test_bench_time_protocol.py`. The prior raw-string pattern contained `\\\\.` (two backslashes followed by a dot in the regex source) where it intended `\\.` (one backslash followed by a dot). Python's regex engine therefore interpreted the former as a literal backslash followed by an arbitrary character, **not** a literal decimal point.

An isolated Python 3 reproduction of the exact prior pattern rejected valid `0.25` and `.5`, while accepting a backslash-prefixed lookalike such as `1\\x25`. This directly contradicts the prior research note's stated positive fixtures; those repository tests had not been verified end-to-end.

## Single intervention

Changed only the decimal-point escapes in `_DECIMAL_TIME` in `scripts/bench.py` and added the escaped lookalike to the existing negative regression fixtures. The intended ASCII decimal/exponent grammar and existing finite-positive timing gate are unchanged.

## Verification and limits

Independent Python 3 `re.fullmatch` reproduction using the corrected pattern: accepted `0.25`, `1e-3`, `+2.5E+1`, `.5`, `1`; rejected `1_0`, `1e1_0`, `1_000.5`, `nan`, `inf`, `0x1p-2`, `1.0 trailing`, and `1\\x25`. All 13 cases matched expectation. This is **isolated grammar verification**, not an end-to-end run of the repository tests or a Mojo benchmark. Attempted `git clone` for a complete checkout, but the container could not resolve `github.com`; GitHub CI status was not verified.

Reproduce in a connected checkout:

```bash
python -m unittest discover -s tests -p 'test_bench_time_protocol.py'
python -m unittest discover -s tests
```

## Conclusion

**Confirmed and corrected a protocol regression introduced by the previous day's change.** It is a correctness repair, not a performance finding. Do not update canonical benchmark results or `ANALYSIS.md` from this investigation. If CI fails, resolve before treating the repair as fully verified.

Source: `scripts/bench.py`, `tests/test_bench_time_protocol.py`, and `experiments/2026-11-16-time-token-grammar.md` on `main`, observed 2026-11-17. Code commit `ef41148f6cc8efd66bf1596f6426c8b022bfb89d`; regression fixture commit `c6b9c13921901638beee42daacfd84243d46d930`.
