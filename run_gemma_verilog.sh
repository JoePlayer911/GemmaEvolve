#!/bin/bash
# Run GemmaEvolve Verilog optimization example

cd "$(dirname "$0")"

# Default iterations
ITERATIONS=${1:-50}

echo "Starting Verilog optimization with $ITERATIONS iterations..."

./venv/bin/python3 -m openevolve.cli \
  examples/verilog_optimization/initial_program.v \
  examples/verilog_optimization/evaluator.py \
  --config examples/verilog_optimization/gemma_config.yaml \
  --iterations "$ITERATIONS" \
  --log-level INFO
