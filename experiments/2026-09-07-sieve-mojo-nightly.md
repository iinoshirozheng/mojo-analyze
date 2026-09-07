# Mojo Sieve: stable 1.0.0 vs Sep-7 1.1 nightly

Date: 2026-09-07

## Research question

Does the exact Sep-7 Mojo nightly (`1.1.0.dev2026090705`) materially change
Category B's raw-pointer Sieve performance or generated code relative to the
canonical stable Mojo 1.0.0 compiler?

This question was prompted by the Sep-7 official compiler work consolidating
ordinary dynamic conditional lowering from `hlcf.if` toward `hlcf.elif`. The
experiment tests the compiler revision as a whole; it **cannot attribute any
observed difference specifically to that one internal migration**.

Official context:
- https://github.com/modular/modular/commit/2b47eeef01fd2d85269184ced847dc75d2c5040a
- https://github.com/modular/modular/commit/0e6151c037e0b8cc4f36ce12e6514f51a53eff73
- https://github.com/modular/modular/commit/7704a2872732dafa201dc0fd370513c7cbc1b831

## Method

The source, input and compiler options are identical. Only the Mojo toolchain
revision changes:

- stable: `Mojo 1.0.0 (ed45d567)`
- nightly: `Mojo 1.1.0.dev2026090705 (6930d976)`
- source: `benchmarks/sieve/sieve.mojo`
- limit: `50,000,000`
- Linux x86_64 and Linux arm64 GitHub-hosted runners
- 2 discarded warmups + 7 measured trials per compiler per architecture
- each binary times itself using the benchmark's existing contract
- result is rejected unless every run produces the same `CHECKSUM`
- both compilers also emit assembly from the exact same source

The reproducible driver is `scripts/bench_sieve_mojo_nightly.py`.

Workflow run:
https://github.com/iinoshirozheng/mojo-analyze/actions/runs/34109988796

Artifacts:
- `sieve-mojo-nightly-20260907-x86_64`
- `sieve-mojo-nightly-20260907-arm64`

## Correctness

Every stable and nightly run on both architectures produced:

`3001134:548121944`

So the performance/codegen comparison is checksum-valid.

## Timing result

| Linux runner | Stable mean | Nightly mean | Nightly vs stable | Stable median | Nightly median |
|---|---:|---:|---:|---:|---:|
| x86_64 | 0.201471 s | 0.215407 s | **6.9% slower** | 0.201267 s | 0.214625 s |
| arm64 | 0.164981 s | 0.164707 s | **0.2% faster / effectively unchanged** | 0.165010 s | 0.164307 s |

Dispersion matters because these are shared runners. x86_64 stable/nightly
stdevs were 0.004956 s and 0.010291 s respectively (about 2.5% and 4.8% of
their means); arm64 stable/nightly stdevs were 0.003239 s and 0.002134 s
(about 2.0% and 1.3%). The x86 mean and median move in the same direction,
but the effect does **not** reproduce on arm64, so this is recorded as an
architecture-specific codegen-regression candidate rather than a portable
"Mojo 1.1 is slower" conclusion.

## Generated-code inspection

The assembly artifacts are not byte-identical, as expected for two compiler
revisions:

| Architecture | Stable assembly | Nightly assembly |
|---|---:|---:|
| x86_64 | 256,756 bytes / 7,691 lines | 258,929 bytes / 7,887 lines |
| arm64 | 250,700 bytes / 7,308 lines | 261,362 bytes / 7,519 lines |

More importantly, the Sieve's inner **marking loop** is structurally unchanged
on both architectures.

x86_64 stable and nightly each emit the same five-instruction loop shape:

```asm
movb  $0, (...)
addq  <prime>, <index>
cmpq  <limit>, <index>
jle   <mark-loop>
jmp   <outer-loop>
```

arm64 stable and nightly likewise keep the same five-instruction shape:

```asm
strb  wzr, [...]
add   <index>, <index>, <prime>
cmp   <index>, <limit>
b.le  <mark-loop>
b     <outer-loop>
```

The final 50-million-element **count + sum scan** is where a concrete x86_64
code-shape difference appears. Stable uses a 10-instruction loop body, while
the nightly uses 11 instructions and introduces an explicit zeroing move plus
a different induction/termination sequence. In simplified form:

```text
x86_64 stable: 10 instructions / element
x86_64 nightly: 11 instructions / element
arm64 stable:   8 instructions / element
arm64 nightly:  8 instructions / element
```

The arm64 scan changes register/termination strategy but not its instruction
count, matching the absence of a measurable timing change there.

This does **not** prove that one extra x86 instruction alone causes the full
6.9% wall-time difference. It does narrow the investigation: the marking loop
that originally motivated Category B is not where stable/nightly diverge, while
a loop executed roughly 50 million times does have a revision-specific x86
codegen change.

Assembly SHA-256s for independent artifact verification:

- x86_64 stable: `cfc09c31c78e29a66ff1a3d14306221ff8ddbc4d5d5ea22a932f8402ead9fbc0`
- x86_64 nightly: `4d3d411e49964f1c507eaa326494304c85ea812e055c767e9967bdf4be190860`
- arm64 stable: `5e0e44b72916b131b2185e1113351b7e8a95cf879a4eb256cf9ea7f8b8c5abb8`
- arm64 nightly: `da876361cc6e28920e93b9f0f571a0dc3937cda80791d628cf4de2d1350138da`

## Conclusion

The Sep-7 nightly is **not a uniform Sieve performance change**. It is
checksum-equivalent and effectively identical to stable on Linux arm64, while
this 7-trial Linux x86_64 campaign is about 6.9% slower in both mean/median.
Generated assembly gives the x86 observation a plausible codegen lead: the
marking loop is unchanged, but the final count/sum scan grows from 10 to 11
instructions per element. That architecture-specific difference is worth
tracking across later nightlies or a controlled x86 host.

The result is deliberately kept out of canonical `ANALYSIS.md` and
`results/results.json`. Shared-runner evidence from one compiler snapshot is
not sufficient to rewrite the stable benchmark scoreboard, and this experiment
does not claim the `hlcf.if` -> `hlcf.elif` migration itself caused the change.
