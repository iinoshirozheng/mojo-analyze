#!/usr/bin/env python3
import argparse
import json
import statistics
import subprocess
from pathlib import Path


def run(cmd):
    p = subprocess.run(cmd, check=True, text=True, capture_output=True)
    elapsed = None
    checksum = None
    for line in p.stdout.splitlines():
        if line.startswith("TIME_SECONDS:"):
            elapsed = float(line.split(":", 1)[1].strip())
        elif line.startswith("CHECKSUM:"):
            checksum = line.split(":", 1)[1].strip()
    if elapsed is None or checksum is None:
        raise RuntimeError(
            f"missing timing/checksum from {cmd}:\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}"
        )
    return elapsed, checksum


def stats(values):
    return {
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
        "trials": values,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arch", required=True)
    ap.add_argument("--mojo11", type=Path, required=True)
    ap.add_argument("--mojo12", type=Path, required=True)
    ap.add_argument("--cbin", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--warmup", type=int, default=2)
    ap.add_argument("--trials", type=int, default=7)
    ns = ap.parse_args()

    csv = Path("benchmarks/csvagg/data/orders.csv")
    variants = {
        "mojo11-span": [str(ns.mojo11), "--csv", str(csv), "--access", "span"],
        "mojo11-ptr": [str(ns.mojo11), "--csv", str(csv), "--access", "ptr"],
        "mojo12-span": [str(ns.mojo12), "--csv", str(csv), "--access", "span"],
        "mojo12-ptr": [str(ns.mojo12), "--csv", str(csv), "--access", "ptr"],
        "c-scan": [str(ns.cbin), "--csv", str(csv), "--scope", "scan"],
    }

    checksums = {}
    for name, cmd in variants.items():
        _, ck = run(cmd)
        checksums[name] = ck
    if len(set(checksums.values())) != 1:
        raise RuntimeError(f"checksum mismatch: {checksums}")

    names = list(variants)
    for warmup in range(ns.warmup):
        order = names[warmup % len(names):] + names[:warmup % len(names)]
        for name in order:
            _, ck = run(variants[name])
            if ck != checksums[name]:
                raise RuntimeError(f"checksum drift in warmup for {name}: {ck}")

    values = {name: [] for name in variants}
    for trial in range(ns.trials):
        order = names[trial % len(names):] + names[:trial % len(names)]
        for name in order:
            elapsed, ck = run(variants[name])
            if ck != checksums[name]:
                raise RuntimeError(f"checksum drift for {name}: {ck}")
            values[name].append(elapsed)

    result = {
        "arch": ns.arch,
        "warmup": ns.warmup,
        "trials": ns.trials,
        "checksum": next(iter(checksums.values())),
        "variants": {name: stats(xs) for name, xs in values.items()},
    }
    s = result["variants"]
    result["ratios"] = {
        "mojo11_span_over_ptr_mean": s["mojo11-span"]["mean"] / s["mojo11-ptr"]["mean"],
        "mojo12_span_over_ptr_mean": s["mojo12-span"]["mean"] / s["mojo12-ptr"]["mean"],
        "mojo11_span_over_c_mean": s["mojo11-span"]["mean"] / s["c-scan"]["mean"],
        "mojo11_ptr_over_c_mean": s["mojo11-ptr"]["mean"] / s["c-scan"]["mean"],
        "mojo12_span_over_c_mean": s["mojo12-span"]["mean"] / s["c-scan"]["mean"],
        "mojo12_ptr_over_c_mean": s["mojo12-ptr"]["mean"] / s["c-scan"]["mean"],
        "mojo12_span_over_mojo11_span_mean": s["mojo12-span"]["mean"] / s["mojo11-span"]["mean"],
        "mojo12_ptr_over_mojo11_ptr_mean": s["mojo12-ptr"]["mean"] / s["mojo11-ptr"]["mean"],
        "mojo12_span_over_mojo11_span_median": s["mojo12-span"]["median"] / s["mojo11-span"]["median"],
        "mojo12_ptr_over_mojo11_ptr_median": s["mojo12-ptr"]["median"] / s["mojo11-ptr"]["median"],
    }

    ns.out_dir.mkdir(parents=True, exist_ok=True)
    out = ns.out_dir / f"csvagg-scan-access-nightly-{ns.arch}.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
