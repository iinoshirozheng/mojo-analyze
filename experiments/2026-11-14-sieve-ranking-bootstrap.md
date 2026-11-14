# 2026-11-14 — Stored Sieve C/Mojo ranking sensitivity under trial resampling

## One focused question
Does the small C-over-Mojo Sieve margin in the canonical Apple M4 Pro snapshot survive resampling the **existing seven recorded trials per implementation**, or is the mean ranking driven by one observation?

## Input and correctness gate
Read `results/results.json` at blob `c8b9084e1839bef977b52d8b517ff905de447cba`, category `sieve` (`limit=50,000,000`). Both C and Mojo carry checksum `3001134:548121944`, and the category records `_checksum_ok=true`. This validates the **recorded** agreement, not an independent algorithm oracle.

C seconds: `[0.111111,0.121305,0.122048,0.120735,0.119041,0.113706,0.115785]`.
Mojo seconds: `[0.121729,0.120651,0.131161,0.122551,0.121886,0.126882,0.126575]`.

## Independent numerical verification
Used NumPy `default_rng(20261114)`, 100,000 independently resampled 7-trial means **within each implementation** (ordinary nonparametric, unpaired bootstrap), and computed `mean(Mojo)-mean(C)` for each pair. Minimal reproducer:

```python
import numpy as np
c=np.array([.111111,.121305,.122048,.120735,.119041,.113706,.115785])
m=np.array([.121729,.120651,.131161,.122551,.121886,.126882,.126575])
rng=np.random.default_rng(20261114); n=100000
ca=c[rng.integers(0,7,(n,7))].mean(axis=1)
ma=m[rng.integers(0,7,(n,7))].mean(axis=1)
d=ma-ca
print(m.mean()-c.mean(), np.mean(d>0), np.quantile(d,[.025,.5,.975]))
```

Local Python execution produced mean difference **0.0068148571 s**, bootstrap positive fraction **0.99999**, percentile interval **[0.00310199, 0.01081959] s**; C is about **5.79% faster** relative to C's mean. This supports the *within-snapshot* direction under the assumed resampling model. It does **not** measure fresh runs, compiler output, CPU time, cross-machine repeatability, autocorrelation or scheduling effects; seven possibly time-correlated samples are not independent machines. The bootstrap interval is conditional on these observations, not a guarantee that the same ranking holds on shared runners. No new performance claim or canonical ranking change is warranted.

## Result and follow-up
**Negative finding:** the canonical Sieve mean ranking is not explained solely by a single high/low recorded trial under ordinary within-variant bootstrap. Keep existing conclusions unchanged. A stronger experiment would randomize variant order across repeated independent runs, preserve checksums, record per-run host/load metadata, and then estimate a paired/blocked difference. Higher-priority unresolved arm64 checked-Span region-scoped CPU-clock diagnosis remains outstanding. No benchmark source, results, charts or `ANALYSIS.md` changed.
