#!/usr/bin/env python3
"""
Benchmark Results Chart Generator
Converts completion_benchmark.json into publication-quality charts:
  Panel 1 – Bar chart: Distribution of iterations required to solve problems
  Panel 2 – Line chart: OpenEvolve cumulative solved progression (iter_100 … iter_800)
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

    # ===== Panel 1: Number of Iterations Required per Solved Problem =====
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor(COLOR_PANEL)

    # Collect data specifically for the chart
    oe_solved_probs = []
    
    unsolved_count = 0
    gemma_zero_count = 0
    
    for d in data:
        if d.get("gemma_solved"):
            gemma_zero_count += 1
        elif d.get("openevolve_solved"):
            prob = d["problem"]
            oe = d.get("openevolve")
            iters = oe.get("solved_iteration", 800) if isinstance(oe, dict) else 800
            
            # Formatting the problem name string to fit nicely (removing "Prob0xx_")
            prob_short = prob.split('_', 1)[1] if '_' in prob else prob
            oe_solved_probs.append((prob_short, iters))
        else:
            unsolved_count += 1

    # Sort array by iteration count (ascending), so that lower iterations appear lower on the Y-axis
    oe_solved_probs.sort(key=lambda x: x[1])
    
    probs = [x[0] for x in oe_solved_probs]
    iters = [x[1] for x in oe_solved_probs]
    
    y_pos = np.arange(len(probs))
    
    # Color the bars depending on their iteration count
    bar_colors = []
    for count in iters:
        if count <= 10: bar_colors.append("#2ECC71")        # Green (fast)
        elif count <= 100: bar_colors.append("#1ABC9C")     # Teal
        elif count <= 300: bar_colors.append("#F1C40F")     # Yellow
        elif count <= 600: bar_colors.append("#E67E22")     # Orange
        else: bar_colors.append(COLOR_EVOLVE)               # Red/Coral (slow/hardest)

    bars = ax1.barh(y_pos, iters, color=bar_colors, zorder=3, alpha=0.9, height=0.6)
    
    # Add numbers to the end of bars
    for i, count in enumerate(iters):
        ax1.annotate(f" {count}", xy=(count, y_pos[i]), va='center', ha='left',
                     fontsize=9, color='white', fontweight='bold')
                     
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(probs, fontsize=9, color=COLOR_TEXT)
    ax1.set_xlabel("Iterations Required for OpenEvolve to Solve", fontsize=11, color=COLOR_TEXT)
    
    # Also add a nice little legend/summary overlay explicitly highlighting what is NOT mapped here
    ax1.set_title("Hardest Problems: Iterations to Solve",
                  fontsize=13, fontweight='bold', color='white', pad=10)
    
    ax1.annotate(f"Problems omitted from left panel:\n"
                 f" • Solved immediately by Gemma (0 iters): {gemma_zero_count}\n"
                 f" • Unsolved by OpenEvolve after 800 iters: {unsolved_count}",
                 xy=(0.95, 0.05), xycoords='axes fraction', ha='right', va='bottom',
                 fontsize=9, color=COLOR_TEXT, bbox=dict(boxstyle="round,pad=0.5", facecolor=COLOR_BG, alpha=0.8, edgecolor=COLOR_GRID))

    ax1.set_xlim(0, max(iters) * 1.15 if iters else 800)
    ax1.grid(axis='x', color=COLOR_GRID, linestyle='--', alpha=0.5, zorder=0)
    ax1.tick_params(colors=COLOR_TEXT)

    # ===== Panel 2: Cumulative problems solved by iteration =====
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_facecolor(COLOR_PANEL)

    # Count how many problems are solved (accuracy >= 1.0) at each iteration checkpoint
    iter_nums = [0] + [int(k.replace("iter_", "")) for k in ITER_KEYS]
    cum_solved_by_iter = [b_solved]
    for key in ITER_KEYS:
        solved_count = 0
        for d in data:
            oe = d.get("openevolve")
            if oe == "skipped" or oe is None:
                # Use baseline accuracy for problems that didn't run OpenEvolve
                if d["baseline"]["accuracy"] >= 1.0:
                    solved_count += 1
            else:
                if key in oe and oe[key]["accuracy"] >= 1.0:
                    solved_count += 1
        cum_solved_by_iter.append(solved_count)

    ix = np.arange(len(iter_nums))
    ax2.plot(ix, cum_solved_by_iter,
             color=COLOR_EVOLVE, linewidth=2.5, marker='o', markersize=6,
             markerfacecolor='white', markeredgecolor=COLOR_EVOLVE, markeredgewidth=2,
             zorder=5, label='OpenEvolve')

    # Horizontal line for Native Gemma's total solved problems
    ax2.axhline(y=b_solved, color=COLOR_BASELINE, linestyle='--',
                linewidth=2.0, alpha=0.9, label=f'Baseline ({b_solved} solved)')

    # Annotate first and last points
    ax2.annotate(f'{cum_solved_by_iter[0]}', (ix[0], cum_solved_by_iter[0]),
                 textcoords="offset points", xytext=(0, 12), ha='center',
                 fontsize=9, color=COLOR_TEXT, fontweight='bold')
    ax2.annotate(f'{cum_solved_by_iter[-1]}', (ix[-1], cum_solved_by_iter[-1]),
                 textcoords="offset points", xytext=(0, 12), ha='center',
                 fontsize=9, color=COLOR_TEXT, fontweight='bold')

    ax2.set_ylim(0, 156)
    ax2.set_xticks(ix)
    ax2.set_xticklabels([str(i) for i in iter_nums], fontsize=9, color=COLOR_TEXT, rotation=45)
    ax2.set_xlabel("Number of Iterations", fontsize=11, color=COLOR_TEXT)
    ax2.set_ylabel("Cumulative Problems Solved", fontsize=11, color=COLOR_TEXT)
    ax2.set_title(f"Problems Solved by Iteration\n({n} total problems)",
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
