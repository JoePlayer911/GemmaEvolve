#!/usr/bin/env python3
"""
Benchmark Results Chart Generator
Converts completion_benchmark.json into a clear, publication-quality chart
comparing Pure Gemma Baseline vs OpenEvolve performance.
Displays simple aggregated charts and numerical data as there are many problems.
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

    problems   = [d["problem"] for d in data]
    b_scores   = []
    e_scores   = []
    b_acc      = []
    e_acc      = []
    
    b_solved   = 0
    e_solved   = 0

    for d in data:
        b = d["baseline"]
        b_scores.append(b["score"])
        b_acc.append(b["accuracy"])
        if b["accuracy"] >= 1.0:
            b_solved += 1
            
        e = d.get("openevolve")
        if e == "skipped":
            e_scores.append(b["score"])
            e_acc.append(b["accuracy"])
            if b["accuracy"] >= 1.0:
                e_solved += 1
        else:
            e_scores.append(e["score"])
            e_acc.append(e["accuracy"])
            if e["accuracy"] >= 1.0:
                e_solved += 1

    # --- Derived stats ---
    score_wins = sum(1 for b, e in zip(b_scores, e_scores) if e > b)
    score_ties = sum(1 for b, e in zip(b_scores, e_scores) if abs(e - b) < 1e-6)
    score_losses = n - score_wins - score_ties
    avg_b_score = np.mean(b_scores)
    avg_e_score = np.mean(e_scores)
    avg_b_acc   = np.mean(b_acc) * 100
    avg_e_acc   = np.mean(e_acc) * 100
    b_pass_rate = (b_solved / n) * 100 if n > 0 else 0
    e_pass_rate = (e_solved / n) * 100 if n > 0 else 0

    # --- Setup figure ---
    plt.style.use('dark_background')
    fig = plt.figure(figsize=(14, 8), facecolor=COLOR_BG)
    fig.suptitle("GemmaEvolve Completion Benchmark Results",
                 fontsize=22, fontweight='bold', color='white', y=0.96)
    fig.text(0.5, 0.91,
             f"Pure Gemma Baseline vs OpenEvolve  •  {n} Problems",
             ha='center', fontsize=12, color=COLOR_TEXT, alpha=0.7)

    gs = gridspec.GridSpec(1, 3, hspace=0.3, wspace=0.3,
                           left=0.05, right=0.95, top=0.82, bottom=0.1)

    # ===== Panel 1: Overall Pass Rate & Average Accuracy (Bar Chart) =====
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor(COLOR_PANEL)
    
    metrics = ["Pass Rate (%)", "Average Accuracy (%)"]
    b_vals = [b_pass_rate, avg_b_acc]
    e_vals = [e_pass_rate, avg_e_acc]
    
    x = np.arange(len(metrics))
    bar_w = 0.35
    
    bars_b = ax1.bar(x - bar_w/2, b_vals, bar_w, label='Baseline',
                     color=COLOR_BASELINE, edgecolor='white', linewidth=0.5, alpha=0.9, zorder=3)
    bars_e = ax1.bar(x + bar_w/2, e_vals, bar_w, label='OpenEvolve',
                     color=COLOR_EVOLVE, edgecolor='white', linewidth=0.5, alpha=0.9, zorder=3)

    for bar in bars_b:
        h = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2, h + 1, f'{h:.1f}%',
                 ha='center', va='bottom', fontsize=9, color=COLOR_TEXT, fontweight='bold')
    for bar in bars_e:
        h = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2, h + 1, f'{h:.1f}%',
                 ha='center', va='bottom', fontsize=9, color=COLOR_TEXT, fontweight='bold')

    ax1.set_title("Performance Overview", fontsize=14, fontweight='bold', color='white', pad=10)
    ax1.set_xticks(x)
    ax1.set_xticklabels(metrics, fontsize=10, color=COLOR_TEXT, fontweight='bold')
    ax1.set_ylim(0, max(max(b_vals), max(e_vals)) * 1.2)
    if ax1.get_ylim()[1] > 115:
        ax1.set_ylim(0, 115)
    ax1.legend(fontsize=9, loc='upper left', framealpha=0.3)
    ax1.grid(axis='y', color=COLOR_GRID, linestyle='--', alpha=0.5, zorder=0)
    ax1.tick_params(colors=COLOR_TEXT)

    # ===== Panel 2: Win/Tie/Loss Donut =====
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_facecolor(COLOR_PANEL)
    sizes = [score_wins, score_ties, score_losses]
    colors_pie = [COLOR_WIN, COLOR_TIE, COLOR_LOSE]
    pie_labels = [f"OE Win ({score_wins})", f"Tie ({score_ties})", f"OE Loss ({score_losses})"]

    filtered = [(s, c, l) for s, c, l in zip(sizes, colors_pie, pie_labels) if s > 0]
    if filtered:
        f_sizes, f_colors, f_labels = zip(*filtered)
    else:
        f_sizes, f_colors, f_labels = [1], ['gray'], ['No data']

    wedges, texts, autotexts = ax2.pie(
        f_sizes, labels=f_labels, colors=f_colors, autopct='%1.0f%%',
        startangle=90, pctdistance=0.75, wedgeprops=dict(width=0.4, edgecolor=COLOR_BG, linewidth=2),
        textprops=dict(color=COLOR_TEXT, fontsize=10))
    for at in autotexts:
        at.set_fontweight('bold')
        at.set_fontsize(11)
    ax2.set_title("OpenEvolve vs Baseline\n(Head-to-head Problem Score)", fontsize=13, fontweight='bold', color='white', pad=10)

    # ===== Panel 3: Summary Stats Table =====
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.set_facecolor(COLOR_BG) # blending with background
    ax3.axis('off')

    table_data = [
        ["Metric",          "Baseline",             "OpenEvolve"],
        ["Problems Solved", f"{b_solved} / {n}",    f"{e_solved} / {n}"],
        ["Pass Rate",       f"{b_pass_rate:.1f}%",  f"{e_pass_rate:.1f}%"],
        ["Avg Accuracy",    f"{avg_b_acc:.1f}%",    f"{avg_e_acc:.1f}%"],
        ["Avg Score",       f"{avg_b_score:.4f}",   f"{avg_e_score:.4f}"],
        ["Head-to-head",    "—",                    f"{score_wins}W - {score_ties}T - {score_losses}L"],
    ]

    table = ax3.table(
        cellText=table_data,
        cellLoc='center',
        loc='center',
        bbox=[0.0, 0.1, 1.0, 0.8]
    )
    table.auto_set_font_size(False)
    table.set_fontsize(11)

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
        cell.set_height(0.15)

    # Save
    plt.savefig(output_path, dpi=DPI, facecolor=COLOR_BG, bbox_inches='tight')
    print(f"✅ Chart saved to: {output_path}")
    print(f"   Resolution: {DPI} DPI")
    print(f"   Problems: {n}")
    print(f"   Problems Solved — Baseline: {b_solved}  |  OpenEvolve: {e_solved}")
    print(f"   Pass Rate — Baseline: {b_pass_rate:.1f}%  |  OpenEvolve: {e_pass_rate:.1f}%")
    print(f"   Avg Score — Baseline: {avg_b_score:.4f}  |  OpenEvolve: {avg_e_score:.4f}")
    print(f"   Score W/T/L: {score_wins}/{score_ties}/{score_losses}")


if __name__ == "__main__":
    main()
