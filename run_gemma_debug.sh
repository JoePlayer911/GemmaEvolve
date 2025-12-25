#!/bin/bash

# Run OpenEvolve function minimization with local Gemma model (DEBUG MODE)
# Shows detailed logging for tracking progress

echo "========================================"
echo "OpenEvolve with Local Gemma (DEBUG)"
echo "========================================"
echo "Starting evolution with detailed debug logging..."
echo

# Run with DEBUG log level
./venv/bin/python3 -m openevolve.cli \
  examples/function_minimization/initial_program.py \
  examples/function_minimization/evaluator.py \
  --config examples/function_minimization/gemma_config.yaml \
  --iterations 50 \
  --log-level DEBUG

echo
echo "========================================"
echo "Run complete!"
echo "========================================"
echo "Check examples/function_minimization/openevolve_output for results:"
echo " - logs/        - Detailed execution logs"
echo " - best/        - Best solution found"
echo " - checkpoints/ - Intermediate checkpoints"
echo
