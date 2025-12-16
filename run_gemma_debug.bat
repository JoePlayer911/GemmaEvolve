@echo off
REM Run OpenEvolve function minimization with local Gemma model (DEBUG MODE)
REM Shows detailed logging for tracking progress

echo ========================================
echo OpenEvolve with Local Gemma (DEBUG)
echo ========================================
echo Starting evolution with detailed debug logging...
echo.

REM Run with DEBUG log level
e:\Project\AI\GemmaEvolve\venv\Scripts\python.exe -m openevolve.cli ^
  examples/function_minimization/initial_program.py ^
  examples/function_minimization/evaluator.py ^
  --config examples/function_minimization/gemma_config.yaml ^
  --iterations 50 ^
  --log-level DEBUG

echo.
echo ========================================
echo Run complete!
echo ========================================
echo Check examples/function_minimization/openevolve_output for results:
echo  - logs/        - Detailed execution logs
echo  - best/        - Best solution found
echo  - checkpoints/ - Intermediate checkpoints
echo.
pause
