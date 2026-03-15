#!/bin/bash
# Generate the benchmark results chart

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

echo "Generating completion benchmark chart..."
python3 "${SCRIPT_DIR}/completion_benchmark_results_chart.py"
echo "Done."
