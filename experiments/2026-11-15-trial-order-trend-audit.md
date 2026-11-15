# 2026-11-15 — Exact trial-order trend audit of the canonical benchmark snapshot

## One question
Do the seven stored trials per implementation show a systematic time-order drift that would undermine naive independent-resampling interpretation? This is a **methodology diagnostic on stored data**, not a fresh Mojo benchmark or a compiler/codegen experiment. The higher-priority arm64 checked-Span region-scoped CPU-clock study still requires an arm64 Mojo runner.

## Inputs and correctness scope
Source: [results/results.json at blob c8b9084e1839bef977b52d8b517ff905de447cba](https://github.com/iinoshirozheng/mojo-analyze/blob/main/results/results.json), five workload categories × five variants × seven trials = **25 series / 175 samples**. Each category records `_checksum_ok=true`, with identical recorded variant checksums; this verifies **stored provenance only**, not an independently rerun algorithm oracle. No result files were modified.

## Method
For each seven-trial vector, compute Kendall's unnormalized score `S = sum_{i<j} sign(t[j]-t[i])`, in chronological trial order. Enumerate all `7! = 5040` permutations of its observed values and compute the **two-sided exact permutation p-value** `count(|S_perm|>=|S_obs|)/5040`. This avoids asymptotic small-sample p-values. Audit all 25 series rather than selecting only an eye-catching trend; apply Bonferroni familywise correction (25 comparisons). The null assumes exchangeability of order under no temporal trend; real benchmark runs may violate this through load, thermals, or scheduling.

Independent reproducer (Python standard library; read the repository's JSON snapshot):
```python
import itertools, json, pathlib
d=json.loads(pathlib.Path("results/results.json").read_text())
def score(a):
    return sum((a[j]>a[i])-(a[j]<a[i]) for i in range(len(a)) for j in range(i+1,len(a)))
rows=[]
for category, bench in d.items():
    vals=[v for k,v in bench["variants"].items() if not k.startswith("_")]
    assert bench["variants"]["_checksum_ok"] and len({v["checksum"] for v in vals})==1
    for label,v in bench["variants"].items():
        if label.startswith("_"): continue
        x=v["times"]; assert len(x)==7
        obs=abs(score(x))
        hits=sum(abs(score(p))>=obs for p in itertools.permutations(x))
        rows.append((hits/5040,category,label,score(x)))
for p,cat,label,s in sorted(rows)[:5]: print(cat,label,s,p,min(1,p*len(rows)))
```

## Verified results
- **25 series evaluated**, all seven stored trials, checksum records agree within every category.
- Strongest unadjusted trend: Mandelbrot naive Python `S=+17`, exact `p=54/5040=0.0107143`; mean of first three trials **2.4373753 s**, last three **2.4699627 s** (later trials slower).
- Second: JSON manual Python `S=-15`, exact `p=152/5040=0.0301587`; first three mean **20.7272520 s**, last three **19.3525299 s** (later trials faster).
- **No series survives 25-way Bonferroni correction**; smallest adjusted p is **0.267857**. The trial order of variants relative to one another was not recovered from this snapshot, so this cannot identify thermal or scheduler causes.

## Conclusion
**Negative finding:** there is no familywise-significant monotone trial-order drift in this seven-trial canonical snapshot under the exact permutation model. The two unadjusted trends are exploratory signals, not proof of warmup/thermal effects. A null finding with seven trials does not establish exchangeability or independence. In particular, yesterday's Sieve unpaired bootstrap remains conditional on the existing samples. A stronger study should record monotonic clock, variant execution order, per-trial host metadata and randomized/interleaved runs across independent sessions; use blocked/paired analysis where the design warrants it. Do not alter canonical performance conclusions, `ANALYSIS.md`, results or charts.
