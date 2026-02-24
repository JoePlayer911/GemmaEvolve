#!/bin/bash

# Run the OpenEvolve Benchmark with the local Gemma model

echo "========================================"
echo "OpenEvolve Benchmark Run"
echo "========================================"
echo "Starting the benchmark process..."
echo

# Source the virtual environment to ensure LD_LIBRARY_PATH and Python are set correctly
source ./venv/bin/activate

# Check if arguments are provided, otherwise use defaults
if [ $# -eq 0 ]; then
    echo "Using default settings (Limit: All, Patience: 30)."
    echo "You can pass custom arguments like this: ./run_benchmark.sh --limit 5 --patience 10"
    python3 benchmark_verilog.py
else
    echo "Running benchmark with arguments: $@"
    python3 benchmark_verilog.py "$@"
fi

# Deactivate virtual environment after completion
deactivate

echo
echo "========================================"
echo "Benchmark complete!"
echo "Check benchmark_results.json for details."
echo "========================================"
echo
