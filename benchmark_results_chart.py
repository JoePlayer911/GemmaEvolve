#!/usr/bin/env python3
"""
Benchmark Results Chart Generator
Converts benchmark_results.json into a clear, publication-quality chart
comparing Pure Gemma Baseline vs OpenEvolve performance.
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
INPUT_FILE = "benchmark_results.json"
OUTPUT_FILE = "benchmark_results_chart.png"
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


def load_data(path):
    with open(path, 'r') as f:
        return json.load(f)


def shorten_name(name):
    """Shorten problem names for chart labels."""
    return name.replace("Prob", "P").replace("_", "\n", 1).replace("_", " ")


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, INPUT_FILE)
    output_path = os.path.join(script_dir, OUTPUT_FILE)

    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        sys.exit(1)

    data = load_data(input_path)
    n = len(data)

    problems   = [d["problem"] for d in data]
    labels     = [shorten_name(p) for p in problems]
    b_scores   = [d["baseline"]["score"] for d in data]
    e_scores   = [d["openevolve"]["score"] for d in data]
    b_acc      = [d["baseline"]["accuracy"] for d in data]
    e_acc      = [d["openevolve"]["accuracy"] for d in data]
    b_time     = [d["baseline"]["time"] for d in data]
    e_time     = [d["openevolve"]["time"] for d in data]

    # --- Derived stats ---
    score_wins = sum(1 for b, e in zip(b_scores, e_scores) if e > b)
    score_ties = sum(1 for b, e in zip(b_scores, e_scores) if abs(e - b) < 1e-6)
    score_losses = n - score_wins - score_ties
    avg_b_score = np.mean(b_scores)
    avg_e_score = np.mean(e_scores)
    avg_b_time  = np.mean(b_time)
    avg_e_time  = np.mean(e_time)
    avg_b_acc   = np.mean(b_acc) * 100
    avg_e_acc   = np.mean(e_acc) * 100

    # --- Setup figure ---
    plt.style.use('dark_background')
    fig = plt.figure(figsize=(16, 10), facecolor=COLOR_BG)
    fig.suptitle("GemmaEvolve Benchmark Results",
                 fontsize=22, fontweight='bold', color='white', y=0.97)
    fig.text(0.5, 0.935,
             f"Pure Gemma Baseline vs OpenEvolve  •  {n} Problems",
             ha='center', fontsize=12, color=COLOR_TEXT, alpha=0.7)

    gs = gridspec.GridSpec(2, 3, hspace=0.42, wspace=0.35,
                           left=0.07, right=0.95, top=0.89, bottom=0.08)

    x = np.arange(n)
    bar_w = 0.35

    # ===== Panel 1: Score Comparison =====
    ax1 = fig.add_subplot(gs[0, 0:2])
    ax1.set_facecolor(COLOR_PANEL)
    bars_b = ax1.bar(x - bar_w/2, b_scores, bar_w, label='Baseline (Pure Gemma)',
                     color=COLOR_BASELINE, edgecolor='white', linewidth=0.5, alpha=0.9, zorder=3)
    bars_e = ax1.bar(x + bar_w/2, e_scores, bar_w, label='OpenEvolve',
                     color=COLOR_EVOLVE, edgecolor='white', linewidth=0.5, alpha=0.9, zorder=3)

    # Value labels on bars
    for bar in bars_b:
        h = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2, h + 0.02, f'{h:.3f}',
                 ha='center', va='bottom', fontsize=7, color=COLOR_TEXT, fontweight='bold')
    for bar in bars_e:
        h = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2, h + 0.02, f'{h:.3f}',
                 ha='center', va='bottom', fontsize=7, color=COLOR_TEXT, fontweight='bold')

    ax1.set_title("Score Comparison", fontsize=14, fontweight='bold', color='white', pad=10)
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontsize=8, color=COLOR_TEXT)
    ax1.set_ylabel("Score", fontsize=10, color=COLOR_TEXT)
    ax1.set_ylim(0, max(max(b_scores), max(e_scores)) * 1.2)
    ax1.legend(fontsize=9, loc='upper right', framealpha=0.3)
    ax1.grid(axis='y', color=COLOR_GRID, linestyle='--', alpha=0.5, zorder=0)
    ax1.tick_params(colors=COLOR_TEXT)

    # ===== Panel 2: Win/Tie/Loss Donut =====
    ax2 = fig.add_subplot(gs[0, 2])
    ax2.set_facecolor(COLOR_PANEL)
    sizes = [score_wins, score_ties, score_losses]
    colors_pie = [COLOR_WIN, COLOR_TIE, COLOR_LOSE]
    pie_labels = [f"Win ({score_wins})", f"Tie ({score_ties})", f"Loss ({score_losses})"]

    # Filter out zero slices
    filtered = [(s, c, l) for s, c, l in zip(sizes, colors_pie, pie_labels) if s > 0]
    if filtered:
        f_sizes, f_colors, f_labels = zip(*filtered)
    else:
        f_sizes, f_colors, f_labels = [1], ['gray'], ['No data']

    wedges, texts, autotexts = ax2.pie(
        f_sizes, labels=f_labels, colors=f_colors, autopct='%1.0f%%',
        startangle=90, pctdistance=0.75, wedgeprops=dict(width=0.4, edgecolor=COLOR_BG, linewidth=2),
        textprops=dict(color=COLOR_TEXT, fontsize=9))
    for at in autotexts:
        at.set_fontweight('bold')
        at.set_fontsize(10)
    ax2.set_title("OpenEvolve vs Baseline\n(Score)", fontsize=12, fontweight='bold', color='white', pad=10)

    # ===== Panel 3: Accuracy Comparison =====
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.set_facecolor(COLOR_PANEL)
    b_acc_pct = [a * 100 for a in b_acc]
    e_acc_pct = [a * 100 for a in e_acc]

    bars_ba = ax3.bar(x - bar_w/2, b_acc_pct, bar_w, label='Baseline',
                      color=COLOR_BASELINE, edgecolor='white', linewidth=0.5, alpha=0.9, zorder=3)
    bars_ea = ax3.bar(x + bar_w/2, e_acc_pct, bar_w, label='OpenEvolve',
                      color=COLOR_EVOLVE, edgecolor='white', linewidth=0.5, alpha=0.9, zorder=3)

    for bar in bars_ba:
        h = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2, h + 1, f'{h:.0f}%',
                 ha='center', va='bottom', fontsize=7, color=COLOR_TEXT, fontweight='bold')
    for bar in bars_ea:
        h = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2, h + 1, f'{h:.0f}%',
                 ha='center', va='bottom', fontsize=7, color=COLOR_TEXT, fontweight='bold')

    ax3.set_title("Accuracy (%)", fontsize=14, fontweight='bold', color='white', pad=10)
    ax3.set_xticks(x)
    ax3.set_xticklabels(labels, fontsize=8, color=COLOR_TEXT)
    ax3.set_ylabel("Accuracy %", fontsize=10, color=COLOR_TEXT)
    ax3.set_ylim(0, 120)
    ax3.legend(fontsize=8, loc='upper right', framealpha=0.3)
    ax3.grid(axis='y', color=COLOR_GRID, linestyle='--', alpha=0.5, zorder=0)
    ax3.tick_params(colors=COLOR_TEXT)

    # ===== Panel 4: Time Comparison =====
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.set_facecolor(COLOR_PANEL)

    bars_bt = ax4.bar(x - bar_w/2, b_time, bar_w, label='Baseline',
                      color=COLOR_BASELINE, edgecolor='white', linewidth=0.5, alpha=0.9, zorder=3)
    bars_et = ax4.bar(x + bar_w/2, e_time, bar_w, label='OpenEvolve',
                      color=COLOR_EVOLVE, edgecolor='white', linewidth=0.5, alpha=0.9, zorder=3)

    for bar in bars_bt:
        h = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2, h + 1, f'{h:.1f}s',
                 ha='center', va='bottom', fontsize=7, color=COLOR_TEXT, fontweight='bold')
    for bar in bars_et:
        h = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2, h + 1, f'{h:.1f}s',
                 ha='center', va='bottom', fontsize=7, color=COLOR_TEXT, fontweight='bold')

    ax4.set_title("Execution Time (seconds)", fontsize=14, fontweight='bold', color='white', pad=10)
    ax4.set_xticks(x)
    ax4.set_xticklabels(labels, fontsize=8, color=COLOR_TEXT)
    ax4.set_ylabel("Time (s)", fontsize=10, color=COLOR_TEXT)
    ax4.legend(fontsize=8, loc='upper right', framealpha=0.3)
    ax4.grid(axis='y', color=COLOR_GRID, linestyle='--', alpha=0.5, zorder=0)
    ax4.tick_params(colors=COLOR_TEXT)

    # ===== Panel 5: Summary Stats Table =====
    ax5 = fig.add_subplot(gs[1, 2])
    ax5.set_facecolor(COLOR_PANEL)
    ax5.axis('off')
    ax5.set_title("Summary", fontsize=14, fontweight='bold', color='white', pad=10)

    table_data = [
        ["Metric",          "Baseline",             "OpenEvolve"],
        ["Avg Score",       f"{avg_b_score:.4f}",   f"{avg_e_score:.4f}"],
        ["Avg Accuracy",    f"{avg_b_acc:.1f}%",    f"{avg_e_acc:.1f}%"],
        ["Avg Time",        f"{avg_b_time:.1f}s",   f"{avg_e_time:.1f}s"],
        ["Problems",        f"{n}",                 f"{n}"],
        ["Score W/T/L",     "—",                    f"{score_wins}/{score_ties}/{score_losses}"],
    ]

    row_colors = [COLOR_ACCENT] + [COLOR_PANEL] * (len(table_data) - 1)
    table = ax5.table(
        cellText=table_data,
        cellLoc='center',
        loc='center',
        bbox=[0.0, 0.05, 1.0, 0.9]
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)

    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor(COLOR_GRID)
        cell.set_linewidth(0.5)
        if row == 0:
            cell.set_facecolor(COLOR_ACCENT)
            cell.set_text_props(color='white', fontweight='bold', fontsize=10)
        else:
            cell.set_facecolor(COLOR_PANEL)
            cell.set_text_props(color=COLOR_TEXT)
            if col == 0:
                cell.set_text_props(color=COLOR_TEXT, fontweight='bold')
        cell.set_height(0.15)

    # Save
    plt.savefig(output_path, dpi=DPI, facecolor=COLOR_BG, bbox_inches='tight')
    print(f"✅ Chart saved to: {output_path}")
    print(f"   Resolution: {DPI} DPI")
    print(f"   Problems: {n}")
    print(f"   Avg Score — Baseline: {avg_b_score:.4f}  |  OpenEvolve: {avg_e_score:.4f}")
    print(f"   Score W/T/L: {score_wins}/{score_ties}/{score_losses}")


if __name__ == "__main__":
    main()
