# How to Use Gemma with OpenEvolve

To run the full 50-iteration evolution (matching your original WSL command):

cd e:\Project\AI\GemmaEvolve
run_gemma_debug.bat
Or directly:

venv\Scripts\python.exe -m openevolve.cli examples/function_minimization/initial_program.py examples/function_minimization/evaluator.py --config examples/function_minimization/gemma_config.yaml --iterations 50 --log-level DEBUG
