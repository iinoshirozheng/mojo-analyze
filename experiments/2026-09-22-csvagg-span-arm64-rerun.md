# Arm64 rerun of the Mojo 1.2-nightly checked-`Span` timing anomaly

**Observed:** 2026-09-22  
**Scope:** one focused reproducibility/methodology follow-up to the 2026-09-21 Category-D scanner experiment.  
**Original workflow run:** `35588217725`.  
**Independent rerun job:** `106703859330` (`ubuntu-24.04-arm`).  
**Exact source checkout:** `14462e8d3fab426d44917df6455fa90a3ae552c8`.

## Question

The Sep-21 Mojo 1.2-nightly scanner experiment found a correctness-preserving but visibly bimodal timing distribution on Linux arm64 for the **checked `Span[UInt8]` path only**. Nine of 15 trials were around 0.330–0.333 s while six were around 0.568–0.617 s; the Mojo 1.1 checked path, both unsafe-pointer controls, and C remained stable.

**Does that arm64 multimodal behavior reproduce when the exact same successful job is independently re-run with the same source, pinned compilers, corpus, checksum contract, and 15-trial methodology?**

This is intentionally a repeatability test of yesterday's anomaly. It does not introduce another benchmark mechanism, change canonical benchmark code, or use today's Sep-22 nightly.

## Method

The successful Sep-21 arm64 job was re-run through GitHub Actions rather than rebuilding a new experiment around the observation. GitHub therefore checked out the same source commit and used the same workflow definition:

- source: `experiments/csvagg_scan_access/csvagg_scan_access.mojo`;
- corpus: **10,000,000 rows / 277.9 MiB / 99 categories**;
- Mojo 1.1: **1.1.0 (`8189361e`)**;
- Mojo 1.2 nightly: **1.2.0.dev2026092105 (`e9569894`)**;
- C: Ubuntu clang **18.1.3**, `-O3`;
- runner image: `ubuntu-24.04-arm`, image version `20260907.118.1`, Neoverse N2 / Azure eastus;
- modes: Mojo 1.1 checked `Span`, Mojo 1.1 unsafe pointer, Mojo 1.2 checked `Span`, Mojo 1.2 unsafe pointer, and C scanner;
- the CSV is loaded before the timed scanner;
- **2 discarded warmups + 15 measured trials**, with variant execution order rotated each trial;
- all variants again produced the exact checksum:
  `10000000:68888897:109183569:15500599:57786009`.

The optimized assembly was regenerated as part of the rerun. It has the same coarse diagnostics as the original job: Mojo 1.1 / 1.2 arm64 assembly lengths **12,364 / 11,957 lines**, one bounds-diagnostic string in each, and whole-binary `b.hs` counts **16 / 16**. These counts remain supporting evidence only, not a hot-loop branch census.

## Result

### Repeat-run summary

| Variant | Mean | Median | Stdev |
|---|---:|---:|---:|
| Mojo 1.1 checked `Span` | 0.331529 s | 0.331421 s | 0.001336 s |
| Mojo 1.1 unsafe pointer | 0.194541 s | 0.194727 s | 0.002209 s |
| Mojo 1.2 nightly checked `Span` | 0.526334 s | 0.571024 s | 0.123098 s |
| Mojo 1.2 nightly unsafe pointer | 0.193264 s | 0.193117 s | 0.001220 s |
| C scanner | 0.178208 s | 0.178192 s | 0.000327 s |

The Mojo-1.2 checked-`Span` trials were:

`0.331888, 0.615424, 0.331326, 0.330952, 0.614322, 0.333645, 0.615653, 0.571024, 0.613645, 0.615473, 0.613378, 0.566622, 0.564470, 0.562391, 0.614795` seconds.

Using the same obvious separation as the first run:

- **4 fast trials:** 0.330952–0.333645 s, mean **0.331953 s**;
- **11 slow trials:** 0.562391–0.615653 s, mean **0.597018 s**.

The anomaly therefore **reproduces**, but the *occupancy of the modes changes materially*: the original run had 9 fast / 6 slow trials, while the rerun has 4 fast / 11 slow trials. Because the slow mode is now the majority, even the ordinary median lands in the slow regime.

### Controls remain stable

The important control behavior is nearly unchanged from the first run:

- the repeated fast-mode center (**0.331953 s**) is within about **0.04%** of the original fast-mode mean (**0.332084 s**);
- Mojo 1.2 unsafe-pointer mean moved only about **+0.19%** versus the original run;
- C mean moved about **-0.04%**;
- Mojo 1.1 checked `Span` mean moved about **+0.06%**.

So this is not evidence that the whole runner slowed down or that the workload/corpus changed. The instability again isolates to the pinned Mojo-1.2 checked-`Span` variant while the same-source pointer intervention and the C control remain stable.

## Conclusion

**The Sep-21 arm64 timing anomaly is independently reproducible under an exact rerun of the same job.** That substantially strengthens the claim that the distribution itself is real for this pinned compiler/source/runner combination. It does **not** yet identify whether the second regime is caused by compiler-generated behavior interacting with the host, runtime behavior, CPU frequency/scheduling, memory-system effects, or another runner-level mechanism.

The repeat also sharpens the methodology lesson: **a median is not automatically robust when mode occupancy can flip.** In the first run, the median represented the fast regime; in the rerun, the same estimator represents the slow regime even though both regimes remain present and the fast-mode center is almost unchanged. For multimodal benchmark data, report the raw distribution or mode-separated summaries, preserve stable controls, and treat a single mean or median as insufficient evidence of one performance population.

A useful next experiment would collect lower-level host evidence (CPU frequency/scheduling/perf counters if available) or run the exact binary on controlled arm64 hardware to attribute the second regime. That is a **separate future task**; it is not bundled into this run.

The unsafe-pointer path remains a diagnostic control rather than a recommendation for canonical benchmark code. This rerun does not update `ANALYSIS.md`, `results/results.json`, charts, or canonical benchmark implementations.

## Evidence / provenance

- workflow run: https://github.com/iinoshirozheng/mojo-analyze/actions/runs/35588217725
- rerun arm64 job: `106703859330`
- rerun artifact: `10688953035` (`csvagg-scan-access-nightly-arm64`)
- rerun artifact SHA-256: `26a2bb372a5af4b077a5ea86b4c7f8a3d200eea6f710acdd06244290eb6c5fde`
- source checkout: `14462e8d3fab426d44917df6455fa90a3ae552c8`
- original result note: `experiments/2026-09-21-csvagg-span-mojo12-nightly.md`
- probe source: `experiments/csvagg_scan_access/csvagg_scan_access.mojo`
- harness: `experiments/csvagg_scan_access/run_nightly_bench.py`
- workflow: `.github/workflows/research-csvagg-scan-access-nightly.yml`
