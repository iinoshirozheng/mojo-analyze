# Category D scanner: Span indexing vs unchecked Pointer reads (2026-09-19)

## Research question

After the 2026-09-18 timing-scope experiment isolated a large in-memory Category-D scanner gap, is Mojo 1.0's checked `Span[UInt8]` indexing a material cause, or does most of the Mojo-vs-C gap remain after removing only the subscript safety machinery?

This is the **single research task for 2026-09-19**. It follows the open Category-D scanner/codegen hypothesis in `CONTRIBUTING.md`; no unrelated benchmark work is bundled into this result.

## Experimental change

A new focused harness, `experiments/csvagg_scan_access/`, keeps the same scanner semantics and the same 10,000,000-row generated CSV corpus as the Sep-18 scanner experiment.

Both Mojo modes run in the **same compiled binary** and preload the CSV before the timer:

- `--access span`: reads each delimiter byte through `data[i]`, where `data` is `text.as_bytes()` (`Span[UInt8]`).
- `--access ptr`: obtains `var ptr = data.unsafe_ptr()` before timing and replaces only byte reads with `ptr[unsafe_offset=i]`.

The explicit logical guards (`i < n`), delimiter constants, field boundaries, accounting, checksum, timer scope, input bytes and compiler are unchanged. The pointer path is intentionally unsafe: its validity depends on the same explicit `i < n` guards being correct. It is a mechanism probe, not a recommendation to make the canonical benchmark unsafe.

The same job also runs the Sep-18 C scanner (`--scope scan`) as a reference under the same corpus and runner.

## Verification contract

- Corpus: 10,000,000 rows, 277.9 MiB, 99 categories.
- Toolchain: Mojo 1.0.0 (`ed45d567`), clang 18.1.3.
- Architectures: GitHub-hosted Ubuntu 24.04 x86_64 and arm64.
- Warmups: 2 per variant.
- Measured trials: 7 per variant, with execution order rotated by trial.
- Correctness gate: all three variants must emit the same checksum before timing results are accepted.
- Expected/observed checksum on both architectures:
  `10000000:68888897:109183569:15500599:57786009`.
- Workflow run: `35436681203`.
- Probe source commit: `c119877a4e703d3afb22bf948bb7b348e6bd542d`.
- Artifacts:
  - x86_64: `csvagg-scan-access-x86_64` / artifact `10582635878`
  - arm64: `csvagg-scan-access-arm64` / artifact `10581264725`

## Results

### x86_64

| Variant | Mean (s) | Median (s) | Relative to C (mean) |
|---|---:|---:|---:|
| Mojo checked Span | 0.322081 | 0.311766 | 1.4088x |
| Mojo unchecked Pointer | 0.245135 | 0.243241 | 1.0723x |
| C scanner | 0.228615 | 0.224856 | 1.0000x |

Within the same Mojo binary, unchecked pointer reads reduce mean scanner time by **23.9%** and median time by **22.0%** relative to checked Span indexing. Using the same-run C reference, the relative gap contracts from 40.9% to 7.2%; this intervention closes about **82% of the measured Mojo-over-C excess ratio** in this focused run.

The checked-Span x86_64 trials are noisier than the pointer/C trials, so exact percent values should not be promoted to a controlled-host regression threshold. The direction and size are nevertheless far larger than the run's ordinary pointer/C scatter.

### arm64

| Variant | Mean (s) | Median (s) | Relative to C (mean) |
|---|---:|---:|---:|
| Mojo checked Span | 0.330938 | 0.330837 | 1.8543x |
| Mojo unchecked Pointer | 0.195733 | 0.195220 | 1.0967x |
| C scanner | 0.178471 | 0.178365 | 1.0000x |

Unchecked pointer reads reduce mean scanner time by **40.9%** and median time by **41.0%** relative to checked Span indexing. The same-run Mojo/C ratio contracts from 1.854x to 1.097x, closing about **89% of the measured Mojo-over-C excess ratio** in this focused run.

The arm64 trials are especially stable: Span stdev is ~0.00085 s and pointer stdev ~0.00241 s, so this is not an ordinary wall-clock fluctuation.

## Codegen evidence

The optimized assembly explains why this is more than a source-level correlation.

### Unchecked pointer path

On both architectures, the pointer branch lowers the delimiter scans to the same basic shape as the C reference: direct byte load/compare, index increment, and the explicit end-of-buffer loop test.

Representative x86_64 pointer loop:

```asm
cmpb $44, (%r13,%rdx)
je   ...
incq %rdx
cmpq %rdx, %rsi
jne  ...
```

Representative arm64 pointer loop:

```asm
ldrb w11, [x26, x9]
cmp  w11, #44
b.eq ...
add  x9, x9, #1
cmp  x10, x9
b.ne ...
```

### Checked Span path

The checked-Span branch retains additional safety-control machinery around later field accesses. On x86_64, several hot loops contain an extra pre-load range guard such as `cmpq ...; jae <bounds slow path>`; on arm64 the corresponding loops use `cmp ...; b.hs <bounds slow path>`. The slow paths are tied to the source file and construct the stdlib's `"index ... is out of bounds, valid range is 0 to ..."` diagnostic.

The Span loops also materialize error-context values before some byte loads. The first field scan is partially optimized into an equality guard against a compiler-derived limit, while later field scans retain explicit range guards. By contrast, the unchecked-pointer branch has no corresponding bounds-diagnostic edges for its delimiter loads.

A whole-binary grep for `std::collections::check_bounds::do_asserts` would have been misleading: that helper still appears elsewhere in the Mojo binary, while the scanner's hot path implements the relevant safety checks as **inlined guards and slow-path edges**, not as one out-of-line helper call per byte.

## Conclusion

**Checked Span byte access is a material cause of the isolated Category-D in-memory scanner gap under Mojo 1.0.0.** Replacing only Span subscripts with unchecked pointer reads removes most of the same-run gap on both x86_64 and arm64, and optimized assembly confirms that the intervention removes the corresponding inlined bounds-control/diagnostic paths from the delimiter scans.

This is stronger than the earlier hypothesis that safety checks merely existed in source: the single-mechanism intervention demonstrates a large causal effect while preserving the input, explicit `i < n` guards, checksum and scanner semantics.

The result does **not** justify changing the canonical benchmark to unsafe pointers. The safe form carries a correctness guarantee that the pointer form deliberately assumes. It also does not prove that current Mojo 1.1/1.2 nightlies behave the same way; this finding is pinned to Mojo 1.0.0 (`ed45d567`) and should be re-verified before generalizing across compiler versions.

A residual same-run gap remains after the unsafe intervention: about **7.2% mean on x86_64 and 9.7% on arm64** versus C. A future task can inspect that smaller residual through loop/control lowering or repeat the safe-vs-pointer probe on Mojo 1.1/nightly. It should not reopen hash-table/storage hypotheses that the preceding semantic-boundary experiments already deprioritized.

## Canonical-results policy

This is a focused hosted-runner mechanism experiment. It does **not** update `ANALYSIS.md`, canonical `results.json`, charts, or headline cross-language benchmark conclusions. Those remain controlled by the repository's existing canonical methodology.
