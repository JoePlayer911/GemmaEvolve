#!/bin/bash
# 1-click benchmark chart generator
# Converts benchmark_results.json into a visual chart

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Benchmark Results Chart Generator ==="
echo ""

# Check for benchmark_results.json
if [ ! -f "benchmark_results.json" ]; then
    echo "Error: benchmark_results.json not found in $SCRIPT_DIR"
    exit 1
fi

# Check matplotlib is available, install if needed
python3 -c "import matplotlib" 2>/dev/null || {
    echo "Installing matplotlib..."
    pip install matplotlib --quiet --break-system-packages
}

echo "Generating chart from benchmark_results.json..."
python3 benchmark_results_chart.py

echo ""
echo "Done! Open benchmark_results_chart.png to view."
