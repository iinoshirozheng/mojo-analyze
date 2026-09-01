"""Renders the benchmark charts embedded in ANALYSIS.md / README.md from
results/results.json. Palette and mark specs follow the dataviz skill: fixed
categorical hues assigned by *role* (never by rank) — orange=Mojo,
blue=optimized library, aqua/green=naive Python — hairline recessive grid,
no borders on marks, direct value labels as the contrast-relief channel for
the aqua slot (which sits under 3:1 against the light surface).

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

# Categorical palette (dataviz skill default, slots 1-3 — validated all-pairs,
# both CVD and normal-vision floors, for exactly 3 series). Roles are assigned
# to hold within this pre-validated triple — swapping in a "purer" green
# (slot 6, #008300) alongside orange was tried and FAILS CVD separation hard
# (protan ΔE 3.2, well under the floor of 6) — green/orange is a classic
# confusion pair, so aqua stays the naive-Python green.
MOJO = "#eb6834"      # orange — role: Mojo (compiled, throughout)
OPT_LIB = "#2a78d6"   # blue — role: optimized C-backed library alt (NumPy / Counter)
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
            ("Counter", "python (Counter)", OPT_LIB),
            ("dict", "python (dict)", NAIVE_PY),
        ],
        "ylabel": "seconds, incl. file read (mean of 7 trials)",
    },
]

LEGEND_HANDLES = [
    plt.Rectangle((0, 0), 1, 1, color=MOJO, label="Mojo"),
    plt.Rectangle((0, 0), 1, 1, color=OPT_LIB, label="Optimized C-backed library (NumPy / Counter)"),
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
    fig, axes = plt.subplots(1, 3, figsize=(13, 5.2))
    fig.subplots_adjust(top=0.74, bottom=0.10, left=0.05, right=0.98, wspace=0.32)

    for ax, panel in zip(axes, PANELS):
        data = RESULTS[panel["key"]]["variants"]
        xs = list(range(len(panel["bars"])))
        width = 0.5
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
        ax.set_xlim(-0.6, len(xs) - 0.4)
        ax.set_title(f"{panel['title']}\n{panel['subtitle']}", fontsize=11.5,
                      fontweight="bold", color=TEXT_PRIMARY, loc="left")
        ax.set_ylabel(panel["ylabel"], fontsize=9, color=TEXT_SECONDARY)
        style_axes(ax)

    fig.suptitle(
        "Mojo vs. Python vs. NumPy — mean wall-clock time, lower is better",
        fontsize=15, fontweight="bold", color=TEXT_PRIMARY, x=0.015, y=0.97, ha="left",
    )
    fig.legend(
        handles=LEGEND_HANDLES, loc="upper center", bbox_to_anchor=(0.5, 0.90),
        ncol=3, frameon=False, fontsize=9.5,
    )
    fig.savefig(OUT / "chart_absolute.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def make_speedup_chart():
    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    fig.subplots_adjust(top=0.80, bottom=0.12, left=0.11, right=0.97)
    group_gap = 1.0
    bar_width = 0.24
    centers = []
    labels = []

    for gi, panel in enumerate(PANELS):
        data = RESULTS[panel["key"]]["variants"]
        means = {key: data[key]["mean"] for _, key, _ in panel["bars"]}
        fastest = min(means.values())
        base_x = gi * group_gap
        for bi, (label, key, color) in enumerate(panel["bars"]):
            ratio = means[key] / fastest
            x = base_x + (bi - 1) * (bar_width + 0.03)
            rounded_bar(ax, x, ratio, bar_width, color)
            tag = "1.0x\n(fastest)" if abs(ratio - 1.0) < 1e-9 else f"{ratio:.1f}x"
            ax.text(x, ratio * 1.1, tag, ha="center", va="bottom",
                     fontsize=8.7, color=TEXT_PRIMARY, linespacing=1.3)
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
        "Same three categories, indexed to a common base — who wins each one",
        fontsize=14.5, fontweight="bold", color=TEXT_PRIMARY, x=0.015, y=0.97, ha="left",
    )
    fig.legend(
        handles=LEGEND_HANDLES, loc="upper center", bbox_to_anchor=(0.5, 0.89),
        ncol=3, frameon=False, fontsize=9.5,
    )
    fig.savefig(OUT / "chart_speedup.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    make_absolute_chart()
    make_speedup_chart()
    print(f"Wrote {OUT / 'chart_absolute.png'}")
    print(f"Wrote {OUT / 'chart_speedup.png'}")
