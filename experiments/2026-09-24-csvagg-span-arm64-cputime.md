# Arm64 child-CPU-time probe for the Mojo 1.2 checked-`Span` timing modes

**Observed:** 2026-09-24  
**Scope:** one focused follow-up to the reproduced Category-D arm64 checked-`Span` timing anomaly.  
**Workflow run:** `35985827133`.  
**Job:** `107588131727` (`ubuntu-24.04-arm`).  
**Probe source commit:** `96d25249849c78a85f41f6bc03204b9e7818c1a4`.

## Question

The Sep-21/Sep-22 experiments reproduced two timing regimes for the Mojo 1.2 checked `Span[UInt8]` scanner on Linux arm64, and the Sep-23 affinity intervention showed that pinning the process to one logical CPU does not remove them.

**Does the slow wall-time mode also carry materially more process CPU time, or is it mainly extra elapsed time while the child is not consuming CPU?**

This is deliberately a runtime-observation probe, not a new scanner implementation. It keeps the checked-Span/pointer/C controls and CPU-0 affinity from the previous experiment.

## Method

The exact scanner source, compiler pin, C control and corpus contract were retained:

- Mojo scanner: `experiments/csvagg_scan_access/csvagg_scan_access.mojo`;
- C control: `experiments/csvagg_scan_scope/csvagg_scan_scope.c`;
- Mojo: **1.2.0.dev2026092105 (`e9569894`)**;
- C: Ubuntu clang **18.1.3**, `-O3`;
- runner: GitHub `ubuntu-24.04-arm`, image `20260907.118.1`, Azure `southcentralus`;
- CPU: **4× Neoverse-N2**, one thread per core; every measured child was pinned to CPU 0;
- corpus: **10,000,000 rows / 277.9 MiB / 99 categories**;
- every variant passed the checksum gate with `10000000:68888897:109183569:15500599:57786009`;
- **2 discarded warmups + 30 measured trials**, rotating checked Span, unsafe pointer and C control.

The wrapper records two timing views for each child:

1. the scanner's existing internal `TIME_SECONDS` wall-clock measurement; and
2. the increment of Python `resource.getrusage(RUSAGE_CHILDREN)` user+system CPU time across the child invocation.

Important limitation: the second quantity covers the **whole child lifecycle**, including pre-timed setup/file materialization, while `TIME_SECONDS` covers the scanner region only. Therefore absolute `child_cpu / scan_wall` ratios are not meaningful as utilization. The useful evidence is the **difference between otherwise identical fast- and slow-mode Span trials**, plus the stable pointer/C controls.

The Mojo binary SHA-256 was `eaf9c8340ba3c4d143d72c25b9c8fae51e24ed195b7c7e0312b9af4d431e8dbb`; the C binary SHA-256 was `77ef74322b4a13a19c0ec3b0e1615f8e7facd4a7bed12e406655599b4d43e234`.

## Result

The checked-Span bimodality reproduced again, this time with **13 fast / 17 slow** trials using the same 0.45 s separation used by the diagnostic harness.

| Span regime | Count | Scan wall mean | Whole-child CPU mean | Scan wall median | Whole-child CPU median |
|---|---:|---:|---:|---:|---:|
| Fast | 13 | **0.333713 s** | **1.000488 s** | 0.333750 s | 1.001881 s |
| Slow | 17 | **0.579662 s** | **1.243970 s** | 0.559620 s | 1.230762 s |

The slow regime adds:

- **+0.245949 s** of scanner wall time (**+73.7%** versus the fast-mode mean);
- **+0.243482 s** of whole-child CPU time (**+24.3%** versus the fast-mode mean).

The added CPU-accounted time is about **99.0% of the added scanner wall time** (`0.243482 / 0.245949`). Because the CPU measurement also contains pre-timed work, that ratio is not a proof that every extra CPU second occurs inside the scanner. It does, however, directly contradict the simple picture in which the slow mode is almost entirely an elapsed-time pause/descheduling episode with unchanged process CPU consumption.

### Controls remain stable

The unsafe-pointer and C controls remained single-regime and tight:

| Variant | Scan wall mean | Wall stdev | Whole-child CPU mean | CPU stdev |
|---|---:|---:|---:|---:|
| Mojo 1.2 unsafe pointer | **0.194616 s** | 0.001892 s | **0.861900 s** | 0.008165 s |
| C scanner | **0.178305 s** | 0.000457 s | **0.267544 s** | 0.001228 s |

This matters because the wrapper, CPU affinity, page-cache environment and host are shared. The large CPU-time split appears only with the checked-Span mode that already shows the wall-time split.

## Conclusion

**A pure host-descheduling / steal-time explanation is not sufficient for the reproduced checked-`Span` slow mode.** Slow-mode trials do not merely take longer on the wall clock; they also accumulate roughly **0.243 s more process CPU time**, nearly matching the roughly **0.246 s extra scanner wall time**.

This still does **not** identify the root cause. CPU time continues to accrue during lower-frequency execution, memory stalls while scheduled, extra runtime/compiler work, kernel work charged to the process, or another CPU-resident path. The whole-child CPU measurement also includes pre-timed setup, so a more precise follow-up would place a process/thread CPU clock around the scanner region itself or use controlled-hardware counters.

The result narrows the diagnostic tree:

1. simple cross-logical-CPU migration was already rejected by the Sep-23 affinity probe;
2. today, “mostly paused/descheduled with unchanged CPU work” is also rejected as a sufficient explanation;
3. next evidence should distinguish **more executed/accounted work** from **same work at a different effective CPU/memory state**, ideally with scanner-scoped CPU clocks and hardware counters on controlled arm64.

The unsafe-pointer path remains a diagnostic control, not a recommendation for canonical benchmark code. This hosted-runner diagnostic does **not** change `ANALYSIS.md`, `results/results.json`, charts, or canonical benchmark implementations.

## Evidence / provenance

- workflow run: https://github.com/iinoshirozheng/mojo-analyze/actions/runs/35985827133
- job: `107588131727`
- artifact: `10802301857` (`csvagg-scan-cputime-arm64`)
- artifact SHA-256: `8ac14c6860eaa0e6559bdf1ed72d00072a77028cc999771b9351286d79d45702`
- probe setup commit: `96d25249849c78a85f41f6bc03204b9e7818c1a4`
- previous affinity note: `experiments/2026-09-23-csvagg-span-arm64-affinity.md`
- harness: `experiments/csvagg_scan_access/run_cpu_time_bench.py`
- workflow: `.github/workflows/research-csvagg-scan-cputime.yml`
