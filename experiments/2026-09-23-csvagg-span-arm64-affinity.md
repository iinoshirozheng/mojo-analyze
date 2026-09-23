# Arm64 CPU-affinity probe for the Mojo 1.2 checked-`Span` timing modes

**Observed:** 2026-09-23  
**Scope:** one focused follow-up to the reproduced Sep-21/Sep-22 Category-D scanner anomaly.  
**Workflow run:** `35848004917`.  
**Job:** `107138717596` (`ubuntu-24.04-arm`).  
**Probe source commit:** `2dd23f86dd0fd8c1d0400623e459c31f64e248e2`.

## Question

The Sep-21 Mojo 1.2-nightly scanner experiment and Sep-22 exact rerun both showed two stable timing regimes for the **checked `Span[UInt8]` path on Linux arm64**, while the unsafe-pointer path and C control stayed stable.

**Is scheduler migration across the runner's four logical CPUs sufficient to explain the two checked-`Span` timing modes?**

The intervention is process CPU affinity only. The Mojo source, compiler, corpus, checked/pointer implementation, C control, and correctness contract are unchanged.

## Method

The probe used the same Category-D in-memory scanner source and pinned Sep-21 nightly that reproduced the anomaly:

- Mojo source: `experiments/csvagg_scan_access/csvagg_scan_access.mojo`;
- C control: `experiments/csvagg_scan_scope/csvagg_scan_scope.c`;
- Mojo: **1.2.0.dev2026092105 (`e9569894`)**;
- C: Ubuntu clang **18.1.3**, `-O3`;
- runner: GitHub `ubuntu-24.04-arm`, image `20260907.118.1`, Azure `eastus`;
- CPU: **4× Neoverse-N2 logical CPUs**, one thread per core, allowed affinity set `0-3`;
- corpus: **10,000,000 rows / 277.9 MiB / 99 categories**;
- every variant produced checksum `10000000:68888897:109183569:15500599:57786009` before timing;
- **2 discarded warmups + 20 measured trials**, with six variants rotated each trial.

One Mojo binary and one C binary were compiled. The affinity intervention therefore cannot change generated code:

- unpinned: normal allowed set `0-3`;
- pinned: `taskset -c 0` for the child process.

Both access modes were tested under both conditions:

1. Mojo 1.2 checked `Span`, unpinned;
2. Mojo 1.2 checked `Span`, pinned to CPU 0;
3. Mojo 1.2 unsafe pointer, unpinned;
4. Mojo 1.2 unsafe pointer, pinned to CPU 0;
5. C scanner, unpinned;
6. C scanner, pinned to CPU 0.

The Mojo binary SHA-256 was `eaf9c8340ba3c4d143d72c25b9c8fae51e24ed195b7c7e0312b9af4d431e8dbb`; the C binary SHA-256 was `77ef74322b4a13a19c0ec3b0e1615f8e7facd4a7bed12e406655599b4d43e234`.

Optimized assembly was emitted once for provenance. The Mojo file has 11,957 lines, one bounds-diagnostic string, and 16 whole-binary `b.hs` matches. Those counts remain supporting diagnostics only; this experiment is intentionally a **same-binary runtime intervention**, not another codegen comparison.

## Result

### Summary

| Variant | Mean | Median | Stdev | Min | Max |
|---|---:|---:|---:|---:|---:|
| Mojo 1.2 checked `Span`, unpinned | 0.412656 s | 0.332356 s | 0.127030 s | 0.329411 s | 0.616634 s |
| Mojo 1.2 checked `Span`, CPU-0 pinned | 0.434360 s | 0.334075 s | 0.128601 s | 0.330837 s | 0.616444 s |
| Mojo 1.2 pointer, unpinned | 0.193670 s | 0.193028 s | 0.002030 s | 0.191554 s | 0.198483 s |
| Mojo 1.2 pointer, CPU-0 pinned | 0.192984 s | 0.192698 s | 0.000826 s | 0.191613 s | 0.194462 s |
| C scanner, unpinned | 0.178233 s | 0.178177 s | 0.000323 s | 0.177730 s | 0.178924 s |
| C scanner, CPU-0 pinned | 0.178192 s | 0.178004 s | 0.000553 s | 0.177482 s | 0.179757 s |

Ordinary aggregate ratios are deliberately secondary because the checked-`Span` distribution is multimodal. Pinning changes the Span mean by **+5.26%** and median by only **+0.52%**; pointer mean changes **-0.35%**, while C mean changes **-0.02%**.

### The two modes survive CPU pinning

Using the same obvious separation used for the prior runs (fast values around 0.33 s; slow values above 0.56 s):

- **unpinned checked `Span`: 14 fast / 6 slow**;
  - fast-mode mean: **0.331947 s**;
  - slow-mode mean: **0.600979 s**;
- **CPU-0-pinned checked `Span`: 12 fast / 8 slow**;
  - fast-mode mean: **0.332661 s**;
  - slow-mode mean: **0.586910 s**.

The unpinned raw trials were:

`0.332337, 0.331638, 0.331779, 0.332035, 0.330991, 0.330913, 0.616634, 0.579347, 0.565129, 0.329411, 0.331992, 0.332104, 0.613008, 0.333822, 0.616166, 0.332578, 0.332376, 0.331009, 0.334271, 0.615589` seconds.

The CPU-0-pinned raw trials were:

`0.330837, 0.616444, 0.332234, 0.330924, 0.614224, 0.574679, 0.332816, 0.332956, 0.330862, 0.568182, 0.567042, 0.615333, 0.333466, 0.571511, 0.332131, 0.332399, 0.333645, 0.567863, 0.334504, 0.335155` seconds.

Both mode centers remain recognizable under the affinity intervention. The fast-mode center changes by only about **+0.22%**. The slow-mode mean is about **2.34% lower** when pinned, but its broad 0.567–0.616 s range overlaps the unpinned slow regime. Most importantly, **pinning does not remove the slow regime or collapse the distribution into one population**.

### Controls stay stable

The unsafe-pointer path and C scanner stay tightly clustered under both affinity policies. Pinning changes their means by roughly **-0.35%** and **-0.02%**, respectively. That makes a generic “taskset itself changed scanner throughput” explanation implausible for the checked-path multimodality.

## Conclusion

**Single-CPU process affinity is not sufficient to eliminate the reproduced Mojo-1.2 checked-`Span` timing modes.** The simple hypothesis that the slow mode is caused merely by the process migrating among the runner's four logical CPUs is therefore rejected for this pinned compiler/source/runner combination.

This is a useful negative result, not a root-cause identification. CPU 0 can still experience frequency/state changes, VM host scheduling, interrupts, memory-system effects, or another runtime/compiler interaction while the guest process remains pinned. The experiment also does not test whether a *specific different* logical CPU has different behavior; it tests the narrower and stronger claim that preventing migration to other logical CPUs makes the two-mode behavior disappear. It does not.

The result strengthens the next diagnostic direction: collect host/runtime evidence that can distinguish the two regimes, or reproduce on controlled arm64 hardware where CPU frequency, counters and scheduling can be observed. Preserve the pointer and C controls and keep raw per-trial samples; neither a mean nor a median alone describes this distribution reliably.

The unsafe-pointer path remains a diagnostic control, not a recommendation for canonical benchmark code. This hosted-runner follow-up does **not** change `ANALYSIS.md`, `results/results.json`, charts, or canonical benchmark implementations.

## Evidence / provenance

- workflow run: https://github.com/iinoshirozheng/mojo-analyze/actions/runs/35848004917
- job: `107138717596`
- artifact: `10744506295` (`csvagg-scan-affinity-arm64`)
- artifact SHA-256: `e2ae486ace92613feb2e6bba9b36118994c6ad3f13b8cc70dadafcd7b75218a2`
- probe setup commit: `2dd23f86dd0fd8c1d0400623e459c31f64e248e2`
- previous reproducibility note: `experiments/2026-09-22-csvagg-span-arm64-rerun.md`
- harness: `experiments/csvagg_scan_access/run_affinity_bench.py`
- workflow: `.github/workflows/research-csvagg-scan-affinity.yml`
