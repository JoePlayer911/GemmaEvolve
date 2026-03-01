#!/bin/bash
# 1-click Completion Benchmark
# Compares whether OpenEvolve can solve problems that native Gemma cannot.
# Only runs OpenEvolve when Gemma's score < 1.0 (patience=300).

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "  Completion Benchmark"
echo "  OpenEvolve vs Native Gemma"
echo "========================================"
echo ""

# Activate virtual environment
source ./venv/bin/activate

# Check if arguments are provided, otherwise use defaults
if [ $# -eq 0 ]; then
    echo "Using default settings (All problems, Iteration Limit: 300, Patience: 100)."
    echo "Customize: ./run_completion_benchmark.sh --limit 5 --max-iterations 300 --patience 100 --jumpstart"
    echo ""
    python3 run_completion_benchmark.py
else
    echo "Running with arguments: $@"
    echo ""
    python3 run_completion_benchmark.py "$@"
fi

deactivate

echo ""
echo "========================================"
echo "  Benchmark complete!"
echo "  Results: completion_benchmark.json"
echo "========================================"
