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
  examples/circle_packing/initial_program.py \
  examples/circle_packing/evaluator.py \
  --config examples/circle_packing/gemma_config.yaml \
  --iterations 50 \
  --log-level DEBUG \
  --checkpoint examples/circle_packing/openevolve_output/checkpoints/checkpoint_50

echo
echo "========================================"
echo "Run complete!"
echo "========================================"
echo "Check examples/circle_packing/openevolve_output for results:"
echo " - logs/        - Detailed execution logs"
echo " - best/        - Best solution found"
echo " - checkpoints/ - Intermediate checkpoints"
echo
