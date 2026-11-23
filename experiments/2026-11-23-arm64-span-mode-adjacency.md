# 2026-11-23 — Exact trial-order adjacency test for arm64 checked-Span timing modes

## One research question

**Are the previously observed slow timing modes of Mojo 1.2's checked-`Span` CSV scanner clustered into consecutive trial runs more often than expected by random placement at the same observed slow-mode frequency?**

This is a **small, independently reproducible methodology/diagnostic task on already captured arm64 measurements**, not a new Mojo execution or CPU-clock measurement. It is intentionally different from the 2026-11-15 monotone-Kendall audit of the canonical five-category snapshot: the signal here is a **binary bimodal state**, tested for **adjacent slow events** under an exact conditional null.

The stronger causal root-cause experiment remains **region-scoped CPU clock/frequency sampling on a Mojo-equipped native arm64 runner** and is not replaced by this secondary diagnosis.

## Provenance, data and correctness gate

Source data: [2026-09-23 affinity experiment](2026-09-23-csvagg-span-arm64-affinity.md), [workflow 35848004917](https://github.com/iinoshirozheng/mojo-analyze/actions/runs/35848004917), source/probe commit `2dd23f86dd0fd8c1d0400623e459c31f64e248e2`, runner `ubuntu-24.04-arm`, Neoverse-N2, pinned Mojo `1.2.0.dev2026092105`.

All variants in the original hardware experiment agreed on the exact checksum `10000000:68888897:109183569:15500599:57786009`, including two warmups and twenty measurements. The source [`run_affinity_bench.py`](csvagg_scan_access/run_affinity_bench.py) explicitly appends timing values **in trial order** for each variant while rotating the six-variant execution order each trial, making trial-adjacency analysis meaningful. No original timing data, program source or benchmark conclusion was changed.

Checked `Span` raw duration range is split by a wide empty gap: fast mode `<=0.335155` seconds, slow mode `>=0.565129` seconds. Define **slow** as duration `>0.45` s, within that empty gap. Cutoffs `0.40`, `0.50`, `0.55` yield exactly the same labels. This is a **pre-specified descriptive classification from the recorded gap**, not an assumed clock-frequency threshold.

## Exact method (zero Monte Carlo noise)

For each group of `n=20` ordered trial outcomes, hold the observed number `k` of slow events fixed. The statistic `A` counts pairs of adjacent slow runs (`i`, `i+1`). Enumerate **every** one of `C(20,k)` placements and compare observed `A` to its exact conditional distribution; test **excess temporal clustering**, i.e. `P(A >= A_observed | n,k)`. Also report a conservative discrete two-sided probability-mass tail for perspective.

This exact combinatorial permutation test assumes that, under the null, all placements of the observed `k` slow labels among trial positions are equally likely. Because variants rotate and a shared runner can have changing operating conditions, **the null is a limited model, not an established physical truth**.

## Independently computed results

| Variant | Slow trial indices (1-based) | Slow count | Adjacent slow pairs | Expected adjacency under fixed-count null | Exact placements | Exact clustering tail `P(A>=obs)` | Discrete two-sided p |
|---|---|---:|---:|---:|---:|---:|---:|
| Mojo 1.2 checked-Span, unpinned | 7,8,9,13,15,20 | 6/20 | **2** | 1.50 | 38,760 | **0.48349** | 0.61262 |
| Mojo 1.2 checked-Span, CPU-0 pinned | 2,5,6,10,11,12,14,18 | 8/20 | **3** | 2.80 | 125,970 | **0.60836** | 1.00000 |

Expectation follows `E[A]=k(k-1)/n`. Neither group shows more adjacent slow-mode trials than the conditional random-placement model would commonly produce. This does **not** demonstrate statistical independence, absence of shorter-lived CPU-state transitions inside a trial, or that the two groups have equal mode probabilities. The original data have only twenty measurements per arm.

**Result: useful negative diagnostic, not a causal explanation.** No evidence from this adjacency statistic that a long-lived contiguous "slow epoch" explains the multimodality. The modes can still arise from clocks, VM scheduling, microarchitecture, interrupt effects, input/run conditions or compiler/runtime interaction.

## Standalone exact reproduction (Python standard library)

Copy and run on any Python 3 runtime. The source vectors below are transcribed in order from the September 23 experiment note; output is **analysis of old samples**, not new measurements.

```python
from itertools import combinations
from math import comb

SAMPLES = {
    "span-unpinned": [
        0.332337,0.331638,0.331779,0.332035,0.330991,0.330913,
        0.616634,0.579347,0.565129,0.329411,0.331992,0.332104,
        0.613008,0.333822,0.616166,0.332578,0.332376,0.331009,
        0.334271,0.615589,
    ],
    "span-pinned": [
        0.330837,0.616444,0.332234,0.330924,0.614224,0.574679,
        0.332816,0.332956,0.330862,0.568182,0.567042,0.615333,
        0.333466,0.571511,0.332131,0.332399,0.333645,0.567863,
        0.334504,0.335155,
    ],
}

def exact_adj(samples, threshold):
    n = len(samples)
    pos = [i for i, value in enumerate(samples) if value > threshold]
    k = len(pos)
    observed = sum(b == a + 1 for a, b in zip(pos, pos[1:]))
    counts = [0] * k
    for positions in combinations(range(n), k):
        adjacent = sum(b == a + 1 for a, b in zip(positions, positions[1:]))
        counts[adjacent] += 1
    placements = comb(n, k)
    assert sum(counts) == placements
    p_cluster = sum(counts[observed:]) / placements
    p_two_sided = sum(count for count in counts
                      if count <= counts[observed]) / placements
    return n, k, observed, placements, p_cluster, p_two_sided, pos

for name, values in SAMPLES.items():
    assert len(values) == 20
    answer = exact_adj(values, 0.45)
    assert all(exact_adj(values, t) == answer for t in (0.40, 0.50, 0.55))
    print(name, answer)

assert exact_adj(SAMPLES["span-unpinned"], .45)[:4] == (20, 6, 2, 38760)
assert exact_adj(SAMPLES["span-pinned"], .45)[:4] == (20, 8, 3, 125970)
```

The standalone script was executed in the current x86_64 Python environment; all assertions passed, with `p_cluster` = 0.48348813209494323 (unpinned) and 0.608359133126935 (pinned).

## Boundaries and next step

- **No new performance measurement**, no codegen/assembly was emitted today, and no Mojo compiler/native arm64 hardware was available here. Do not transfer these p-values to a different runner/compiler.
- The exact test probes only *consecutive-state clustering*; it cannot measure host frequency or exclude nonconsecutive cyclic/hardware state behavior, and its power is limited by twenty trials.
- Original pointer and C controls had tightly clustered times; they are provenance context rather than "slow/fast" classified samples.
- **Next genuine causal test:** on a native arm64 Mojo runner, interleave repeated checked/pointer/C runs; record region CPU clocks and frequency where exposed, check every checksum, retain precise trial order and timestamps, and inspect matching binary/assembly. Compare host-state traces **conditioned on fast vs slow mode**; only then consider changing `ANALYSIS.md`.

**No changes** to canonical benchmark source, `results/results.json`, charts, `CONTRIBUTING.md` or `ANALYSIS.md` are warranted by this bounded negative finding.
