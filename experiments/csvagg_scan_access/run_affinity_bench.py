#!/usr/bin/env python3
import argparse
import json
import os
import statistics
import subprocess
from pathlib import Path


def run(cmd, cpu=None):
    full = list(cmd)
    if cpu is not None:
        full = ["taskset", "-c", str(cpu)] + full
    p = subprocess.run(full, check=True, text=True, capture_output=True)
    elapsed = None
    checksum = None
    for line in p.stdout.splitlines():
        if line.startswith("TIME_SECONDS:"):
            elapsed = float(line.split(":", 1)[1].strip())
        elif line.startswith("CHECKSUM:"):
            checksum = line.split(":", 1)[1].strip()
    if elapsed is None or checksum is None:
        raise RuntimeError(
            f"missing timing/checksum from {full}:\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}"
        )
    return elapsed, checksum


def stats(values):
    return {
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
        "min": min(values),
        "max": max(values),
        "trials": values,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arch", required=True)
    ap.add_argument("--mojo12", type=Path, required=True)
    ap.add_argument("--cbin", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--warmup", type=int, default=2)
    ap.add_argument("--trials", type=int, default=20)
    ns = ap.parse_args()

    allowed = sorted(os.sched_getaffinity(0))
    if not allowed:
        raise RuntimeError("empty process CPU affinity set")
    pin_cpu = allowed[0]

    csv = Path("benchmarks/csvagg/data/orders.csv")
    base = {
        "mojo12-span": [str(ns.mojo12), "--csv", str(csv), "--access", "span"],
        "mojo12-ptr": [str(ns.mojo12), "--csv", str(csv), "--access", "ptr"],
        "c-scan": [str(ns.cbin), "--csv", str(csv), "--scope", "scan"],
    }
    variants = {}
    for name, cmd in base.items():
        variants[f"{name}-unpinned"] = (cmd, None)
        variants[f"{name}-pinned"] = (cmd, pin_cpu)

    checksums = {}
    for name, (cmd, cpu) in variants.items():
        _, ck = run(cmd, cpu)
        checksums[name] = ck
    if len(set(checksums.values())) != 1:
        raise RuntimeError(f"checksum mismatch: {checksums}")

    names = list(variants)
    for warmup in range(ns.warmup):
        order = names[warmup % len(names):] + names[:warmup % len(names)]
        for name in order:
            cmd, cpu = variants[name]
            _, ck = run(cmd, cpu)
            if ck != checksums[name]:
                raise RuntimeError(f"checksum drift in warmup for {name}: {ck}")

    values = {name: [] for name in variants}
    for trial in range(ns.trials):
        order = names[trial % len(names):] + names[:trial % len(names)]
        for name in order:
            cmd, cpu = variants[name]
            elapsed, ck = run(cmd, cpu)
            if ck != checksums[name]:
                raise RuntimeError(f"checksum drift for {name}: {ck}")
            values[name].append(elapsed)

    result = {
        "arch": ns.arch,
        "allowed_cpus": allowed,
        "pinned_cpu": pin_cpu,
        "warmup": ns.warmup,
        "trials": ns.trials,
        "checksum": next(iter(checksums.values())),
        "variants": {name: stats(xs) for name, xs in values.items()},
    }
    s = result["variants"]
    result["ratios"] = {
        "span_pinned_over_unpinned_mean":
            s["mojo12-span-pinned"]["mean"] / s["mojo12-span-unpinned"]["mean"],
        "span_pinned_over_unpinned_median":
            s["mojo12-span-pinned"]["median"] / s["mojo12-span-unpinned"]["median"],
        "ptr_pinned_over_unpinned_mean":
            s["mojo12-ptr-pinned"]["mean"] / s["mojo12-ptr-unpinned"]["mean"],
        "c_pinned_over_unpinned_mean":
            s["c-scan-pinned"]["mean"] / s["c-scan-unpinned"]["mean"],
    }

    ns.out_dir.mkdir(parents=True, exist_ok=True)
    out = ns.out_dir / f"csvagg-scan-affinity-{ns.arch}.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
