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
    Evaluates a Verilog module by simulating it against a reference module.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary with keys:
            - accuracy: The accuracy of the module (float).
            - line_count: The number of lines in the module (int).
            - combined_score: A combined score based on accuracy and line count (float).
            - error: An error message if any occurred (str), otherwise None.
    """
    try:
        # Write the code to a temporary file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-o", "test_exec", "candidate.sv", "testbench.sv", "ref.sv"],
            capture_output=True,
            text=True
        )

        if compile_result.returncode != 0:
            return {
                "accuracy": 0.0,
                "line_count": len(code.splitlines()),
                "combined_score": 0.0,
                "error": compile_result.stderr
            }

        # Run the simulation
        simulation_result = subprocess.run(
            ["vvp", "test_exec"],
            capture_output=True,
            text=True
        )

        # Parse the simulation output
        output = simulation_result.stdout
        line_count = len(code.splitlines())
        accuracy = 1.0
        error = None

        if "FAIL" in output:
            accuracy = 0.0

        mismatches_pattern = r"Mismatches: (\d+) in (\d+)"
        mismatch_match = re.search(mismatches_pattern, output)
        if mismatch_match:
            mismatches = int(mismatch_match.group(1))
            total_samples = int(mismatch_match.group(2))
            accuracy = 1.0 - (float(mismatches) / total_samples)

        if "PASS" in output:
            accuracy = 1.0

        # Calculate combined score (higher accuracy and fewer lines is better)
        combined_score = accuracy * (1.0 / (1.0 + (line_count / 100.0)))  # Normalize line count

        return {
            "accuracy": accuracy,
            "line_count": line_count,
            "combined_score": combined_score,
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
            subprocess.run(["rm", "candidate.sv"], check=False)
            subprocess.run(["rm", "test_exec"], check=False)
        except:
            pass