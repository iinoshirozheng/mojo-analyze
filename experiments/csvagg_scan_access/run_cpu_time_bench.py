#!/usr/bin/env python3
import argparse
import json
import os
import resource
import statistics
import subprocess
from pathlib import Path


def child_cpu_seconds():
    r = resource.getrusage(resource.RUSAGE_CHILDREN)
    return r.ru_utime + r.ru_stime


def run(cmd, cpu):
    full = ["taskset", "-c", str(cpu)] + list(cmd)
    before = child_cpu_seconds()
    p = subprocess.run(full, check=True, text=True, capture_output=True)
    after = child_cpu_seconds()
    reported_wall = None
    checksum = None
    for line in p.stdout.splitlines():
        if line.startswith("TIME_SECONDS:"):
            reported_wall = float(line.split(":", 1)[1].strip())
        elif line.startswith("CHECKSUM:"):
            checksum = line.split(":", 1)[1].strip()
    if reported_wall is None or checksum is None:
        raise RuntimeError(
            f"missing timing/checksum from {full}:\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}"
        )
    return {
        "wall": reported_wall,
        "child_cpu": after - before,
        "checksum": checksum,
    }


def stats(values):
    return {
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
        "min": min(values),
        "max": max(values),
        "trials": values,
    }


def mode_stats(samples, threshold=0.45):
    fast = [x for x in samples if x["wall"] < threshold]
    slow = [x for x in samples if x["wall"] >= threshold]

    def summarize(xs):
        if not xs:
            return {"count": 0}
        walls = [x["wall"] for x in xs]
        cpus = [x["child_cpu"] for x in xs]
        return {
            "count": len(xs),
            "wall_mean": statistics.mean(walls),
            "wall_median": statistics.median(walls),
            "cpu_mean": statistics.mean(cpus),
            "cpu_median": statistics.median(cpus),
            "cpu_over_wall_mean": statistics.mean(
                x["child_cpu"] / x["wall"] for x in xs
            ),
        }

    return {"threshold": threshold, "fast": summarize(fast), "slow": summarize(slow)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arch", required=True)
    ap.add_argument("--mojo12", type=Path, required=True)
    ap.add_argument("--cbin", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--warmup", type=int, default=2)
    ap.add_argument("--trials", type=int, default=30)
    ns = ap.parse_args()

    allowed = sorted(os.sched_getaffinity(0))
    if not allowed:
        raise RuntimeError("empty process CPU affinity set")
    cpu = allowed[0]
    csv = Path("benchmarks/csvagg/data/orders.csv")
    variants = {
        "mojo12-span": [str(ns.mojo12), "--csv", str(csv), "--access", "span"],
        "mojo12-ptr": [str(ns.mojo12), "--csv", str(csv), "--access", "ptr"],
        "c-scan": [str(ns.cbin), "--csv", str(csv), "--scope", "scan"],
    }

    checksums = {}
    for name, cmd in variants.items():
        sample = run(cmd, cpu)
        checksums[name] = sample["checksum"]
    if len(set(checksums.values())) != 1:
        raise RuntimeError(f"checksum mismatch: {checksums}")

    names = list(variants)
    for warmup in range(ns.warmup):
        order = names[warmup % len(names):] + names[: warmup % len(names)]
        for name in order:
            sample = run(variants[name], cpu)
            if sample["checksum"] != checksums[name]:
                raise RuntimeError(f"checksum drift in warmup for {name}")

    samples = {name: [] for name in variants}
    for trial in range(ns.trials):
        order = names[trial % len(names):] + names[: trial % len(names)]
        for name in order:
            sample = run(variants[name], cpu)
            if sample["checksum"] != checksums[name]:
                raise RuntimeError(f"checksum drift for {name}")
            samples[name].append(sample)

    result = {
        "arch": ns.arch,
        "allowed_cpus": allowed,
        "pinned_cpu": cpu,
        "warmup": ns.warmup,
        "trials": ns.trials,
        "checksum": next(iter(checksums.values())),
        "variants": {},
    }
    for name, xs in samples.items():
        result["variants"][name] = {
            "wall": stats([x["wall"] for x in xs]),
            "child_cpu": stats([x["child_cpu"] for x in xs]),
            "cpu_over_wall": stats([x["child_cpu"] / x["wall"] for x in xs]),
            "samples": xs,
        }
    result["span_modes"] = mode_stats(samples["mojo12-span"])

    ns.out_dir.mkdir(parents=True, exist_ok=True)
    out = ns.out_dir / f"csvagg-scan-cputime-{ns.arch}.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
