# 2026-11-24 — Exact rotating execution-slot diagnostic for arm64 checked-Span timing modes

## Question

Does the slow mode of the checked-Span scanner associate with its **within-trial execution slot** in the existing six-variant rotating schedule? This is different from yesterday's temporal adjacency test: a repeating position effect could exist without adjacent slow trials. It tests a possible harness-order confound, not a new performance ranking or CPU-clock measurement.

## Provenance and correctness

[Original Sep 23 experiment](2026-09-23-csvagg-span-arm64-affinity.md), [run 35848004917](https://github.com/iinoshirozheng/mojo-analyze/actions/runs/35848004917), [pinned harness at 2dd23f8](https://github.com/iinoshirozheng/mojo-analyze/blob/2dd23f86dd0fd8c1d0400623e459c31f64e248e2/experiments/csvagg_scan_access/run_affinity_bench.py). Linux arm64 Neoverse-N2, Mojo 1.2.0.dev2026092105, same binary for pinned/unpinned modes. The source note records checksum 10000000:68888897:109183569:15500599:57786009 for all variants, and pinned harness checks checksum on each warmup and trial before appending. No new native execution here. Current environment x86_64, no Mojo or Pixi found.

Original measured arrays (also reproduced in [Nov 23 adjacency note](2026-11-23-arm64-span-mode-adjacency.md)) split at 0.45 seconds, inside the empty gap 0.335155–0.565129 seconds. Slow labels at 1-based trial numbers: unpinned 7,8,9,13,15,20; pinned 2,5,6,10,11,12,14,18. All thresholds strictly between gap endpoints give identical labels. Original source explicitly orders variants span-unpinned, span-pinned, pointer-unpinned, pointer-pinned, C-unpinned, C-pinned and rotates left by zero-based trial index modulo six, independently restarting at trial zero after warmups.

## Method and result

For original variant index i and zero-based trial t, execution slot = (i-t) mod 6. Hold the number of slow observations k fixed and enumerate all C(20,k) placements. The statistic S = sum over slots of observed slow count squared divided by slot capacity is monotonic in the Pearson 2-by-6 contingency statistic under fixed margins. Multiply by 12 for integer exact comparisons (slot capacities are 3 or 4). The upper tail is an omnibus association test without asymptotic chi-square assumptions for tiny cell sizes. Two exploratory tests use Bonferroni correction.

| Condition | Capacity by slots 1–6 | Slow counts by slots 1–6 | Tail placements / all | Exact p | Bonferroni p |
|---|---|---|---|---:|---:|
| Unpinned | 4,3,3,3,3,4 | 2,0,0,0,2,2 | 6468 / 38760 | 0.166873 | 0.333746 |
| CPU0 pinned | 4,4,3,3,3,3 | 2,0,3,2,1,0 | 9627 / 125970 | 0.076423 | 0.152846 |

Pinned slot 3 is 3/3 slow but a post-hoc cell observation is not a separately confirmed effect. Neither omnibus association is significant at 0.05, even before correction. **No sufficient evidence of a rotating-slot explanation in this sample; cannot exclude order effects.** Fixed cyclic ordering confounds slot and trial phase and the null assumes exchangeable labels conditional on k. Only 20 trials per arm, sparse cells, no randomized schedule or host-state logs. This is a descriptive, exact conditional audit, not a causal test of ordering or a proof of independence.

## Reproduction

Executed Python 3 standard-library enumeration in current environment; no external dependencies, no Monte Carlo noise. The inputs are slow labels from the original measured durations and original variant indices.

```python
from itertools import combinations
from collections import Counter
from math import comb

cases = [(0,[7,8,9,13,15,20]), (1,[2,5,6,10,11,12,14,18])]
expected = [(6468,38760), (9627,125970)]
for (idx,slow), target in zip(cases, expected):
    slots = [(idx-t)%6 for t in range(20)]
    capacity = Counter(slots)
    k = len(slow)
    observed = Counter(slots[t-1] for t in slow)
    weights = [12//capacity[s] for s in range(6)]
    def score(counts):
        return sum(counts[s]**2*weights[s] for s in range(6))
    cutoff = score(observed)
    ge = total = 0
    for placement in combinations(range(20),k):
        total += 1
        ge += score(Counter(slots[t] for t in placement)) >= cutoff
    assert total == comb(20,k)
    assert (ge,total) == target
    print(idx, [capacity[s] for s in range(6)],
          [observed[s] for s in range(6)], cutoff, ge,total,
          ge/total, min(1,2*ge/total))
```

## Next step and boundaries

The stronger unresolved experiment remains region-scoped CPU clock/frequency evidence on a native ARM64 Mojo runner, with checksum-verified checked/pointer/C controls and same-binary assembly provenance. Randomize/counterbalance execution order rather than interpreting deterministic rotation as randomization; retain actual order and per-trial clocks. No new assembly or timing measurements today; no change to canonical source, ANALYSIS.md, charts or results. This single research note is a secondary diagnostic of previously captured data, not a repeat of adjacency testing.
