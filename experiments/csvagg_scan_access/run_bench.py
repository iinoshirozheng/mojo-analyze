#!/usr/bin/env python3
import argparse
import json
import statistics
import subprocess
from pathlib import Path


def run(cmd):
    p = subprocess.run(cmd, check=True, text=True, capture_output=True)
    t = None
    checksum = None
    for line in p.stdout.splitlines():
        if line.startswith("TIME_SECONDS:"):
            t = float(line.split(":", 1)[1].strip())
        elif line.startswith("CHECKSUM:"):
            checksum = line.split(":", 1)[1].strip()
    if t is None or checksum is None:
        raise RuntimeError(f"missing timing/checksum from {cmd}:\n{p.stdout}\n{p.stderr}")
    return t, checksum


def stats(xs):
    return {
        "mean": statistics.mean(xs),
        "median": statistics.median(xs),
        "stdev": statistics.stdev(xs) if len(xs) > 1 else 0.0,
        "trials": xs,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arch", required=True)
    ap.add_argument("--bin-dir", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--warmup", type=int, default=2)
    ap.add_argument("--trials", type=int, default=7)
    ns = ap.parse_args()

    csv = Path("benchmarks/csvagg/data/orders.csv")
    mojo = ns.bin_dir / "scan-access-mojo"
    cbin = ns.bin_dir / "scan-scope-c"
    variants = {
        "mojo-span": [str(mojo), "--csv", str(csv), "--access", "span"],
        "mojo-ptr": [str(mojo), "--csv", str(csv), "--access", "ptr"],
        "c-scan": [str(cbin), "--csv", str(csv), "--scope", "scan"],
    }

    checksums = {}
    for name, cmd in variants.items():
        _, ck = run(cmd)
        checksums[name] = ck
    if len(set(checksums.values())) != 1:
        raise RuntimeError(f"checksum mismatch: {checksums}")

    for _ in range(ns.warmup):
        for name in variants:
            run(variants[name])

    values = {name: [] for name in variants}
    names = list(variants)
    for trial in range(ns.trials):
        order = names[trial % len(names):] + names[:trial % len(names)]
        for name in order:
            t, ck = run(variants[name])
            if ck != checksums[name]:
                raise RuntimeError(f"checksum drift for {name}: {ck}")
            values[name].append(t)

    result = {
        "arch": ns.arch,
        "warmup": ns.warmup,
        "trials": ns.trials,
        "checksum": next(iter(checksums.values())),
        "variants": {name: stats(xs) for name, xs in values.items()},
    }
    s = result["variants"]
    result["ratios"] = {
        "span_over_ptr_mean": s["mojo-span"]["mean"] / s["mojo-ptr"]["mean"],
        "span_over_ptr_median": s["mojo-span"]["median"] / s["mojo-ptr"]["median"],
        "span_over_c_mean": s["mojo-span"]["mean"] / s["c-scan"]["mean"],
        "ptr_over_c_mean": s["mojo-ptr"]["mean"] / s["c-scan"]["mean"],
        "span_over_c_median": s["mojo-span"]["median"] / s["c-scan"]["median"],
        "ptr_over_c_median": s["mojo-ptr"]["median"] / s["c-scan"]["median"],
    }

    ns.out_dir.mkdir(parents=True, exist_ok=True)
    out = ns.out_dir / f"csvagg-scan-access-{ns.arch}.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
