import os
import subprocess
import re
import tempfile
import logging

logger = logging.getLogger(__name__)

import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module by running it through a simulation and analyzing the output.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary with keys: 'accuracy', 'line_count', 'combined_score', 'error'.
    """
    try:
        exec_name = "a.out"  # Temporary executable name
        candidate_file = "candidate.sv"
        ref_file = "testbench.sv"  # Assuming testbench.sv contains reference module

        with open(candidate_file, "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_cmd = f"iverilog -g2012 -o {exec_name} {candidate_file} {ref_file}"
        compile_result = subprocess.run(compile_cmd, shell=True, capture_output=True, text=True)

        if compile_result.returncode != 0:
            return {
                "accuracy": 0.0,
                "line_count": len(code.splitlines()),
                "combined_score": 0.0,
                "error": f"Compilation failed: {compile_result.stderr}"
            }

        # Run the simulation
        run_cmd = f"./{exec_name}"
        run_result = subprocess.run(run_cmd, shell=True, capture_output=True, text=True)

        output = run_result.stdout
        line_count = len(code.splitlines())

        # Check for explicit "FAIL"
        if "FAIL" in output:
            mismatches = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatches:
                errors = int(mismatches.group(1))
                clocks = int(mismatches.group(2))
                accuracy = 1.0 - (float(errors) / clocks) if clocks > 0 else 0.0
                return {
                    "accuracy": accuracy,
                    "line_count": line_count,
                    "combined_score": accuracy,
                    "error": None
                }
            else:
                return {
                    "accuracy": 0.0,
                    "line_count": line_count,
                    "combined_score": 0.0,
                    "error": None
                }

        # Check for explicit "PASS" or if no mismatches found
        if "PASS" in output:
            return {
                "accuracy": 1.0,
                "line_count": line_count,
                "combined_score": 1.0,
                "error": None
            }

        # Parse mismatch counts from the output
        mismatches = re.search(r"Mismatches: (\d+) in (\d+)", output)
        if mismatches:
            errors = int(mismatches.group(1))
            clocks = int(mismatches.group(2))
            accuracy = 1.0 - (float(errors) / clocks) if clocks > 0 else 0.0
            return {
                "accuracy": accuracy,
                "line_count": line_count,
                "combined_score": accuracy,
                "error": None
            }
        else:
            return {
                "accuracy": 1.0,
                "line_count": line_count,
                "combined_score": 1.0,
                "error": None
            }

    except Exception as e:
        return {
            "accuracy": 0.0,
            "line_count": len(code.splitlines()),
            "combined_score": 0.0,
            "error": str(e)
        }
    finally:
        # Clean up temporary files
        try:
            subprocess.run(f"rm {candidate_file}", shell=True, capture_output=True)
            subprocess.run(f"rm {exec_name}", shell=True, capture_output=True)
        except:
            pass  # Ignore errors during cleanup