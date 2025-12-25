#!/bin/bash

# Run OpenEvolve function minimization with local Gemma model

./venv/bin/python3 -m openevolve.cli \
  examples/function_minimization/initial_program.py \
  examples/function_minimization/evaluator.py \
  --config examples/function_minimization/gemma_config.yaml \
  --iterations 50

echo
echo "Run complete! Check examples/function_minimization/openevolve_output for results."
