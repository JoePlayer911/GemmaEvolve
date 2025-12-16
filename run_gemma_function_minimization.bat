@echo off
REM Run OpenEvolve function minimization with local Gemma model
REM Equivalent to the WSL command but for Windows

e:\Project\AI\GemmaEvolve\venv\Scripts\python.exe -m openevolve.cli ^
  examples/function_minimization/initial_program.py ^
  examples/function_minimization/evaluator.py ^
  --config examples/function_minimization/gemma_config.yaml ^
  --iterations 50

echo.
echo Run complete! Check examples/function_minimization/openevolve_output for results.
pause
