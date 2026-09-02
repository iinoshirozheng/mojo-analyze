"""Renders the benchmark charts embedded in ANALYSIS.md / README.md from
results/results.json. Palette and mark specs follow the dataviz skill: fixed
categorical hues assigned by *role* (never by rank) — orange=Mojo,
blue=optimized library, aqua/green=naive Python, violet=Rust — hairline
recessive grid, no borders on marks, direct value labels as the
contrast-relief channel for the aqua slot (which sits under 3:1 against the
light surface).

Usage:
    pixi run charts
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parent.parent
RESULTS = json.loads((ROOT / "results/results.json").read_text())
OUT = ROOT / "results"

# Categorical palette (dataviz skill default hues). 4-color set (orange/
# blue/aqua/violet) validated ALL-PAIRS earlier; adding a 5th slot for C
# (magenta) failed all-pairs (contrast/CVD budget exhausted past 4 series --
# expected per the skill's own docs, which cap all-pairs forms at 3-4), so
# the 5-bar panels are validated ADJACENT-PAIRS instead (the correct test
# for grouped bar charts, where only neighbors are ever directly compared --
# `node validate_palette.js "#eb6834,#4a3aa7,#e87ba4,#2a78d6,#1baf7a"
# --mode light`, bar order Mojo/Rust/C/OptLib/NaivePy exactly as drawn):
# ALL CHECKS PASS, worst adjacent CVD 13.0, worst normal-vision 24.0. Do not
# reorder the bars within a panel without re-validating this exact sequence.
# Two rejected candidates for the 4th (Rust) slot, tried and failed before
# landing on violet: pure green #008300 alongside orange (CVD 3.2 protan,
# classic green/orange confusion), and red #e34948 (CVD 5.6, normal-vision
# 7.1, both warm hues too close to orange).
MOJO = "#eb6834"      # orange — role: Mojo (compiled, throughout)
RUST = "#4a3aa7"      # violet — role: Rust reference (release build, std only)
C_LANG = "#e87ba4"    # magenta — role: C reference (-O3, std only)
OPT_LIB = "#2a78d6"   # blue — role: optimized C-backed library alt (NumPy / Counter / pandas / json)
NAIVE_PY = "#1baf7a"  # aqua/green — role: naive/pure Python

TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
TEXT_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
BASELINE = "#c3c2b7"
SURFACE = "#fcfcfb"

plt.rcParams.update({
    "font.family": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "text.color": TEXT_PRIMARY,
    "axes.edgecolor": BASELINE,
    "axes.labelcolor": TEXT_SECONDARY,
    "xtick.color": TEXT_SECONDARY,
    "ytick.color": TEXT_MUTED,
})

PANELS = [
    {
        "key": "mandelbrot",
        "title": "A — Mandelbrot",
        "subtitle": "800×600px, 500 max iter",
        "bars": [
            ("Mojo", "mojo", MOJO),
            ("Rust", "rust", RUST),
            ("C", "c", C_LANG),
            ("NumPy", "numpy", OPT_LIB),
            ("Python", "python", NAIVE_PY),
        ],
        "ylabel": "seconds (mean of 7 trials)",
    },
    {
        "key": "sieve",
        "title": "B — Sieve of Eratosthenes",
        "subtitle": "primes up to 50,000,000",
        "bars": [
            ("Mojo", "mojo", MOJO),
            ("Rust", "rust", RUST),
            ("C", "c", C_LANG),
            ("NumPy", "numpy", OPT_LIB),
            ("Python", "python", NAIVE_PY),
        ],
        "ylabel": "seconds (mean of 7 trials)",
    },
    {
        "key": "wordfreq",
        "title": "C — Word frequency",
        "subtitle": "15M tokens, 62.4 MiB corpus",
        "bars": [
            ("Mojo", "mojo", MOJO),
            ("Rust", "rust", RUST),
            ("C", "c", C_LANG),
            ("Counter", "python (Counter)", OPT_LIB),
            ("dict", "python (dict)", NAIVE_PY),
        ],
        "ylabel": "seconds, incl. file read (mean of 7 trials)",
    },
    {
        "key": "csvagg",
        "title": "D — CSV aggregation",
        "subtitle": "10M rows, group-by + sum",
        "bars": [
            ("Mojo", "mojo", MOJO),
            ("Rust", "rust", RUST),
            ("C", "c", C_LANG),
            ("pandas", "python (pandas)", OPT_LIB),
            ("manual", "python (manual)", NAIVE_PY),
        ],
        "ylabel": "seconds, incl. file read (mean of 7 trials)",
    },
    {
        "key": "jsonparse",
        "title": "E — JSON parsing",
        "subtitle": "3M nested events, 327 MiB",
        "bars": [
            ("Mojo", "mojo", MOJO),
            ("Rust", "rust", RUST),
            ("C", "c", C_LANG),
            ("json", "python (json)", OPT_LIB),
            ("manual", "python (manual)", NAIVE_PY),
        ],
        "ylabel": "seconds, incl. file read (mean of 7 trials)",
    },
]

LEGEND_HANDLES = [
    plt.Rectangle((0, 0), 1, 1, color=MOJO, label="Mojo"),
    plt.Rectangle((0, 0), 1, 1, color=RUST, label="Rust (release build, std only)"),
    plt.Rectangle((0, 0), 1, 1, color=C_LANG, label="C (-O3, std only)"),
    plt.Rectangle((0, 0), 1, 1, color=OPT_LIB, label="Optimized library (NumPy/Counter/pandas/json)"),
    plt.Rectangle((0, 0), 1, 1, color=NAIVE_PY, label="Naive Python"),
]


def rounded_bar(ax, x, height, width, color, radius_frac=0.12):
    if height <= 0:
        return
    radius = width * radius_frac
    patch = FancyBboxPatch(
        (x - width / 2, 0),
        width,
        height,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        linewidth=0,
        facecolor=color,
        mutation_aspect=1,
        zorder=3,
    )
    ax.add_patch(patch)


def style_axes(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color(BASELINE)
    ax.spines["bottom"].set_linewidth(1)
    ax.yaxis.grid(True, color=GRIDLINE, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(axis="both", length=0)


def fmt_seconds(v):
    return f"{v:.3f}s" if v < 1 else f"{v:.2f}s"


def make_absolute_chart():
    fig, axes = plt.subplots(2, 3, figsize=(17.5, 11))
    fig.subplots_adjust(top=0.83, bottom=0.06, left=0.05, right=0.98,
                         hspace=0.42, wspace=0.30)
    for extra_ax in axes.flat[len(PANELS):]:
        extra_ax.axis("off")

    for ax, panel in zip(axes.flat, PANELS):
        data = RESULTS[panel["key"]]["variants"]
        xs = list(range(len(panel["bars"])))
        width = 0.55
        top = 0
        for x, (label, key, color) in zip(xs, panel["bars"]):
            v = data[key]
            rounded_bar(ax, x, v["mean"], width, color)
            ax.errorbar(
                x, v["mean"], yerr=v["stdev"],
                ecolor=TEXT_MUTED, elinewidth=1, capsize=3, capthick=1,
                zorder=4, fmt="none",
            )
            top = max(top, v["mean"] + v["stdev"])
        for x, (label, key, color) in zip(xs, panel["bars"]):
            v = data[key]
            ax.text(
                x, v["mean"] + v["stdev"] + top * 0.05, fmt_seconds(v["mean"]),
                ha="center", va="bottom", fontsize=9.5, color=TEXT_PRIMARY,
            )
        ax.set_xticks(xs)
        ax.set_xticklabels([b[0] for b in panel["bars"]], fontsize=10)
        ax.set_ylim(0, top * 1.28)
        ax.set_xlim(-0.65, len(xs) - 0.35)
        ax.set_title(f"{panel['title']}\n{panel['subtitle']}", fontsize=12,
                      fontweight="bold", color=TEXT_PRIMARY, loc="left")
        ax.set_ylabel(panel["ylabel"], fontsize=9, color=TEXT_SECONDARY)
        style_axes(ax)

    fig.suptitle(
        "Mojo vs. Rust vs. C vs. Python vs. NumPy/pandas/json — mean wall-clock time, lower is better",
        fontsize=15.5, fontweight="bold", color=TEXT_PRIMARY, x=0.012, y=0.985, ha="left",
    )
    fig.legend(
        handles=LEGEND_HANDLES, loc="upper center", bbox_to_anchor=(0.5, 0.945),
        ncol=3, frameon=False, fontsize=9.5,
    )
    fig.savefig(OUT / "chart_absolute.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def make_speedup_chart():
    fig, ax = plt.subplots(figsize=(16, 6.4))
    fig.subplots_adjust(top=0.80, bottom=0.13, left=0.07, right=0.98)
    group_gap = 1.35
    bar_width = 0.19
    centers = []
    labels = []

    for gi, panel in enumerate(PANELS):
        data = RESULTS[panel["key"]]["variants"]
        means = {key: data[key]["mean"] for _, key, _ in panel["bars"]}
        fastest = min(means.values())
        n_bars = len(panel["bars"])
        base_x = gi * group_gap
        for bi, (label, key, color) in enumerate(panel["bars"]):
            ratio = means[key] / fastest
            x = base_x + (bi - (n_bars - 1) / 2) * (bar_width + 0.03)
            rounded_bar(ax, x, ratio, bar_width, color)
            tag = "1.0x\n(fastest)" if abs(ratio - 1.0) < 1e-9 else f"{ratio:.1f}x"
            ax.text(x, ratio * 1.1, tag, ha="center", va="bottom",
                     fontsize=8, color=TEXT_PRIMARY, linespacing=1.3)
        centers.append(base_x)
        labels.append(f"{panel['title']}\n{panel['subtitle']}")

    ax.set_yscale("log")
    ax.set_ylim(0.8, 90)
    ax.set_yticks([1, 2, 5, 10, 20, 50])
    ax.set_yticklabels(["1x", "2x", "5x", "10x", "20x", "50x"])
    ax.set_xticks(centers)
    ax.set_xticklabels(labels, fontsize=9.5)
    ax.set_xlim(-0.65, centers[-1] + 0.65)
    ax.axhline(1.0, color=BASELINE, linewidth=1, zorder=1)
    ax.set_ylabel("× slower than the fastest variant in its category (log scale)",
                   fontsize=9.5, color=TEXT_SECONDARY)
    style_axes(ax)
    ax.yaxis.grid(True, which="both", color=GRIDLINE, linewidth=0.7, zorder=0)

    fig.suptitle(
        "Same five categories, indexed to a common base — who wins each one",
        fontsize=14.5, fontweight="bold", color=TEXT_PRIMARY, x=0.015, y=0.97, ha="left",
    )
    fig.legend(
        handles=LEGEND_HANDLES, loc="upper center", bbox_to_anchor=(0.5, 0.885),
        ncol=3, frameon=False, fontsize=9,
    )
    fig.savefig(OUT / "chart_speedup.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def make_gpu_chart():
    gpu = RESULTS.get("mandelbrot_gpu")
    if gpu is None:
        return

    GPU_PANELS = [
        ("mandelbrot_gpu", "A — Mandelbrot", "Float32 GPU vs Float64 CPU (disclosed precision gap)"),
        ("sieve_gpu", "B — Sieve of Eratosthenes", "checksum-gated, exact match required"),
        ("wordfreq_gpu", "C — Word frequency", "checksum-gated, exact match required"),
        ("csvagg_gpu", "D — CSV aggregation", "checksum-gated, exact match required"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.subplots_adjust(top=0.85, bottom=0.06, left=0.07, right=0.97,
                         hspace=0.38, wspace=0.25)

    for ax, (key, title, subtitle) in zip(axes.flat, GPU_PANELS):
        comp = RESULTS.get(key)
        if comp is None:
            ax.axis("off")
            continue
        sizes = comp["sizes"]
        xs = list(range(len(sizes)))
        bar_width = 0.32
        top = 0
        for x, size in zip(xs, sizes):
            cpu_v = size["cpu"]["mean"]
            gpu_v = size["gpu"]["mean"]
            rounded_bar(ax, x - bar_width / 2 - 0.02, cpu_v, bar_width, MOJO)
            rounded_bar(ax, x + bar_width / 2 + 0.02, gpu_v, bar_width, OPT_LIB)
            top = max(top, cpu_v, gpu_v)
            ax.text(x - bar_width / 2 - 0.02, cpu_v + top * 0.04, fmt_seconds(cpu_v),
                     ha="center", va="bottom", fontsize=9, color=TEXT_PRIMARY)
            if gpu_v < cpu_v:
                tag = f"{fmt_seconds(gpu_v)}\n({cpu_v / gpu_v:.1f}x faster)"
            else:
                tag = f"{fmt_seconds(gpu_v)}\n({gpu_v / cpu_v:.1f}x slower)"
            ax.text(x + bar_width / 2 + 0.02, gpu_v + top * 0.04, tag,
                     ha="center", va="bottom", fontsize=9, color=TEXT_PRIMARY, linespacing=1.3)
        ax.set_xticks(xs)
        ax.set_xticklabels([s["label"] for s in sizes], fontsize=9.5)
        ax.set_ylim(0, top * 1.38)
        ax.set_xlim(-0.6, len(xs) - 0.4)
        ax.set_title(f"{title}\n{subtitle}", fontsize=10.5, fontweight="bold",
                      color=TEXT_PRIMARY, loc="left")
        ax.set_ylabel("seconds, mean of 7 trials", fontsize=8.5, color=TEXT_SECONDARY)
        style_axes(ax)

    handles = [
        plt.Rectangle((0, 0), 1, 1, color=MOJO, label="Mojo — CPU/SIMD"),
        plt.Rectangle((0, 0), 1, 1, color=OPT_LIB, label="Mojo — GPU/MAX, Apple Metal"),
    ]
    fig.suptitle(
        "CPU/SIMD vs. GPU, same Mojo toolchain — four categories, one clear win",
        fontsize=15, fontweight="bold", color=TEXT_PRIMARY, x=0.012, y=0.97, ha="left",
    )
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.925),
               ncol=2, frameon=False, fontsize=9.5)
    fig.savefig(OUT / "chart_gpu.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    make_absolute_chart()
    make_speedup_chart()
    make_gpu_chart()
    print(f"Wrote {OUT / 'chart_absolute.png'}")
    print(f"Wrote {OUT / 'chart_speedup.png'}")
    if (OUT / "chart_gpu.png").exists():
        print(f"Wrote {OUT / 'chart_gpu.png'}")
