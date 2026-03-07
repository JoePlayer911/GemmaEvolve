#!/bin/bash
# 1-click Completion Benchmark (Multi-Checkpoint)
# Compares Native Gemma vs OpenEvolve at 100-iteration checkpoints (100-800).
# Only runs OpenEvolve when Gemma's score < 1.0. Skips problems with errors.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "  Completion Benchmark (Multi-Checkpoint)"
echo "  Native Gemma vs OpenEvolve @100-800"
echo "========================================"
echo ""

# Activate virtual environment
source ./venv/bin/activate

# Check if arguments are provided, otherwise use defaults
if [ $# -eq 0 ]; then
    echo "Using default settings (All problems, 800 iterations, checkpoints every 100)."
    echo "Customize: ./run_completion_benchmark.sh --limit 5 --jumpstart --fill-gaps"
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
