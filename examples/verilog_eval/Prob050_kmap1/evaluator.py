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
    Evaluates a Verilog module by running it through Iverilog and comparing its output
    to the testbench output.

    Args:
        code: The Verilog code of the module to evaluate.

    Returns:
        A dictionary with keys: 'accuracy', 'line_count', 'combined_score', 'error'.
    """
    exec_name = "a.out"  # Or any name you prefer
    try:
        # Write the candidate module to a temporary file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-o", exec_name, "candidate.sv", "testbench.sv", "ref.sv"],
            capture_output=True,
            text=True
        )

        if compile_result.returncode != 0:
            return {
                "accuracy": 0.0,
                "line_count": 0,
                "combined_score": 0.0,
                "error": compile_result.stderr
            }

        # Run the simulation
        sim_result = subprocess.run(
            [exec_name],
            capture_output=True,
            text=True
        )

        output = sim_result.stdout

        # Check for "FAIL"
        if "FAIL" in output:
            mismatches = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatches:
                errors = int(mismatches.group(1))
                clocks = int(mismatches.group(2))
                accuracy = 1.0 - (float(errors) / clocks) if clocks > 0 else 0.0
            else:
                accuracy = 0.0
        # Check for "PASS"
        elif "PASS" in output:
            accuracy = 1.0
        else:
            # Parse mismatch counts
            mismatches = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatches:
                errors = int(mismatches.group(1))
                clocks = int(mismatches.group(2))
                accuracy = 1.0 - (float(errors) / clocks) if clocks > 0 else 0.0
            else:
                accuracy = 1.0

        # Get line count of the candidate code
        line_count = len(code.splitlines())

        # Combined score (simple average of accuracy and line count)
        combined_score = (accuracy + line_count) / 2

        return {
            "accuracy": accuracy,
            "line_count": line_count,
            "combined_score": combined_score,
            "error": ""
        }

    except Exception as e:
        return {
            "accuracy": 0.0,
            "line_count": 0,
            "combined_score": 0.0,
            "error": str(e)
        }
    finally:
        # Clean up temporary files
        try:
            subprocess.run(["rm", "-f", "candidate.sv", exec_name], check=False)
        except:
            pass