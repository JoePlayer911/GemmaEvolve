#!/usr/bin/env python3
"""
Benchmark Results Chart Generator
Converts completion_benchmark.json into publication-quality charts:
  Panel 1 – Line chart: Native Gemma accuracy vs OpenEvolve iter_800 accuracy per problem
  Panel 2 – Line chart: OpenEvolve accuracy progression (iter_100 … iter_800) averaged across problems
  Panel 3 – Summary metrics table
"""

import json
import sys
import os
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

# --- Configuration ---
INPUT_FILE = "completion_benchmark.json"
OUTPUT_FILE = "completion_benchmark_results_chart.png"
DPI = 150

# Color palette
COLOR_BASELINE = "#4A90D9"   # Steel blue
COLOR_EVOLVE   = "#E8573A"   # Vibrant coral
COLOR_BG       = "#1A1A2E"   # Dark navy
COLOR_PANEL    = "#16213E"   # Slightly lighter panel
COLOR_TEXT     = "#E0E0E0"   # Light grey text
COLOR_GRID     = "#2A2A4A"   # Subtle grid
COLOR_ACCENT   = "#0F3460"   # Accent
COLOR_WIN      = "#2ECC71"   # Green for win
COLOR_TIE      = "#F39C12"   # Yellow for tie
COLOR_LOSE     = "#E74C3C"   # Red for lose

ITER_KEYS = [f"iter_{i}" for i in range(100, 900, 100)]  # iter_100 … iter_800


def load_data(path):
    with open(path, 'r') as f:
        return json.load(f)


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, INPUT_FILE)
    output_path = os.path.join(script_dir, OUTPUT_FILE)

    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        sys.exit(1)

    data = load_data(input_path)
    n = len(data)

    # --- Extract per-problem data ---
    problems     = [d["problem"] for d in data]
    b_acc        = [d["baseline"]["accuracy"] for d in data]

    # For iter_800 accuracy: use iter_800 if openevolve ran, else baseline accuracy
    e800_acc = []
    for d in data:
        oe = d.get("openevolve")
        if oe == "skipped":
            e800_acc.append(d["baseline"]["accuracy"])
        else:
            e800_acc.append(oe["iter_800"]["accuracy"])

    # --- Iteration progression (only for problems where openevolve actually ran) ---
    iter_labels = [str(i) for i in range(100, 900, 100)]
    # Collect per-iteration average accuracy across all problems that ran openevolve
    oe_problems = [d for d in data if d.get("openevolve") not in (None, "skipped")]
    iter_avg_acc = []
    for key in ITER_KEYS:
        accs = [d["openevolve"][key]["accuracy"] for d in oe_problems]
        iter_avg_acc.append(np.mean(accs) if accs else 0.0)

    # Baseline average for the same subset
    oe_baseline_avg = np.mean([d["baseline"]["accuracy"] for d in oe_problems]) if oe_problems else 0.0

    # --- Derived stats ---
    b_solved  = sum(1 for a in b_acc if a >= 1.0)
    e_solved  = sum(1 for a in e800_acc if a >= 1.0)
    avg_b_acc = np.mean(b_acc) * 100
    avg_e_acc = np.mean(e800_acc) * 100
    b_pass    = (b_solved / n) * 100 if n > 0 else 0
    e_pass    = (e_solved / n) * 100 if n > 0 else 0
    wins      = sum(1 for b, e in zip(b_acc, e800_acc) if e > b + 1e-6)
    ties      = sum(1 for b, e in zip(b_acc, e800_acc) if abs(e - b) < 1e-6)
    losses    = n - wins - ties

    # --- Setup figure ---
    plt.style.use('dark_background')
    fig = plt.figure(figsize=(20, 9), facecolor=COLOR_BG)
    fig.suptitle("GemmaEvolve Completion Benchmark Results",
                 fontsize=22, fontweight='bold', color='white', y=0.97)
    fig.text(0.5, 0.92,
             f"Pure Gemma Baseline vs OpenEvolve  •  {n} Problems  •  {len(oe_problems)} ran OpenEvolve",
             ha='center', fontsize=12, color=COLOR_TEXT, alpha=0.7)

    gs = gridspec.GridSpec(1, 3, width_ratios=[2, 1.3, 1.2],
                           hspace=0.3, wspace=0.35,
                           left=0.05, right=0.98, top=0.85, bottom=0.12)

    # ===== Panel 1: Cumulative problems solved =====
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor(COLOR_PANEL)

    x = np.arange(1, n + 1)  # 1-indexed: total problems attempted

    # Build cumulative solved for each model line
    # Native Gemma
    gemma_cum = np.cumsum([1 if a >= 1.0 else 0 for a in b_acc])
    ax1.plot(x, gemma_cum, color=COLOR_BASELINE, linewidth=2.0, alpha=0.9, label='Native Gemma')

    # OpenEvolve iterations (iter_100 through iter_800)
    iter_cmap = plt.cm.YlOrRd(np.linspace(0.25, 0.95, len(ITER_KEYS)))
    for idx, key in enumerate(ITER_KEYS):
        iter_acc = []
        for d in data:
            oe = d.get("openevolve")
            if oe == "skipped" or oe is None:
                # If openevolve didn't run, use baseline accuracy for this problem
                iter_acc.append(d["baseline"]["accuracy"])
            else:
                iter_acc.append(oe[key]["accuracy"])
        cum_solved = np.cumsum([1 if a >= 1.0 else 0 for a in iter_acc])
        label = key.replace("_", " ").title()
        ax1.plot(x, cum_solved, color=iter_cmap[idx], linewidth=1.4, alpha=0.85, label=label)

    ax1.set_xlabel("Total Problems Attempted", fontsize=11, color=COLOR_TEXT)
    ax1.set_ylabel("Number of Problems Solved", fontsize=11, color=COLOR_TEXT)
    ax1.set_title("Cumulative Problems Solved",
                  fontsize=13, fontweight='bold', color='white', pad=10)
    ax1.set_ylim(0, n + 2)
    ax1.legend(fontsize=8, loc='upper left', framealpha=0.4, ncol=2)
    ax1.grid(axis='y', color=COLOR_GRID, linestyle='--', alpha=0.5, zorder=0)
    ax1.tick_params(colors=COLOR_TEXT)

    # ===== Panel 2: Line chart – Accuracy progression iter 100-800 =====
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_facecolor(COLOR_PANEL)

    ix = np.arange(len(iter_labels))
    ax2.plot(ix, [a * 100 for a in iter_avg_acc],
             color=COLOR_EVOLVE, linewidth=2.5, marker='o', markersize=6,
             markerfacecolor='white', markeredgecolor=COLOR_EVOLVE, markeredgewidth=2,
             zorder=5, label='Avg Accuracy (%)')
    ax2.axhline(y=oe_baseline_avg * 100, color=COLOR_BASELINE, linestyle='--',
                linewidth=1.5, alpha=0.8, label=f'Baseline avg ({oe_baseline_avg*100:.1f}%)')

    # Annotate first and last points
    ax2.annotate(f'{iter_avg_acc[0]*100:.1f}%', (ix[0], iter_avg_acc[0]*100),
                 textcoords="offset points", xytext=(0, 12), ha='center',
                 fontsize=9, color=COLOR_TEXT, fontweight='bold')
    ax2.annotate(f'{iter_avg_acc[-1]*100:.1f}%', (ix[-1], iter_avg_acc[-1]*100),
                 textcoords="offset points", xytext=(0, 12), ha='center',
                 fontsize=9, color=COLOR_TEXT, fontweight='bold')

    ax2.set_xticks(ix)
    ax2.set_xticklabels(iter_labels, fontsize=9, color=COLOR_TEXT, rotation=45)
    ax2.set_xlabel("Iteration Checkpoint", fontsize=11, color=COLOR_TEXT)
    ax2.set_ylabel("Avg Accuracy (%)", fontsize=11, color=COLOR_TEXT)
    ax2.set_title(f"OpenEvolve Accuracy Progression\n({len(oe_problems)} problems that ran OE)",
                  fontsize=13, fontweight='bold', color='white', pad=10)
    ax2.legend(fontsize=9, loc='lower right', framealpha=0.4)
    ax2.grid(axis='y', color=COLOR_GRID, linestyle='--', alpha=0.5, zorder=0)
    ax2.tick_params(colors=COLOR_TEXT)

    # ===== Panel 3: Summary Metrics Table =====
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.set_facecolor(COLOR_BG)
    ax3.axis('off')

    table_data = [
        ["Metric",      "Baseline",           "OpenEvolve"],
        ["Solved",      f"{b_solved}/{n}",     f"{e_solved}/{n}"],
        ["Pass Rate",   f"{b_pass:.1f}%",      f"{e_pass:.1f}%"],
        ["Avg Acc",     f"{avg_b_acc:.1f}%",   f"{avg_e_acc:.1f}%"],
        ["W / T / L",   "—",                   f"{wins}/{ties}/{losses}"],
        ["OE Runs",     "—",                   f"{len(oe_problems)}"],
    ]

    table = ax3.table(
        cellText=table_data,
        cellLoc='center',
        loc='center',
        bbox=[0.0, 0.15, 1.0, 0.75]
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)

    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor(COLOR_GRID)
        cell.set_linewidth(1.0)
        if row == 0:
            cell.set_facecolor(COLOR_ACCENT)
            cell.set_text_props(color='white', fontweight='bold', fontsize=12)
        else:
            cell.set_facecolor(COLOR_PANEL)
            cell.set_text_props(color=COLOR_TEXT)
            if col == 0:
                cell.set_text_props(color=COLOR_TEXT, fontweight='bold')
        cell.set_height(0.14)

    ax3.set_title("Summary Metrics", fontsize=14, fontweight='bold', color='white', pad=10)

    # Save
    plt.savefig(output_path, dpi=DPI, facecolor=COLOR_BG, bbox_inches='tight')
    print(f"✅ Chart saved to: {output_path}")
    print(f"   Resolution: {DPI} DPI")
    print(f"   Total problems: {n}")
    print(f"   Problems that ran OpenEvolve: {len(oe_problems)}")
    print(f"   Problems Solved — Baseline: {b_solved}  |  OpenEvolve: {e_solved}")
    print(f"   Pass Rate — Baseline: {b_pass:.1f}%  |  OpenEvolve: {e_pass:.1f}%")
    print(f"   Avg Accuracy — Baseline: {avg_b_acc:.1f}%  |  OpenEvolve: {avg_e_acc:.1f}%")
    print(f"   Head-to-head W/T/L: {wins}/{ties}/{losses}")


if __name__ == "__main__":
    main()
